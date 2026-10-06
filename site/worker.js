// NinFenz 站点 Worker：把 www.* 301 到裸域，其余全部交给静态资产。
//
// 为什么放在 Worker 层而不是 Cloudflare Redirect Rules：
// Redirect Rules 需要 Zone Rules 权限（当前 API token 为 403），而 Worker 自持 301
// 不依赖额外授权，且随版本一起受代码评审与回滚。
// 配合 wrangler.jsonc 的 assets.run_worker_first = true：每个请求都先进这里，
// 非 www 主机再原样交回 env.ASSETS.fetch()（_headers 规则照旧生效）。

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname.startsWith('www.')) {
      url.hostname = url.hostname.slice(4);
      return Response.redirect(url.toString(), 301);
    }
    return env.ASSETS.fetch(request);
  },
};
