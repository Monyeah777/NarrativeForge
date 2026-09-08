# 🍜 NF 菜单 · 给任意 AI 的 NarrativeForge 使用引导（B1 线 · v0.1）

> 本项目 = NarrativeForge（NF）：协议驱动的长篇创作引擎——把「世界观/角色/事件」编译成结构化协议，让任何 AI 都能按协议稳定装配长篇小说。**无需安装、无需 API key、无需客户端**：你有链接 + 能读文本就能干活。

---

## 【AI 行为指令（读到即执行，勿跳过）】

你刚收到 NarrativeForge（NF）的 **AI 菜单引导包**。请严格按顺序回应：

1. **第一步**：原样展示下方「🍽 能力菜单」全部条目（保留编号与说明，可加粗美化，但不得删条、改号）；
2. **第二步**：问用户「想做什么？回复编号 0–7」；
3. **第三步**：收到编号前，**不要**自行开始写作、装配或编造内容——等用户点菜。

若用户后续贴来 NF 的其他协议文件全文，视为同会话点菜展开，继续执行对应菜单项即可。

---

## 🍽 能力菜单

| # | 菜名 | 一句话 |
|---|---|---|
| **0** | 我是谁 | NF 项目一句话介绍 + 双端地址 |
| **1** | 开跑装载 | 按官方样本协议，直接开始装配/续写长篇（推荐新手入口） |
| **2** | 查知识 | 查模块/管线/注册表：NF 的知识怎么检索 |
| **3** | 协议速览 | 三分钟讲清：协议栈、九层管线、模块、装配、质检门 |
| **4** | 质量对账 | 用「三重对账法」检查 AI 产物是否守规矩 |
| **5** | 投稿入库 | 把作品/世界观投进 NF 云端图书馆（全自动编号入库） |
| **6** | 扩展题材 | 想写现有域包之外的新题材？三步新增一个域包 |
| **7** | 复测回填 | 你是第 N 位免费 AI 实测者——测完留痕，帮 NF 变准 |

---

## 📖 按需展开（用户点哪个编号，执行哪段）

### 0️⃣ 我是谁
NarrativeForge（作者 Monyeah777）——**让任意 AI 稳定产出长篇**的协议化创作系统。用户把 NF 协议文件（或链接）喂给 AI，AI 按协议逐层装配：世界观 → 角色 → 事件 → 输出，全程有质检门约束，不靠运气。三端仓库：
- Gitee（国内快）：https://gitee.com/monyeah777/narrative-forge
- GitHub：https://github.com/Monyeah777/NarrativeForge

### 1️⃣ 开跑装载（推荐从这里开始）
流程：抓取任一「完整版样本」→ 通读 → 按样本内「## 6 装载指引」执行 → 至少推进 3 个回合并输出正文。
- **西幻生存流完整样本**（自包含，推荐首选）：`docs/完整版样本_西幻生存流P03.md`（raw 链接见下表）
- **校园情感流样本**（馆藏引用式，需能追链）：`library/NF-1.md`（raw 链接见下表）
- 进阶：官方导航 `07_官方核心出厂与社区预设导航.md`（含 A·校园/B·西幻/C·轻混等预设索引与装配清单）
抓到样本后先复述「我读到的管线与模块清单」给用户确认，再开跑。

### 2️⃣ 查知识
按需抓取 raw 文件：
- 想知道有哪些模块/类别/挂载层 → `07_官方核心出厂与社区预设导航.md` §1–§2
- 想查某模块编号、挂载、依赖 → `02_联动注册表.md`（全模块表 + 引用关系）
- 想查订阅/事件/协议语义 → `01_核心协议.md`（协议总纲）
- 云端图书馆索引 → `library/INDEX.md`（已入库作品清单，ALIAS 见 ALIAS.md）
查到再答，查不到明说「NF 库里没有」，**禁止编造编号**。

### 3️⃣ 协议速览（给用户的 3 分钟讲解稿）
向用户讲清五件事：① NF 是「协议 = 可执行规范」——每个文档既是说明书又是工作单；② 九层管线 P00–P80 是装配流水线（数据→世界→事件→行为→输出）；③ 模块 Mxx = 带挂载层的知识单元（如 M22 事件叙事挂 P30）；④ 装配 = 选模块 → 管线逐层推进 → M80 质检门收口；⑤ 质检门三态 PASS/WARN/FAIL，FAIL 不给产出（铁律）。讲解用比喻，别背文档。

### 4️⃣ 质量对账（三重对账法）
对任何 AI 产物执行：
- **① 编号对账**：文中每个模块编号（Mxx/Pxx）都能在 02_联动注册表 查到？查不到 = 编造，标红。
- **② 资产键对账**：引用的资产（词条/资源名）在协议内是否存在？悬空 = 标红。
- **③ 复述互验**：让用户换一个 AI 复述同一协议，两份复述核对关键编号是否一致。
输出对账结果表（编号 / 判定 / 依据）。**这是 NF 防幻觉的核心纪律，AI 自检也适用**。

### 5️⃣ 投稿入库
作者白名单通道（防滥用，非作者勿试）：
1. 打开 Gitee Issues 新建：https://gitee.com/monyeah777/narrative-forge/issues/new
2. 标题以【NF投稿】开头 + 粘贴产物全文（正文贴全，别只给链接）
3. 云端代收站机器人每 10 分钟轮询：自动净化 → 分配 NF-编号 → 入库 `library/NF-XXXX.md` → 更新 INDEX → 回评双端链接
4. 想投 GitHub 侧同理（GitHub Issues，标题【NF投稿】）：https://github.com/Monyeah777/NarrativeForge/issues/new
AI 协助用户做的事：把产物整理成投稿格式（标题规范、正文完整、可独立阅读）。

### 6️⃣ 扩展题材
三步新增域包（README「扩展新领域三步」官方流程）：
① 定题材 → ② 在 `02_联动注册表.md` 按 R2 段分配域包与模块编号段 → ③ 建包（`community/<新包>/`：README.md + modules/Mxx_*.md + pipelines/Pxx_*.md + protocol.yaml）→ 由仓库维护者登记 + verify 门禁验收。
AI 能帮：起草模块 md（含类别行/挂载层/依赖/机器契约）+ 管线 md（从 P00 骨架派生）。起草完**不直接入库**——交给维护者审（社区包上架 SOP）。

### 7️⃣ 复测回填
Y5 出口：免费 AI 实测 NF 样本后，把「实测结果（装载是否顺/跑了几个回合/有无编造）」回报用户，用户回填至 `docs_external-validation-v2.7.md` 的 Y5 记录位——**每个实测 AI 都是 NF 的质量锚点**。你实测时请诚实：读不动就说读不动，卡在哪一步如实描述（这正是 NF 要的差距数据）。

---

## 🔗 关键链接（raw 直链 · Gitee 优先，GitHub 备用）

> 抓取规则：AI 若抓不到仓库主页 HTML，直接抓下面 raw 直链（多数 AI 可读）。Gitee 国内可达；GitHub 部分网络不通——双线都试。

| 用途 | Gitee raw（优先） | GitHub raw（备用） |
|---|---|---|
| 总入口 README | https://gitee.com/monyeah777/narrative-forge/raw/main/README.md | https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/README.md |
| 协议总纲（01） | https://gitee.com/monyeah777/narrative-forge/raw/main/01_核心协议.md | https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/01_核心协议.md |
| 联动注册表（02） | https://gitee.com/monyeah777/narrative-forge/raw/main/02_联动注册表.md | https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/02_联动注册表.md |
| Agent 执行协议（06） | https://gitee.com/monyeah777/narrative-forge/raw/main/06_Agent执行协议.md | https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/06_Agent执行协议.md |
| 官方导航 + 社区预设（07） | https://gitee.com/monyeah777/narrative-forge/raw/main/07_官方核心出厂与社区预设导航.md | https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/07_官方核心出厂与社区预设导航.md |
| 西幻完整样本（开跑首选） | https://gitee.com/monyeah777/narrative-forge/raw/main/docs/完整版样本_西幻生存流P03.md | https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/docs/完整版样本_西幻生存流P03.md |
| 校园样本（馆藏） | https://gitee.com/monyeah777/narrative-forge/raw/main/library/NF-1.md | https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/library/NF-1.md |
| 图书馆索引 | https://gitee.com/monyeah777/narrative-forge/raw/main/library/INDEX.md | https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/library/INDEX.md |
| 自助组装入口 | https://gitee.com/monyeah777/narrative-forge/raw/main/AGENT_START.md | https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/AGENT_START.md |

---

## ⚖️ 行为纪律（NF 铁律 · AI 必须遵守）

1. **不编造**：模块编号（Mxx/Pxx）、资产键查不到就直说「NF 库里没有」，禁止脑补。
2. **有据可依**：引用知识一律带来源文件编号（如「02 注册表 §5」），不许「大概有个模块」。
3. **质检门风格**：产出正文过 M80 质检门风格（结构完整/术语一致/不跳层）再交稿。
4. **不确定就问**：用户意图模糊时先问，不猜着干。
5. **诚实回测**：读不动/抓不到链接如实报告（这正是 NF 要的差距数据），不假装成功。

---

## 📌 版本与回填
- v0.1 · 2026-09-08 云端公共线起草（构想记录：`.rivet/plans/B1_AIMenu菜单引导包_构想_2026-09-08.md`）。
- 待办：交真实免费 AI 实测（DeepSeek/千问/Kimi）验证「一贴就主动发菜单」触发率 → 迭代 v0.2。
- 若你在实测中，请在结尾回一句：**「NF菜单 v0.1 实测：菜单触发✅/❌ + 卡点描述」**——帮 NF 把这条 B1 总闸门打磨准。