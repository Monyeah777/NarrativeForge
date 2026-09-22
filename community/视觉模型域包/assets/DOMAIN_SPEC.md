<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 视觉模型

> 用途：本域包的**内容资产与口径面**——把「视觉模型」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
> 资产键：`DOMAIN_SPEC`｜机读同源面 = `outputs/DOMAIN_SPEC.json`（双源一致由 check32 output_forms 断言；**本表是唯一人读真相，JSON 是它的机读投影**）。

## 1. 口径纪律

1. **定义可判定**：每条细分的定义必须能回答「什么算做对/做错」，不允许只给形容词。
2. **判据可机检**：每条细分给出可写进校验器的判据（字段 / 范围 / 词表 / 一致性）。
3. **锚可复核**：每条挂一个外部权威锚（规范 / 论文 / 参考实现），URL 与可达性实测记于 `STANDARDS_ANCHORS`。
4. **失效模式显式**：写清该细分最常见的错法——它是质检单，不是介绍页。
5. **口径不合并**：不同细分不共用同一条判据文本；相似即拆细。

## 2. 细分口径表（12 条）

| 条目键 | 细分 | 定义口径 | 可机验判据 | 常见失效模式 |
|---|---|---|---|---|
| `A03-01` | 图像分类与主干网络 | 图像分类的口径：类别空间、top-k 报告方式与主干网络口径（层数 / 宽度 / 输入分辨率）。 | 声明 num_classes、top_k（枚举 1|5）、input_resolution（正整数）与 backbone_id；四者齐备方可比较。 | 类别空间不同却直接比 top-1；分辨率提升带来的收益与推理成本未一并报告。 |
| `A03-02` | 目标检测 | 目标检测的口径：IoU 阈值、NMS 参数、置信度阈值与框格式。 | 声明 iou_threshold、nms_iou、score_threshold、box_format（xyxy|xywh）四项；缺一即检测口径未定。 | NMS 阈值变动使 mAP 不可比；框格式未声明导致坐标错位。 |
| `A03-03` | 语义与实例分割 | 语义分割与实例分割的口径：掩码粒度、忽略类、评估指标（mIoU / mask AP）。 | 声明 mask_granularity（semantic|instance|panoptic）、ignore_index（类别 id 或 none）、metric（mIoU|mask_AP）。 | 忽略类处理不同导致 mIoU 虚高；语义与实例指标混用。 |
| `A03-04` | 关键点与姿态估计 | 关键点与姿态估计的口径：关键点数量与顺序、OKS 阈值、单人 / 多人设定。 | 声明 keypoint_count、keypoint_order（定义表引用）、oks_threshold 与 setting（single|multi person）。 | 关键点顺序不同造成精度骤降的假象；阈值未声明导致 AP 不可比。 |
| `A03-05` | 深度估计与点云 | 深度估计与点云的误差口径：尺度对齐方式、截断阈值与单位。 | 声明 scale_alignment（none|median|least-squares）、max_depth（截断，米）、unit，以及指标（AbsRel|RMSE）。 | 未做尺度对齐就报 AbsRel；截断阈值不同导致跨报告不可比。 |
| `A03-06` | 人脸识别与活体检测 | 人脸识别与活体检测的口径：阈值选择、误识率口径与活体攻击类型覆盖。 | 声明 far（误识率，如 1e-4）、threshold、以及活体攻击类型清单（print|replay|mask）；三者齐备。 | 只报准确率不报误识率；活体只测打印攻击却宣称防多种攻击。 |
| `A03-07` | 图像检索与重识别 | 图像检索与重识别的口径：查询库规模、mAP / CMC 口径与跨域设定。 | 声明 gallery_size、mAP 计算口径（是否用 CMC 单查询）、以及跨域测试设定（same|cross domain）。 | gallery 规模不同直接比 mAP；跨域设定未声明导致泛化结论失真。 |
| `A03-08` | 视频理解与动作识别 | 视频理解与动作识别的口径：采样帧数与间隔、时序窗口、clip 级还是视频级判定。 | 声明 frames_per_clip、sampling_rate（帧间隔）、temporal_window（秒）与 granularity（clip|video）。 | 用更多帧换分数却不报推理成本；clip 级精度当视频级结论。 |
| `A03-09` | 医学影像分析 | 医学影像分析的口径：数据划分（患者级 / 切片级）、敏感度与特异度口径、阅片参考标准。 | 声明 split_level（patient|slice）、sensitivity/specificity（各含阈值）、以及 reference_standard（金标准来源）。 | 切片级划分导致同一患者跨训练与测试集；只报 AUC 不报阈值下的敏感度与特异度。 |
| `A03-10` | 工业缺陷检测 | 工业缺陷检测的口径：缺陷类型定义、漏检与误检口径、监督设定。 | 声明 defect_taxonomy（类型清单）、image_level vs pixel_level 指标、以及 setting（supervised|unsupervised）。 | 图级 AUROC 当像素级分割性能；缺陷类型定义随批次变化导致指标漂移。 |
| `A03-11` | 遥感与航拍解译 | 遥感与航拍解译的口径：地物类别体系、影像分辨率与地理划分（按区域切分）。 | 声明 class_taxonomy（类别体系来源）、gsd（地面采样距离，米/像素）、以及 split_by（region|random）。 | 随机切分让相邻瓦片跨集，指标虚高；类别体系不同却比较 mIoU。 |
| `A03-12` | 数据增强与预训练策略 | 数据增强与预训练策略的口径：增强管线、预训练目标与下游微调设定。 | 声明 aug_policy（策略名 + 版本）、pretrain_objective（对比|掩码|监督）、finetune_epochs；三者齐备。 | 预训练目标不同却只比下游分数（无法归因）；增强策略未记录导致不可复现。 |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`classification`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `视觉模型:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `视觉模型:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
