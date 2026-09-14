---
id: error-message-guidance
name: 报错必须带修复指引
status: active
scope:
  - 代码层
  - 协议层
applies_to:
  - desktop/src/core
  - verify.sh
rules:
  - 每条 raise/异常消息必须写出「缺什么 · 补什么」（含具体路径/命令或可照做的下一步）
  - 门禁对缺失指引的 raise 判 FAIL，不做"提示性通过"
  - 修复指引里不得出现无法执行的占位（如「请自行检查」）
evidence:
  - check27
  - desktop/src/core/purity_scan.py
---

## 为什么

报错是**最后一次可执行的交互**。只说"失败了"会把定位成本全部推给读者；NF 的读者常常是 AI，
没有修复指引时它会**猜**——猜出的补丁比错误本身更贵。

## 怎么用

```python
raise ValueError("资产键未找到：%s（修复指引：nf asset ls / 包 assets/README.md 可枚举）" % key)
```

## 反例

```python
raise ValueError("invalid input")          # ✗ 无修复指引
raise ValueError("模块未找到，请检查")        # ✗ 指引不可执行
```

## 已有的实证

`purity_scan.py` 的 R4 规则在 check27 里常驻；本轮它还真拦下过一次我自己的提交（`取代者不能是自己`）。
