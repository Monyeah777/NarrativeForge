# NF 验证卡册（既有 39 条门禁的人读复跑说明）

> 生成日期：2026-09-15 ｜ 生成方式：`bash verify.sh` 的 check 函数逐条抽取（`build_verification_cards.ps1`，可复现）
> 适用者：**不需要读代码**的人（含作者本人、未来接手的维护者、外部审查者）。

## 为什么有这份卡册

NF 的门禁是一份 bash 脚本、39 条 check，当前基线声明为 `check1-39` · `PASS=68`（行数与 check 数为 verify.sh 实测；基线取自仓库真源 `quality_baseline.EXPECTED_*`，并由 `nf stats --check` 断言入口文件同步）。
但「PASS=68」本身不说话——它不告诉你每一条到底断言了什么，也不告诉你哪一条可以自己复跑。
这份卡册把每条 check 翻译成同一张五格卡：**结论 / 判据 / 步骤 / 谁验 / 记录**。

它不新增任何机制，也不修改门禁本体；它只是把既有门禁的结论变成可继承的说明。

## 怎么用（三步，约 10 分钟）

1. 在仓库根目录执行：`bash verify.sh`（Windows 下用 Git Bash）。
2. 看最后一行的统计：`PASS=68  WARN=0  FAIL=0`——只有 FAIL 才是阻断，PASS 数以当次输出为准。
3. 若某条不放心，在下表找到它的编号，按卡片里的「复跑命令」单独验证，
   或按卡片里的「记录」字段去找对应日志（**有 FAIL 时脚本会打印日志保留路径**）。

## 全册概况（由生成器统计，非手写）

| 项 | 值 |
|---|---|
| 卡片总数 | 39（= verify.sh 的 check 函数数，实测） |
| 门禁脚本 | 2409 行（verify.sh 实测） |
| 声明基线 | check1-39 · PASS=68（源自 quality_baseline.EXPECTED_*） |
| 段位分布 | 段A 官方核心 6 · 段B 社区包 5 · 段C 代码层 28 |
| 断言种类 | 真实单测 6 条 · 语义校验 14 条 · 其余为结构断言 |
| 复跑入口 | `bash verify.sh`（全量）；单条见各卡片的「复跑命令」 |

## 卡片索引

| # | 段位 | 门禁标题 | 断言种类 |
|---|---|---|---|
| 1 | 段A | [1/6·A] 官方核心目录结构（07 §7 项1） | 结构断言（文件/目录在场与内容） |
| 2 | 段A | [2/6·A] 重号 ID 全限定·官方层（07 §7 项5） | 结构断言（文件/目录在场与内容） |
| 3 | 段A | [3/6·A] 五条不变式落点（01 §5 ↔ 07 §7 项6） | 结构断言 |
| 4 | 段A | [4/6·A] 认知边界（06 §4 管线 ↔ M23 认知域） | 结构断言 |
| 5 | 段A | [5/6·A] 质检门（M80 gate_action 流水线 ↔ 06 §5） | 结构断言 |
| 6 | 段A | [6/6·A] 入口导航（README → 07 → 协议链/官方目录） | 结构断言（文件/目录在场与内容） |
| 7 | 段B | [7/4·B] 社区两包结构完整（07 §7 项2，T6 在册数一致性） | 结构断言（文件/目录在场与内容） |
| 8 | 段B | [8/4·B] 社区资产行数溯源（07 §7 项3） | 结构断言（文件/目录在场与内容） |
| 9 | 段B | [9/4·B] 模块-资产引用可寻址 + 社区 README 重号限定（07 §7 项4/5） | 结构断言（文件/目录在场与内容） |
| 10 | 段B | [10/4·B] EXT 闭合 + 社区红线落地（07 §7 项2/8） | 结构断言（文件/目录在场与内容） |
| 11 | 段B | [11/5·B] 资产-模块三方对账（08 方案 T5 A5；02 §8.1 ↔ modules/ ↔ assets/README） | 结构断言（文件/目录在场与内容） |
| 12 | 段C | [12/代码层] 桌面核心单元测试 + 全量 py_compile 语法抽查（v0.6.0 治理补漏） | 真实单测（unittest） |
| 13 | 段C | [13/段C] 协议版本一致性 + 迁移完整性（09 方案 T2.3） | 结构断言 |
| 14 | 段C | [14/段C] 社区协议登记门禁（v0.7.0 check14：01 §6.1 Schema + 02 §8.3 登记三要件 + registry protocols[] 投影） | 结构断言（文件/目录在场与内容） |
| 15 | 段C | [15/段C] 组合引用门禁（v0.8.0 check15：02 §8.4 references 五断言） | 结构断言 |
| 16 | 段C | [16/段C] 契约仲裁门禁（v1.0.0 check16：01 §1.1 machine_contract 机读结构 + 02 §8.4 规则④ references 装配自动仲裁 + 运行时寻址授权一致） | 结构断言 |
| 17 | 段C | [17/段C] 质量治理门禁（v1.4.0 check17：16_v1.4.0_质量治理闭环方案.md） | 真实单测（unittest） |
| 18 | 段C | [18/段C] 导出契约门禁（v2.0.0 check18：17_v2.0.0_导出层CCV3方案.md） | 真实单测（unittest） |
| 19 | 段C | [19/段C] 导出产物 schema 合规（v2.2.0 A1：export_schema 5 格式 shape 自检） | 真实单测（unittest） |
| 20 | 段C | [20/段C] 文档完整性门禁（v2.2.0 A3：模块文档必填项——对齐 check16 过渡策略分层） | 结构断言 |
| 21 | 段C | [21/段C] registry 引用图闭合门禁（v2.2.0 A4：impact_check 变更影响面——registry 自洽无悬空引用/无裸号重复） | 真实单测（unittest） |
| 22 | 段C | [22/段C] 导出物规范体检门禁（v2.4.0 A4：export_schema 硬约束——spec_version 数值/name 规范/description 上限） | 真实单测（unittest） |
| 23 | 段C | [23/段C] 资产供应链闭合门禁（40 总纲 v2.7 波A S2：每资产可溯源/可发现/键无孤儿；台账=provenance.json + 文件头双源一致） | 语义校验（core 模块：asset_ledger） |
| 24 | 段C | [24/段C] 模块生命周期门禁（40 总纲 v2.8 波B S5：模块 status 位 + deprecate/restore + 引用门禁——deprecated/retired 不得被引用） | 语义校验（core 模块：module_lifecycle） |
| 25 | 段C | [25/段C] 协议知识签名门禁（41 波C C2：01-36 全量文档签名两遍可复现——知识指纹稳定 = 编译期冲突可发现） | 语义校验（core 模块：knowledge_sig） |
| 26 | 段C | [26/段C] 语义矛盾扫描门禁（41 波C C3：techdoc 链事件契约断链 + 挂载点/类别漂移——补 check15/21 结构自洽之上的语义空白） | 语义校验（core 模块：semantic_conflict） |
| 27 | 段C | [27/段C] 架构纯度体检门禁（42 M3：端壳残留/私货可变物/重复标题 grep 断言族 + core raise 消息修复指引审计） | 语义校验（core 模块：purity_scan） |
| 28 | 段C | [28/段C] 协议层 IDL schema 门禁（43 A1：protocol/schema 五定义在场 + 全量件过 schema——machine_contract/registry 投影/管线声明/协议包/资产台账，任一字段漂移即 FAIL） | 语义校验（core 模块：schema_lint） |
| 29 | 段C | [29/段C] Conformance 一致性分级门禁（43 A2：01 §1.2 分级——模块机读块/协议包/导出 manifest 声明 ≤ 可证级别，防虚标） | 语义校验（core 模块：conformance_scan） |
| 30 | 段C | [30/段C] 扩展策略 + bump 迁移门禁（43 A3：EXTENSION 判据在场 + 版本字段结构性变更须带 01 §7/02 §9.3 迁移记录） | 结构断言 |
| 31 | 段C | [31/段C] 生成物同仓 golden 门禁（43 A4：schema 定义 → 生成物可复现，仓库内产物 == 实时重算——双源不一致即过期 FAIL） | 语义校验（core 模块：protocol_golden） |
| 32 | 段C | [32/段C] 质量纵深汇总门禁（45 W28：载荷注册表/资产 ledger/指令审计/资产密度·厚度·零引用 + world_model/world_slots） | 语义校验（core 模块：quality_depth_scan） |
| 33 | 段C | [33/段C] 新面汇总门禁（MCP dual-era / attestation / 基线回归评分 / 机械修复 / 正文 lint / 许可证门 / 遥测 semconv） | 语义校验（core 模块：doc_hygiene） |
| 34 | 段C | [34/段C] 云端图书馆面门禁（frontmatter 真源 / INDEX·ALIAS 投影一致 / 生命周期 / 四型覆盖 / llms.txt 入口） | 语义校验（core 模块：doc_hygiene / library） |
| 35 | 段C | [35/段C] 深化面门禁（管线抽象执行 / 馆藏回执单根 / 模块边界冻结 / 内容绑定批准 / 一致性报告工件 / 无效语料） | 语义校验（core 模块：conformance_report / pipelinerun / receipts） |
| 36 | 段C | [36/段C] 治理面门禁（一致性声明 / RFC 版本史 / 指令档机器面路由 / 实践包 / 跑分台 / 端点契约） | 结构断言 |
| 37 | 段C | [37/段C] 知识层门禁（双源知识：权威分层 / 查询有序 / 时效 / 消化可追溯 / 认知裁剪） | 结构断言 |
| 38 | 段C | [38/段C] 出口自动化门禁（自述数字 / 他证通道 / GEO 出口 / FDE 样例） | 语义校验（core 模块：repo_stats；scripts：interop_thirdparty_kit / geo_export / fde_sample_run） |
| 39 | 段C | [39/段C] 终端与端壳残留门禁（端壳退役零回潮 / nf shell 终端入口 / 菜单无死命令 / 输出确定） | 语义校验（core 模块：terminal + 全树端壳残留扫描） |

---

## 逐条卡片

### V1 · [1/6·A] 官方核心目录结构（07 §7 项1）

| 字段 | 内容 |
|---|---|
| 结论 | [1/6·A] 官方核心目录结构（07 §7 项1） |
| 判据 | 结构断言（文件/目录在场与内容） |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V2 · [2/6·A] 重号 ID 全限定·官方层（07 §7 项5）

| 字段 | 内容 |
|---|---|
| 结论 | [2/6·A] 重号 ID 全限定·官方层（07 §7 项5） |
| 判据 | 结构断言（文件/目录在场与内容） |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V3 · [3/6·A] 五条不变式落点（01 §5 ↔ 07 §7 项6）

| 字段 | 内容 |
|---|---|
| 结论 | [3/6·A] 五条不变式落点（01 §5 ↔ 07 §7 项6） |
| 判据 | 结构断言 |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V4 · [4/6·A] 认知边界（06 §4 管线 ↔ M23 认知域）

| 字段 | 内容 |
|---|---|
| 结论 | [4/6·A] 认知边界（06 §4 管线 ↔ M23 认知域） |
| 判据 | 结构断言 |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V5 · [5/6·A] 质检门（M80 gate_action 流水线 ↔ 06 §5）

| 字段 | 内容 |
|---|---|
| 结论 | [5/6·A] 质检门（M80 gate_action 流水线 ↔ 06 §5） |
| 判据 | 结构断言 |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V6 · [6/6·A] 入口导航（README → 07 → 协议链/官方目录）

| 字段 | 内容 |
|---|---|
| 结论 | [6/6·A] 入口导航（README → 07 → 协议链/官方目录） |
| 判据 | 结构断言（文件/目录在场与内容） |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V7 · [7/4·B] 社区两包结构完整（07 §7 项2，T6 在册数一致性）

| 字段 | 内容 |
|---|---|
| 结论 | [7/4·B] 社区两包结构完整（07 §7 项2，T6 在册数一致性） |
| 判据 | 结构断言（文件/目录在场与内容） |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V8 · [8/4·B] 社区资产行数溯源（07 §7 项3）

| 字段 | 内容 |
|---|---|
| 结论 | [8/4·B] 社区资产行数溯源（07 §7 项3） |
| 判据 | 结构断言（文件/目录在场与内容） |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V9 · [9/4·B] 模块-资产引用可寻址 + 社区 README 重号限定（07 §7 项4/5）

| 字段 | 内容 |
|---|---|
| 结论 | [9/4·B] 模块-资产引用可寻址 + 社区 README 重号限定（07 §7 项4/5） |
| 判据 | 结构断言（文件/目录在场与内容） |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V10 · [10/4·B] EXT 闭合 + 社区红线落地（07 §7 项2/8）

| 字段 | 内容 |
|---|---|
| 结论 | [10/4·B] EXT 闭合 + 社区红线落地（07 §7 项2/8） |
| 判据 | 结构断言（文件/目录在场与内容） |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V11 · [11/5·B] 资产-模块三方对账（08 方案 T5 A5；02 §8.1 ↔ modules/ ↔ assets/README）

| 字段 | 内容 |
|---|---|
| 结论 | [11/5·B] 资产-模块三方对账（08 方案 T5 A5；02 §8.1 ↔ modules/ ↔ assets/README） |
| 判据 | 结构断言（文件/目录在场与内容） |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 无独立日志；结论直接打印在门禁输出中 |

### V12 · [12/代码层] 桌面核心单元测试 + 全量 py_compile 语法抽查（v0.6.0 治理补漏）

| 字段 | 内容 |
|---|---|
| 结论 | [12/代码层] 桌面核心单元测试 + 全量 py_compile 语法抽查（v0.6.0 治理补漏） |
| 判据 | 真实单测（unittest） |
| 复跑命令 | cd desktop && python -m unittest discover -s tests -q -q |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check12_unittest.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V13 · [13/段C] 协议版本一致性 + 迁移完整性（09 方案 T2.3）

| 字段 | 内容 |
|---|---|
| 结论 | [13/段C] 协议版本一致性 + 迁移完整性（09 方案 T2.3） |
| 判据 | 结构断言 |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check13_cmp.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V14 · [14/段C] 社区协议登记门禁（v0.7.0 check14：01 §6.1 Schema + 02 §8.3 登记三要件 + registry protocols[] 投影）

| 字段 | 内容 |
|---|---|
| 结论 | [14/段C] 社区协议登记门禁（v0.7.0 check14：01 §6.1 Schema + 02 §8.3 登记三要件 + registry protocols[] 投影） |
| 判据 | 结构断言（文件/目录在场与内容） |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check14.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V15 · [15/段C] 组合引用门禁（v0.8.0 check15：02 §8.4 references 五断言）

| 字段 | 内容 |
|---|---|
| 结论 | [15/段C] 组合引用门禁（v0.8.0 check15：02 §8.4 references 五断言） |
| 判据 | 结构断言 |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check15.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V16 · [16/段C] 契约仲裁门禁（v1.0.0 check16：01 §1.1 machine_contract 机读结构 + 02 §8.4 规则④ references 装配自动仲裁 + 运行时寻址授权一致）

| 字段 | 内容 |
|---|---|
| 结论 | [16/段C] 契约仲裁门禁（v1.0.0 check16：01 §1.1 machine_contract 机读结构 + 02 §8.4 规则④ references 装配自动仲裁 + 运行时寻址授权一致） |
| 判据 | 结构断言 |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check16a.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V17 · [17/段C] 质量治理门禁（v1.4.0 check17：16_v1.4.0_质量治理闭环方案.md）

| 字段 | 内容 |
|---|---|
| 结论 | [17/段C] 质量治理门禁（v1.4.0 check17：16_v1.4.0_质量治理闭环方案.md） |
| 判据 | 真实单测（unittest） |
| 复跑命令 | cd desktop && python -m unittest tests.test_quality_gate -q -q |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check17_unittest.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V18 · [18/段C] 导出契约门禁（v2.0.0 check18：17_v2.0.0_导出层CCV3方案.md）

| 字段 | 内容 |
|---|---|
| 结论 | [18/段C] 导出契约门禁（v2.0.0 check18：17_v2.0.0_导出层CCV3方案.md） |
| 判据 | 真实单测（unittest） |
| 复跑命令 | cd desktop && python -m unittest tests.test_ccv3_adapter tests.test_exporter -q -q |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check18_unittest.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V19 · [19/段C] 导出产物 schema 合规（v2.2.0 A1：export_schema 5 格式 shape 自检）

| 字段 | 内容 |
|---|---|
| 结论 | [19/段C] 导出产物 schema 合规（v2.2.0 A1：export_schema 5 格式 shape 自检） |
| 判据 | 真实单测（unittest） |
| 复跑命令 | cd desktop && python -m unittest tests.test_export_schema -q -q |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check19_unittest.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V20 · [20/段C] 文档完整性门禁（v2.2.0 A3：模块文档必填项——对齐 check16 过渡策略分层）

| 字段 | 内容 |
|---|---|
| 结论 | [20/段C] 文档完整性门禁（v2.2.0 A3：模块文档必填项——对齐 check16 过渡策略分层） |
| 判据 | 结构断言 |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check20.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V21 · [21/段C] registry 引用图闭合门禁（v2.2.0 A4：impact_check 变更影响面——registry 自洽无悬空引用/无裸号重复）

| 字段 | 内容 |
|---|---|
| 结论 | [21/段C] registry 引用图闭合门禁（v2.2.0 A4：impact_check 变更影响面——registry 自洽无悬空引用/无裸号重复） |
| 判据 | 真实单测（unittest） |
| 复跑命令 | cd desktop && python -m unittest tests.test_impact_check -q -q |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check21_unittest.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V22 · [22/段C] 导出物规范体检门禁（v2.4.0 A4：export_schema 硬约束——spec_version 数值/name 规范/description 上限）

| 字段 | 内容 |
|---|---|
| 结论 | [22/段C] 导出物规范体检门禁（v2.4.0 A4：export_schema 硬约束——spec_version 数值/name 规范/description 上限） |
| 判据 | 真实单测（unittest） |
| 复跑命令 | cd desktop && python -m unittest tests.test_export_schema tests.test_ccv3_adapter tests.test_skill_adapter -q -q |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check22_unittest.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V23 · [23/段C] 资产供应链闭合门禁（40 总纲 v2.7 波A S2：每资产可溯源/可发现/键无孤儿；台账=provenance.json + 文件头双源一致）

| 字段 | 内容 |
|---|---|
| 结论 | [23/段C] 资产供应链闭合门禁（40 总纲 v2.7 波A S2：每资产可溯源/可发现/键无孤儿；台账=provenance.json + 文件头双源一致） |
| 判据 | 语义校验（core 模块：asset_ledger） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import asset_ledger"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check23.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V24 · [24/段C] 模块生命周期门禁（40 总纲 v2.8 波B S5：模块 status 位 + deprecate/restore + 引用门禁——deprecated/retired 不得被引用）

| 字段 | 内容 |
|---|---|
| 结论 | [24/段C] 模块生命周期门禁（40 总纲 v2.8 波B S5：模块 status 位 + deprecate/restore + 引用门禁——deprecated/retired 不得被引用） |
| 判据 | 语义校验（core 模块：module_lifecycle） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import module_lifecycle"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check24.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V25 · [25/段C] 协议知识签名门禁（41 波C C2：01-36 全量文档签名两遍可复现——知识指纹稳定 = 编译期冲突可发现）

| 字段 | 内容 |
|---|---|
| 结论 | [25/段C] 协议知识签名门禁（41 波C C2：01-36 全量文档签名两遍可复现——知识指纹稳定 = 编译期冲突可发现） |
| 判据 | 语义校验（core 模块：knowledge_sig） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import knowledge_sig"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check25.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V26 · [26/段C] 语义矛盾扫描门禁（41 波C C3：techdoc 链事件契约断链 + 挂载点/类别漂移——补 check15/21 结构自洽之上的语义空白）

| 字段 | 内容 |
|---|---|
| 结论 | [26/段C] 语义矛盾扫描门禁（41 波C C3：techdoc 链事件契约断链 + 挂载点/类别漂移——补 check15/21 结构自洽之上的语义空白） |
| 判据 | 语义校验（core 模块：semantic_conflict） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import semantic_conflict"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check26.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V27 · [27/段C] 架构纯度体检门禁（42 M3：端壳残留/私货可变物/重复标题 grep 断言族 + core raise 消息修复指引审计）

| 字段 | 内容 |
|---|---|
| 结论 | [27/段C] 架构纯度体检门禁（42 M3：端壳残留/私货可变物/重复标题 grep 断言族 + core raise 消息修复指引审计） |
| 判据 | 语义校验（core 模块：purity_scan） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import purity_scan"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check27.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V28 · [28/段C] 协议层 IDL schema 门禁（43 A1：protocol/schema 五定义在场 + 全量件过 schema——machine_contract/registry 投影/管线声明/协议包/资产台账，任一字段漂移即 FAIL）

| 字段 | 内容 |
|---|---|
| 结论 | [28/段C] 协议层 IDL schema 门禁（43 A1：protocol/schema 五定义在场 + 全量件过 schema——machine_contract/registry 投影/管线声明/协议包/资产台账，任一字段漂移即 FAIL） |
| 判据 | 语义校验（core 模块：schema_lint） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import schema_lint"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check28.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V29 · [29/段C] Conformance 一致性分级门禁（43 A2：01 §1.2 分级——模块机读块/协议包/导出 manifest 声明 ≤ 可证级别，防虚标）

| 字段 | 内容 |
|---|---|
| 结论 | [29/段C] Conformance 一致性分级门禁（43 A2：01 §1.2 分级——模块机读块/协议包/导出 manifest 声明 ≤ 可证级别，防虚标） |
| 判据 | 语义校验（core 模块：conformance_scan） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import conformance_scan"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check29.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V30 · [30/段C] 扩展策略 + bump 迁移门禁（43 A3：EXTENSION 判据在场 + 版本字段结构性变更须带 01 §7/02 §9.3 迁移记录）

| 字段 | 内容 |
|---|---|
| 结论 | [30/段C] 扩展策略 + bump 迁移门禁（43 A3：EXTENSION 判据在场 + 版本字段结构性变更须带 01 §7/02 §9.3 迁移记录） |
| 判据 | 结构断言 |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check30.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V31 · [31/段C] 生成物同仓 golden 门禁（43 A4：schema 定义 → 生成物可复现，仓库内产物 == 实时重算——双源不一致即过期 FAIL）

| 字段 | 内容 |
|---|---|
| 结论 | [31/段C] 生成物同仓 golden 门禁（43 A4：schema 定义 → 生成物可复现，仓库内产物 == 实时重算——双源不一致即过期 FAIL） |
| 判据 | 语义校验（core 模块：protocol_golden） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import protocol_golden"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check31.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V32 · [32/段C] 质量纵深汇总门禁（45 W28：载荷注册表/资产 ledger/指令审计/资产密度·厚度·零引用 + world_model/world_slots）

| 字段 | 内容 |
|---|---|
| 结论 | [32/段C] 质量纵深汇总门禁（45 W28：载荷注册表/资产 ledger/指令审计/资产密度·厚度·零引用 + world_model/world_slots） |
| 判据 | 语义校验（core 模块：quality_depth_scan） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import quality_depth_scan"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check32.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V33 · [33/段C] 新面汇总门禁（MCP dual-era / attestation / 基线回归评分 / 机械修复 / 正文 lint / 许可证门 / 遥测 semconv）

| 字段 | 内容 |
|---|---|
| 结论 | [33/段C] 新面汇总门禁（MCP dual-era / attestation / 基线回归评分 / 机械修复 / 正文 lint / 许可证门 / 遥测 semconv） |
| 判据 | 语义校验（core 模块：doc_hygiene） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import doc_hygiene"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check33.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V34 · [34/段C] 云端图书馆面门禁（frontmatter 真源 / INDEX·ALIAS 投影一致 / 生命周期 / 四型覆盖 / llms.txt 入口）

| 字段 | 内容 |
|---|---|
| 结论 | [34/段C] 云端图书馆面门禁（frontmatter 真源 / INDEX·ALIAS 投影一致 / 生命周期 / 四型覆盖 / llms.txt 入口） |
| 判据 | 语义校验（core 模块：doc_hygiene / library） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import doc_hygiene, library"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check34.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V35 · [35/段C] 深化面门禁（管线抽象执行 / 馆藏回执单根 / 模块边界冻结 / 内容绑定批准 / 一致性报告工件 / 无效语料）

| 字段 | 内容 |
|---|---|
| 结论 | [35/段C] 深化面门禁（管线抽象执行 / 馆藏回执单根 / 模块边界冻结 / 内容绑定批准 / 一致性报告工件 / 无效语料） |
| 判据 | 语义校验（core 模块：conformance_report / pipelinerun / receipts） |
| 复跑命令 | python -c "import sys; sys.path.insert(0,'desktop/src'); from core import conformance_report, pipelinerun, receipts"  # 直接复跑请用下面的整段命令 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check35.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V36 · [36/段C] 治理面门禁（一致性声明 / RFC 版本史 / 指令档机器面路由 / 实践包 / 跑分台 / 端点契约）

| 字段 | 内容 |
|---|---|
| 结论 | [36/段C] 治理面门禁（一致性声明 / RFC 版本史 / 指令档机器面路由 / 实践包 / 跑分台 / 端点契约） |
| 判据 | 结构断言 |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check36.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V37 · [37/段C] 知识层门禁（双源知识：权威分层 / 查询有序 / 时效 / 消化可追溯 / 认知裁剪）

| 字段 | 内容 |
|---|---|
| 结论 | [37/段C] 知识层门禁（双源知识：权威分层 / 查询有序 / 时效 / 消化可追溯 / 认知裁剪） |
| 判据 | 结构断言 |
| 复跑命令 | （结构断言类，随全量门禁执行；无独立入口） |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check37.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V38 · [38/段C] 出口自动化门禁（自述数字 / 他证通道 / GEO 出口 / FDE 样例）

| 字段 | 内容 |
|---|---|
| 结论 | [38/段C] 出口自动化门禁（自述数字 / 他证通道 / GEO 出口 / FDE 样例） |
| 判据 | 语义校验（core 模块：repo_stats；scripts：interop_thirdparty_kit / geo_export / fde_sample_run 四子扫描） |
| 复跑命令 | `python scripts/nf.py stats --check`（自述数字）；其余三面随全量门禁执行 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check38_*.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

### V39 · [39/段C] 终端与端壳残留门禁（端壳退役零回潮 / nf shell 终端入口 / 菜单无死命令 / 输出确定）

| 字段 | 内容 |
|---|---|
| 结论 | [39/段C] 终端与端壳残留门禁（端壳退役零回潮 / nf shell 终端入口 / 菜单无死命令 / 输出确定） |
| 判据 | 语义校验（core 模块：terminal；判据 = 残留落点 + 全树源件扫描 + 菜单示例解析 + 两遍输出比对） |
| 复跑命令 | `python scripts/nf.py shell --exec "/menu" --no-banner`（终端面）；端壳残留随全量门禁执行 |
| 谁验 | 任何有 Python 3 与 bash 的人；不需要读代码 |
| 记录 | 运行日志 nf_check39.log（本次运行的临时目录内；有 FAIL 时脚本会打印保留路径） |

---

> 本册可重建：仓库根执行 `powershell -File ..\build_verification_cards.ps1`（本地生成器，未随仓库分发），产物逐字节一致。
> 门禁变更后应重新生成（否则卡册与门禁会静默漂移——这正是它想防的那种问题）。
> 2026-09-25：check38/39 卡片按同一模板补齐，基线行同步为 check1-39 · PASS=68；下次跑生成器即回归逐字节重建。
