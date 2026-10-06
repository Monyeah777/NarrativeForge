#!/usr/bin/env node
// 统一切换站点 origin（canonical / hreflang / og:url / og:image / JSON-LD @id / sitemap / robots / llms.txt）
//
// 用法：
//   node site/tools/set-origin.mjs                                  # 只报告现状（dry-run）
//   node site/tools/set-origin.mjs https://example.dev --write       # 切换到该 origin
//
// 为什么需要它：origin 散落在 5 个文件里（含 JSON-LD 的 @id 与 sitemap 的 hreflang 互指），
// 手改必漏；有了它，将来买下 ninfenz.dev 时只需一条命令切回。

import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const SITE = path.resolve(HERE, '..');
const FILES = ['index.html', 'en/index.html', 'robots.txt', 'sitemap.xml', 'llms.txt'];
// 已知 origin 池：切换时把池里任意一个替换成目标
const KNOWN = ['https://ninfenz.dev', 'https://ninfenz.1764861918.workers.dev'];

const target = (process.argv[2] || '').replace(/\/+$/, '');
const write = process.argv.includes('--write');

let current = null;
for (const f of FILES) {
  const t = fs.readFileSync(path.join(SITE, f), 'utf8');
  for (const o of KNOWN) if (t.includes(o)) current = current || o;
}
if (!current) {
  console.error('未在任何文件里找到已知 origin（KNOWN 池需要补充）');
  process.exit(2);
}
console.log('当前 origin = ' + current);

if (!target) {
  console.log('（dry-run）要切换请加目标：node site/tools/set-origin.mjs <origin> --write');
  process.exit(0);
}
if (!/^https:\/\/[a-z0-9.-]+$/i.test(target)) {
  console.error('origin 形如 https://host（不带结尾斜杠）');
  process.exit(2);
}
if (!KNOWN.includes(target)) KNOWN.push(target);

for (const f of FILES) {
  const p = path.join(SITE, f);
  const before = fs.readFileSync(p, 'utf8');
  let after = before;
  for (const o of KNOWN) if (o !== target) after = after.split(o).join(target);
  if (after === before) { console.log('  ' + f + ': 无变化'); continue; }
  const n = KNOWN.reduce((acc, o) => acc + (o !== target ? before.split(o).length - 1 : 0), 0);
  console.log('  ' + f + ': ' + n + ' 处 -> ' + target);
  if (write) fs.writeFileSync(p, after, 'utf8');
}
console.log(write ? '已写入。接着重新部署：npx wrangler deploy' : '（dry-run，未写盘）');
