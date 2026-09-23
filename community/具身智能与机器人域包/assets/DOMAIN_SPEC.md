<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 具身智能与机器人

> 用途：本域包的**内容资产与口径面**——把「具身智能与机器人」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
> 资产键：`DOMAIN_SPEC`｜机读同源面 = `outputs/DOMAIN_SPEC.json`（双源一致由 check32 output_forms 断言；**本表是唯一人读真相，JSON 是它的机读投影**）。
> **内容档位**：authored（逐条撰写，含领域专属判据与权威锚）。

## 1. 口径纪律

1. **定义可判定**：每条细分的定义必须能回答「什么算做对/做错」，不允许只给形容词。
2. **判据可机检**：每条细分给出可写进校验器的判据（字段 / 范围 / 词表 / 一致性）。
3. **锚可复核**：每条挂一个外部权威锚（规范 / 论文 / 参考实现），URL 与可达性实测记于 `STANDARDS_ANCHORS`。
4. **失效模式显式**：写清该细分最常见的错法——它是质检单，不是介绍页。
5. **口径不合并**：不同细分不共用同一条判据文本；相似即拆细。

## 2. 细分口径表（12 条）

| 条目键 | 细分 | 定义口径 | 可机验判据 | 常见失效模式 | 可扩展标准（绑定） |
|---|---|---|---|---|---|
| `A13-01` | 机器人运动规划 | 机器人运动规划的口径：规划空间、约束（碰撞 / 关节限位）、规划时间与成功率。 | 声明 planning_space（joint|task）、constraints（清单）、plan_timeout_ms 与 success_rate（含试验次数）。 | 只报单次成功（不给试验次数）；约束未写全导致「成功」不可复现。 | `eu-machinery` 机械条例 2023/1230（EU） |
| `A13-02` | 抓取与精细操作 | 抓取与精细操作的口径：抓取位姿表示、成功率定义与失败模式分类。 | 声明 grasp_repr（6DoF|top-down）、success_definition（阈值）与 failure_taxonomy（滑落/碰撞/未接触等）。 | 成功定义含糊（抬升算不算）；失败不分类型导致无法迭代。 | `uptane` OTA 安全框架（Uptane） |
| `A13-03` | 视觉语言动作模型 | 视觉语言动作模型（VLA）的口径：动作空间、观测模态与指令跟随评测。 | 声明 action_space（关节增量|末端位姿 + 频率）、obs_modalities（枚举）与 instruction_following（评测集 id）。 | 动作频率未声明导致轨迹不可执行；指令跟随只用训练分布内指令评测。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A13-04` | 遥操作与示教 | 遥操作与示教的口径：遥操作时延、示教数据量与质量过滤规则。 | 声明 teleop_latency_ms、demo_episodes（条数）与 quality_filter（成功/人工剔除规则）。 | 示教含失败样本未过滤；时延未声明导致遥操作可用性结论无效。 | `uptane` OTA 安全框架（Uptane） |
| `A13-05` | 仿真到现实迁移 | 仿真到现实迁移的口径：域随机化维度、真机微调规模与性能落差报告。 | 声明 randomization_dims（清单）、real_steps（真机样本量）与 sim2real_gap（仿真与真机指标差）。 | 只报仿真成绩；真机样本量与落差未报告。 | `eu-machinery` 机械条例 2023/1230（EU） |
| `A13-06` | 多传感器感知融合 | 多传感器感知融合的口径：传感器集合、时间同步方式与融合层级。 | 声明 sensors（枚举）、sync（硬件触发|软同步 + 容差 ms）与 fusion_level（early|late|hybrid）。 | 时间同步容差不声明导致融合结果不可复现；传感器缺失时无降级策略。 | `uptane` OTA 安全框架（Uptane） |
| `A13-07` | 任务与技能库 | 任务与技能库的口径：技能表示（参数化 / 学习策略）、前置条件与组合接口。 | 声明 skill_repr（参数化|policy）、preconditions（字段清单）与 composition_api（调用契约）。 | 技能无前置条件（组合即失败）；接口无契约导致复用不了。 | `eu-machinery` 机械条例 2023/1230（EU） |
| `A13-08` | 人机协作安全 | 人机协作安全的口径：安全标准引用、速度与力限制、急停与风险评估。 | 声明 safety_standard（如 ISO/TS 15066）、speed_force_limits（数值 + 依据）与 e_stop（响应时间 ms）。 | 安全限值无标准依据；急停响应时间未实测。 | `owasp-llm` LLM 应用十大风险（OWASP） |
| `A13-09` | 移动机器人与导航 | 移动机器人与导航的口径：定位方式、建图指标与导航成功率。 | 声明 localization（lidar|视觉|融合 + 精度 cm）、mapping_metric（ATE/RPE）与 nav_success（含场景数）。 | 只报里程计误差不报闭环一致性；导航成功率未给场景分布。 | `covesa-vss` Vehicle Signal Specification（COVESA） |
| `A13-10` | 机械臂标定 | 机械臂标定的口径：标定方法、残差指标与复检周期。 | 声明 calibration_method（手眼|DH）、residual（mm / 度）与 recalibration_interval（小时或次数）。 | 标定残差不公开（精度无据）；无复检周期导致漂移未被发现。 | `eu-machinery` 机械条例 2023/1230（EU） |
| `A13-11` | 数据集与基准 | 数据集与基准的口径：任务集合、演示模态（视觉 / 动作）与切分方式。 | 声明 task_count、modalities（枚举）与 split_policy（按任务|按场景|随机）。 | 随机切分让同一任务跨训练与测试；模态清单与实际不符。 | `mlcommons-croissant` Croissant 数据集元数据（MLCommons） |
| `A13-12` | 具身 Agent | 具身 Agent 的口径：状态表示、动作原语与长程任务成功率。 | 声明 state_repr（字段清单）、action_primitives（枚举）与 long_horizon_success（分步数与成功率曲线）。 | 长程任务只报最终成功（中间失败被掩盖）；动作原语未封闭。 | `mcp` Model Context Protocol（Anthropic/MCP） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`exact_judgement`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `具身智能与机器人:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `具身智能与机器人:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
