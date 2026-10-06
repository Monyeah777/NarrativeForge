#!/usr/bin/env node
// 发布钩子：把「质量凭证」数字从仓库真源同步进站点三面，防止站点发布旧数字。
//
// 真源 = 仓库根 llms.txt 的 nf:stats 区块（该块由 nf stats --write 生成，是唯一事实）。
// 用法：
//   node site/tools/sync-numbers.mjs           # 只检查；有漂移则退出码 1（用于发布前把关）
//   node site/tools/sync-numbers.mjs --write   # 同步写入
//
// 为什么需要它：site/ 是独立于生成器的手写静态面，一旦仓库发版改了 verify/check/PASS 数字，
// 站点不会自动跟随——2026-10-06 实测就漂移成 v2.29/check1-39/PASS=68（真源 v2.30/check1-40/PASS=72）。

import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const SITE = path.resolve(HERE, '..');
const ROOT = path.resolve(SITE, '..');
const FILES = ['index.html', 'en/index.html', 'llms.txt'];
const RE = /verify v\d+\.\d+ · check\d+-\d+ · PASS=\d+/g;

const src = fs.readFileSync(path.join(ROOT, 'llms.txt'), 'utf8');
const m = src.match(/verify v(\d+\.\d+) · check(\d+)-(\d+) · PASS=(\d+)/);
if (!m) { console.error('未能在 llms.txt 的 nf:stats 区找到质量凭证真源'); process.exit(2); }
const want = 'verify v' + m[1] + ' · check' + m[2] + '-' + m[3] + ' · PASS=' + m[4];
console.log('真源（llms.txt）: ' + want);

let drift = 0;
let touched = 0;
for (const f of FILES) {
  const p = path.join(SITE, f);
  const t = fs.readFileSync(p, 'utf8');
  const found = t.match(RE) || [];
  const bad = [...new Set(found.filter((x) => x !== want))];
  if (!found.length) { console.log('  ' + f + ': 未出现该组数字（跳过）'); continue; }
  if (!bad.length) { console.log('  ' + f + ': ' + found.length + ' 处一致'); continue; }
  drift += bad.length;
  console.log('  ' + f + ': ' + bad.length + ' 处漂移 -> ' + bad.join(' / '));
  if (process.argv.includes('--write')) { fs.writeFileSync(p, t.replace(RE, want), 'utf8'); touched++; }
}
if (!drift) { console.log('✓ 站点数字与真源一致'); process.exit(0); }
if (!process.argv.includes('--write')) { console.error('✗ 站点数字漂移 ' + drift + ' 处：跑 node site/tools/sync-numbers.mjs --write 同步'); process.exit(1); }
console.log('✓ 已同步 ' + touched + ' 个文件到 ' + want);
