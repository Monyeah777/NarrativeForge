#!/usr/bin/env node
// 统一切换站点基址（canonical / hreflang / og:url / og:image / JSON-LD @id / sitemap / robots / llms.txt / 404 导航）
//
// 用法：
//   node site/tools/set-origin.mjs                              # 只报告现状（dry-run）
//   node site/tools/set-origin.mjs https://host[/path] --write   # 切换到该基址
//
// 为什么需要它：基址散落在 6 个文件（含 JSON-LD @id、sitemap 的 hreflang 互指、404 页导航），手改必漏。
// 支持带路径的基址（GitHub Pages 项目站是子路径，形如 https://user.github.io/repo）。
//
// 踩坑留档（本波实测）：曾用「顺序 replace」实现——把 workers.dev 换成 https://user.github.io/repo 之后，
// 池里更短的 https://user.github.io 又命中了**刚写进去的新文本**，于是变成 .../repo/repo。
// 现改为「两遍法」：先把池内任意基址换成不含任何基址的占位符（长者优先），再把占位符换成目标；
// 对「池内互相包含」天然免疫，末尾还有重复段自检。

import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const SITE = path.resolve(HERE, '..');
const FILES = ['index.html', 'en/index.html', 'robots.txt', 'sitemap.xml', 'llms.txt', '404.html'];
const PLACEHOLDER = '\u0000NF_BASE\u0000';

// 已知基址池（切换时把池里任意一个替换成目标；替换时长者优先）
const KNOWN = [
  'https://ninfenz.dev',
  'https://ninfenz.1764861918.workers.dev',
  'https://monyeah777.github.io/NinFenz',
  'https://monyeah777.github.io',
];

const target = (process.argv[2] || '').replace(/\/+$/, '');
const write = process.argv.includes('--write');

let current = null;
for (const f of FILES) {
  const t = fs.readFileSync(path.join(SITE, f), 'utf8');
  for (const o of KNOWN) if (t.includes(o)) current = current || o;
}
if (!current) { console.error('未在任何文件里找到已知基址（KNOWN 池需要补充）'); process.exit(2); }
console.log('当前基址 = ' + current);

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
  if (after === before) { console.log('  ' + f + ': 无变化'); continue; }
  console.log('  ' + f + ': ' + n + ' 处 -> ' + target);
  if (write) fs.writeFileSync(p, after, 'utf8');
}
console.log(write ? '已写入。接着部署：npx wrangler deploy / 推 gh-pages 分支' : '（dry-run，未写盘）');
if (write) {
  const seg = target.slice(target.lastIndexOf('/'));
  const bad = FILES.filter((f) => fs.readFileSync(path.join(SITE, f), 'utf8').includes(target + seg));
  if (bad.length) { console.error('自检失败：基址出现重复段 -> ' + bad.join(', ')); process.exit(1); }
  console.log('自检通过：无重复基址段');
}
