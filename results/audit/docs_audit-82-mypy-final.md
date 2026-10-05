---
id: AUD-0034
title: 类型分批收敛收尾（desktop/src 剩余 31 条全部清零，24 模块）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」；承接 AUD-0033。开工依据为内部实测（mypy desktop/src 错误条数 31）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/silent_skip.py:7a9e953f959d31161f29dcb5de4ef755a63d31ff807bdf333403c4b048f07457
  - desktop/src/core/round_drill.py:4ad4faa28a2251a51897b8d96a6f7cfcc5d48f2bfb5b5c83b3c7af5be40ce9fb
  - desktop/src/core/quant_metrics.py:ae2bd5a5b71531ee4cf4abe920f75a939a30a5bea105efa7aed011cc92369ce3
  - desktop/src/core/module_lifecycle.py:7b84396342e77fea32e6b54cd78e296f1dddf925937b8331dbcdebeb4e9ad1d0
  - desktop/src/core/market_analyzer.py:797870b6ac5d8f012e94b0ecbe4785b001b3df825bd90c1507e18aa8f71a5989
  - desktop/src/core/protocol_golden.py:b37b80ee8691fd76ed2df41f5006285c92914449bdfd6a2210164c7bc1f3e353
  - desktop/src/core/knowledge_sig.py:2e1177ae8701b38cff3b26e92892b3cbef4a347a48b986dd8b1f95934f60323b
  - desktop/src/core/output_forms.py:4981ef6aea157be3d26754b4eade7a40340fd235795c50ba50fe193642cd5ea8
  - desktop/src/core/pipeline_loader.py:4c58b842a8b79abdce6917305f8f5c307e4334cfa377cb3dc1b9d6f226871588
  - desktop/src/core/community_inventory.py:88659eb0df649794d4fcfaab2f0fb894ba53c190f3e57ed8b661cdca2216d7a0
  - desktop/src/core/retriever.py:1bab0db39be26c025e37cecab19e65d8fb439140f3bb224e869b771666c777fd
  - desktop/src/core/lazy_yaml.py:19df29d70c5a694ae63527f46e4537b041cd2b889baca358e6262b4dad0e151b
  - desktop/src/core/json_schema.py:06c0e26f503fb53a6f23653417f889c8168b7579c412f963e507052c55c28f5d
  - desktop/src/core/export_schema.py:9052dc891be0c70ceb5b42544eceeceeeb4dee8c4f107b1ec660913cf922ad3d
  - desktop/src/core/orchestration.py:a2c50663819521a2bb1b7064f14382e7254910a39eb6cf88785cb05efdfdf558
  - desktop/src/core/machine_contract.py:68e83ea3e474a788acc8574969b35573d7522726be8d9b98f30c4b6733aff3af
  - desktop/src/core/decisions.py:84f19a75ac32048c5849e71226a9c6ca3bf138ac8ed928f33a550b6be552cf58
  - desktop/src/core/layer_model.py:f9988ba40d9db789f7acaf1af24a0e3e8dc07eee14e7a487bc94742d11f778f1
  - desktop/src/core/import_graph.py:929b6cdff4715dc4b007bbcd273cee5581fc6744ed5abcd90157c4cfef0a80b0
  - desktop/src/core/bench.py:a66769543e0a4546ec52d869baa326916a996748f86a4798ca1dd0f238c70153
  - desktop/src/core/import_adapter.py:5130103b8a9fff436ca4bab1b7ec3ba710652d8f767f24f1d983a0d9a21991de
  - desktop/src/core/daemon.py:ac60f99e9b2e8d72d568884bc4e3840f1b69bff9fa8f9a0647c155f4f85948af
  - desktop/src/core/decision_layer.py:4105c5e1b61adcc5a0b8b49568ec38df05705c2a02f2cdbb4d3f3c109b94aa99
  - desktop/src/core/exporter.py:d396f742ccf012331c855c4f52f0925daebc6100cadff30d4e1f510a9dff4c04
  - protocol/code_metrics_baseline.json:060667035d17d359d69ad3603052e079d70b52d19000bac7db6a2bc50536b5ce

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因 7 个模块行数/圈复杂度增长按工具指引重冻。

## 一、结果

`python -m mypy desktop/src --ignore-missing-imports` 错误条数 **31 → 0**（默认口径）。

## 二、交付（按修法归类）

| 类 | 模块 | 修法 |
|---|---|---|
| 真标注错配 | `import_graph` | `parse` 标注写成 3 元组而实现返回 2 元组 `(deps, dyn)`、调用方也按 2 元组解包——三处只有两处一致；标注改为 `Optional[Tuple[frozenset, bool]]`，两处差错同消 |
| 变量复用解耦 | `round_drill`（allowed→allowed_set）· `orchestration`（tools→wf_tools）· `export_schema`（e→entry） | |
| 声明/集合显式类型 | `module_lifecycle` · `market_analyzer` · `pipeline_loader` · `community_inventory` · `retriever` · `knowledge_sig` · `silent_skip` · `decisions` · `machine_contract` · `exporter` · `decision_layer` | 补 `dict`/`list`/`Dict[str, Any]` 标注 |
| 可空收窄 | `bench`（局部 match 判空）· `daemon`（spec is None 守卫）· `import_adapter`（body 拆原始值）· `json_schema`（py: Any） | |
| 平台/属性 | `lazy_yaml`（os.sys→import sys）· `layer_model`（getattr(node, lineno, 0)） | |
| 数值文本 | `quant_metrics`（float(x or 空串)，与原 float(None) 同落 except） | |
| 键归 str | `output_forms`（str(f.get(category))）· `protocol_golden`（str(len(...))） | |

## 三、验收证据（本机实测）

- `mypy desktop/src` 错误条数 **31 → 0**。
- `python -m unittest`（本批相关 19 组）→ **282 例**（skipped=1）全绿。
- `python scripts/code_metrics.py` → 7 个模块行数或圈复杂度增长，按工具指引重冻。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. **范围限定**：本次清零的是 `desktop/src`（core 库）；`scripts/**` 与 `desktop/tests` 未纳入本线。
2. radon 复杂度仍为存量；62 §三·② 余量与 §二·2 .NET 重冻不在本件范围。
3. `import_graph` 的标注错配是真缺陷面（三处不一致），但运行时按实现走、未产生错误行为；本件只校准标注，不改运行路径。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑↑ | desktop/src mypy 归零；282 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面（两处守卫均收窄到原路径） |
| 架构纯度 | → | 只改类型标注/变量命名 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
