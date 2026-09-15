# 断言表（assertions）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-15

## 是什么

把「能确定性判定的形状类断言」从 check 代码里搬到**数据**里：真源 `protocol/assertions.json`，
每条 = `id / severity / kind / params / message / fix`。机制借鉴 Schematron 的 patterns→rules→assertions
（ISO/IEC 19757-3）——**新增规则 = 加一行数据，不必改 check 代码**。

## 怎么用

```bash
python scripts/nf.py assertions            # 跑全表（fail 级不通过即 exit 1）
python scripts/nf.py assertions --json
python scripts/nf.py lint --kinds          # 四型写法判据（信息类型化的"定型"面）
```

## 判据（kind 为**封闭集**，不自造 DSL）

| kind | 用途 | 必填 params |
|---|---|---|
| `regex_absent` | 某类件里**不得**出现某模式（如绝对路径泄漏） | `globs`、`pattern` |
| `regex_present` | 某件必须含若干锚点 | `path`、`patterns` |
| `count_at_least` | 匹配件数下限（如 IDL 五定义在场） | `glob`、`min` |
| `json_value` | 读 JSON 键并判定（`exists` / `nonempty` / `equals` / `in_vocab` / `contains_keys`） | `path`、`key`、`op`、（`value`） |

表自身也过门：schema、severity/kind 词表必须与 runner 的封闭集逐项一致、id 唯一、
**每条必须有 `fix`**（没有修复指引的断言不许入表）。

## 边界

- 只搬「已在别处被判定过的形状类断言」，**不在本表里新增语义政策**；业务语义断言留在 check 代码里。
- 不引第三方依赖、不扩表达力：表达力扩张会让"零依赖 + 可读"同时失控。
