# site/ · 静态站（NinFenz 官网）

> **线上地址**：https://ninfenz.dev （Cloudflare Workers + 自定义域 ninfenz.dev；切源：`node site/tools/set-origin.mjs <base> --write`）

纯静态、**零外部依赖**（无 CDN、无 webfont、无遥测）；双语 `/`（zh-CN）与 `/en/`。

## 目标形态

| 面 | 落地 |
|---|---|
| 实体面 | 首屏定义句 + 「不是什么」+ 一句话故事 |
| 证据面 | 可引用事实（每个数字带真源）+ 对比表 + 编号步骤 + 演示动图 |
| 机器面 | JSON-LD（SoftwareApplication + FAQPage）、canonical、hreflang、sitemap.xml、robots.txt、llms.txt |
| 部署面 | 全静态；两条路径任选 |

## 路径 A · Cloudflare Pages（推荐）

1. 在 Cloudflare Pages 连接本仓库
2. Build command：`mkdir -p dist && cp -r site/* dist/`
3. Build output directory：`dist`
4. Custom domain：`ninfenz.dev`（DNS 交给 Cloudflare，HTTPS 自动）
5. 之后每次 push 自动发布

## 路径 B · GitHub Pages（从分支发布，零 workflow = 零未固定 action）

1. 把 `site/` 的内容推到 `gh-pages` 分支**根目录**
2. Settings → Pages → Source: **Deploy from a branch** → `gh-pages` / (root)
3. Custom domain 填 `ninfenz.dev`（`site/CNAME` 已就位）
4. 勾选 Enforce HTTPS

> 不走 Actions 的原因：仓库门禁要求所有 `uses:` 固定到 40 位提交 SHA，而本机无法核对 `actions/deploy-pages` 的 SHA；分支发布天然规避这个风险。

## 本地预览

```bash
python -m http.server 8080 --directory site
# http://127.0.0.1:8080/      中文
# http://127.0.0.1:8080/en/   英文
```

## 发布前检查

- [ ] 两个页面的 JSON-LD 可 `JSON.parse`
- [ ] 无外部资源引用（`link/script/img` 的 URL 全部同源）
- [ ] canonical / hreflang 指向 `ninfenz.dev`
- [ ] robots.txt 显式允许 AI 爬虫并指向 sitemap
- [ ] `site/llms.txt` 的数字与仓库 `llms.txt` 一致（**发版后必须同步**）
- [ ] `assets/og.png` 最好是 1200×630（当前复用 TUI 静帧 80 KB，需要时我另做一张）
- [ ] `assets/demo.gif` 432 KB（如需更轻可换 mp4 + poster）

## 域名（已实测）

| 域 | 判据 | 结果 |
|---|---|---|
| **ninfenz.dev** | RDAP + 同 TLD 对照（flutter.dev / vite.dev / svelte.dev → 200） | **未注册** |
| **ninfenz.com** | RDAP + 同 TLD 对照（deno.com → 200） | **未注册** |
| .app / .org / .net / .xyz / .ai | 各有对照通过 | 未注册 |
| .io / .sh / .me / .cn | **IANA 无 RDAP 端点**，本机无法核实 | 不作选项 |

## 改名联动（待执行）

站内已用新名 **NinFenz / 宁封子**；仓库侧仍是 `NinFenz`。改名执行后需回改本目录的 canonical 与仓库链接（3 处：两个页面的 canonical/og/codeRepository + 页脚链接）。
