#!/usr/bin/env node
// 站点体检：对给定 origin 跑一套 GEO/可用性判据（只读、不写盘）
// 用法：node site/tools/site-check.mjs [origin]     # 缺省读 site/index.html 里的 canonical
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const SITE = path.resolve(HERE, '..');
const idx = fs.readFileSync(path.join(SITE, 'index.html'), 'utf8');
const origin = (process.argv[2] || (idx.match(/rel="canonical" href="(https:\/\/[^\/"]+)/) || [])[1] || '').replace(/\/+$/, '');
if (!origin) { console.error('无法确定 origin'); process.exit(2); }

(async () => {
  const rows = [];
  const get = async (p, method = 'GET') => {
    for (let i = 0; i < 3; i++) {
      try { return await fetch(origin + p, { method }); } catch { await new Promise((r) => setTimeout(r, 600)); }
    }
    return null;
  };
  const check = (name, ok, detail) => rows.push({ 判据: name, 结果: ok ? 'PASS' : 'FAIL', 详情: detail });

  const idxRes = await get('/');
  const html = idxRes ? await idxRes.text() : '';
  check('首页 200', !!idxRes && idxRes.status === 200, idxRes ? String(idxRes.status) : 'no response');
  const canon = (html.match(/rel="canonical" href="([^"]+)"/) || [])[1] || '';
  check('canonical 自指', canon === origin + '/', canon || '(缺失)');
  check('hreflang 三向', ['zh-CN', 'en', 'x-default'].every((l) => html.includes('hreflang="' + l + '"')), (html.match(/hreflang="([^"]+)"/g) || []).join(','));
  const lds = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  let ldTypes = [];
  let ldOk = lds.length > 0;
  for (const b of lds) { try { const j = JSON.parse(b); ldTypes.push(...(j['@graph'] ? j['@graph'].map((x) => x['@type']) : [j['@type']])); } catch { ldOk = false; } }
  check('JSON-LD 可解析', ldOk, ldTypes.join('+'));
  // 判据应是「除自身 canonical 基址外，不出现其他已知基址」——不能写死某一个旧域名，否则换域后必误报。
  const KNOWN_BASES = ['https://ninfenz.dev', 'https://ninfenz.1764861918.workers.dev', 'https://monyeah777.github.io/NinFenz', 'https://monyeah777.github.io'];
  const foreign = KNOWN_BASES.filter((b) => b !== origin).filter((b) => html.includes(b));
  check('无其他基址残留', foreign.length === 0, foreign.length ? foreign.join(' , ') : '0 处');

  for (const p of ['/en/', '/robots.txt', '/sitemap.xml', '/llms.txt', '/404.html', '/assets/site.css']) {
    const r = await get(p + '?v=' + Math.random().toString(36).slice(2));
    check(p + ' 200', !!r && r.status === 200, r ? String(r.status) : 'no response');
  }
  const nf = await get('/definitely-not-here-' + Date.now());
  check('未知路径 404', !!nf && nf.status === 404, nf ? String(nf.status) : 'no response');

  const head = await get('/', 'HEAD');
  const want = ['X-Content-Type-Options', 'Referrer-Policy', 'X-Frame-Options', 'Permissions-Policy'];
  check('安全头齐备', !!head && want.every((h) => head.headers.get(h)), head ? want.map((h) => h + '=' + (head.headers.get(h) ? 'y' : 'n')).join(' ') : 'no response');
  const css = await get('/assets/site.css', 'HEAD');
  check('资产长缓存', !!css && /max-age=31536000/.test(css.headers.get('cache-control') || ''), css ? (css.headers.get('cache-control') || '') : 'no response');

  console.table(rows);
  const failed = rows.filter((r) => r.结果 === 'FAIL');
  console.log(failed.length ? '✗ ' + failed.length + ' 项未过' : '✓ 全部通过（origin=' + origin + '）');
  process.exit(failed.length ? 1 : 0);
})();
