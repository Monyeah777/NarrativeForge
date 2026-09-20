# 管线 P07 · AI系统域装配流
> 社区版「AI系统域包」使用的管线（第 2 个非叙事域战例落盘）。以「概念前置依赖的求值 → 装载序」为流主轴：官方核心 M00 数据槽（P00 位）承载概念状态，通用:M10 节拍（P10 位）给求值定拍，M50 主循环（调度器，无层挂载）在回卷点推进下一回合；本包自带 AI系统:M25 挂 P40 位做**前置闭包求值**（读图算 `closure(c)` / `missing(c, L)`），AI系统:M26 挂 P60 位做**装载序与就绪门**收口（`toposort` 确定性线性化 + 逐概念就绪判定）；P80 输出呈现仍由官方核心 M80 质检渲染（gate 唯一出口，同其它流）。
> 实例声明：本管线是通用骨架 **P00**（03_管线库/P00_通用文档生成管线.md）在**AI系统·概念前置域**的实例——九层位（P00–P80）名沿用骨架；本包 P40/P60 两驻留自带模块（AI系统:M25/M26），其余层位由官方核心承载，本包不自建重复模块（I5 单一真相源，官方模块文件不复制进包）。
> **允许编号段固化（R2）**：本包 `allowed_modules` 只含官方核心承载件与本包类内段编号——P00 数据基座 M00 / P10 世界推进 通用:M10 / P20 角色状态 M23 / P30 事件生产 事件:M22·M06·M13 / P40 行为决策 **AI系统:M25** / P50 交互执行 M12 / P60 长期演变 **AI系统:M26** / P70 叙事素材 M20·M24 / P80 输出呈现 M80；M50 主循环为全局调度器（无层挂载），以 core 依赖引用参与回卷。references=[] 零跨包零借阅——其余编号一律不得引入。
> **挂载层规避（check15 ③）**：官方骨架 P00 九层 default 均空；既有社区包同层 default（校园 P40=[情感:M22,M40,M41,M43,M55]、P60=[M40,M65]；西幻 P40=[M04,M11]、P60=[生存:M10,M07,M09,M14,M15,M16]；技术文档 P40=[M97]、P60=[M98]）与本包 P40=[AI系统:M25]、P60=[AI系统:M26] 无交集——类内段新编号唯一，独立装载不冲突（卸载本包不影响官方核心与既有包）。
```yaml
Pipeline:
  id: P07
  name: AI系统域装配流
  structure:
    type: linear
    flow:
      - from: P00
        to: P10
      - from: P10
        to: P20
      - from: P20
        to: P30
      - from: P30
        to: P40
      - from: P40
        to: P50
      - from: P50
        to: P60
      - from: P60
        to: P70
      - from: P70
        to: P80
      - from: P80
        to: P00
        condition: 主循环回卷（M50 调度下一回合；通用:M10 节拍同拍推进）
  layers:
    - id: P00
      name: 数据基座
      description: 官方核心 M00 数据槽承载 PrereqState（闭包/缺失/就绪/节拍四域）；M00 本体驻官方核心位不搬移，本包零重复挂载
      optional: false
      default_modules: []
      allowed_modules: [M00]
    - id: P10
      name: 世界推进
      description: 官方核心 通用:M10 时间推进提供求值节拍（tick_day/minute_tick）；本体驻官方核心位不搬移
      optional: false
      default_modules: []
      allowed_modules: [通用:M10]
    - id: P20
      name: 角色状态
      description: 官方核心 M23 认知边界承载可见域裁剪（概念可见性由外部治理面裁决）；本包不重复挂载
      optional: false
      default_modules: []
      allowed_modules: [M23]
    - id: P30
      name: 事件生产
      description: 官方核心事件流在此生产（事件:M22 事件总线 / M06 任务剧情 / M13 NPC 交互）；本包事件经总线对外可见，不直连他包模块
      optional: false
      default_modules: []
      allowed_modules: [事件:M22, M06, M13]
    - id: P40
      name: 行为决策
      description: 闭包求值层：自带 AI系统:M25 解析检索词（条目键 / 别名 / 概念名）并读概念图 CONCEPT_GRAPH，对目标概念求前置闭包与缺失清单，写 PrereqState 并发布 concept_closure_ready / prereq_missing（M50 主循环调度本体驻官方核心位，不搬移）
      optional: false
      default_modules: [AI系统:M25]
      allowed_modules: [AI系统:M25]
    - id: P50
      name: 交互执行
      description: 回合流转由官方核心 M50 主循环与 M12 NPC 对话承载；本包只提供装载序/就绪门查询面，不重复挂载
      optional: false
      default_modules: []
      allowed_modules: [M12]
    - id: P60
      name: 长期演变
      description: 装载序层：自带 AI系统:M26 订 concept_closure_ready / prereq_missing，收口确定性拓扑装载序（load_order）、逐概念就绪门（readiness_gate）与下一步可装载集（ready_frontier），发布 load_order_ready
      optional: false
      default_modules: [AI系统:M26]
      allowed_modules: [AI系统:M26]
    - id: P70
      name: 叙事素材
      description: 素材与知识查证由官方核心 M20 世界知识库 / M24 组合规则承载；本包概念图自持于包内资产，不借阅他包资产
      optional: false
      default_modules: []
      allowed_modules: [M20, M24]
    - id: P80
      name: 输出呈现
      description: 官方核心 M80 输出生成器（gate 唯一出口；读 concept_closure_ready / prereq_missing / load_order_ready 与 PrereqState 后质检渲染）
      optional: false
      default_modules: []
      allowed_modules: [M80]
  dependencies:
    - from: P40
      to: P60
      reason: M25 的闭包与缺失清单（concept_closure_ready / prereq_missing）进入 M26 的装载序与就绪门
    - from: P00
      to: P40
      reason: PrereqState 落 M00 数据槽，闭包求值读写同一槽位
    - from: P10
      to: P40
      reason: 通用:M10 节拍给闭包求值定拍（tick 记入 PrereqState）
    - from: P60
      to: P80
      reason: load_order_ready 交 M80 输出门渲染（gate 唯一出口）
  tags: [AI系统, 非叙事域, 概念前置闭包, 装载序]
```
## 运行规则
- 只叠加、不搬移：官方核心配合件（M00 / 通用:M10 / M23 / M50 / M80，以及空跑层位的 M06/M13/M12/M20/M24/事件:M22）本体驻官方核心层位；本包以 core_only 依赖引用协作，**禁止**复制官方模块文件入本包 modules/ 或写入官方层 default 槽（I5 单一真相源）。
- 契约闭合：AI系统:M25 零订阅（求值由调度与层序触发）；AI系统:M26 subscribe（concept_closure_ready / prereq_missing）⊆ AI系统:M25 publish——本包内发布/订阅自洽无越界（check16 ③ 语义的同包形态）。
- 同层 default 无交集（check15 ③）：本包 P40 只挂 AI系统:M25、P60 只挂 AI系统:M26；官方骨架各层 default 为空、既有社区包同层 default 无本包编号——独立装载不冲突。
- 四件产物（前置闭包 / 缺失清单 / 合法装载序 / 下一步可装载集）由 P40→P60 顺序产出；概念图 v1.1 双支 47 概念 + 概念别名表，可经 `python scripts/ai_domain_closure.py` 逐字节复现；判据面缺口（图内部一致性不在 verify check 族内）如实记档于 `results/audit/docs_audit-50-ai-domain.md` 与 `results/audit/docs_audit-51-ai-domain-deepen.md`。
- 本包 references=[] 恒空（零跨包零借阅）；后续包可经 references 协议级通道引用本包模块（届时按 02 §8.4 组合登记另立装配）。
---
