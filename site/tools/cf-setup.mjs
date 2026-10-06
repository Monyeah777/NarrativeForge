#!/usr/bin/env node
// NinFenz 站点上线：Cloudflare Registrar 注册 + Worker 自定义域 + Zone 加固
//
// 设计纪律：
//  - 默认 **dry-run**（只查价格与状态，不产生任何费用/变更）
//  - 注册是**计费且不可退**的动作 → 必须同时给 --register 且 CF_CONFIRM_REGISTER=<域名>
//  - 不写任何密钥到磁盘；token 只从环境变量读
//
// 用法：
//   CLOUDFLARE_API_TOKEN=... node site/tools/cf-setup.mjs                    # 只查价（安全）
//   CLOUDFLARE_API_TOKEN=... node site/tools/cf-setup.mjs --attach           # 绑定已注册域 + Zone 加固
//   CLOUDFLARE_API_TOKEN=... CF_CONFIRM_REGISTER=ninfenz.dev node site/tools/cf-setup.mjs --register
//
// 代理（本机必需）：HTTPS_PROXY=http://127.0.0.1:65532  HTTP_PROXY=http://127.0.0.1:65532

const API = 'https://api.cloudflare.com/client/v4';
const TOKEN = process.env.CLOUDFLARE_API_TOKEN || '';
const WORKER = process.env.CF_WORKER_NAME || 'ninfenz';
const WANT = (process.env.CF_DOMAINS || 'ninfenz.dev,ninfenz.com').split(',').map((s) => s.trim()).filter(Boolean);
const args = new Set(process.argv.slice(2));
const DO_REGISTER = args.has('--register');
const DO_ATTACH = args.has('--attach');

if (!TOKEN) {
  console.error('缺 CLOUDFLARE_API_TOKEN（环境变量；不要写进文件）');
  process.exit(2);
}

async function cf(path, init = {}) {
  const res = await fetch(API + path, {
    ...init,
    headers: {
      Authorization: 'Bearer ' + TOKEN,
      'Content-Type': 'application/json',
      ...(init.headers || {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!body.success) {
    const err = (body.errors || []).map((e) => e.code + ':' + e.message).join(' | ');
    throw new Error(res.status + ' ' + path + ' -> ' + (err || 'unknown error'));
  }
  return body.result;
}

(async () => {
  console.log('== 0. token 自校验 ==');
  const v = await cf('/user/tokens/verify');
  console.log('   token status = ' + v.status);

  console.log('== 1. 解析账号 ==');
  let accountId = process.env.CLOUDFLARE_ACCOUNT_ID || '';
  if (!accountId) {
    const accs = await cf('/accounts');
    if (!accs.length) throw new Error('该 token 看不见任何账号（需 Account: Workers Scripts:Edit 或显式给 CLOUDFLARE_ACCOUNT_ID）');
    accountId = accs[0].id;
    console.log('   账号: ' + accs[0].name + ' / ' + accountId);
  } else {
    console.log('   账号(env): ' + accountId);
  }

  console.log('== 2. 域名实时查价（domain-check，直连注册局）==');
  const check = await cf('/accounts/' + accountId + '/registrar/domain-check', {
    method: 'POST',
    body: JSON.stringify({ domains: WANT }),
  });
  const rows = [];
  for (const d of check.domains || []) {
    const p = d.pricing || {};
    rows.push({ name: d.name, registrable: d.registrable, tier: d.tier, price: p.registration_cost, renew: p.renewal_cost, currency: p.currency, reason: d.reason || '' });
  }
  console.table(rows);

  if (!DO_REGISTER) {
    console.log('== 3. 未注册（dry-run）==');
    console.log('   要真正注册：先确认上表价格，然后设 CF_CONFIRM_REGISTER=<域名> 并加 --register');
    return;
  }

  const target = WANT.find((d) => rows.some((r) => r.name === d && r.registrable));
  if (!target) throw new Error('目标域名不可注册（见上表 reason）');
  if (process.env.CF_CONFIRM_REGISTER !== target) {
    throw new Error('拒绝执行：注册计费且不可退。请显式设置 CF_CONFIRM_REGISTER=' + target);
  }
  const price = (rows.find((r) => r.name === target) || {}).price;
  console.log('== 3. 注册 ' + target + '（价格 ' + price + '，计费且不可退）==');

  const reg = await cf('/accounts/' + accountId + '/registrar/registrations', {
    method: 'POST',
    body: JSON.stringify({ domain_name: target }),
  });
  console.log('   state=' + reg.state + ' completed=' + reg.completed);
  console.log('   ' + JSON.stringify(reg.context ? reg.context.registration : {}));

  if (!DO_ATTACH) {
    console.log('== 4. 未绑定（加 --attach 会绑定 Worker 自定义域并做 Zone 加固）==');
    return;
  }
  await attach(accountId, target);
})().catch((e) => {
  console.error('X ' + e.message);
  process.exit(1);
});

async function attach(accountId, domain) {
  console.log('== 4. 绑定 Worker 自定义域 ==');
  const dom = await cf('/accounts/' + accountId + '/workers/domains', {
    method: 'PUT',
    body: JSON.stringify({ zone_name: domain, hostname: domain, service: WORKER, environment: 'production' }),
  });
  console.log('   ' + JSON.stringify(dom));

  console.log('== 5. Zone 加固（GEO/安全默认值）==');
  const zones = await cf('/zones?name=' + domain);
  if (!zones.length) {
    console.log('   zone 尚未激活（刚注册的域可能要等 NS 生效 + 几分钟）；稍后重跑 --attach');
    return;
  }
  const zoneId = zones[0].id;
  const settings = [
    ['ssl', 'strict'],
    ['always_use_https', 'on'],
    ['min_tls_version', '1.2'],
    ['automatic_https_rewrites', 'on'],
    ['brotli', 'on'],
    ['http3', 'on'],
    ['early_hints', 'on'],
  ];
  for (const [id, value] of settings) {
    try {
      await cf('/zones/' + zoneId + '/settings/' + id, { method: 'PATCH', body: JSON.stringify({ value }) });
      console.log('   ✓ ' + id + ' = ' + value);
    } catch (e) {
      console.log('   ✗ ' + id + ' -> ' + e.message);
    }
  }
  console.log('== 6. 上线自检 ==');
  console.log('   curl -sI https://' + domain + '/ | findstr /I "HTTP/ cache-control x-content-type"');
  console.log('   curl -s  https://' + domain + '/llms.txt');
}
