// 把仓库的受跟踪文件暂存成 npm payload（含 sha256 清单 + 固定 mtime），并做口径一致性闸门。
// 用法：node tools/stage-payload.mjs [--allow-tests-off] [--quiet]
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { PACKAGE_ROOT, PAYLOAD_DIR } from '../lib/paths.mjs';

const args = process.argv.slice(2);
const quiet = args.includes('--quiet');
const pkg = JSON.parse(fs.readFileSync(path.join(PACKAGE_ROOT, 'package.json'), 'utf8'));
const REPO_ROOT = path.resolve(PACKAGE_ROOT, '..', '..');

// 排除面：非运行时/历史/CI/打包器自身/构建产物（其余全收，保证 verify.sh 可跑）。
const EXCLUDE_DIRS = ['engine/', 'results/', '.github/', '.gitee/', 'packaging/', '.git/'];
const EXCLUDE_ANY = ['__pycache__/', '.pyc', 'tui/dist/', '.DS_Store'];
const EPOCH = new Date('2020-01-01T00:00:00Z');

function trackedFiles() {
  const r = spawnSync('git', ['ls-files', '-z'], { cwd: REPO_ROOT, maxBuffer: 128 * 1024 * 1024 });
  if (r.error || r.status !== 0) {
    throw new Error('git ls-files 失败（修复指引：在 git 检出里跑；' + (r.error ? r.error.message : 'status ' + r.status) + '）');
  }
  return String(r.stdout).split('\u0000').filter(Boolean).map(function (s) { return s.replace(/\\/g, '/'); });
}

function keep(rel) {
  // npm 打包会剔除点文件（.gitignore 等）——payload 按构造不含点文件，
  // 这样清单就与 tarball 逐文件一致（否则首次运行会因校验不过而 fail-closed）。
  if (rel.split('/').pop().startsWith('.')) return false;
  for (const d of EXCLUDE_DIRS) if (rel.startsWith(d)) return false;
  for (const a of EXCLUDE_ANY) if (rel.indexOf(a) >= 0) return false;
  return true;
}

function sha256(buf) { return crypto.createHash('sha256').update(buf).digest('hex'); }

function cliVersion() {
  const text = fs.readFileSync(path.join(REPO_ROOT, 'scripts', 'nf.py'), 'utf8');
  const m = text.match(/^NF_CLI_VERSION\s*=\s*"([^"]+)"/m);
  return m ? m[1] : null;
}

function sourceCommit() {
  const r = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: REPO_ROOT, encoding: 'utf8' });
  return r.status === 0 ? String(r.stdout).trim() : 'unknown';
}

const cli = cliVersion();
if (!cli) throw new Error('取不到 scripts/nf.py 的 NF_CLI_VERSION（修复指引：确认文件在场且格式未变）');
if (cli !== pkg.version) {
  throw new Error('版本口径不一致：package.json=' + pkg.version + ' vs NF_CLI_VERSION=' + cli
    + '（修复指引：发版时两处必须同值——npm 版本即 CLI 版本）');
}

fs.rmSync(PAYLOAD_DIR, { recursive: true, force: true });
fs.mkdirSync(PAYLOAD_DIR, { recursive: true });

// 清单用**数组**而非对象键：仓库路径里含 `+` 等合法文件名字符，而本仓卫生判据把
// JSON 对象键当「标识面」（字符集受限）——用键会让 13 个 `AI+…` 管线文件名被判违规。
const entries = [];
let total = 0;
let count = 0;
for (const rel of trackedFiles()) {
  if (!keep(rel)) continue;
  const src = path.join(REPO_ROOT, rel);
  if (!fs.existsSync(src) || !fs.statSync(src).isFile()) continue;
  const buf = fs.readFileSync(src);
  const dst = path.join(PAYLOAD_DIR, rel);
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.writeFileSync(dst, buf);
  fs.utimesSync(dst, EPOCH, EPOCH);
  entries.push({ path: rel, sha256: sha256(buf) });
  total += buf.length;
  count += 1;
}
if (count === 0) throw new Error('payload 为空（修复指引：确认在仓库根且 git ls-files 可用）');

entries.sort(function (a, b) { return a.path < b.path ? -1 : (a.path > b.path ? 1 : 0); });
const h = crypto.createHash('sha256');
for (const e of entries) h.update(e.path + '\u0000' + e.sha256 + '\n');
const tree = h.digest('hex');

const manifest = {
  schema: 'nf-npm-payload/1',
  package_version: pkg.version,
  cli_version: cli,
  source_commit: sourceCommit(),
  generated_at: new Date().toISOString(),
  count: count,
  total_bytes: total,
  tree_sha256: tree,
  files: entries
};
fs.writeFileSync(path.join(PAYLOAD_DIR, 'payload-manifest.json'), JSON.stringify(manifest, null, 2) + '\n', { mode: 420 });

// 包根也放一份 LICENSE（npm 页面与法务面惯例；payload 内那份仍随工作树走）。
const licSrc = path.join(REPO_ROOT, 'LICENSE');
if (fs.existsSync(licSrc)) {
  const licDst = path.join(PACKAGE_ROOT, 'LICENSE');
  fs.writeFileSync(licDst, fs.readFileSync(licSrc));
  fs.utimesSync(licDst, EPOCH, EPOCH);
}

const mb = function (n) { return (n / (1024 * 1024)).toFixed(2) + ' MB'; };
if (!quiet) {
  process.stdout.write('== NF npm payload 暂存 ==\n');
  process.stdout.write('  文件 ' + count + ' 件 · 解包 ' + mb(total) + ' · tree_sha256 ' + tree.slice(0, 16) + '\n');
  process.stdout.write('  CLI 版本 ' + cli + ' · 源提交 ' + manifest.source_commit.slice(0, 12) + '\n');
  process.stdout.write('  预算（解包） ' + pkg.config.payload_budget_mb + ' MB × 3.5 ≈ ' + mb(pkg.config.payload_budget_mb * 3.5 * 1024 * 1024) + '\n');
}
// 包页文案的体积口径与清单**同步**（verify 里做判死）：同 site/tools/sync-numbers.mjs 的分工。
// 为什么：README 就是 npm 页面正文，写着过期件数/体积等于发布旧数字（2026-10-07 实测：README 写
// 2809 件 / 18.74 MB / 39 条门禁，真值已是 2939 件 / 19.72 MB / check1-40）。
const README_PATH = path.join(PACKAGE_ROOT, 'README.md');
const SIZE_RE = /当前体积：\*\*(\d+) 件 · 解包 ([\d.]+) MB\*\*/;
if (fs.existsSync(README_PATH)) {
  const text = fs.readFileSync(README_PATH, 'utf8');
  const want = '当前体积：**' + count + ' 件 · 解包 ' + mb(total) + '**';
  if (!SIZE_RE.test(text)) {
    if (!quiet) process.stdout.write('  [WARN] README 缺体积口径行（verify 会判死；修复指引：补回「当前体积：**N 件 · 解包 X MB**」）\n');
  } else if (!text.includes(want)) {
    fs.writeFileSync(README_PATH, text.replace(SIZE_RE, want));
    if (!quiet) process.stdout.write('  ✓ README 体积口径已同步：' + count + ' 件 · ' + mb(total) + '\n');
  }
}

