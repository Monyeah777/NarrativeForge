#!/usr/bin/env node
// IndexNow 提交器：把站点 URL 推给 api.indexnow.org（Bing / Yandex / Seznam / Naver 共享）。
//
// 用法：
//   node site/tools/indexnow.mjs              # 按 site/tools/indexnow.json 的 urlList 提交
//   node site/tools/indexnow.mjs --all        # 提交 sitemap.xml 里的全部 loc
//   node site/tools/indexnow.mjs --dry-run    # 只打印将提交的内容（不联网）
//
// 前置：密钥文件必须已在站点根可访问（https://<host>/<key>.txt，内容逐字等于 key）。
// 设计纪律：先自证密钥可达再提交；响应码按官方口径解释；失败给修复指引，不静默。
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const SITE = path.resolve(HERE, '..');
const cfg = JSON.parse(fs.readFileSync(path.join(HERE, 'indexnow.json'), 'utf8'));
const dry = process.argv.includes('--dry-run');
const all = process.argv.includes('--all');

function sitemapUrls() {
  const xml = fs.readFileSync(path.join(SITE, 'sitemap.xml'), 'utf8');
  return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
}
const urlList = all ? sitemapUrls() : cfg.urlList;
const payload = { host: cfg.host, key: cfg.key, keyLocation: cfg.keyLocation, urlList };

console.log('== IndexNow 提交 ==');
console.log('  端点 ' + cfg.endpoint);
console.log('  覆盖 ' + (cfg.enginesCovered || []).join(' / '));
console.log('  keyLocation ' + cfg.keyLocation);
console.log('  URL ' + urlList.length + ' 条');
for (const u of urlList) console.log('    - ' + u);

if (dry) {
  console.log('（dry-run：未联网）');
  process.exit(0);
}

async function main() {
  const kf = await fetch(cfg.keyLocation, { cache: 'no-store' });
  const body = (await kf.text()).trim();
  if (!kf.ok) { console.error('✗ 密钥文件不可达 HTTP ' + kf.status + '（修复指引：确认 ' + cfg.keyLocation + ' 已部署）'); process.exit(2); }
  if (body !== cfg.key) { console.error('✗ 密钥文件内容与 key 不一致（修复指引：文件内容必须逐字等于 key）'); process.exit(2); }
  console.log('  ✓ 密钥文件可达且一致');

  const res = await fetch(cfg.endpoint, {
    method: 'POST',
    headers: { 'content-type': 'application/json; charset=utf-8' },
    body: JSON.stringify(payload)
  });
  const text = (await res.text()).trim();
  const explain = {
    200: '已接收', 202: '已接收，待处理', 400: '请求格式错误', 403: '密钥校验失败',
    422: 'URL 不属于该 host 或格式非法', 429: '提交过频（等一天再试）'
  }[res.status] || '未知响应码';
  console.log('  → HTTP ' + res.status + ' ' + explain + (text ? ' · ' + text.slice(0, 200) : ''));
  console.log(res.status === 200 || res.status === 202
    ? '✓ 已分发（Bing / Yandex / Seznam / Naver）'
    : '✗ 未通过（按上表处理；各引擎也可直连：bing/yandex/seznam/naver + /indexnow）');
  process.exit(res.status === 200 || res.status === 202 ? 0 : 1);
}
main().catch(function (e) {
  console.error('✗ 提交失败：' + (e && e.message ? e.message : e));
  console.error('  修复指引：本机出网需代理时设 HTTPS_PROXY=http://127.0.0.1:65532 与 NODE_USE_ENV_PROXY=1');
  process.exit(1);
});
