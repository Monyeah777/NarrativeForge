#!/usr/bin/env node
// 统一切换站点基址（canonical / hreflang / og:url / og:image / JSON-LD @id / sitemap / robots /
// llms.txt / 404 导航 / 机器面 / 机器面清单），并做重复段自检。
//
// 用法：
//   node site/tools/set-origin.mjs                              # 只报告现状（dry-run）
//   node site/tools/set-origin.mjs https://host[/path] --write   # 切换到该基址
//
// 覆盖面 = **自动发现**：site/ 下所有文本文件（.html/.txt/.xml/.json/.md/.sh/.js/.css），
// 排除 tools/ 与 assets/（前者自身持有基址池，改写会自伤；后者是二进制与样式）。
// 自动发现取代早先的 6 文件硬编码列表：新增页面若忘了登记，换域会**静默半切**。
//
// 支持带路径的基址（GitHub Pages 项目站是子路径，形如 https://user.github.io/repo）。
//
// 踩坑留档（实测）：曾用「顺序 replace」实现——把 workers.dev 换成 https://user.github.io/repo 之后，
// 池里更短的 https://user.github.io 又命中了**刚写进去的新文本**，于是变成 .../repo/repo。
// 现改为「两遍法」：先把池内任意基址换成不含任何基址的占位符（长者优先），再把占位符换成目标；
// 对「池内互相包含」天然免疫，末尾还有重复段自检。

import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const SITE = path.resolve(HERE, '..');
const PLACEHOLDER = '\u0000NF_BASE\u0000';

// 已知基址池（切换时把池里任意一个替换成目标；替换时长者优先）
const KNOWN = [
  'https://ninfenz.dev',
  'https://ninfenz.1764861918.workers.dev',
  'https://monyeah777.github.io/NinFenz',
  'https://monyeah777.github.io',
];
const SKIP_DIRS = new Set(['tools', 'assets', 'node_modules', '.git']);
const TEXT_EXT = new Set(['.html', '.txt', '.xml', '.json', '.md', '.sh', '.js', '.css']);

function walk(dir, out) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (!SKIP_DIRS.has(e.name)) walk(p, out); continue; }
    if (TEXT_EXT.has(path.extname(e.name).toLowerCase())) out.push(path.relative(SITE, p).split(path.sep).join('/'));
  }
  return out;
}
const FILES = walk(SITE, []).sort();

const target = (process.argv[2] || '').replace(/\/+$/, '');
const write = process.argv.includes('--write');

let current = null;
for (const f of FILES) {
  const t = fs.readFileSync(path.join(SITE, f), 'utf8');
  for (const o of KNOWN) if (t.includes(o)) current = current || o;
}
if (!current) { console.error('未在任何文件里找到已知基址（KNOWN 池需要补充）'); process.exit(2); }
console.log('扫到文本面 ' + FILES.length + ' 个；当前基址 = ' + current);

if (!target) {
  console.log('（dry-run）要切换请加目标：node site/tools/set-origin.mjs <base> --write');
  console.log('已知候选：' + KNOWN.join('  '));
  process.exit(0);
}
if (!/^https:\/\/[a-z0-9.-]+(\/[A-Za-z0-9._~\/-]*)?$/i.test(target)) {
  console.error('基址形如 https://host 或 https://host/path（不带结尾斜杠）');
  process.exit(2);
}

const pool = KNOWN.filter((o) => o !== target).sort((a, b) => b.length - a.length);
let touched = 0;
for (const f of FILES) {
  const p = path.join(SITE, f);
  const before = fs.readFileSync(p, 'utf8');
  let n = 0;
  let mid = before;
  for (const o of pool) {
    const c = mid.split(o).length - 1;
    if (c) { n += c; mid = mid.split(o).join(PLACEHOLDER); }
  }
  const after = mid.split(PLACEHOLDER).join(target);
  if (after === before) continue;
  console.log('  ' + f + ': ' + n + ' 处 -> ' + target);
  touched++;
  if (write) fs.writeFileSync(p, after, 'utf8');
}
console.log(write ? '已写入 ' + touched + ' 个面。接着部署：npx wrangler deploy' : '（dry-run，未写盘；加 --write 才改）');
if (write) {
  const seg = target.slice(target.lastIndexOf('/'));
  const bad = FILES.filter((f) => fs.readFileSync(path.join(SITE, f), 'utf8').includes(target + seg));
  if (bad.length) { console.error('自检失败：基址出现重复段 -> ' + bad.join(', ')); process.exit(1); }
  const leftover = FILES.filter((f) => {
    const t = fs.readFileSync(path.join(SITE, f), 'utf8');
    return KNOWN.filter((o) => o !== target).some((o) => t.includes(o));
  });
  if (leftover.length) { console.error('自检失败：仍有旧基址残留 -> ' + leftover.join(', ')); process.exit(1); }
  console.log('自检通过：无重复基址段、无旧基址残留');
}
