---
id: AUD-0036
title: 类型收敛扩面到 desktop/tests（66 条清零，27 文件）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」；承接 AUD-0034/0035。开工依据为内部实测（mypy desktop/tests 错误条数 66）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/tests/test_write_flag_gate.py:1e2bc2f592b8a3eee57a7e43d5857a388eb74dfe2e60c4e89321963bbfdb1657
  - desktop/tests/test_verification_cards.py:e5ebad23cd0e7465ef4bc5b2aaa21d2df5fbde9a9715bcd754805bfe1bd35d8a
  - desktop/tests/test_serve_default.py:f7e74df3d53b22cad3d0daf0f81c39a3c4e2a19228d210c8f445a315f24b9da8
  - desktop/tests/test_selfcontained_rebuild.py:b0b7d252053ed69a41665ca5c4da0c2f2c84b9a85e644ae42d896a4ce4f430a3
  - desktop/tests/test_rust_fastlane.py:b50481a83b030f5037f14601ae2056bce0253a31c127074c73a5e9bdb2d47e56
  - desktop/tests/test_quant_domain_package.py:d0ca63155f193536f7ef5509f4145b9375c04747f0b48438936ba611b1db2b51
  - desktop/tests/test_mcp_write_freedom.py:905806f235c67577594d4673140aa8709297f3673027c6b50e941a1de525d1c1
  - desktop/tests/test_mcp_runtime.py:12d48890a73f60721fe39ce33c7b189c13601b29cfdd16bcc87ecc949a9adee0
  - desktop/tests/test_live_doc_counts.py:97d927f138d8a01bf3647a6a4aef4fd67b4c5efc87f276d66148eeb840d1a6c9
  - desktop/tests/test_layer_model.py:b8f0d653573f088ae8c4b1a66a415697b82496fd3fd4443d2e6cb8f4983aa54e
  - desktop/tests/test_knowledge_sig.py:49d296144924aef62ecf80447ab631f98712c9f1113f8e7ec1f90b4677c66df3
  - desktop/tests/test_judgement_coverage.py:1ef21354be3d9046aa24f845f32a0f24a4e7cc84ef5061a0948779458d93b2b7
  - desktop/tests/test_judge_references.py:b9dd886b02f45c3fbf3c2c73a28ebc33b6783afeb31f5df94b2986368e304453
  - desktop/tests/test_intake_gate.py:cf8e3677e40981b5b70b88798318e252bacfbb9b1c72ecda9fe3191a1f01d3c8
  - desktop/tests/test_import_injection.py:bb39860e1dfa3276a648d38a7be3ec015279866a1407372f8c57c0a81a9fabc0
  - desktop/tests/test_gap_review.py:a66c19073a942e7e4d825ac759ffb9b2f8ecde7d981748f0290051cefb8a67fc
  - desktop/tests/test_explain_coverage.py:a64bc7bf7dacb57296b94d1babf8f2daa3aa51556d61676a603546804e4e3084
  - desktop/tests/test_doc_reachability.py:3fc87bd136fe15a375ff23da9ba3fb5c7a529ef5fd07bde1938adad696f06291
  - desktop/tests/test_dead_code.py:b511d344795c8d1f9c2ab6483f8c952ae0e85b3abc922bae943dd1f0eda3a687
  - desktop/tests/test_daemon_parity.py:10582b2d9f5d7f9f6b2cb2f7e6bccc43b8b0ba1226d5153627ad7ff13cf89acb
  - desktop/tests/test_concept_graph_gate.py:446dbfd023c9d5171578ac4e7741c099fc40dce77e2f3bf1944f243f1f29a7e0
  - desktop/tests/test_commit_msg.py:505be6ffbee18922dc31eee174baf8a962d35f5dca9c28ba29fba352b3262cf8
  - desktop/tests/test_cli_json_face.py:0af5d3e2955b01417dbbd242189f06f6ea4397614083df83c8cd87850c1b5c9d
  - desktop/tests/test_ccv3_adapter.py:38960758d0f9487b70e02963e3e79bfd0c1d30f1e6160944e3d5b65bdc584516
  - desktop/tests/test_ai_domain_closure.py:dc6a45d68ae576ae90a87700191ef5688aeb7db194139eff92317ecbc1140204
  - desktop/tests/test_terminal.py:6b5bfa40968209709789adfee5bc03d40432279a86207df91daf8f638e910e24
  - desktop/tests/test_nf_cli.py:f21e9ce45b104179274cc79eaefc5d9dd2cc9852ee3bf8757331bf7ba2d9771e

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；测试文件不在 `code_metrics` 棘轮面，未触发重冻。

## 一、结果

`python -m mypy desktop/tests --ignore-missing-imports` 错误条数 **66 → 0**。至此 **`desktop/src` + `scripts` + `desktop/tests` 全树 0 条**（默认口径）。

## 二、交付（按修法归类）

| 类 | 模块/修法 |
|---|---|
| `module_from_spec` 契约（最大块，约 21 条） | 10 个测试模块补 `assert spec is not None and spec.loader is not None`（typeshed 的 `spec_from_file_location` 返回可空）；含 test_terminal / test_nf_cli / test_commit_msg / test_layer_model 等 |
| 声明/集合显式类型（约 15 条） | `counts`/`found`/`params`/`args`/`_CACHE`/`_PRESET_STATE`/`_REPORT`/`KNOWN_EXTERNAL`/`NAMED_COUNTS`/`REVIEWED_UNREFERENCED` 等标注 |
| 类级夹具属性 | test_doc_reachability（`commands: set` / `tops: set` 类级声明）、test_daemon_parity（`doc: dict`）——mypy 不认 `setUpClass` 里的 `cls.x = ...` |
| 可空契约 | test_judgement_coverage（`schema: Optional[str]`）、test_intake_gate（`doc`/`index_text` Optional）、test_ccv3_adapter（`body` 拆原始值） |
| 跨平台/属性 | test_knowledge_sig（`os.sys`→`import sys`）、test_mcp_runtime（FakeIn 覆写只读 `buffer`，单点 `# type: ignore[misc]`） |
| **重名测试（真缺陷）** | `test_gap_review.ReviewLimitTest` 有两个同名 `test_limit_zero_means_all_rows`——**后者遮蔽前者，前者从未执行**；第二个按其实体改为 `test_limit_two_caps_rows`，两例自此都会跑 |

## 三、验收证据（本机实测）

- `mypy desktop/tests` 错误条数 **66 → 0**。
- `python scripts/code_metrics.py` → 通过（测试文件不在棘轮面）。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**（check12 会全量跑这些测试）。

## 四、遗留与设计偏差

1. 类型线至此覆盖全 Python 树；radon 复杂度面（≥C 319 / ≥D 99）仍未动。
2. `test_gap_review` 的重名是**既有真缺陷**（被遮蔽的用例从未跑），本件只更名、不删任何用例。
3. 62 §三·② 余量与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑↑ | 全树 mypy 0 条；verify 双绿；顺带恢复一条从未执行的重名用例 |
| 动态可执行 | ↑ | 被遮蔽用例恢复执行 |
| 架构纯度 | → | 只改测试内标注/断言/命名 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
