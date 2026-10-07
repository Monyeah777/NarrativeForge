# site/ · 静态站（NinFenz 官网）

> **线上地址**：https://ninfenz.dev （Cloudflare Workers + 自定义域；切源：node site/tools/set-origin.mjs <base> --write）

纯静态、**零外部依赖**（无 CDN、无 webfont、无遥测）；双语 /（zh-CN）与 /en/。

## 三层目标形态

| 面 | 落地 |
|---|---|
| 实体面 | 首屏 canonical 定义句 + 「不是什么」+ 名称考据 + 术语表 |
| 证据面 | 可引用事实（每个数字带真源与落地锚点 #fact-*）+ 对比表 + 演示动图 + 引用段（纯文本 / APA / BibTeX） |
| 机器面 | JSON-LD（SoftwareApplication + WebSite + Person + DefinedTerm + FAQPage）· canonical · hreflang · sitemap.xml · robots.txt（Content-Signal + 20+ AI 抓取面）· llms.txt · llms-full.txt · facts.json · nf.txt · agent.txt · run.sh · 内容协商（Accept: text/markdown） |
| 部署面 | 全静态 + 轻量 Worker（见 DEPLOY-cloudflare-workers.md） |

## 文件清单

| 文件 | 给谁 | 说明 |
|---|---|---|
| index.html / en/index.html | 人 | 主页：定义 / 事实 / 三种接法 / 上手 / 对比 / FAQ / 引用段 |
| use/index.html / en/use/index.html | 人 | 「让 AI 用起来」：三种接法 + 一键复制块 + 每步期望输出 |
| llms.txt | AI（索引） | 有哪些面可读（llms.txt 惯例的清单面） |
| llms-full.txt | AI（完整） | 一文件读全：定义 / 事实 / 术语 / 上手 / FAQ / 引用 / 机器面清单 |
| nf.txt | 客户端 AI | 装载指令：三条铁律 + 分支表 + 取件基底 + 判定（读到即执行） |
| agent.txt | agent | 命令序列 + 每步期望输出（doctor 16/16 · verify.sh PASS=72 · conformance 27/27） |
| facts.json | AI（机读） | 事实清单：每条带真源与锚点；scale.values 与 repo_stats.json 机检对齐 |
| run.sh | agent | 免安装引导（默认 clone + 只读体检；--full 追加全量门禁；逐条先打印再执行） |
| robots.txt | 爬虫 | 显式欢迎 AI 检索/引用/训练取用 + Content-Signal + sitemap |
| sitemap.xml | 爬虫 | 四页（/ · /en/ · /use/ · /en/use/）+ hreflang 互指 |
| _headers | 边缘 | 安全头 + 缓存策略 + 机器面 CORS/类型 + 首页 Vary: Accept |
| worker.js | 边缘 | www -> 裸域 301；首页 Accept: text/markdown 时回 llms-full.txt |
| 404.html · CNAME · .nojekyll · .assetsignore | 平台 | 站内 404 / Pages 域 / Jekyll 关 / 上传排除 |
| assets/site.css · demo.gif · og.png | 展示 | 样式 / TUI 演示（9 秒，由 tools/make-demo-gif.py 生成）/ 分享图 |
| tools/*.mjs · tools/make-demo-gif.py | 维护 | 切源 / 数字同步 / 体检 / 演示图生成 |

## 发布前检查（先跑离线，再跑联网）

    node site/tools/sync-numbers.mjs            # 数字与真源一致（漂移即退出码 1）
    node site/tools/site-check.mjs --offline    # 离线判据：JSON-LD / 机器面齐 / CORS / 抓取规则 / 无旧基址
    npx wrangler deploy                         # 部署
    node site/tools/site-check.mjs              # 联网判据：状态码 / 响应头 / 协商 / facts 数字真值

清单一并人工过一遍：JSON-LD 可 JSON.parse；无外部资源引用（同源）；canonical / hreflang 指向 ninfenz.dev；
机器面都带 CORS 与明确 Content-Type；数字来自真源而不是手抄。

## 本地预览

    python -m http.server 8080 --directory site
    # http://127.0.0.1:8080/      中文
    # http://127.0.0.1:8080/en/   英文
    # http://127.0.0.1:8080/use/  让 AI 用起来

## 域名

| 域 | 状态 |
|---|---|
| **ninfenz.dev** | 已注册并挂上自定义域（www -> 裸域 301；大陆裸网直连可达） |
| ninfenz.com | 未注册（备选） |

## 已知状态（诚实面）

- **npm 包尚未公开发布**：packaging/npm 已备好（包名 ninfenz，npx 启动器 + payload），发布通道在
  .github/workflows/npm-publish.yml；首次发布前，站内所有 npx 说法都标注「发布后可用」。
- **workers.dev 域名**：已关闭（wrangler.jsonc 的 workers_dev: false）。大陆对该域 DNS 污染，别把它当入口。
