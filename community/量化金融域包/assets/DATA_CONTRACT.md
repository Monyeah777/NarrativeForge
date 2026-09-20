<!-- nf-asset: key="DATA_CONTRACT" version="1.0" status="active" -->
# 数据与对象契约表 · 量化金融域

> 用途：本域包的第三件内容资产——把**数据字段与交易对象的口径**写成契约（字段名 / 类型 / 频率 / 时点 / 单位 / 缺失语义），供 量化金融:M31 / 量化金融:M32 校验与命名引用；也是「换数据源后回测结果变了」这类事故的事前解药。
> 资产键：`DATA_CONTRACT`｜正文自撰（域内通行字段口径的规范化表述），不含任何外部文本。

## 1. 契约纪律（五条）

1. **契约先行**：任何数据进入研究前，先登记字段契约（本节表内取值）；未登记字段不得进入因子或回测口径。
2. **字段即接口**：字段名一旦发布不改语义；语义变更 = 新字段名（或新版本），不得原地改写。
3. **时点必标**：每条数据须能回答「**何时可得**」（`available_ts`）——没有可得时点的数据不得用于回测。
4. **单位与货币显式**：金额类字段须标货币与单位（元 / 万元 / 手 / 股）；跨市场数据不得混用单位。
5. **缺失有语义**：缺失 ≠ 0；停牌 / 无成交 / 未披露 三类缺失须分别标（见 §5 陷阱）。

## 2. 行情契约（`QUOTE_*`）

| 键 | 字段 | 类型 | 频率 | 口径要求 |
|---|---|---|---|---|
| `QUOTE_SYMBOL` | 标的代码 | string | — | 含市场后缀（如 `.SH` / `.SZ`），全表唯一 |
| `QUOTE_TS` | 时间戳 | timestamp | 分钟 / 日 | 时区显式（本地 / UTC）；日频取收盘时点 |
| `QUOTE_OPEN` | 开盘价 | number | 同 `QUOTE_TS` | 复权口径须声明（见 `QUOTE_ADJ_FACTOR`） |
| `QUOTE_HIGH` | 最高价 | number | 同上 | — |
| `QUOTE_LOW` | 最低价 | number | 同上 | — |
| `QUOTE_CLOSE` | 收盘价 | number | 同上 | 回测成交价默认取**次日**开盘，见 `COST_FILL_PRICE` |
| `QUOTE_VOLUME` | 成交量 | number | 同上 | 单位显式（股 / 手） |
| `QUOTE_AMOUNT` | 成交额 | number | 同上 | 货币显式 |
| `QUOTE_ADJ_FACTOR` | 复权因子 | number | 同日 | 前复权 / 后复权 / 不复权三选一并全表一致 |
| `QUOTE_TRADABLE` | 可否交易 | boolean | 同日 | 停牌 / 一字板 / 退市整理期为 false |
| `QUOTE_AVAILABLE_TS` | 可得时点 | timestamp | 同日 | **须晚于** `QUOTE_TS` 的收盘可得时点（防前视） |

## 3. 标的与合约元数据（`INSTR_*`）

| 键 | 字段 | 说明 |
|---|---|---|
| `INSTR_TYPE` | 标的类型 | 股票 / ETF / 期货 / 期权 / 外汇 |
| `INSTR_EXCHANGE` | 交易所 | 用于交易日历与交易时段口径 |
| `INSTR_LIST_DATE` | 上市日 | 用于存活偏差口径（时点化标的池） |
| `INSTR_DELIST_DATE` | 退市日 | 同上；空 = 仍在市 |
| `INSTR_MULTIPLIER` | 合约乘数 | 期货 / 期权必填（影响容量与成本） |
| `INSTR_TICK_SIZE` | 最小变动价位 | 影响滑点与「一格」口径 |
| `INSTR_CURRENCY` | 计价货币 | 跨市场组合必填 |

## 4. 基本面与另类数据（`FUND_*` / `ALT_*`）

| 键 | 字段 | 说明 |
|---|---|---|
| `FUND_PERIOD` | 报告期 | 会计期间末（如 2025-12-31） |
| `FUND_ANNOUNCE_TS` | 公告时点 | 披露时间；**唯一可用于回测的时点** |
| `FUND_AVAILABLE_TS` | 可得时点 | 数据商回填时间，通常晚于公告时点 |
| `ALT_SOURCE` | 另类数据源标识 | 每个源须有可得性与覆盖期声明 |
| `ALT_AVAILABLE_TS` | 另类数据可得时点 | 同上（防止用未来信息） |

## 5. 账户与交易对象契约（`ACCT_*` / `ORDER_*` / `FILL_*`）

| 键 | 对象 / 字段 | 说明 |
|---|---|---|
| `ACCT_POSITION` | 持仓：`symbol` / `qty` / `avg_cost` / `available_qty` | `available_qty` 与 `qty` 的差 = 冻结口径 |
| `ACCT_CASH` | 资金：`total` / `available` / `frozen` | 冻结口径须声明（保证金 / 在途） |
| `ORDER_OBJ` | 委托：`order_id` / `side` / `type` / `price` / `qty` / `status` / `ts` | `status` 词表须封闭（未报 / 部成 / 全成 / 撤单 / 废单） |
| `FILL_OBJ` | 成交：`order_id` / `price` / `qty` / `fee` / `ts` | `fee` 构成须分项（佣金 / 税 / 过户） |
| `ACCT_RECON` | 对账口径 | 持仓 / 资金 / 委托三方对账时点与容差须声明 |

## 6. 数据源抽象与标准化（`PROVIDER_*`）

| 键 | 项 | 口径要求 |
|---|---|---|
| `PROVIDER_ID` | 数据源标识 | 一个源一个 id；同一字段多源时须声明**主源**与**备源** |
| `PROVIDER_MAP` | 字段映射表 | 源字段 → 本表标准字段；映射表须随源版本登记 |
| `PROVIDER_COVERAGE` | 覆盖期与频率 | 起止日期 + 频率；缺口须显式（不得静默补值） |
| `PROVIDER_MISSING` | 缺失语义 | 每个源声明其缺失表示法（空 / NaN / 0 / 哨兵值） |

## 7. 三个口径陷阱（回测必查）

| 陷阱 | 现象 | 契约层对策 |
|---|---|---|
| 复权不一致 | 同标的两种收益序列 | `QUOTE_ADJ_FACTOR` 全表一致 + 口径声明（§2） |
| 停牌与不可交易 | 以停牌价成交 → 回测虚高 | `QUOTE_TRADABLE=false` 不得参与成交（§2） |
| 退市与存活偏差 | 标的池只含活着的 | `INSTR_LIST_DATE` / `INSTR_DELIST_DATE` 时点化（§3） |

## 8. 词表引用关系

- `量化金融:M31`（因子与信号口径）：因子定义须引用本表的 `QUOTE_*` / `FUND_*` / `ALT_*` 字段键，不得自造字段名。
- `量化金融:M32`（回测与绩效口径）：成本与成交假设引用 `QUOTE_TRADABLE` / `INSTR_MULTIPLIER` / `INSTR_TICK_SIZE`；偏差口径检查引用 `QUOTE_AVAILABLE_TS` / `FUND_ANNOUNCE_TS` / `INSTR_DELIST_DATE`。
