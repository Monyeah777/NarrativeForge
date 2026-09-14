# 机读块 retro-fit（L0 → L1/L2）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

把**没有机读契约**（L0）的模块补上 `machine_contract`——**只做投影，不编造**：

| 字段 | 来源 |
|---|---|
| `id` / `name` | 标题行 `# 模块 Mxx · 名称` |
| `category` / `layer` | 人读头 `类别：` / `挂载点：Pxx` |
| `inputs` | 人读头 `依赖：` 段内的 `Mxx` 令牌 |
| `events.publish/subscribe` | 人读头 **∪ 正文 yaml 事件契约**（取全集——只读头会漏订阅侧） |
| `outputs` / `interfaces` | 人读头未声明 → `[]`（不猜） |
| `conformance` | 按可证事实：在册 + 被管线引用 → `L2`；否则 `L1` |

## 怎么用

```bash
python scripts/nf.py module contract            # 覆盖报告（仍为 L0 的件数）
python scripts/nf.py module contract --write    # 补机读块（幂等）
python scripts/nf.py module outputs --write     # 有事件载荷证据的模块补 outputs
```

## 边界

- 补块会改变模块**边界签名** → 须 `nf module signature --write` 重冻结。
- 新事件若未登记进 `protocol/event_registry.json`，门禁会报缺口（如实登记为 `declared`）。
