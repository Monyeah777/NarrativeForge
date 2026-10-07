#!/usr/bin/env node
// 站点数字与真源同步（发布钩子）：站点一次都不许发布旧数字。
//
// 真源两条：
//   1) 质量凭证 = 仓库根 llms.txt 的 nf:stats 区块（由 nf stats --write 生成，唯一事实）
//   2) 规模数字 = protocol/repo_stats.json（生成物）
//   并交叉核对两者（version / checks / PASS 三处必须自洽）。
//
// 用法：
//   node site/tools/sync-numbers.mjs           # 只检查；漂移或缺失即退出码 1（发布前把关）
//   node site/tools/sync-numbers.mjs --write   # 把质量凭证串同步进所有出现的面
//
// 覆盖面：站点全部对外面，含机器面（nf.txt / agent.txt / llms-full.txt / facts.json / use 页）。
// 机读面**必须**带 canonical 质量凭证串——机器面写着一组过时数字，比没写更糟（会被当成事实引用）。
//
// 为什么需要它：2026-10-06 实测漂移过（站点写 v2.29/check1-39/PASS=68，真源已 v2.30/check1-40/PASS=72）。

import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const SITE = path.resolve(HERE, '..');
const ROOT = path.resolve(SITE, '..');

//: 必须出现 canonical 质量凭证串的面（缺 = 失败）
const REQUIRED = ['index.html', 'en/index.html', 'llms.txt', 'llms-full.txt', 'facts.json',
                  'nf.txt', 'agent.txt', 'use/index.html', 'en/use/index.html'];
//: 允许出现（出现即必须是 canonical；不要求出现）
const OPTIONAL = ['robots.txt', 'sitemap.xml', '404.html', 'README.md'];
//: 规模数字必须齐全的面（同一条规模行上）
const SCALE_FILES = ['index.html', 'en/index.html', 'llms.txt', 'llms-full.txt'];

const RE = /verify v\d+\.\d+ · check\d+-\d+ · PASS=\d+/g;

function read(p) { return fs.readFileSync(p, 'utf8'); }

// ---- 真源 1：llms.txt 的 nf:stats 区 ----
const src = read(path.join(ROOT, 'llms.txt'));
const m = src.match(/verify v(\d+\.\d+) · check(\d+)-(\d+) · PASS=(\d+)/);
if (!m) { console.error('未能在 llms.txt 的 nf:stats 区找到质量凭证真源'); process.exit(2); }
const want = 'verify v' + m[1] + ' · check' + m[2] + '-' + m[3] + ' · PASS=' + m[4];

// ---- 真源 2：protocol/repo_stats.json（交叉核对）----
const stats = JSON.parse(read(path.join(ROOT, 'protocol', 'repo_stats.json')));
const want2 = 'verify v' + stats.verify_version + ' · check1-' + stats.verify_checks + ' · PASS=' + stats.baseline_pass;
console.log('真源（llms.txt）      : ' + want);
console.log('真源（repo_stats.json）: ' + want2);
let fail = 0;
if (want !== want2) {
  console.error('✗ 两条真源不自洽：llms.txt 与 protocol/repo_stats.json 的质量凭证不一致');
  fail = 1;
}

// ---- 质量凭证面 ----
const write = process.argv.includes('--write');
for (const f of REQUIRED.concat(OPTIONAL)) {
  const p = path.join(SITE, f);
  if (!fs.existsSync(p)) {
    if (REQUIRED.includes(f)) { console.error('✗ 缺面：site/' + f + '（REQUIRED 列表里的机器面不在场）'); fail = 1; }
    continue;
  }
  const t = read(p);
  const found = t.match(RE) || [];
  const bad = [...new Set(found.filter((x) => x !== want))];
  if (!found.length) {
    if (REQUIRED.includes(f)) {
      console.error('✗ site/' + f + ' 未出现 canonical 质量凭证串（机读面必须带上：' + want + '）');
      fail = 1;
    } else {
      console.log('  ' + f + ': 未出现该组数字（非必含面，跳过）');
    }
    continue;
  }
  if (bad.length) {
    fail = 1;
    console.error('✗ site/' + f + ': ' + bad.length + ' 处漂移 -> ' + bad.join(' / '));
    if (write) {
      fs.writeFileSync(p, t.replace(RE, want), 'utf8');
      console.error('  └ 已改写为 ' + want + '（请复核后提交）');
    }
  } else {
    console.log('  ' + f + ': ' + found.length + ' 处一致');
  }
}

// ---- 规模数字面（同一条规模行必须齐 8 个数）----
const SCALE = [stats.registered_packs, stats.pack_assets, stats.concept_graphs,
               stats.standards_total, stats.standards_reachable, stats.standards_unreachable,
               stats.standard_bindings, stats.library_items];
const MARK = /登记包|registered packs/;
for (const f of SCALE_FILES) {
  const p = path.join(SITE, f);
  if (!fs.existsSync(p)) { continue; }
  const lines = read(p).split(/\r?\n/).filter((ln) => MARK.test(ln));
  if (!lines.length) { console.error('✗ site/' + f + ' 找不到规模行（应含「登记包」或「registered packs」）'); fail = 1; continue; }
  const missing = [];
  for (const ln of lines) {
    for (const n of SCALE) {
      if (!new RegExp('(^|[^0-9])' + n + '([^0-9]|$)').test(ln)) { missing.push(f + ' 缺 ' + n); }
    }
  }
  if (missing.length) { console.error('✗ ' + [...new Set(missing)].join('；') + '（真源 protocol/repo_stats.json）'); fail = 1; }
  else { console.log('  ' + f + ': 规模 8 个数齐全'); }
}
const factsPath = path.join(SITE, 'facts.json');
if (fs.existsSync(factsPath)) {
  let fj = null;
  try { fj = JSON.parse(read(factsPath)); } catch (e) { console.error('✗ site/facts.json 不是合法 JSON：' + e.message); fail = 1; }
  if (fj) {
    const sf = (fj.facts || []).find((x) => x.id === 'scale');
    const got = sf && sf.values ? sf.values : {};
    const pairs = [[got.registered_packs, stats.registered_packs], [got.pack_assets, stats.pack_assets],
                   [got.concept_graphs, stats.concept_graphs], [got.standards_total, stats.standards_total],
                   [got.standards_reachable, stats.standards_reachable], [got.standards_unreachable, stats.standards_unreachable],
                   [got.standard_bindings, stats.standard_bindings], [got.library_items, stats.library_items]];
    const offBad = pairs.filter((x) => x[0] !== x[1]);
    if (offBad.length) { console.error('✗ site/facts.json 的 scale.values 与 repo_stats.json 不一致：' + offBad.length + ' 处'); fail = 1; }
    else { console.log('  facts.json: scale.values 与真源一致（8 项）'); }
  }
}

if (!fail) { console.log('✓ 站点数字与真源一致（质量凭证 + 规模）'); process.exit(0); }
console.error('✗ 站点数字未过：跑 node site/tools/sync-numbers.mjs --write 同步可自动改写的项，其余按上面指引手改');
process.exit(1);
