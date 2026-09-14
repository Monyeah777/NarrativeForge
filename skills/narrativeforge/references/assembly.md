# NarrativeForge AI 装配流程

NF 的运行循环是：**读 → 判 → 配 → 装 → 执 → 验**。每次都要引用仓库真实件，禁止凭记忆编造编号、资产键或依赖。

## 1. 判断需求

- 组装完整版：从领域包选管线、模块、资产，生成单文件 `.md`。
- 运行现成完整版：按产物内 `##6. 装载指引` 执行。
- 制作单件：做模块、资产包或协议包。
- 逛云端馆：读 `library/INDEX.md`、`ROUTES.md`。

## 2. 取货

优先读：

- `AGENT_START.md`
- `agent_组装指令包_v0.2.md`
- `AI_ROUTING.md`
- `01_核心协议.md`
- `02_联动注册表.md`
- `06_Agent执行协议.md`
- `07_官方核心出厂与社区预设导航.md`

按需求再读对应包：

```bash
python scripts/nf.py market --list
python scripts/nf.py market community/西幻生存领域包
python scripts/nf.py market community/校园情感领域包
```

## 3. 装配

- 管线决定层序，模块按挂载层填入，资产经五接口取用：`asset_get`、`asset_query`、`asset_match`、`asset_roll`、`asset_register`。
- 社区新建模块号应落在 M91–M99 预留段；重号字段必须带类别限定，如 `通用:M10`、`生存:M10`、`事件:M22`、`情感:M22`。
- 事件、状态、引用必须闭合；依赖不闭合要留空并标注。

## 4. 执行与输出

成品是**单文件自包含 Markdown**，须含完整骨架与装载指引。完整版应具备八段骨架，具体以 `agent_组装指令包_v0.2.md` 的 `##7` 自检为准。

## 5. 验收

机器验收：

```bash
python scripts/nf.py assemble "<需求>" --check 成品.md
python scripts/nf.py assemble "<需求>" --save 需求档案.md
python scripts/nf.py assemble "<需求>" --trace trace.json --rounds
```

出口前逐项检查：八段骨架齐、编号合法、模块要素齐、事件闭合、资产键真实、装配记录写明来源与缺口。任一为否，先修正再交付。
