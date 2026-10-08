# 搜索引擎提交：站点地图 · IndexNow · 各站控制台（详细流程）

> 适用对象：NinFenz 站点（https://ninfenz.dev）。本文件是**操作手册**，不参与站点资产上传（已在 .assetsignore 里排除）。
> 最后更新：2026-10-08

---

## 0 一页速览：要提交什么、提交到哪、谁来做

| 通道 | 覆盖引擎 | 提交物 | 谁做 | 状态 |
|---|---|---|---|---|
| IndexNow（api.indexnow.org） | **Bing · Yandex · Seznam · Naver** | 4 个 URL（或整站） | 自动化，一条命令 | 已提交（见 §2 证据） |
| Google Search Console | Google | sitemap.xml + 逐 URL 请求编入 | 你（需 Google 账号） | 待你操作（§3） |
| Bing Webmaster Tools | Bing（供 DuckDuckGo/Ecosia 等下游） | 从 GSC 导入或自行验证 + sitemap | 你（微软/Google 账号） | 待你操作（§4） |
| Yandex Webmaster | Yandex | sitemap.xml | 你（Yandex 账号） | 可选（§5） |
| 百度搜索资源平台 | 百度 | sitemap.xml + 普通收录 API | 你（百度账号 + 实名） | 中国区主要入口（§6） |
| 360 / 神马 / 搜狗 / 头条 | 中国其它 | sitemap / 提交入口 | 你 | 视需要（§7） |
| AI 生成式引擎 | ChatGPT/Claude/Perplexity/… | **没有提交口**，靠 llms.txt 与抓取面 | 已在做 | 见 §9 |

**要提交的 URL 清单（四处 + 站点地图本身）**

    https://ninfenz.dev/
    https://ninfenz.dev/en/
    https://ninfenz.dev/use/
    https://ninfenz.dev/en/use/
    https://ninfenz.dev/sitemap.xml      ← 站点地图

> 机器面（/llms.txt /llms-full.txt /facts.json /nf.txt /agent.txt /run.sh）**不要**放进 sitemap：它们是给 AI 与 agent 直取的接口，不是给通用搜索引擎排名的页面；它们靠 robots.txt 显式允许 + 被引用进入 AI 索引。

---

## 1 提交前的一次性自检（都已在位，列出来便于复核）

    node site/tools/site-check.mjs --offline      # 33+ 项离线判据：canonical/hreflang/JSON-LD/机器面/CORS/抓取规则
    node site/tools/site-check.mjs https://ninfenz.dev   # 28 项联网判据：状态码/响应头/内容协商/数字真值
    node site/tools/sync-numbers.mjs             # 站点数字与仓库真源一致（防"发布旧数字"）

三项都必须绿。**搜索引擎最忌讳的两种状态**是 canonical 指向别处、sitemap 里的 URL 返回非 200 —— 这两条判据都已覆盖。

---

## 2 IndexNow：一条命令覆盖 4 个引擎（已完成）

IndexNow 是 Bing 发起、Yandex / Seznam / Naver 共同采纳的即时提交协议。它**不是**搜索引擎控制台、**不需要账号**，只要能证明域名所有权（把密钥文件放到站点根）。

已做过的事：

1. 生成密钥：ninfenzff1511339a8885ca8dbee4b8（8–128 位字母数字）
2. 放到站点根，文件内容就是密钥本身：
   https://ninfenz.dev/ninfenzff1511339a8885ca8dbee4b8.txt
3. 向 https://api.indexnow.org/indexnow POST 了 4 个 URL（见下方"响应码"与 §10 验收）

复跑（任何时候改了页面就跑）：

    node site/tools/indexnow.mjs             # 读 site/tools/indexnow.json 的 urlList 提交
    node site/tools/indexnow.mjs --dry-run   # 只打印将提交什么

等价的裸 curl（便于排查，整条一行即可）：

    curl -sS -o /dev/null -w '%{http_code}\n' -X POST 'https://api.indexnow.org/indexnow' -H 'Content-Type: application/json; charset=utf-8' -d '{"host":"ninfenz.dev","key":"ninfenzff1511339a8885ca8dbee4b8","keyLocation":"https://ninfenz.dev/ninfenzff1511339a8885ca8dbee4b8.txt","urlList":["https://ninfenz.dev/","https://ninfenz.dev/en/","https://ninfenz.dev/use/","https://ninfenz.dev/en/use/"]}'

响应码怎么读：

| 码 | 含义 | 处理 |
|---|---|---|
| 200 | 已接收 | 正常 |
| 202 | 已接收，待处理 | 正常 |
| 400 | 请求格式错误 | 检查 JSON |
| 403 | 密钥校验失败 | 确认密钥文件可访问且内容逐字等于密钥 |
| 422 | URL 不属于该 host 或格式非法 | 检查 URL |
| 429 | 提交过频 | 等一天再试，别轮询 |

各引擎也可直接收：https://www.bing.com/indexnow · https://yandex.com/indexnow · https://search.seznam.cz/indexnow · https://searchadvisor.naver.com/indexnow。用 api.indexnow.org 一次即可（它负责分发）。

---

## 3 Google Search Console（需能访问 Google）

### 3.1 建属性：选"网域（Domain）"

| 类型 | 覆盖 | 验证方式 |
|---|---|---|
| 网域 | ninfenz.dev 全部子域与协议（推荐） | 仅 DNS TXT |
| 网址前缀 | 仅你写的那个前缀 | HTML 文件 / meta 标签 / DNS / GA / GTM |

1. 打开 https://search.google.com/search-console → 添加资源 → 选 **网域** → 填 ninfenz.dev
2. Google 给一条 TXT 记录：名称填 @（或 ninfenz.dev），值为 google-site-verification=XXXXXXXX
3. **把这条值发我，我用 Cloudflare API 直接加进 DNS**（我们的 token 对该 Zone 有 DNS 编辑权）；或你自己加：Cloudflare 面板 → ninfenz.dev → DNS → 记录 → 添加记录 → 类型 TXT / 名称 @ / 内容粘贴 / TTL Auto → 保存
4. 回控制台点"验证"。DNS 生效通常 1–5 分钟；失败就等 10 分钟再点（Google 会缓存失败结果）

### 3.2 提交站点地图

左侧"站点地图" → 输入 sitemap.xml → 提交。状态应变成"成功"。

- 显示"无法获取"：先确认 sitemap 返回 200，再确认 robots.txt 里那行 Sitemap 指向同一地址
- 显示"已提交"但 URL 数 0：Google 把 sitemap 当**提示**而非保证，等 1–3 天看"已编入的网页"

### 3.3 逐个 URL 请求编入（可选，新站推荐）

顶部搜索框粘 https://ninfenz.dev/ → 回车 → "请求编入索引"。每天配额有限，只对 / 与 /use/ 用。

### 3.4 看什么指标

"网页"（已编入 / 未编入 + 原因）·"效果"（查询词、点击）·"体验"。新站头两周常见"已发现，尚未编入"，正常，别反复请求。

---

## 4 Bing Webmaster Tools

1. https://www.bing.com/webmasters → 用微软或 Google 账号登录
2. 首选路径：**从 Google Search Console 导入**（省一次验证；前提是 §3 已完成）
3. 独立验证也可以：加一条 BingSiteAuth.xml 或 DNS TXT（值发我，我加）
4. 提交站点地图：左侧"站点地图" → 填 https://ninfenz.dev/sitemap.xml
5. IndexNow：Bing 侧无需额外配置；§2 的提交会体现在"URL 提交"日志里

**本次已就位的三个验证面（2026-10-08 实测）**

| 方式 | 落地 | 实测 |
|---|---|---|
| 文件 | site/BingSiteAuth.xml（内容 user = BC986533673F959259865E7DE5291890） | https://ninfenz.dev/BingSiteAuth.xml → HTTP 200，内容逐字一致 |
| meta | 两语首页 head 的 msvalidate.01 | / 与 /en/ 的 head 均含该标签 |
| CNAME | 8cc813b1e1544d36dcad3a23c48528da → verify.bing.com | Cloudflare 记录 proxied=false（**DNS-only**），已创建 |

> 坑：这条验证用 CNAME **必须保持 DNS-only（灰云）**。若日后手滑开了橙色云代理，Bing 的校验会失败（它拿到的将是 Cloudflare 的 IP 而不是 verify.bing.com）。改任何 DNS 记录前先看这里的说明。

> Bing 的索引也供给 DuckDuckGo、Ecosia、Yahoo 等下游，Bing 一遍等于覆盖一批。

---

## 5 Yandex Webmaster（可选）

1. https://webmaster.yandex.com → 添加站点 → 验证选 DNS TXT（值发我）或 meta 标签
2. "索引" →"站点地图" → 添加 https://ninfenz.dev/sitemap.xml
3. Yandex 是 IndexNow 参与方，§2 已覆盖即时提交

---

## 6 百度搜索资源平台（中国区主要入口）

1. https://ziyuan.baidu.com → 注册/登录（需实名）→ 用户中心 → 站点管理 → 添加网站，填 https://ninfenz.dev
2. 验证三选一：
   - **DNS 验证**（推荐）：百度给一条 TXT，值发我 → 我加进 Cloudflare DNS
   - 文件验证：下载 baidu_verify_*.html 放到 site/ 根 → 我重新部署
   - CNAME 验证：可做，会多一条记录
3. 提交 sitemap：普通收录 → 资源提交 → sitemap → 填 https://ninfenz.dev/sitemap.xml
4. **主动推送 API**（比 sitemap 快，有配额）：token 在"普通收录 → 资源提交 → 推送接口"页

       curl -sS -H 'Content-Type:text/plain' --data-binary @urls.txt 'http://data.zz.baidu.com/urls?site=https://ninfenz.dev&token=你的TOKEN'
       # urls.txt 每行一个 URL；返回 {"remain":N,"success":4} 表示成功

5. 百度对备案有偏好但目前不强制；长期不收录优先查"抓取诊断"（它真的会用百度蜘蛛 UA 抓一次，能看到是否被 Cloudflare 拦或超时）

---

## 7 中国其它入口（按性价比，可选）

| 平台 | 入口 | 说明 |
|---|---|---|
| 360 搜索 | https://info.so.com/site_submit.html | 填域名 + sitemap；收录慢但成本低 |
| 神马（移动） | https://zhanzhang.sm.cn | 移动端份额不小，需注册 |
| 搜狗 | https://zhanzhang.sogou.com | 与微信搜索有协同，需注册 |
| 头条搜索 | https://zhanzhang.toutiao.com | 有 sitemap/推送入口 |

建议顺序：百度 → 360 → 神马 → 其余。后面几家基本是"填同一个 sitemap"，边际成本低。

---

## 8 其它区域（按需）

- Naver（韩）：https://searchadvisor.naver.com → 站点验证 + sitemap；已在 IndexNow 参与方内
- Seznam（捷）：https://search.seznam.cz → 同一套；IndexNow 参与方
- DuckDuckGo / Brave / Startpage：**没有提交口**。DDG 与 Startpage 主要吃 Bing/Google 索引；Brave 用自己的爬虫，靠 robots.txt 允许 + 时间。不要为它们做额外动作。

---

## 9 AI / 生成式引擎：没有"提交"，只有"喂"

ChatGPT / Claude / Perplexity / Gemini / Copilot 等**不提供站点地图提交**，它们的抓取与引用取决于下列面（我们已全部就位）：

| 面 | 状态 |
|---|---|
| robots.txt 显式欢迎 20+ AI 抓取 UA（GPTBot / OAI-SearchBot / ChatGPT-User / ClaudeBot / PerplexityBot / Google-Extended / Applebot-Extended / Bytespider …） | 已做 |
| Content-Signal: search=yes, ai-input=yes, ai-train=yes | 已做 |
| 机器入口 llms.txt（清单） | https://ninfenz.dev/llms.txt |
| 完整单文件 llms-full.txt（定义/事实/术语表/FAQ/引用格式） | https://ninfenz.dev/llms-full.txt |
| 机读事实 facts.json（每条带真源） | https://ninfenz.dev/facts.json |
| 内容协商 Accept: text/markdown（首页直接回完整单文件） | 已做 |
| 可引用锚点 #fact-* | 已做 |

自查是否被抓取：

1. Cloudflare 面板 → Security/Analytics → 按 User-Agent 过滤，看有没有 GPTBot / ClaudeBot 的请求
2. 直接模拟抓取（本机实测全部 200）：

       for ua in "GPTBot/1.0" "ClaudeBot/1.0" "PerplexityBot/1.0" "ChatGPT-User/1.0"; do curl -s -o /dev/null -w "%{http_code}  $ua\n" -A "$ua" https://ninfenz.dev/nf.txt; done

3. 直接问引擎：在 ChatGPT/Perplexity 里问"NinFenz 宁封子是什么？官方入口是哪个？"，看它是否引到 ninfenz.dev 与那句 canonical 定义

---

## 10 验收：怎么确认"真的被收录了"

| 检查 | 命令 / 位置 | 期望 |
|---|---|---|
| robots 允许 | curl -s https://ninfenz.dev/robots.txt | 含 Sitemap 与各 AI UA |
| sitemap 合法 | curl -s https://ninfenz.dev/sitemap.xml | 4 个 loc，XML 可解析 |
| Google 收录 | 搜 site:ninfenz.dev | 出现主页/子页 |
| Bing 收录 | Bing 搜 site:ninfenz.dev | 同上（通常比 Google 快） |
| GSC | 网址检查 → 测试实际网址 | "网址在 Google 上"/"已发现" |
| IndexNow | §2 命令返回 200/202 | 已分发 Bing/Yandex/Seznam/Naver |
| 结构化数据 | https://search.google.com/test/rich-results?url=https://ninfenz.dev/ | 识别 SoftwareApplication / FAQPage / DefinedTerm |

---

## 11 时间预期与常见坑

- **新域名**没有历史权重：Google 编入通常 3–14 天；Bing/IndexNow 常常几小时到 2 天；百度更慢（1–4 周）
- **别做的**：反复请求编入（浪费配额、可能被判滥用）；买第三方"快速收录"；把机器面（.txt/.json）塞进 sitemap
- **验证失败的三种典型**：TXT 记录名写成 @.ninfenz.dev（应只填 @）；值里多带引号；Cloudflare 代理导致文件验证被 301（文件验证要确保直达无重定向）
- **改版后**：跑一次 node site/tools/indexnow.mjs 即可；Google 侧不必重新提交 sitemap（它会按 lastmod 与抓取频率回访）

---

## 12 附录：DNS TXT 怎么加（我可以代劳）

| 平台 | 记录名 | 值来源 |
|---|---|---|
| Google GSC | @ | google-site-verification=… |
| Bing | @ | 若不用 GSC 导入，则给一条 |
| 百度 | @ | baidu-site-verification=… |

**把控制台给出的"名称 + 值"原样发我，我用 Cloudflare API 加好并复核**（我们的 token 对该 Zone 有 DNS 编辑权，实测可改 Zone 设置、可删误建 zone）。

Cloudflare 面板路径：ninfenz.dev → DNS → 记录 → 添加记录 → 类型 TXT / 名称 @ / 内容粘贴 / TTL Auto → 保存。
