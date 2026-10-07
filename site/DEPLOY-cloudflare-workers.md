# Cloudflare Workers 部署（NinFenz 静态站）

> **当前工期（2026-10-06）**：域名 **ninfenz.dev** 已注册并挂上自定义域（大陆裸网直连可达），
> 站内 canonical / hreflang / og:url / JSON-LD @id / sitemap / robots / llms.txt **已全部指向该地址**（自洽）。
> 买下 `ninfenz.dev` 后切回：`node site/tools/set-origin.mjs https://ninfenz.dev --write && npx wrangler deploy`。


> 对应文档：Workers Builds → Settings → Build（字段名与默认值取自 Cloudflare 官方文档，2026-09-22 / 10-01 更新）。
> 本仓库是**纯静态站**（`site/`），因此走 **Workers 静态资产（assets-only，无 `main` 脚本）**，不需要任何构建步骤。

---

## 一、面板四个字段（照抄）

| 字段 | 填什么 | 说明 |
|---|---|---|
| **构建命令**（Build command，可选） | **留空** | 站点是预构建的静态 HTML，没有构建步骤。留空即跳过（Cloudflare 仍会尝试依赖安装，但仓库根无 `package.json`/锁文件，等于无操作）。 |
| **部署命令**（Deploy command） | `npx wrangler deploy` | 即默认值。它读取仓库根的 `wrangler.jsonc`，把 `./site` 作为静态资产上传并发布。 |
| **预览命令**（Preview command） | `npx wrangler versions upload` | 二选一，见下方「预览命令怎么选」。 |
| **根目录**（Root directory，高级设置） | **留空** | 部署命令在仓库根执行；`wrangler.jsonc` 与 `site/` 都在根。 |

### 预览命令怎么选

| 选项 | 产物 | 何时用 |
|---|---|---|
| `npx wrangler preview`（**Cloudflare 默认**） | 一个 **Preview**（含 Preview URL），切换生产流量时才需要 promote | 想看「改动后的整站」并且要一个稳定 URL 给人点开 |
| `npx wrangler versions upload`（**推荐**） | 一个 **Worker Version**（含 Version URL） | 静态站改动的常规评审：更快、更轻；不产生分支隔离资源 |

> 官方文档原话：Preview command「defaults to `npx wrangler preview`, which creates or updates a Preview and produces a Preview URL」；改成 `npx wrangler versions upload` 则「creates a Worker version and Version URL instead of a Preview」。

---

## 二、高级设置（逐项）

| 项 | 我们的取值 | 备注 |
|---|---|---|
| **根目录 / Root directory** | 留空 | 若将来把站点挪到子目录（如 monorepo），这里填子目录路径 |
| **构建输出目录 / Build output directory** | **不存在这一项** | 那是 **Pages** 的字段。Workers 的资产目录由 `wrangler.jsonc` 的 `assets.directory`（=`./site`）决定 |
| **构建变量与密钥 / Build variables and secrets** | 可选：`WRANGLER_SEND_METRICS=false` | 只在构建期可见，运行期不可见；构建镜像相关的变量以官方 Build image 文档为准 |
| **生产分支 / Branch control** | `main` | 推到 `main` → 构建 + **部署命令** |
| **预览构建 / Preview builds** | 开启 | 非 `main` 分支 → 走**预览命令**；GitHub 仓库还会在 PR 里回评论 |
| **Wrangler 版本** | 用 Cloudflare 默认 | 官方说明「Workers Builds will use the Wrangler version set in your `package.json`」；仓库根无 `package.json`，故取默认。要钉版本就在根加 `package.json` 的 `devDependencies.wrangler`（需要时我加，并生成锁文件） |
| **API token / Git 账号** | 用 Cloudflare 生成的 token 或自备 | 首次连接仓库时选择 |

---

## 三、配套文件（已在仓库里）

| 文件 | 作用 |
|---|---|
| `wrangler.jsonc` | Worker 名 `ninfenz`；`assets.directory = ./site`；`html_handling = auto-trailing-slash`；`not_found_handling = 404-page` |
| `site/_headers` | 安全头（nosniff / Referrer-Policy / X-Frame-Options / Permissions-Policy）+ 缓存策略（`/assets/*` 长缓存；HTML 不缓存；llms.txt/robots/sitemap 短缓存） |
| `site/.assetsignore` | 不把 `CNAME`、`README.md`、`.nojekyll`、`_headers` 当资产上传 |

> `_headers` 与 `.assetsignore` 的语义均来自官方文档：`_headers` 放在**静态资产目录根**、自身不被当作资产提供、其规则**覆盖**默认响应头；`.assetsignore` 语法同 `.gitignore`。

---

## 四、自定义域

面板里 **Workers → 你的 Worker → Settings → Domains & Routes → Add custom domain** 填 `ninfenz.dev`（DNS 在 Cloudflare 时自动建记录并签证书）。
**不要**用 `site/CNAME`——那是 GitHub Pages 的做法，Workers 不读它（已加入 `.assetsignore` 不上传）。

---

## 五、上线后自检

```bash
curl -sI https://ninfenz.dev/ | findstr /I "HTTP/ cache-control x-content-type"
curl -s  https://ninfenz.dev/ | findstr /I "NinFenz 宁封子"       # 中文页
curl -s  https://ninfenz.dev/en/ | findstr /I "NinFenz contract" # 英文页
curl -sI https://ninfenz.dev/assets/demo.gif | findstr /I cache  # 应命中 immutable
curl -s  https://ninfenz.dev/nope | findstr /I "404"             # 应回站内 404.html
```

同时确认：`/robots.txt` 指向 `/sitemap.xml`；`/llms.txt` 可读；两个页面的 canonical/hreflang 指向 `ninfenz.dev`。

---

## 六、注意

- **仓库改名与域名的先后**：仓库内链接已指向 `github.com/Monyeah777/NinFenz`，**GitHub 仓库改名之前会 404**；站点上线前建议先完成 GitHub 改名。
- **静态站不含构建**：以后若引入构建（例如压缩 HTML），把命令写进 **构建命令** 字段并把产物目录改成 `assets.directory` 指向的目录即可；当前不需要。

---

## 七、网址形状与 canonical（`ninfenz.<账号subdomain>.workers.dev` 是什么）

| 网址 | 由什么决定 | 说明 |
|---|---|---|
| `ninfenz.<账号subdomain>.workers.dev`（例：`ninfenz.1764861918.workers.dev`） | Worker `name`（= `ninfenz`，见 `wrangler.jsonc`）+ **账号级** workers.dev subdomain | 官方规则：`<YOUR_WORKER_NAME>.<YOUR_SUBDOMAIN>.workers.dev`。`1764861918` 这种数字段是**账号的 subdomain**，可在 **Workers & Pages →「Your subdomain」旁的 Change** 修改；改一次，该账号下**所有** Worker 的 workers.dev 网址一起变 |
| `https://ninfenz.dev` | 自定义域（Settings → Domains & Routes → Add custom domain） | **官方明确建议生产用 route 或自定义域**；workers.dev 被当作 Free website，定位是个人 / 爱好项目，不适合business-critical |

- **`ninfenz.workers.dev`（只有两段）不存在**——必须有账号 subdomain 那一段。
- 站内 canonical / hreflang 已全部指向 `https://ninfenz.dev/`；两个源同时可访问时，canonical 声明首选是 `ninfenz.dev`。
- 若要让 workers.dev 副本**彻底不被检索到**：绑定自定义域成功后，取消 `wrangler.jsonc` 里 `"workers_dev": false` 的注释，再 `npx wrangler deploy` 一次。
- `npx wrangler versions upload`（预览命令）产出的 Version URL 同样挂在 workers.dev subdomain 下；关闭 `workers_dev` 前请确认自己不再需要它做预览评审。

---

## 八、上线后的实际架构（2026-10-06 定稿）

| 组成 | 说明 |
|---|---|
| `wrangler.jsonc` · `main: site/worker.js` | 从 assets-only 升级为**静态资产 + 轻量 Worker**：Worker 只做 `www.*` → 裸域 **301**，其余原样交回 `env.ASSETS.fetch()` |
| `assets.binding: "ASSETS"` | **必需**。`run_worker_first: true` 时若不声明绑定，`env.ASSETS` 是 `undefined`（本波 dry-run 实测拦下，否则全站崩） |
| `assets.run_worker_first: true` | 每个请求先过 Worker（www 跳转必须），非 www 再交回资产层——`_headers` 规则实测照旧生效 |
| `workers_dev: false` | 关掉 `*.workers.dev` 路由，全网只留 `ninfenz.dev` / `www` 一个可达源 |
| 自定义域 | `ninfenz.dev` + `www.ninfenz.dev`（Workers 路由托管，证书自签）；Zone：`ssl=strict` · `always_use_https` · `min_tls_version=1.2` · `automatic_https_rewrites` · `brotli` · `http3` · `early_hints` · HSTS(180d) |

### 为什么不用 Cloudflare Redirect Rules 做 www 跳转

Redirect Rules 需要 Zone Rules 权限（当前 API token 返回 403）；放在 Worker 层不依赖额外授权，且 301 逻辑随版本一起受评审与回滚。

### 发布钩子：站点数字必须与真源同步

`site/` 是独立于生成器的手写静态面，仓库发版改了 verify/check/PASS 数字它不会自动跟随。
2026-10-06 实测就漂移过：站点三面写 `v2.29/check1-39/PASS=68`，真源已是 `v2.30/check1-40/PASS=72`。

```bash
node site/tools/sync-numbers.mjs          # 检查（漂移则退出码 1）——发布前把关
node site/tools/sync-numbers.mjs --write  # 同步写入
```

真源 = 仓库根 `llms.txt` 的 `nf:stats` 区块（由 `nf stats --write` 生成）。

### 上线自检（一条命令，14 项判据）

```bash
node site/tools/site-check.mjs https://ninfenz.dev
```
---

## 九、机器面（2026-10-07 增补：让 AI 客户端与 agent 直取）

站点从「给人看的页面」扩到「给机器直取的面」。全部同源、纯静态、无构建步骤：

| 面 | 给谁 | 内容 |
|---|---|---|
| `/llms.txt` | 检索 / AI（索引） | 有哪些面可读（llms.txt 惯例清单） |
| `/llms-full.txt` | AI（完整） | 一文件读全：定义 / 事实 / 术语表 / 上手四条路径 / FAQ / 引用格式 |
| `/nf.txt` | 客户端 AI | 装载指令：三条铁律 + 分支表 + 取件基底（读到即执行） |
| `/agent.txt` | agent | 命令序列 + 每步期望输出（doctor 16/16 · verify.sh PASS=72 · conformance 27/27） |
| `/facts.json` | AI（机读） | 事实清单，每条带真源与落地锚点；scale.values 与 protocol/repo_stats.json 机检对齐 |
| `/run.sh` | agent | 免安装引导（默认 clone + 只读体检；--full 追加全量门禁） |

### 为什么机器面要显式 Content-Type 与 CORS

浏览器内的 AI 客户端（网页版助理、插件）抓取跨域资源时，缺 Access-Control-Allow-Origin 会被浏览器直接挡掉；
缺明确 Content-Type 时有些客户端会按二进制处理。故 `_headers` 对上述六个面统一下发
`Content-Type: text/plain|application/json; charset=utf-8` 与 `Access-Control-Allow-Origin: *`，
并给 300 秒短缓存（改版后快速生效）。

### 内容协商（Accept: text/markdown）

`site/worker.js` 在 `/` 与 `/en/` 上：若请求带 `Accept: text/markdown`，直接回 `/llms-full.txt`
（`content-type: text/markdown`，`Vary: Accept`）。浏览器不会发这个 Accept，故对人零影响；
生成式引擎与 agent 常用该协商拿单文件。

### 抓取与引用信号

`robots.txt` 逐条列出 20+ AI 抓取面（GPTBot / OAI-SearchBot / ClaudeBot / PerplexityBot /
Google-Extended / Applebot-Extended / Amazonbot / CCBot / Bytespider / DuckAssistBot / Meta-ExternalAgent /
MistralAI-User / cohere-ai 等）并显式 `Allow: /`，另加 `Content-Signal: search=yes, ai-input=yes, ai-train=yes`
声明本域对检索、生成式引用与训练取用的立场。

### 站点侧门禁（两条，都不需要网络）

```bash
node site/tools/sync-numbers.mjs            # 数字与真源一致（质量凭证 + 规模 8 个数）；漂移即红
node site/tools/site-check.mjs --offline    # 离线判据：JSON-LD / 机器面在场 / _headers 覆盖 / robots / 无旧基址
node site/tools/site-check.mjs              # 联网判据（部署后）：状态码 / CORS / Content-Type / 协商 / facts 真值
```

CI 里已接 `sync-numbers.mjs` 与 `site-check.mjs --offline` 两步（.github/workflows/ci-verify.yml），
所以站点数字或机器面漂移会与仓库门禁一起红。

