// 把 npm payload 复制成 Space 的 NF 树（hf-space/nf/），使 Space 与 npm 包同源同版本。
// 用法：node tools/stage-space.mjs [--quiet]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SPACE = path.resolve(HERE, '..');
const SRC = path.resolve(SPACE, '..', 'npm', 'payload');
const DST = path.join(SPACE, 'nf');
const quiet = process.argv.includes('--quiet');

if (!fs.existsSync(SRC)) {
  throw new Error('缺 npm payload：' + SRC + '（修复指引：先在 packaging/npm 跑 npm run stage）');
}

function copy(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const ent of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, ent.name);
    const d = path.join(dst, ent.name);
    if (ent.isDirectory()) copy(s, d);
    else if (ent.isFile()) fs.copyFileSync(s, d);
  }
}

fs.rmSync(DST, { recursive: true, force: true });
copy(SRC, DST);
const manifest = path.join(DST, 'payload-manifest.json');
if (fs.existsSync(manifest)) fs.rmSync(manifest);

let files = 0;
let bytes = 0;
(function walk(dir) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p);
    else { files += 1; bytes += fs.statSync(p).size; }
  }
})(DST);

if (!quiet) {
  process.stdout.write('== NF Space 装载 ==\n');
  process.stdout.write('  nf/ ' + files + ' 件 · ' + (bytes / 1048576).toFixed(2) + ' MB\n');
  process.stdout.write('  下一步：python server.py --port 7860（或直接推 Space）\n');
}
