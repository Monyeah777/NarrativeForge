<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 三维与世界模型

> 用途：本域包的**内容资产与口径面**——把「三维与世界模型」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
> 资产键：`DOMAIN_SPEC`｜机读同源面 = `outputs/DOMAIN_SPEC.json`（双源一致由 check32 output_forms 断言；**本表是唯一人读真相，JSON 是它的机读投影**）。
> **内容档位**：authored（逐条撰写，含领域专属判据与权威锚）。

## 1. 口径纪律

1. **定义可判定**：每条细分的定义必须能回答「什么算做对/做错」，不允许只给形容词。
2. **判据可机检**：每条细分给出可写进校验器的判据（字段 / 范围 / 词表 / 一致性）。
3. **锚可复核**：每条挂一个外部权威锚（规范 / 论文 / 参考实现），URL 与可达性实测记于 `STANDARDS_ANCHORS`。
4. **失效模式显式**：写清该细分最常见的错法——它是质检单，不是介绍页。
5. **口径不合并**：不同细分不共用同一条判据文本；相似即拆细。

## 2. 细分口径表（12 条）

| 条目键 | 细分 | 定义口径 | 可机验判据 | 常见失效模式 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|---|
| `A08-01` | 三维重建与辐射场 | 三维重建与辐射场的口径：输入视图数、坐标约定、指标（PSNR/SSIM/LPIPS）与视角划分。 | 声明 views（训练/测试视角数）、coord_system（右手/左手 + 上轴）与 metric（PSNR/SSIM/LPIPS + 下采样口径）。 | 测试视角与训练视角重叠（虚高）；分辨率与下采样口径不同直接比 PSNR。 | `opengeospatial` OGC 标准（含 GeoJSON/3D Tiles）（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A08-02` | 点云处理 | 点云处理的口径：点云来源（扫描/生成）、采样密度与旋转平移不变性设定。 | 声明 source（lidar|rgbd|generated）、density（点/平方米或总点数）与 invariance（旋转|平移|尺度 是否要求）。 | 训练/测试采样密度不同；宣称旋转不变却未做旋转增强测试。 | `opengeospatial` OGC 标准（含 GeoJSON/3D Tiles）（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A08-03` | 纹理与材质生成 | 纹理与材质生成的口径：材质表示（PBR 通道）、分辨率与光照一致性要求。 | 声明 pbr_channels（albedo/normal/roughness/metallic 等）、texture_resolution 与 lighting_consistency（是否做重光照检验）。 | 只有 albedo 却宣称材质完整；生成纹理烘焙进光照（不可重光照）。 | `onnx` ONNX（opset 扩展）（iface｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A08-04` | 文生 3D 资产 | 文生 3D 资产的口径：表示形式（网格/高斯/隐式）、面数与多视角一致性判据。 | 声明 representation（mesh|gaussian|implicit）、face_count（或点数）与 multiview_consistency（一致性指标 + 采样视角数）。 | 只展示单视角好看；面数不声明导致不可用于下游管线。 | `ietf-json-schema` JSON Schema 2020-12（data｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `A08-05` | 场景生成与布局 | 场景生成与布局的口径：房间类型 / 布局约束、可通行性检查与物理合理性。 | 声明 room_types、constraints（可通行/支撑面/无穿插）与 physics_check（碰撞检测是否执行）。 | 生成结果物体穿插或悬空；无通行性检查导致不可用。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（eng｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `A08-06` | 物理仿真与碰撞 | 物理仿真与碰撞的口径：求解器、时间步长、接触模型与稳定性判据。 | 声明 solver（含版本）、dt（时间步长 s）、contact_model 与 stability_check（能量守恒/穿透深度上限）。 | 时间步长过大导致穿透（结论无效）；求解器版本未记录。 | `onnx` ONNX（opset 扩展）（iface｜✓） | `ietf-json-schema` JSON Schema 2020-12（data｜✓） |
| `A08-07` | 世界模型与状态预测 | 世界模型与状态预测的口径：状态表示、预测时域与 rollout 误差累积报告。 | 声明 state_repr（字段/维度）、horizon（预测步数）与 rollout_error（分步误差曲线，不只报单步）。 | 只报一步预测误差；长时域误差发散未报告。 | `onnx` ONNX（opset 扩展）（iface｜✓） | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） |
| `A08-08` | SLAM 与定位 | SLAM 与定位的口径：传感器配置、轨迹误差指标（ATE/RPE）与失败场景记录。 | 声明 sensors（相机/IMU/LiDAR）、metric（ATE|RPE + 对齐方式）与 failure_cases（动态物体/弱纹理等）。 | 只在理想序列评测；对齐方式（SE3/Sim3）未声明导致尺度误差被掩盖。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（eng｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A08-09` | 数字孪生 | 数字孪生的口径：孪生粒度、同步频率与偏差监控指标。 | 声明 twin_granularity（设备/产线/园区）、sync_hz 与 drift_metric（孪生与实测偏差）。 | 孪生只做静态建模（无同步）；偏差无监控（孪生与实际脱节不可见）。 | `onnx` ONNX（opset 扩展）（iface｜✓） | `mermaid` Mermaid 图语言（form｜✓） |
| `A08-10` | 3D 资产格式与管线 | 3D 资产格式与管线的口径：格式（glTF/USD/FBX）、坐标系、单位与压缩策略。 | 声明 format（含版本）、up_axis、unit（米/厘米）与 compression（Draco/USDZ 等）。 | 单位与上轴不一致导致缩放/朝向错；压缩后属性丢失未核。 | `ietf-json-schema` JSON Schema 2020-12（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A08-11` | 骨骼绑定与动画 | 骨骼绑定与动画的口径：骨骼层级、蒙皮权重与动画重定向误差。 | 声明 skeleton_joints、skin_weight_norm（是否归一化）与 retarget_error（关节位置误差 mm/度）。 | 权重未归一化导致蒙皮坍缩；重定向误差不报导致动画不可用。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（eng｜✓） | `ietf-json-schema` JSON Schema 2020-12（data｜✓） |
| `A08-12` | 三维评测 | 三维评测的口径：几何指标（Chamfer/F-score）、感知指标与评测集划分。 | 声明 geom_metric（Chamfer|F-score + 阈值）、perceptual_metric 与 split（同类别内 vs 跨类别）。 | 只报 Chamfer 不报感知质量；跨类别评测当同类别结论。 | `opengeospatial` OGC 标准（含 GeoJSON/3D Tiles）（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`regression`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `三维与世界模型:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `三维与世界模型:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
