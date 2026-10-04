---
title: NarrativeForge Contract Gate
emoji: 🧾
colorFrom: indigo
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Run real NarrativeForge read-only gates in the browser
---

# NarrativeForge · Contract Gate（在线 demo / S1 入口）

**NarrativeForge（NF）是内容契约层（content contract layer）**：把「AI 稳定产出长内容」变成可装载、可质检、可复现的工程。本 Space 让你**在浏览器里跑真实的 NF 只读门禁**——不是模拟，是同源 CLI。

## 能做什么

| 模式 | 跑的其实是 | 回答的问题 |
|---|---|---|
| 文档语义体检 | `nf lint <你的文本>` | 这段内容过不过仓库的文档判据 |
| 自述数字核对 | `nf stats --check` | README / llms.txt 里的数字与实算是否一致 |
| 契约一致性 | `nf conformance` | 协议件与 registry 是否自洽 |
| 只读体检 | `nf doctor` | 仓库级 16 项只读体检 |

## 实现纪律

- **零第三方 Python 依赖**：一个 `http.server` 服务 + 仓库原样 CLI，容器里没有 pip install。
- **只读白名单**：服务端只接受上面四条命令，命令以 argv 列表调用（无 shell），输入上限 200 KB、超时 180 s。
- **不写仓库**：`lint` 模式只往临时文件写，跑完即删。

## 本地复现（与 Space 同源）

```bash
npm i -g narrativeforge
narrativeforge doctor                                    # 16 项只读体检

# 完整 39 条门禁需要真实检出（verify.sh 依赖 .git / .github / results）
git clone https://github.com/Monyeah777/NarrativeForge && cd NarrativeForge && bash verify.sh
```

## 链接

- 仓库（canonical）：https://github.com/Monyeah777/NarrativeForge
- 机器入口 `llms.txt`：https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/llms.txt
- 许可：MIT
