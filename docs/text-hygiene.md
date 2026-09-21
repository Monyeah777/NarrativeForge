# 编码与标识面卫生（text-hygiene）
> 最后更新：2026-09-21

## 是什么

NF 的门禁长期只判**内容语义**，不判**承载编码**。`core/text_hygiene.py`（check33 新面）
把四类「看起来没事、机器侧会出事」的编码缺陷变成可拦判据：

| 规则 | 依据 | 会出什么事 |
|---|---|---|
| 文本件为 UTF-8、无 BOM | RFC 3629 | BOM 让 `json`/`yaml` 首键解析失败；摘要随编辑器变化 |
| 行尾 LF（`.gitattributes` 声明 `* text=auto eol=lf`） | 仓库 EOL 纪律 | 跨平台检出漂移 → 字节级读取的摘要两边不一致 |
| JSON 键唯一、无重复 | RFC 8259 §4 / RFC 7493 I-JSON | 后值覆盖前值，静默丢数据（不报错） |
| 标识面 NFC + 字符集（ASCII + CJK 汉字） | UAX #15 / UTS #39 | 全角字母、零宽字符、NBSP 让「看起来同名的两个键」不相等 |

## 判据

- 扫描 = 文件系统全仓走查（排除 `.git` / `.rivet` / 缓存 / 二进制哨兵），纯只读、纯 stdlib、确定性。
- 标识面白名单：ASCII 字母数字 + `_ - . : /` + 空格（说明性键）+ CJK 统一表意汉字
  （类内段 id `通用:M10` 是既有合法形态，故进白名单而非禁掉）+ `$`（JSON Schema 保留键前缀）。
- 违规 = FAIL，每条带修复指引；本门不产 WARN（要么合规要么违规）。

## 怎么用

```bash
cd desktop/src && python -m core.text_hygiene ../..
python scripts/nf.py doctor
```

## 边界

本门只判**编码与标识面**，不判内容质量、不判文风（文风见 `nf lint --prose`），
也不替作者做术语统一裁决——同形字判据只看「机器侧能否区分同一标识」。
