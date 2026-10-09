#!/usr/bin/env node
// 站点 Worker 的**行为判据**（真跑模块 + 桩 ASSETS，逐条核协商/跳转/回落）。
//
// 为什么需要（2026-10-08 审计）：此前 worker.js 只被 site-check.mjs 用**字符串包含**判过
// （`wk.includes('text/markdown')`）——它抓不到任何真实行为缺陷：把协商写成永不触发、
// 把 q=0 当同意、回落逻辑写反，字符串判据都全绿。本件把公开入口立成**可跑的行为表**。
//
// 用法：node site/tools/worker-check.mjs [--worker <path>]
// 退出码：0 = 全过；1 = 有 FAIL（可指向被改坏的副本，供变异负例使用）。
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const argv = process.argv.slice(2);
const workerPath = argv.includes('--worker') ? argv[argv.indexOf('--worker') + 1] : 'site/worker.js';

const mod = await import(pathToFileURL(resolve(workerPath)).href);
const worker = mod.default;
if (!worker || typeof worker.fetch !== 'function') {
  console.log('✗ ' + workerPath + ' 没有导出 fetch 处理器');
  process.exit(1);
}

const rows = [];
function check(name, ok, detail) {
  rows.push({ 判据: name, 结果: ok ? 'PASS' : 'FAIL', 详情: String(detail === undefined ? '' : detail) });
}

function makeEnv(hooks = {}) {
  const seen = [];
  return {
    seen,
    env: {
      ASSETS: {
        async fetch(req) {
          const url = new URL(req.url);
          seen.push(url.pathname);
          if (hooks.throwOn && url.pathname === hooks.throwOn) throw new Error('assets 崩了');
          if (url.pathname === '/llms-full.txt') {
            if (hooks.markdownMissing) return new Response('nope', { status: 404 });
            return new Response('# 机器面', { status: 200, headers: { 'content-type': 'text/plain' } });
          }
          return new Response('<html>页</html>', { status: 200, headers: { 'content-type': 'text/html' } });
        },
      },
    },
  };
}

async function call(url, headers = {}, method = 'GET', hooks = {}) {
  const { env, seen } = makeEnv(hooks);
  const req = new Request(url, { method, headers });
  const res = await worker.fetch(req, env);
  return { res, seen };
}

const H = (accept) => ({ accept });

// ---- 机器面内容协商 ----
for (const path of ['/', '/en/', '/en']) {
  const { res } = await call('https://ninfenz.dev' + path, H('text/markdown'));
  const ct = res.headers.get('content-type') || '';
  check('协商 ' + path, res.status === 200 && ct.startsWith('text/markdown')
        && res.headers.get('x-ninfenz-negotiated') === 'llms-full.txt'
        && (res.headers.get('vary') || '').includes('Accept'), res.status + ' ' + ct);
}

for (const [label, accept] of [
  ['q=0 明确不要', 'text/markdown;q=0'],
  ['q=0.0 明确不要', 'text/markdown;q=0.0'],
  ['通配 */*', '*/*'],
  ['未点名 markdown', 'text/html'],
]) {
  const { res } = await call('https://ninfenz.dev/', H(accept));
  const ct = res.headers.get('content-type') || '';
  check('不协商 · ' + label, res.status === 200 && ct.startsWith('text/html') && !res.headers.get('x-ninfenz-negotiated'), ct);
}

for (const [label, accept] of [
  ['列表里带 markdown', 'text/html, text/markdown;q=0.9'],
  ['text/* 通配', 'text/*'],
  ['带其他参数', 'text/markdown; charset=utf-8'],
]) {
  const { res } = await call('https://ninfenz.dev/', H(accept));
  check('协商 · ' + label, (res.headers.get('content-type') || '').startsWith('text/markdown'), label);
}

// 非协商路由 / 非 GET：一律回落静态资产
const useRes = await call('https://ninfenz.dev/use/', H('text/markdown'));
check('非协商路由不触发', (useRes.res.headers.get('content-type') || '').startsWith('text/html'), '/use/');
const postRes = await call('https://ninfenz.dev/', H('text/markdown'), 'POST');
check('非 GET 不触发', (postRes.res.headers.get('content-type') || '').startsWith('text/html'), 'POST');

// ---- 回落纪律（协商失败不得改变正常行为） ----
const miss = await call('https://ninfenz.dev/', H('text/markdown'), 'GET', { markdownMissing: true });
check('机器面缺失 → 回落原请求', (miss.res.headers.get('content-type') || '').startsWith('text/html')
      && miss.seen.includes('/'), miss.seen.join(','));
const boom = await call('https://ninfenz.dev/', H('text/markdown'), 'GET', { throwOn: '/llms-full.txt' });
check('机器面取件抛错 → 回落原请求', (boom.res.headers.get('content-type') || '').startsWith('text/html'), boom.seen.join(','));

// ---- www → 裸域 301（路径与查询串必须原样保留） ----
const www = await call('https://www.ninfenz.dev/use/?q=1&x=2');
check('www 301 且保留路径/查询', www.res.status === 301
      && www.res.headers.get('location') === 'https://ninfenz.dev/use/?q=1&x=2',
      www.res.status + ' ' + www.res.headers.get('location'));

// ---- 其余请求原样透传 ----
const passthrough = await call('https://ninfenz.dev/nf.txt');
check('其余透传 ASSETS', passthrough.res.status === 200 && passthrough.seen.join(',') === '/nf.txt', passthrough.seen.join(','));

console.table(rows);
const bad = rows.filter((r) => r.结果 === 'FAIL');
console.log(bad.length
  ? '✗ worker 行为判据 ' + bad.length + '/' + rows.length + ' 项未过（worker=' + workerPath + '）'
  : '✓ worker 行为判据全过（' + rows.length + ' 项 · worker=' + workerPath + '）');
process.exit(bad.length ? 1 : 0);
