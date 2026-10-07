// 发布前自检：把「顶尖 npm 包」的硬要求做成可失败项（prepack 会跑它）。
import fs from 'node:fs';
import path from 'node:path';
import { PACKAGE_ROOT, PAYLOAD_DIR } from '../lib/paths.mjs';
import { verifyTree, treeSha256 } from '../lib/payload.mjs';

const pkg = JSON.parse(fs.readFileSync(path.join(PACKAGE_ROOT, 'package.json'), 'utf8'));
const issues = [];
const warns = [];
function need(cond, msg) { if (!cond) issues.push(msg); }

// 1) 供应链：禁安装脚本（npm 生态最常被投放的一环）。
for (const bad of ['preinstall', 'install', 'postinstall']) {
  need(!pkg.scripts || !pkg.scripts[bad], 'package.json 含安装脚本 ' + bad + '（供应链红线：改为惰性首次运行初始化）');
}
// 2) 元数据完整性。
need(pkg.name && pkg.version, '缺 name/version');
need(pkg.license, '缺 license');
need(pkg.repository && pkg.repository.url, '缺 repository');
need(pkg.bugs && pkg.bugs.url, '缺 bugs');
need(pkg.homepage, '缺 homepage');
need(pkg.engines && pkg.engines.node, '缺 engines.node（须声明 Node 下限）');
need(pkg.type === 'module', 'type 应为 module（ESM）');
need(pkg.publishConfig && pkg.publishConfig.provenance === true, 'publishConfig.provenance 必须为 true（发布须带来源证明）');
need(Array.isArray(pkg.files) && pkg.files.indexOf('payload/') >= 0, 'files 未包含 payload/');
need(Array.isArray(pkg.files) && pkg.files.indexOf('bin/') >= 0, 'files 未包含 bin/');
need(pkg.bin && pkg.bin.nf === 'bin/nf.mjs' && pkg.bin.ninfenz === 'bin/nf.mjs', 'bin 须同时暴露 nf 与 ninfenz');
need(Array.isArray(pkg.keywords) && pkg.keywords.length >= 8, 'keywords 过少（影响可发现性）');
// 3) 入口件在位且可执行位由 npm 处理，这里只查存在。
for (const rel of ['bin/nf.mjs', 'lib/paths.mjs', 'lib/python.mjs', 'lib/payload.mjs', 'README.md']) {
  need(fs.existsSync(path.join(PACKAGE_ROOT, rel)), '缺入口件 ' + rel);
}
// 4) payload 清单与逐文件校验。
const manifestPath = path.join(PAYLOAD_DIR, 'payload-manifest.json');
if (!fs.existsSync(manifestPath)) {
  issues.push('缺 payload 清单（修复指引：先跑 npm run stage）');
} else {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  need(manifest.package_version === pkg.version, 'payload.package_version 与 package.json 不一致');
  need(manifest.cli_version === pkg.version, 'payload.cli_version 与 CLI 版本不一致');
  const bad = verifyTree(PAYLOAD_DIR, manifest);
  need(bad.length === 0, 'payload 逐文件校验不过：' + bad.slice(0, 3).join(', '));
  need(treeSha256(manifest) === manifest.tree_sha256, 'payload.tree_sha256 自洽性不过');
  for (const must of ['scripts/nf.py', 'tui/nf.py', 'verify.sh', 'llms.txt', 'LICENSE', 'desktop/src/core/paths.py']) {
    need(manifest.files.some(function (e) { return e.path === must; }), 'payload 缺关键件 ' + must);
  }
  const paths = manifest.files.map(function (e) { return e.path; });
  const dots = paths.filter(function (r) { return r.split('/').pop().startsWith('.'); });
  need(dots.length === 0, 'payload 含点文件（npm 打包含剔除，会导致 tarball 与清单不一致）：' + dots.slice(0, 3).join(', '));
  const pyc = paths.filter(function (r) { return r.indexOf('__pycache__') >= 0 || r.endsWith('.pyc'); });
  need(pyc.length === 0, 'payload 混入字节码缓存：' + pyc.slice(0, 3).join(', '));
  const budget = Number(pkg.config && pkg.config.payload_budget_mb || 14) * 1024 * 1024;
  need(manifest.total_bytes <= budget * 4, 'payload 解包体积超预算：' + (manifest.total_bytes / 1048576).toFixed(1) + ' MB');
  if (manifest.total_bytes > budget * 2) warns.push('payload 偏大（' + (manifest.total_bytes / 1048576).toFixed(1) + ' MB），建议只带运行时面');
}
// 5) 许可证文件。
need(fs.existsSync(path.join(PAYLOAD_DIR, 'LICENSE')), 'payload 缺 LICENSE');

// 6) 包页文案的体积口径必须与 payload 清单一致（发布旧数字比不写更糟；同 site 的 sync-numbers 口径）。
if (fs.existsSync(manifestPath)) {
  const pageManifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const readmePage = path.join(PACKAGE_ROOT, 'README.md');
  if (!fs.existsSync(readmePage)) {
    issues.push('缺包页 README.md（npm 页面正文）');
  } else {
    const mm = fs.readFileSync(readmePage, 'utf8').match(/当前体积：\*\*(\d+) 件 · 解包 ([\d.]+) MB\*\*/);
    if (!mm) {
      issues.push('README 缺体积口径行（修复指引：补回「当前体积：**N 件 · 解包 X MB**」，npm run stage 会自动同步）');
    } else {
      const wantCount = String(pageManifest.count);
      const wantMb = (pageManifest.total_bytes / 1048576).toFixed(2);
      need(mm[1] === wantCount, 'README 件数过期：README=' + mm[1] + ' vs 清单=' + wantCount + '（修复指引：npm run stage 自动同步后提交）');
      need(mm[2] === wantMb, 'README 体积过期：README=' + mm[2] + ' MB vs 清单=' + wantMb + ' MB（修复指引：npm run stage 自动同步后提交）');
    }
  }
}


process.stdout.write('== NF npm 发布前自检 ==\n');
for (const w of warns) process.stdout.write('  [WARN] ' + w + '\n');
if (issues.length === 0) {
  process.stdout.write('  ✓ 全部通过（0 issue）\n');
} else {
  for (const i of issues) process.stdout.write('  ✗ ' + i + '\n');
  process.exitCode = 1;
}
