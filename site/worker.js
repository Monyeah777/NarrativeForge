// NinFenz 站点 Worker：www.* 301 到裸域；首页支持机器面内容协商；其余交给静态资产。
//
// 三件事，按序：
//   1) www.* -> 裸域 301（Redirect Rules 需要 Zone Rules 权限，Worker 自持不依赖额外授权）
//   2) 首页与 /en/ 上出现 Accept: text/markdown 时，回 /llms-full.txt 单文件机器面
//      （生成式引擎与 agent 常用该协商；浏览器不会发这个 Accept，故对人无影响）
//   3) 其余一律原样交回 env.ASSETS.fetch()（_headers 规则照旧生效）
//
// 配合 wrangler.jsonc 的 assets.run_worker_first = true 与 assets.binding = "ASSETS"。

const MARKDOWN_ROUTES = new Set(['/', '/en/', '/en']);

// 客户端是否**明确**点名 markdown（2026-10-08 修）：
// - `q=0` 按 RFC 9110 §12.5.1 = 明确不要，旧实现用 includes() 会照回 markdown；
// - 通配 `*/*` / `text/html` 不触发——curl 等通用客户端默认发 `*/*`，据此回 markdown 会让
//   它们拿到「意外类型」；协商只在客户端点名 text/markdown（或 text/*）时生效。
function wantsMarkdown(accept) {
  for (const part of String(accept).split(',')) {
    const [raw, ...params] = part.split(';');
    const type = raw.trim().toLowerCase();
    if (type !== 'text/markdown' && type !== 'text/*') continue;
    const q = params.map((p) => p.trim().toLowerCase()).find((p) => p.startsWith('q='));
    if (q !== undefined && Number(q.slice(2)) === 0) continue;
    return true;
  }
  return false;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname.startsWith('www.')) {
      url.hostname = url.hostname.slice(4);
      return Response.redirect(url.toString(), 301);
    }
    if (request.method === 'GET' && MARKDOWN_ROUTES.has(url.pathname)) {
      const accept = request.headers.get('accept') || '';
      if (wantsMarkdown(accept)) {
        try {
          const assetReq = new Request(new URL('/llms-full.txt', url.origin), { headers: request.headers });
          const res = await env.ASSETS.fetch(assetReq);
          if (res.ok) {
            return new Response(res.body, {
              status: 200,
              headers: {
                'content-type': 'text/markdown; charset=utf-8',
                'cache-control': 'public, max-age=300',
                'vary': 'Accept',
                'x-ninfenz-negotiated': 'llms-full.txt',
              },
            });
          }
        } catch (e) {
          // 协商失败不改变正常行为：回落到静态资产
        }
      }
    }
    return env.ASSETS.fetch(request);
  },
};
