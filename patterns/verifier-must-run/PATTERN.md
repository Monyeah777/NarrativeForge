---
id: verifier-must-run
name: 判据必须接线：没跑过的判据不算判据
status: active
scope:
  - 代码层
applies_to:
  - desktop/tests/*.py
  - verify.sh
  - .github/workflows/*.yml
rules:
  - 新套件/新入口必须**接线**才算出货：要么进 discover 面，要么登记「由谁跑」；两张表都只许缩小，登记了却已不存在的项即 FAIL
  - 「有哪些判据」这类面清单必须**多源取并**（文档 usage ∪ 二进制自述 ∪ 探针 ∪ 实现源码），且每个来源都要有「解析塌缩即红」的下限
  - 覆盖率元判据与接线表都要有**变异自证**：喂一个未登记项必须判红，否则这条元判据自己就是空转
evidence:
  - desktop/tests/test_suite_wiring.py
  - desktop/tests/test_npm_package.py
  - desktop/tests/test_rust_fastlane.py
  - .github/workflows/npm-publish.yml
---

## 为什么

「有判据」和「判据在跑」是两件事，而**缺失是静默的**：没人跑的套件不会报错、不会变红，它只是
永远不给出结论——直到发布当天。它比「判据写错」更难发现，因为仓库里那条命令看着好好的。

实测（2026-10-03）三次：① `packaging/npm/test/smoke.test.mjs` 只在发布工作流里跑，常驻门禁
从未执行过它；② 新加的 CLI 入口 `scripts/orchestrate.py` 一度只有自己能跑、没有任何判据；
③ 快线新增的 `pyval` / `density` / `score` / `schema-lint` / `schema-validate` 五个面**都能跑**，
却都不在 `--help` 的 usage 里——只看 usage 的面清单会做出一份「假全覆盖」。

## 怎么用

```bash
cd desktop && python -m unittest tests.test_suite_wiring -q   # 套件接线：要么 discover，要么登记执行方
cd desktop && python -m unittest tests.test_npm_package -q    # 交付线冒烟套件接进常驻面
cd desktop && python -m unittest tests.test_rust_fastlane -q  # 逐面 oracle + 面来源四取并
```

代码形态：`EXTERNAL_SUITES = {"<套件路径>": "<谁跑、怎么跑>"}` + 两个方向的断言（未登记即红、
登记已消失即红）；面清单则写成 `_documented_faces() | _self_declared_subfaces() | _probed_faces() | _source_faces()`
并配下限。

## 反例

把套件放进 `test/` 目录就以为「CI 会跑」——实际只有发布工作流引用它；或把面清单硬编码成
前 5 个面，后来新增的 5 个面长期无人对账，而元判据因为只列了旧的 5 个，永远报绿。

## 相关

- 与 `fail-closed-verification` 的区别：那条管「验证器**缺失**时不许降级成通过」；这条管
  「验证器**存在**却没被执行」——一个防放过坏东西，一个防没人检查。
- 与 `single-source-truth` 的关系：面清单本身也要单源（多源取并是为了**取全**，不是为了各留一份）。
