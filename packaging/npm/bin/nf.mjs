#!/usr/bin/env node
// NinFenz npm 一键入口：探测 Python → 首次解包 payload → 原样转发给 NF CLI。
// 设计纪律：零安装脚本、零网络、零遥测；payload 带 sha256 清单，校验不过就拒绝启动。
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { PACKAGE_ROOT, findRepoRoot } from '../lib/paths.mjs';
import { readManifest, ensurePayload, materialize } from '../lib/payload.mjs';
import { findPython, MIN_PYTHON } from '../lib/python.mjs';

const pkg = JSON.parse(fs.readFileSync(path.join(PACKAGE_ROOT, 'package.json'), 'utf8'));

function usage() {
  const lines = [
    'NinFenz (NF) ' + pkg.version + ' - content contract layer for AI long-form output',
    '',
    '用法：',
    '  npx -y ninfenz <nf 子命令> [...]      在 payload 工作树里跑 NF CLI',
    '  npx -y ninfenz tui [--demo|--selftest]  打开 NF 终端 TUI（纯标准库）',
    '  npx -y ninfenz --repo <目录> <子命令>   在已有仓库检出上跑（跳过解包）',
    '  npx -y ninfenz install --dest <目录>    把 payload 落成一份真实工作树',
    '  npx -y ninfenz --version | --help',
    '',
    '环境变量：',
    '  NINFENZ_PYTHON  指定 Python 解释器（需 >= ' + MIN_PYTHON.join('.') + '）',
    '  NINFENZ_CACHE   指定解包缓存目录',
    ''
  ];
  return lines.join('\n');
}

function fail(msg, code) {
  process.stderr.write('✗ ' + msg + '\n');
  process.exit(code || 2);
}

function parse(argv) {
  const out = { repo: null, install: false, dest: null, force: false, rest: [] };
  let i = 0;
  while (i < argv.length) {
    const a = argv[i];
    if (a === '--') { out.rest = out.rest.concat(argv.slice(i + 1)); break; }
    if (a === '--repo') { out.repo = argv[i + 1]; i += 2; continue; }
    if (a === '--dest' && out.install) { out.dest = argv[i + 1]; i += 2; continue; }
    if (a === '--force' && out.install) { out.force = true; i += 1; continue; }
    if (a === 'install') { out.install = true; i += 1; continue; }
    out.rest.push(a);
    i += 1;
  }
  return out;
}

const argv = process.argv.slice(2);
if (argv.includes('--version') || argv.includes('-v')) { process.stdout.write('nf ' + pkg.version + '\n'); process.exit(0); }
if (argv.includes('--help') || argv.includes('-h')) { process.stdout.write(usage()); process.exit(0); }

const parsed = parse(argv);
const loaded = readManifest();
if (loaded.error) fail(loaded.error, 4);
const manifest = loaded.manifest;

if (parsed.install) {
  if (!parsed.dest) fail('install 缺 --dest <目录>（修复指引：npx -y ninfenz install --dest ./nf）', 2);
  materialize(manifest, path.resolve(parsed.dest), parsed.force)
    .then(function (dest) {
      process.stdout.write('✓ 已落盘：' + dest + '\n');
      process.stdout.write('  提示：这是运行时树（CLI / TUI / MCP 可用）。要跑完整 check1-40 门禁请 git clone 后 bash verify.sh\n');
    })
    .catch(function (e) { fail(e.message, 3); });
} else {
  const found = findPython();
  if (found.error) fail(found.error, 4);
  const py = found.python;
  let cwd = null;
  if (parsed.repo) {
    const repo = path.resolve(parsed.repo);
    if (!fs.existsSync(path.join(repo, 'scripts', 'nf.py'))) fail('--repo 不是 NF 仓库：' + repo + '（修复指引：指向含 scripts/nf.py 的目录）', 4);
    cwd = repo;
  } else {
    const local = findRepoRoot(process.cwd(), fs);
    cwd = local || null;
  }
  const finish = function (workdir) {
    const isTui = parsed.rest[0] === 'tui';
    const script = isTui ? path.join('tui', 'nf.py') : path.join('scripts', 'nf.py');
    const args = isTui ? parsed.rest.slice(1) : parsed.rest;
    const child = py.pre.concat([script]).concat(args);
    const env = Object.assign({}, process.env, { PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8', NF_NPM_LAUNCHER: pkg.version });
    const r = spawnSync(py.cmd, child, { cwd: workdir, stdio: 'inherit', env: env });
    if (r.error) fail('无法启动 NF CLI：' + r.error.message, 4);
    if (r.signal) { process.kill(process.pid, r.signal); return; }
    process.exit(r.status === null ? 1 : r.status);
  };
  if (cwd) finish(cwd);
  else ensurePayload(manifest).then(finish).catch(function (e) { fail(e.message, 3); });
}
