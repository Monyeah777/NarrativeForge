#!/usr/bin/env node
// 站点体检：GEO / 可用性判据。两种模式：
//   node site/tools/site-check.mjs [origin]   联网面（缺省 origin = index.html 的 canonical）
//   node site/tools/site-check.mjs --offline  离线面（只读本目录文件；部署前把关，无需网络）
//
// 判据两类：① 静态面（域名自洽 / JSON-LD 可解析 / 机器面齐 / 抓取规则 / 无外部资源）
//           ② 联网面（状态码 / 响应头 / 跨域 / 内容协商 / 数字真值）
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const SITE = path.resolve(HERE, '..');
const OFFLINE = process.argv.includes('--offline');
const idx = fs.readFileSync(path.join(SITE, 'index.html'), 'utf8');
const origin = (process.argv.slice(2).find((a) => !a.startsWith('--')) ||
  (idx.match(/rel="canonical" href="(https:\/\/[^\/"]+)/) || [])[1] || '').replace(/\/+$/, '');
const KNOWN_BASES = ['https://ninfenz.dev', 'https://ninfenz.1764861918.workers.dev', 'https://monyeah777.github.io/NinFenz', 'https://monyeah777.github.io'];
const MACHINE = ['/llms.txt', '/llms-full.txt', '/nf.txt', '/agent.txt', '/facts.json', '/run.sh', '/robots.txt', '/sitemap.xml', '/use/', '/en/use/', '/404.html', '/assets/site.css'];
const rows = [];
const check = (name, ok, detail) => rows.push({ 判据: name, 结果: ok ? 'PASS' : 'FAIL', 详情: String(detail) });

function ldTypesOf(html) {
  const out = [];
  let ok = true;
  for (const m of html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)) {
    try { const j = JSON.parse(m[1]); out.push(...(j['@graph'] ? j['@graph'].map((x) => x['@type']) : [j['@type']])); }
    catch { ok = false; }
  }
  return { ok, types: out };
}

if (OFFLINE) {
  const read = (p) => fs.readFileSync(path.join(SITE, p), 'utf8');
  const has = (p) => fs.existsSync(path.join(SITE, p));
  for (const p of ['index.html', 'en/index.html', 'use/index.html', 'en/use/index.html']) {
    if (!has(p)) { check('在场 ' + p, false, '缺文件'); continue; }
    const html = read(p);
    const { ok, types } = ldTypesOf(html);
    check(p + ' JSON-LD 可解析', ok && types.length > 0, types.join('+') || '(无)');
    check(p + ' 无外部资源', !/(?:<link[^>]+rel="stylesheet"[^>]+href|<script[^>]+src|<img[^>]+src)="https?:/i.test(html), '同源');
  }
  const canon = (idx.match(/rel="canonical" href="([^"]+)"/) || [])[1] || '';
  check('首页 canonical 自指', canon === origin + '/', canon || '(缺失)');
  check('首页 hreflang 三向', ['zh-CN', 'en', 'x-default'].every((l) => idx.includes('hreflang="' + l + '"')), 'zh-CN/en/x-default');
  for (const p of ['llms.txt', 'llms-full.txt', 'nf.txt', 'agent.txt', 'facts.json', 'run.sh', 'robots.txt', 'sitemap.xml', 'worker.js', '_headers']) {
    check('机器面在场 ' + p, has(p), has(p) ? String(fs.statSync(path.join(SITE, p)).size) + 'B' : '缺');
  }
  let fj = null;
  try { fj = JSON.parse(read('facts.json')); } catch (e) { check('facts.json 可解析', false, e.message); }
  if (fj) {
    check('facts.json schema', fj.schema === 'nf-facts/1', fj.schema);
    const q = ((fj.facts || []).find((x) => x.id === 'quality') || {}).claim_zh || '';
    check('facts 质量凭证与 llms-full 一致', read('llms-full.txt').includes(q.replace('质量凭证：', '')), q);
    check('facts 定义句在场', (fj.subject || {}).definition_zh && read('llms-full.txt').includes(fj.subject.definition_zh), 'definition_zh');
  }
  const hd = read('_headers');
  const missing = MACHINE.filter((p) => p !== '/use/' && p !== '/en/use/' && p !== '/404.html' && p !== '/assets/site.css').filter((p) => !hd.includes('\n' + p + '\n'));
  check('_headers 覆盖机器面', missing.length === 0, missing.length ? missing.join(' ') : '全覆盖');
  check('_headers 有跨域', (hd.match(/Access-Control-Allow-Origin/g) || []).length >= 5, String((hd.match(/Access-Control-Allow-Origin/g) || []).length) + ' 处');
  const rb = read('robots.txt');
  const ua = (rb.match(/^User-agent:/gm) || []).length;
  check('robots AI 抓取面', ua >= 12 && rb.includes('GPTBot') && rb.includes('ClaudeBot') && rb.includes('PerplexityBot'), ua + ' 条 User-agent');
  check('robots 内容信号', rb.includes('Content-Signal:'), 'Content-Signal');
  check('robots 指向 sitemap', rb.includes('Sitemap: ' + origin + '/sitemap.xml'), 'sitemap');
  const sm = read('sitemap.xml');
  check('sitemap 覆盖四页', ['/', '/en/', '/use/', '/en/use/'].every((p) => sm.includes('<loc>' + origin + p + '</loc>')), '4 个 loc');
  check('run.sh 是脚本', read('run.sh').startsWith('#!'), read('run.sh').split('\n')[0]);
  const wk = read('worker.js');
  check('worker 内容协商', wk.includes('text/markdown') && wk.includes('env.ASSETS'), 'markdown + ASSETS');
  check('worker www 跳转', wk.includes('301'), '301');
  const foreign = [];
  for (const p of ['index.html', 'en/index.html', 'use/index.html', 'en/use/index.html', 'llms.txt', 'llms-full.txt', 'nf.txt', 'agent.txt', 'facts.json', 'robots.txt', 'sitemap.xml']) {
    const t = read(p);
    for (const b of KNOWN_BASES) { if (b !== origin && t.includes(b)) { foreign.push(p + ' <- ' + b); } }
  }
  check('无其他基址残留', foreign.length === 0, foreign.length ? foreign.join(' , ') : '0 处');
  console.table(rows);
  const bad = rows.filter((r) => r.结果 === 'FAIL');
  console.log(bad.length ? '✗ 离线体检 ' + bad.length + ' 项未过' : '✓ 离线体检全过（' + rows.length + ' 项 · origin=' + origin + '）');
  process.exit(bad.length ? 1 : 0);
}

(async () => {
  const get = async (p, opt) => {
    for (let i = 0; i < 3; i++) {
      try { return await fetch(origin + p, opt || {}); } catch { await new Promise((r) => setTimeout(r, 600)); }
    }
    return null;
  };
  const idxRes = await get('/');
  const html = idxRes ? await idxRes.text() : '';
  check('首页 200', !!idxRes && idxRes.status === 200, idxRes ? idxRes.status : 'no response');
  const canon = (html.match(/rel="canonical" href="([^"]+)"/) || [])[1] || '';
  check('canonical 自指', canon === origin + '/', canon || '(缺失)');
  check('hreflang 三向', ['zh-CN', 'en', 'x-default'].every((l) => html.includes('hreflang="' + l + '"')), (html.match(/hreflang="([^"]+)"/g) || []).join(','));
  const { ok: ldOk, types: ldTypes } = ldTypesOf(html);
  check('JSON-LD 可解析', ldOk, ldTypes.join('+'));
  check('JSON-LD 含如何接入', ldTypes.includes('SoftwareApplication') || ldTypes.includes('HowTo'), ldTypes.join('+'));
  const foreign = KNOWN_BASES.filter((b) => b !== origin).filter((b) => html.includes(b));
  check('无其他基址残留', foreign.length === 0, foreign.length ? foreign.join(' , ') : '0 处');

  const q = (html.match(/verify v\d+\.\d+ · check\d+-\d+ · PASS=\d+/) || [])[0] || '';
  const fj = await get('/facts.json?v=' + Math.random().toString(36).slice(2));
  let fjText = '';
  if (fj) { fjText = await fj.text(); }
  check('facts.json 200 + JSON', !!fj && fj.status === 200, fj ? fj.status : 'no response');
  let fjOk = false; let fjQuality = '';
  try { const j = JSON.parse(fjText); fjQuality = ((j.facts || []).find((x) => x.id === 'quality') || {}).claim_zh || ''; fjOk = j.schema === 'nf-facts/1'; } catch { fjOk = false; }
  check('facts.json 可解析 + schema', fjOk, fjOk ? 'nf-facts/1' : 'bad');
  check('facts 与首页数字一致', !!q && fjQuality.includes(q), q + ' vs ' + fjQuality);

  for (const p of MACHINE) {
    const r = await get(p + '?v=' + Math.random().toString(36).slice(2));
    check(p + ' 200', !!r && r.status === 200, r ? r.status : 'no response');
  }
  const nf = await get('/definitely-not-here-' + Date.now());
  check('未知路径 404', !!nf && nf.status === 404, nf ? nf.status : 'no response');

  const c1 = await get('/nf.txt', { method: 'HEAD' });
  check('/nf.txt 类型与跨域', !!c1 && /text\/plain/.test(c1.headers.get('content-type') || '') && c1.headers.get('access-control-allow-origin') === '*',
        c1 ? (c1.headers.get('content-type') || '') + ' / ' + (c1.headers.get('access-control-allow-origin') || '') : 'no response');
  const c2 = await get('/facts.json', { method: 'HEAD' });
  check('/facts.json 类型与跨域', !!c2 && /application\/json/.test(c2.headers.get('content-type') || '') && c2.headers.get('access-control-allow-origin') === '*',
        c2 ? (c2.headers.get('content-type') || '') + ' / ' + (c2.headers.get('access-control-allow-origin') || '') : 'no response');
  const md = await get('/', { headers: { accept: 'text/markdown' } });
  const mdType = md ? (md.headers.get('content-type') || '') : '';
  const mdBody = md ? await md.text() : '';
  check('首页内容协商 text/markdown', /text\/markdown/.test(mdType) && mdBody.includes('NinFenz'), mdType || 'no response');

  const head = await get('/', { method: 'HEAD' });
  const want = ['X-Content-Type-Options', 'Referrer-Policy', 'X-Frame-Options', 'Permissions-Policy'];
  check('安全头齐备', !!head && want.every((h) => head.headers.get(h)), head ? want.map((h) => h + '=' + (head.headers.get(h) ? 'y' : 'n')).join(' ') : 'no response');
  const css = await get('/assets/site.css', { method: 'HEAD' });
  check('资产长缓存', !!css && /max-age=31536000/.test(css.headers.get('cache-control') || ''), css ? (css.headers.get('cache-control') || '') : 'no response');
  const www = await get('/', { redirect: 'manual' });
  check('根请求 200', !!www && (www.status === 200 || www.status === 301), www ? www.status : 'no response');

  console.table(rows);
  const failed = rows.filter((r) => r.结果 === 'FAIL');
  console.log(failed.length ? '✗ ' + failed.length + ' 项未过' : '✓ 全部通过（' + rows.length + ' 项 · origin=' + origin + '）');
  process.exit(failed.length ? 1 : 0);
})();
