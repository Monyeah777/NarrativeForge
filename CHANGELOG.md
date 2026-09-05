## [Unreleased] - v2.0.x（2.0 E2-E5 收口，工作分支 feat/v1.1-fix 已提交未发布）
### Added
- **v2.0.x-E2 协议定义向导（方案 19，031f543 docs + 9bf5055 feat）**：自定义协议 GUI 化落地——`desktop/src/core/protocol_wizard.py`（ProtocolForm + build_protocol_yaml 生成合规 protocol.yaml v2 + self_check）+ `desktop/src/ui/protocol_wizard_dialog.py`（向导 QDialog）+ zone_g「创建自定义协议…」入口（协议定义从手写 Schema 门槛降为填表生成）。
- **v2.0.x-E3 组合运行时调度引擎（方案 20，07b8bf0 docs + caa45f4 feat）**：references 跨包引用运行时消费——`desktop/src/core/composer.py`（resolve_combination 按 registry protocols references 闭包解析 + build_assembly 装配前合并 own+reference 模块正文，轻混 P04 导出 world 现含校园 M55/西幻 M17）；e2e [8] + zone_d 生成默认含引用。
- **v2.0.x-E4 模块市场雏形（方案 21，6699566 docs + 7d3678f feat）**：zone_g 升级检索驱动一站式视图——消费 retriever.search 四类（module/asset_pack/pipeline/protocol 本地资源）结果表 + 按 kind 分流动作（module 加入装配追加进 selected / pipeline 设为当前管线 / asset_pack 选用资产包 / protocol 查看详情）；main_window 增 add_module_to_assembly（追加语义，区别于预设重填）+ set_current_pipeline；装配态标记随 ②③ 勾选联动；`scripts/smoke_zone_g_market.py` offscreen 冒烟（检索命中→加入装配→层树同步→四类齐备）。
- **v2.0.x-E5 模块市场雏形深化（方案 22，69dd4b2 W1 core + 47c0dfd W2 UI）**：community 仓库盘点——新增 `desktop/src/core/community_inventory.py`（catalog 盘点 4 包 29 模块 + 4 管线 + 已装判定；install_module save_module 幂等 / install_pipeline pipelines cache 按 id merge 不覆盖既有）；retriever.search 扩 kind=community_module/community_pipeline（显式指定才并入，E4 四类语义隔离，Hit tags=[来源包,✓已装/可装载]）；zone_g kind 下拉加「社区模块/社区管线」档——未装一键装载入库（module → on_modules_changed / pipeline → reload_pipelines）、已装转加入装配/设为当前管线；`scripts/smoke_zone_g_market.py` [7][8] 装载冒烟（M55 装载入库→标记翻转、P04 cache merge→③ 下拉含）。I5 边界裁决：references 跨包只读（E3）与用户工作区装载（E5，等同 seed_from_repo 既有模式）正交不冲突。
- **v2.1.0-B2 全链管道化（方案 24，f25ea79 W1 + c59b11f W2）**：retrieve→compose→gate→export 单命令——新增 `desktop/src/core/pipeline.py`（pipe() 单一入口：selected full_id → build_assembly(E3 references 并入) → render_ir → quality_gate 三态 → gate.ok 且非禁阻断才 export；本地缺失项跳过入 warnings；fail_on_gate=False 强制导出诊断产物但 ok 仍 False——可信任度不变量不破）+ `scripts/nf.py` CLI（run 子命令，GateResult 摘要 + FAIL exit 1 镜像 verify 铁律；skill 拒 narrative 的产物×适配矩阵纪律 warnings 透传）。CLI/库先行薄壳形态（L3_FROZEN.md）的地基，L2 首个里程碑。
- **v2.1.0-A1 AGENTS/CLAUDE 适配器 + SKILL 边界裁决机制化（方案 25，74db425 W1 + 98ed908 W2）**：产物×适配矩阵第三格——新增 `desktop/src/core/semantics.py`（两判据裁决唯一真源：`classify_doc_semantics(ir)` meta 显式声明 > title/模块名项目约定词启发 > 缺省回退 skill）+ `agent_rules_adapter.py`（techdoc+project_rules → AGENTS.md/CLAUDE.md 项目约定出口，narrative/能力语义拒出同 skill 纪律）+ exporter 注册 agents/claude；protocol_wizard.self_check 内置 doc_semantics 值域校验 + nf.py --fmt 扩 agents/claude。CLI/库先行 + 裁决规则供向导/生成器复用。
- **v2.1.0-B1 质量门可解释化（方案 26，9d396df）**：quality_gate 三态门 → 可解释报告 + 自动修复建议——`Issue` 加 `suggestion` 字段（缺省空串，向后兼容）+ 四条默认规则各补 actionable 修复指引（R1 空装配→勾选含核心 M00/M80 / R2 缺锚点→勾选 P00/P80 / W1 资产悬空→装包或删引用 / W2 层外→移层位或改层序）+ `GateResult.report_text()` 可解释报告（fail 优先、warn 可行动）；nf.py 质量门打印带建议。warn 从"只提示"变"告诉你怎么改"。
### Changed
- README 协议链追加 19/20/21/22（治理指针 2，收口 E2-E5 落地）。
- **23 方案分层治理**：L3 端壳冻结移出主仓库演进主线——verify.sh v2.9 分层门禁（check13① 去 android 两处比对、check12② compileall 去 android、版本号收口，clone 即绿零前置）+ CI 新增 ci-verify（L0-L2 闸门）+ build-desktop/build-android 退役 main 自动触发（仅 v* tag/手动）+ `L3_FROZEN.md` 真相源落盘（含移出清单索引与接回路径）。L2 core 语义零回归（135 单测/verify PASS=24/e2e 全绿）。

## [2.0.0] - 2026-09-05（v2.0.0 导出层：上游生成器——E0 三件套 + CCV3/SKILL 出口）
### Added
- **v1.2.0 协议中转站 v2（IR 内容归一化，2.0 E0-①）**：ir.py IRDocument/IRLayer/IRModule + normalize_module_body + ir_to_md（IR 默认 MD 适配器）；generator.render_ir 装配→IR（层序/层外/资产 refs+missing 归一），generate_document 改两段（render_ir+ir_to_md），对外 MD 输出零回归（一致性 diff 逐字节）。方案 14。
- **v1.3.0 Agentic 检索（2.0 E0-②）**：retriever.search() 四类统一入口（module/asset_pack/pipeline/protocol），结构化 grep 不上向量 + Hit 元数据卡片（对齐 Agent Skills Discovery）。方案 15。
- **v1.4.0 质量治理闭环（2.0 E0-③）**：quality_gate.run_gate 三态质检门（空装配+核心锚点 fail / 资产悬空+层外 warn，ok()=fail==0 不变量）；zone_d 生成后三态展示；verify check17 入段 C（PASS→23）。方案 16。
- **v2.0.0 导出层 CCV3 首发（2.0 E1 收口）**：立项核心发现=CCV3 语义错配（NF 装配=世界规则集→character_book 主承载，persona 主角占位）；ccv3_adapter（IR→chara_card_v3+world，引擎锚点排除/资产独立/无静默丢弃）；exporter 格式注册表 + PNG 卡（QImage tEXt，零新依赖）；e2e 导出战例（真实组合包→IR→质量门→export 全绿）；zone_d「导出 CCV3」按钮（质量门 FAIL 阻断）；verify check18 入段 C（PASS→24）。方案 17。
- **v2.0.x SKILL 出口插件**：skill_adapter（techdoc IR→SKILL.md agentskills 格式；narrative IR 拒出——产物×适配矩阵第二行机制化）。方案 18。
### Changed
- verify.sh v2.6→v2.8（check17 质量门 / check18 导出契约，PASS 22→24）。
### Fixed（Windows 跨平台，本分支修复）
- registry_loader.asset_get 路径包含硬编码 '/' → is_relative_to（Windows resolve 反斜杠致资产寻址全拒）。
- verify.sh check16 漏用裸 python3 stub（对齐 PY3 回退）。
- e2e_desktop_headless stdout GBK reconfigure（Windows cp936 ✓ 崩溃）。

# Changelog

> 格式约定：Keep a Changelog 中文化（Added/Changed/Fixed 语义）；版本段按时间倒序；[Unreleased] = 当前主线开发中；发布即归档为 [版本号] + 日期段并打 annotated tag（ROADMAP §8 治理指针 3）。
> 基线说明：本文件随 v0.6.0 方案 B 第①步落盘（2026-09-04）；早期版本（v0.1.0–v0.5.0）条目按 git 版本史（八 tag）回写简述。

## [1.1.0] - 2026-09-04（v1.1.0 社区通用核心基础包）
### Added
- T4-1 通用核心基础包（P05 核心基础流）战例落盘（C1=395e59a）：community 新增第 4 个社区包——protocol.yaml（schema v2，core_only 12 件官方配合、references 零跨包、0 资产）+ README 装载手册 + pipelines/P05（核心基础流）+ M93–M96 四模块（各带 machine_contract）；登记三要件②③实况落位（02 §8.3 通用类整包登记 + registry protocols[] 第 4 条投影程序化生成自 protocol.yaml、双源一致）；community/README 目录导览新增本包行（4 包全覆盖）；verify.sh check14/check15 扩容（CORE 第三类变量独立入 ALL_PKGS、①段/降级段 for 3→4 目录、check15 PKGS 3→4），复验 PASS=22 WARN=0 FAIL=0 全绿。

## [1.0.0] - 2026-09-04（v1.0.0 全平台正式版）
### Added
- 13_v1.0.0_全平台正式版方案.md 落盘（方案真相源，I5）：v1.0.0 定位为「全平台正式版·打好地基——协议层收口 + 社区生态收口 + 双端质量收口，功能扩展一律外推」。连续八版（v0.1–v0.9）协议/平台/生态快速演进后，历版方案 §6 开放问题与 ROADMAP 范围外声明累计 6+ 条「明示留待 v1.0.0」收口项一次兑现。问题全景 A1–A3（A1 协议层三处半收口：契约仲裁仅 WARN / 模块头契约无机读 / asset_readonly 无运行时 / A2 社区生态无协作流程与真实战例 / A3 双端发布质量无端到端闸门）；改进收口 B1–B3（B1 协议层收口：模块头契约机读化 + 自动契约仲裁 WARN→FAIL + desktop Runtime asset_get 跨包只读寻址 / B2 社区生态收口：CONTRIBUTING 协作流程五步 + community/「校园 × 西幻轻混」完整可玩组合包战例 / B3 双端发布质量收口：端到端测试入 CI 缺口⑩闭环（桌面 headless 断言 + Android 模拟器启动冒烟最小集）+ 正式发布仪式三件套终态收口）；任务分解 T1 协议层收口（T1-1 机读化 → T1-2 仲裁升级 → T1-3 只读寻址，check16 随 T1-3 一次性入段 C）→ T2 社区生态收口（T2-1 流程文档化 → T2-2 完整战例，依赖 T1）→ T3 双端发布质量收口（T3-1 端到端入 CI，依赖 T2-2 → T3-2 发布仪式终态 + tag v1.0.0）；提交规划 C0–C8（C0 仅动文档 PASS=20 保持；C1–C3 中间态 PASS=20 保持；C4 起 PASS=22 终态）。ROADMAP §1 L15 v1.0.0 状态切「🔵 当前主线」+ §7 一句话展开完整范围（✅三做/❌三不做）落盘；README 协议链追加 13、新增 v1.0.0 🔵 块引用、v0.9.0 块引用切「✅ 已发布 2026-09-04」；本段下方 [0.9.0] 段归档为治理指针 3 发布归档收口（v0.9.0 发布时遗留，原 [Unreleased] v0.9.0 段内容原样迁入不增删改）。
- T1-1 模块头 machine_contract 机读块落地（A1/B1，C1-1=49e8f93）：01_核心协议.md §1 模块契约声明补 machine_contract 机读块规范 + §7 迁移记录（+33 行）；04_模块库官方 13 件模块头各补 machine_contract 机读块（各 +15 行）——模块契约（inputs/outputs/events）从人读声明升级为机读可解析字段，为 check16 自动契约仲裁提供机读判据（11 §6 开放问题 4 收紧路径的机读前提；字段级新增不 bump，C1–C3 中间态 PASS=20 保持）。
- T1-2 自动契约仲裁升级（A1/B1，C1-2=e0300cd）：02 §8.4 登记判定规则④由「契约 WARN 提示、不阻断装配」升级为「契约断裂 FAIL 阻断 + 自动仲裁」（删除「留 v1.0.0 生态收口」标记，条款原文更新）+ 仲裁判据条款（模块头机读契约 inputs/outputs/events + 01 §1 events publish⊆subscribe 语义）+ §9.1/§9.2 同步。
- T1-3 desktop Runtime asset_get 跨包只读寻址（A1/B1，C3=17eac3a）：desktop/src/core/registry_loader 实现 references.asset_readonly 声明资产的跨包只读寻址运行时通道（白名单授权校验 + 只读不复制，I5 单一真相源闭环）——组合包声明 asset_readonly: true 后即有运行时通道可消费源包资产，「组合可玩」最后一块拼图补齐（引擎级组合调度不做，❌②纪律）。
- T1-3 check16 契约仲裁门禁入段 C（A1/B1，C4=69b078e）：verify.sh v2.6 四处同步 + check16 双断言入段 C（check16-A 契约仲裁 FAIL 断言：相邻装配 publish ⊄ subscribe 即 FAIL；check16-B 运行时寻址授权一致断言），PASS 20→22 全绿——自动契约仲裁从人读复核升级为 CI 自动闸门。
- T2-1 第三方协作流程文档化（A2/B2，C5=8380d3f）：CONTRIBUTING.md 升级「社区包协作流程」章节（§4.4 提交→PR 评审→登记→发布五步含检查单）+ 02 §9.2 补协作流程纪律条——10 §6 开放问题 4「流程治理留待 v1.0.0 生态收口」兑现。
- T2-2 完整可玩组合包战例落盘（A2/B2，C6=5e5f957）：community/「校园 × 西幻轻混」完整可玩组合包（P04 轻混装配流管线 + M91 异界身份桥/M92 轻混装配执行 + references 组合引用 M55/M17 + asset_readonly 资产只读授权 + README 装载手册；02 §8.4 YAML 骨架示例升级为真实可装载包）；registry protocols[] 投影第 3 条；verify.sh check14/15/16 适配组合包自动发现，verify PASS=22 全绿 + headless 端到端冒烟可跑通——11 §6 开放问题 3 + 02 §8.4 战例延期 1 版兑现。
- T3-1 端到端测试入 CI（A3/B3，C7=5b35c44）：scripts/e2e_desktop_headless.py 桌面端到端断言（真实生成链路：装载组合包 → 选管线 → 按层装配 → 生成文档 → 产物断言，33 项断言实跑全绿 exit 0）入 CI（.github/workflows/e2e-desktop.yml 独立 workflow）；build-android.yml 追加 android-emulator-smoke job（模拟器 boot → 安装 release APK → 真实启动不闪退冒烟最小集）——缺口⑩（双端「真实启动 + 真实生成链路」自动化端到端验证）闭环；12 §6 开放问题 1 运行时答案；真机手动验收保留为发布前最终门禁。
## [0.9.0] - 2026-09-04（v0.9.0 Android 同步门禁 + APK 闪退修复）
### Added
- 12_v0.9.0_Android同步门禁与APK闪退修复方案.md 落盘（方案真相源，I5）：v0.9.0 定位为「Android 同步门禁 + APK 闪退修复——把 sync --check 差异校验接入 CI（缺口⑦闭环：Android↔真源一致性不再靠人工）；对 APK 闪退修复做验证归档 + 纳入 CI 回归门禁保障」。关键前提（git merge-base 实证）：三处闪退修复代码（6b9445e MDRadioButton→MDCheckbox + MDTopAppBar 去 subtitle / 7fd6c0f bump / e92f119 CJK 字体注册）均已含于 v0.8.0 历史——本版对闪退定位 =「验证修复已含历史版本 + 归档根因链 + CI 门禁保障」，非新写修复代码。问题全景 A1–A3（A1 闪退修复已含 v0.8.0 但无 CI 回归保障 / A2 CI 同步不带 --check 缺口⑦ / A3 三件套版本状态滞后于 git 事实）；改进收口 B1–B3（B1 验证归档 + selftest_android.py UI 启动安全静态断言三断言：无 MDRadioButton import / MDTopAppBar 无 subtitle kwarg / _register_cjk_fonts 定义 + build() 首行调用 / B2 build-android.yml 同步步骤后追加 sync --check 自证闸门（保留生成步骤再自证，规避 fresh checkout 生成物缺失边界）/ B3 三件套收口 + v0.9.0 语义厘清）；任务分解 T1 静态断言（无前置）→ T2 CI --check 闸门（无前置，与 T1 可并行）→ T3 版本收口核验（依赖 T1/T2）；提交规划 C0–C3（本版无协议层改动，verify.sh PASS=20 不变）。ROADMAP §1 L14 v0.9.0 状态切「🔵 当前主线」+ §6 范围细化落盘；README 协议链追加 12、新增 v0.9.0 🔵 块引用、v0.8.0 块引用切「✅ 已发布 2026-09-04」；本段下方 [0.8.0] 段归档为治理指针 3 发布归档收口（v0.8.0 发布时遗留，原 [Unreleased] v0.8.0 段内容原样迁入不增删改）。

- T1 UI 启动安全静态断言入冒烟（A1/B1，C1=6bea61f）：scripts/selftest_android.py 在控制器纯逻辑链路后追加第 [10] 段「UI 启动安全静态断言」三则（纯 python3 文件读取零 Kivy 依赖，任一 FAIL = 冒烟 exit 1）——①screens.py 行锚定正则（`^\s*from\s+kivymd\.uix\.selectioncontrol\s+import\s+MDRadioButton\b`，re.M）断言无 MDRadioButton 真实 import（KivyMD 1.2.0 已移除该类 → ImportError 闪退根因一；行锚定排除 _radio_row docstring 中旧代码根因描述文本误伤——首版裸子串匹配被正向运行实证误伤后修正）②main.py `MDTopAppBar\([^)]*subtitle=` 正则断言无 subtitle= kwarg（TypeError 闪退根因二）③main.py `_register_cjk_fonts` 定义在场 + build() 函数体首个非空非注释行断言含调用（CJK 方块字根因三）。三修复点（6b9445e MDRadioButton→MDCheckbox + MDTopAppBar 去 subtitle / e92f119 CJK 字体注册）均已含于 v0.8.0 历史（git merge-base 实证），本断言将修复点纳入 CI 回归保障——KivyMD 再 bump 或修复代码回退即被拦截；反向验证实证：sed 注入 MDRadioButton import → selftest exit 1 且 [10.a] 精确 FAIL，mv 恢复后 exit 0 全绿。
- T2 CI 同步步骤追加 --check 自证闸门（A2/B2，C2=66579c3）：build-android.yml「同步共享源码与种子数据」步骤后追加一步「双端一致性自证闸门（sync --check，缺口⑦）」（`run: bash scripts/sync_android.sh --check`）+ 注释说明——缺口⑦闭环：android/app/{core,seed} 为 .gitignore 生成物（不入库），v0.8.0 收口曾现人工漏同步双端漂移（core/registry.json 源 6110B vs 生成物 4186B 停旧快照）实证，一致性不再靠人工；保留生成步骤后再自证（fresh checkout 下生成物缺失，直接替换 --check 会命中缺失边界必然失败，已实证删生成物→sync 重建→--check exit 0）；有差异 exit 1 fail CI、无差异放行后续冒烟/构建。

## [0.8.0] - 2026-09-04（v0.8.0 自定义模块组合）
### Added
- 11_v0.8.0_自定义模块组合方案.md 落盘（方案真相源，I5）：v0.8.0 定位为「自定义模块组合——在 v0.7 开放协议注册之上对外开放模块组合，第三方题材模块可在 P00 骨架上自由组合装配为新的社区管线（方案甲：references 受控跨包引用）」。问题全景 A1–A3（A1 模块组合无机读通道 / A2 组合装配合法性无门禁 / A3 管线派生纯人读无组合清单）；改进收口 B1–B3（B1 组合引用 Schema 化 / B2 组合登记机制 + registry protocols[] references 投影 / B3 check15 组合门禁）；任务分解 T1 组合引用 Schema 规范 → T2 组合登记 + 两包 retro-fit + registry protocols[] → T3 verify.sh check15 + v2.5；提交规划 C0–C4。ROADMAP §1 行 13 v0.8.0 状态切「🔵 当前主线」+ §5 范围细化落盘；README 协议链追加 11、版本行切 v0.8.0（当前主线·开发中）。
## [0.7.0] - 2026-09-04（v0.7.0 自定义协议）

### Added
- T1 协议声明 Schema 机读化（B1）：01 §6 新增 6.1 第三方协议声明 protocol.yaml Schema 规范（必填 12 字段表 + R1→dependencies / R2→categories+module_id_range / R3→pipeline+mount_layers 映射 + M91-M99 编号规则 + 模板），社区包根目录必带 protocol.yaml。
- T2 注册流程机读化 + 投影扩展（B2）：02 §8.3 升级「登记 = protocol.yaml 在场 + 本表在册 + registry.json protocols[] 投影」三要件 + §9.1 字段映射表 §8↔protocols[] 行 + §9.2 社区登记同步纪律第 4 条；校园/西幻两包 retro-fit 落 protocol.yaml（校园 51 行 / 西幻 69 行）作首例战例，两包 README 补双源一致声明；registry.json 增 protocols[] 两包投影（schema_version 保持 "2"，V1 只增不删）。
- T3 注册门禁 check14（B3）：verify.sh 升 v2.4 新增 check14 社区协议登记门禁（入段 C 无条件执行）——protocol.yaml 在场 / Schema 必填 12 字段 yaml 解析 / R2 类别不冲突 / R1 依赖边界 / M91-M99 不占用 + 编号在册一致 / protocol.yaml↔README 双源一致 / registry protocols[] 投影一致，七项全绿 PASS=19。

### Changed
- 10_v0.7.0_自定义协议方案.md 落盘（方案真相源，I5）：v0.7.0 定位为「自定义协议——在 v0.6 统一入口之上对外开放协议注册，第三方可按协议声明注册自定义协议，进入注册表登记与门禁调度」。问题全景 A1–A3（A1 第三方协议注册无机读入口 / A2 协议声明无机读 Schema / A3 注册无门禁校验）；改进收口 B1–B3（B1 protocol.yaml Schema 机读化 / B2 注册流程机读化 + registry.json protocols[] 投影 / B3 check14 注册门禁）；任务分解 T1 协议声明 Schema 规范 → T2 两包 retro-fit + 02 §8.3/§9 升级 + registry.json protocols[] → T3 verify.sh check14 + v2.4；提交规划 C0–C4。ROADMAP §1 行 12 v0.7.0 状态切「🔵 当前主线」+ §4 范围细化落盘；README 协议链追加 10、版本行切 v0.7.0（当前主线·开发中）。

## [0.6.0] - 2026-09-04（v0.6.0 协议中转站）

### Added
- 工程治理三件套落盘：ROADMAP.md（五版本路线唯一规划真相源 + 治理指针四项）/ CHANGELOG.md（本文件）/ CONTRIBUTING.md（Conventional Commits + 四步验证门槛 + 三改动域细则）。
- .github 模板：ISSUE_TEMPLATE（bug_report / feature_request）+ PULL_REQUEST_TEMPLATE（改动域勾选 + 门禁自检清单）。
- verify.sh 增 check12 代码层门禁（desktop/tests/test_core.py 40 用例 unittest + py_compile 语法抽查）。
- T1.1 机读投影落地（协议中转站 B1 第一步）：desktop/src/core/registry.json 落盘（registry_schema_version "2"，13 件模块表 / P00–P80 挂载点含 P40/P60 optional / 四组固定订阅）；02 §9 机读投影声明 + 字段映射 + 同步纪律；registry_schema_version 1→2 V2 bump 首例（迁移记录四步见 02 §9.3）。
- T2 迁移机制落地（B2 第二步）：verify.sh 增 check13 迁移完整性门禁（02 §2 模块表 13 件 ↔ registry.json modules 逐条机读比对，python3 heredoc 断言）；verify.sh 升 v2.3 三段式门禁（段 A check1–6 / 段 B check7–11 / 段 C check12–13 无条件执行）。
- T3 sync --check 落地（B3 第三步）：scripts/sync_android.sh 增 `--check` 只读差异校验（core 段 diff -rq 排除 __pycache__ / seed 段逐目录 diff / `_ck_err` 汇总 exit 0/1），基态/异态双态自测通过，同步逻辑本体零改动。

### Changed
- 09_v0.6.0_协议中转站方案.md 落盘（方案真相源，I5）：v0.6.0 定位为「协议中转站——协议体系从人读规范文档升级为机读可驱动的通用协议层」。三项改进收口：B1 协议统一入口（02 §9 机读投影 registry.json + desktop Runtime 装载器 registry_loader，I5 扩展为「文档层 + 机读投影双校验唯一」）；B2 迁移机制落地（01 §7 实操模板 + registry_schema_version 1→2 V2 bump 首例 + verify.sh check13 断言）；B3 同步工具链 --check（sync_android.sh 只读差异校验，有差异 exit 1）。任务分解 T1 协议统一入口 → T2 迁移机制（依赖 T1.1 bump 素材）→ T3 sync --check（独立并行）；提交规划 C0–C5。

## [0.5.0] - 2026-09-04（v0.5.0 优化版）

### Added
- T1 编号治理收口：重号类别前缀全限定（M22/M10 等带 通用:/事件:/生存:/情感: 前缀），verify.sh check2 限定扫描。
- T2 社区包装配：P02 校园情感流 / P03 西幻生存流两套预设；R1 包间禁互引 / R2 类别独占 / R3 装配契约；07 §7 终验清单 Mxx 引用全限定收口。
- T3 记忆分层：认知边界（M23）与记忆分层模块落地。
- T4 M80 门禁流水线：M80 §3 gate 三档升级为声明式 gate_action 流水线（pass: [direct] / warn: [self_correct, log_revision] / fail: [rewrite, retry_limit:3, fallback: white_sketch]）+ gate_decision_record 决策记录格式（系统日志独立通道，不进叙事文本）；P90 引用闭合（以 M80 §3 为唯一真相源）；verify.sh check5 补 gate_action / gate_decision_record 断言。
- T5 资产工作台化：三方对账脚本 scripts/reconcile_assets.sh + verify.sh check11 门禁 + 两份 assets/README 标注列与官方核心对照修正。
- T6 社区发布规范收口。

### Changed
- verify.sh v2.1：两段式门禁（段 A 官方核心 check1–6 / 段 B 社区领域包 check7–11，缺包 WARN 跳过）。

## [0.4.0] - 2026-09-04（两级结构收口）

- 平台 v1.1 起两级结构：官方核心 13 件（通用 6 / 事件 5 / 世界 1 / 技术文档 M90）+ 社区领域包登记（02 §8）。
- 07 §7 项 8 裸 M22/M40 补情感: 类别前缀；selftest_android.py 对齐官方收敛结构（管线 P02→P01，android seed 仅 P00/P01/P90）。

## [0.3.0 / 0.3.1 / 0.3.2 / 0.3.3] - 2026-09-03 / 09-04（Android 首次 APK 发布与构建链修复系列）

- v0.3.0：Android 首次 APK Release（buildozer 裸机 master 方案 + KivyMD 五屏 UI 闭环）。
- 0.3.1–0.3.3：构建链修复——minapi 23→24（CPython3.14 remote_debugging 用 preadv/pwritev，bionic 自 API24 才声明）；pin NDK r25b（解锁 kivy 2.3.0 cgl_gl clang compile）；p4a pin #3180；python -m build --skip-dependency-check（绕过 dist-info 残留误报）；CI 失败诊断注解回传（::error::、TAIL30、clang error 行精确抓取）。

## [0.2.0] - 2026-09-03（Android 端落地）

- Android 端 KivyMD 五屏 UI + controller 闭环 + buildozer CI 工作流（弃三方 docker action，改裸机 master 方案）。

## [0.1.0] - 2026-09-03（桌面首发）

- 模块化叙事引擎项目文件全量交付（01 协议 / 02 注册表 / 03 管线 / 04 模块 / 05 资产 / 06 执行协议 / 07 社区预设 + 十项验收 verify.sh）。
- 桌面三平台 Release（CI 构建，Release 资产加平台后缀）+ 社区版模板工作流 + MIT License。
