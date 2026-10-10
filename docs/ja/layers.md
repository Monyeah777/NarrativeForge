# NF 抽象階梯（layers）

> 最后更新：2026-09-26 (last updated)

> ⛔ 操作指示：本ファイルには直接実行できるコマンドと判定が含まれます。読んだら実行してください。資料として読まないでください。

## このファイルが解決するもの

NF にはもともと「層」の呼び方が四通りありました：**L0–L3**（依存ガバナンスの番号。`L3_FROZEN.md` 参照）、**P00–P80**（パイプライン階位）、
**mount_layers**（モジュールマウント層）、**標準ディレクトリ layer**（data/eng/form/gov/iface）。四つはそれぞれ意味を持ちますが、
「誰が動いているか」（端末、AI、外部ツール）と「加工される物」（プロトコル、資産）が以前は同じ梯子の上に混在していました——そのため
「端末が最下段、AI が最上段」のような、**役割**を**層**と取り違えるずれが生じました。端シェルの退役はこの混載の代償をすでに証明しています：ある役割
を一つの層として扱うと、層ごと退役したときに能力の置き場がなくなり、事後に判定を補って受け止めるしかありませんでした。

本階梯は両者を分離し、規則を**毎回のコミットで走る**判定に変えます（文書のスローガンではありません）：

- **抽象軸の四階**：契約 → 資産 → エンジン → 出口。下へ行くほど安定し、変更コストも高くなります。依存は下向きのみ。
- **入口面**：役割のみを登録します（人機 / AI アセンブリライン / MCP / 図書館取り出し）。**真源には決してなりません**。
- **検証縦断**：ゲートと証跡は四階を横断するため、これは「層」ではありません。

命名の規律：本階梯は「**階 / 面 / 縦断**」だけを使い、上の四つの語彙はいずれも再利用しません。

## 使い方

```bash
python scripts/nf.py layers            # 人読の階梯（インターフェース面と実装面の注記つき）
python scripts/nf.py layers --json     # 機読（階ごとの真源面 / インターフェース面 / 判定）
python scripts/nf.py layers --verify   # 階梯の健診を実行（verify check27 と同源。終了コードがゲートの意味を持つ）
python scripts/nf.py layers --write    # 本ファイルの生成区を再描画（真源を変更したら必ず実行）
```

何かを変える前に三つの問いを立ててください。答えは下の表に書かれています：

1. **それはどの階に属するか？**（真源面が決めます）
2. **他者はそのどの面に依存するか？**（階をまたぐ依存が許されるのはインターフェース面のみ。実装面は自由に変更可）
3. **この変更はどの区分か？**（editorial / additive / bump。語彙は `protocol/EXTENSION.md` と同じ）

## 階梯（生成区 · 真源 = `protocol/LAYERS.json`）

<!-- nf:layers:begin -->
### 抽象軸：四階

| 階 | 真源面 | インターフェース面（階をまたいで依存できる唯一の面） | 既存の判定 | 状態 / 変更区分 |
|---|---|---|---|---|
| **契約** | `01_核心协议.md`、`02_联动注册表.md`、`06_Agent执行协议.md`、`07_官方核心出厂与社区预设导航.md`、`STRATEGY.md`、`protocol/*.md`、`protocol/*.json`、`protocol/schema/*.json`、`desktop/src/core/registry.json`、`integrations/*/integration.json` | `protocol/schema/*.json`、`protocol/CONFORMANCE.md`、`desktop/src/core/registry.json` | check13、check28、check29、check30、check31 | active（bump） |
| **資産** | `03_管线库/*.md`、`04_模块库/*/*.md`、`05_资产库/**/*`、`community/**/*`、`library/*.md`、`patterns/*/PATTERN.md` | `community/*/protocol.yaml`、`05_资产库/provenance.json` | check7、check8、check9、check10、check11、check14、check15、check16、check23、check24、check34 | active（additive） |
| **エンジン** | `desktop/src/core/*.py`、`desktop/tests/**/*.py`、`desktop/scripts/*.py`、`scripts/*.py`、`scripts/*.sh`、`scripts/nf`、`scripts/nf.cmd` | `scripts/nf.py` | check12、check17、check18、check19、check20、check21、check22、check27、check32、check33 | active（additive） |
| **出口** | `results/interop/*.json`、`docs/standards/*.md`、`docs/fde-sample/**/*` | `results/interop/*.json`、`docs/standards/index.md` | check18、check19、check22、check33、check38 | active（editorial） |

### 資産階の五つの子階（同一セル内で異質。コストは別々に見る）

| 子階 | 真源面 | 既存の判定 | 口径 |
|---|---|---|---|
| **宣言** | `community/*/protocol.yaml` | check14 | 契約の実例：変更には登録三要件（01 §6.1 + 02 §8.3 + registry 投影）を経ること。 |
| **内容** | `03_管线库/*.md`、`04_模块库/*/*.md`、`community/*/modules/*.md`、`community/*/pipelines/*.md` | check7、check9、check24 | モジュールとパイプラインの本文：番号名前空間とマウント層に拘束されます。 |
| **データ** | `05_资产库/**/*`、`community/*/assets/*.md` | check8、check11、check23 | 資産キーと来歴台帳：判定は「アドレス可能 / 追跡可能 / 孤児キーなし」。 |
| **知識** | `protocol/knowledge_sources.json`、`protocol/transform_log.json` | check37 | 二重ソース知識層：判定は「権威の階層化 / クエリ順序 / 鮮度 / 消化の追跡可能性」（エントリ系資産とは別口径）。 |
| **オントロジー** | `protocol/standards_catalog.json`、`protocol/standards_binding.json`、`protocol/domain_packs.json` | check32 | 概念グラフと標準カタログ/バインディング：判定は「概念密度 / 標準到達性 / データの真実性」。 |

### 入口面（役割のみを登録し、真源にはならない）

| 面 | 入口件 | 提供先の階 | 口径 |
|---|---|---|---|
| **人機入口** | `scripts/nf`、`scripts/nf.cmd`、`scripts/nf.py` | engine | 引数なしで端末に入ります（nf shell → desktop/src/core/terminal.py）。その他の引数は CLI に透過します。 |
| **AI アセンブリライン** | `docs/agent/AGENT_START.md`、`docs/agent/agent_组装指令包_v0.2.md`、`docs/agent/AI_ROUTING.md` | asset | 任意の agent がリポジトリ URL だけで自助的に取り出し、「完全版」をアセンブルできます。A ライン（人機）と同格で、モデルを前提にしません。 |
| **MCP サービス面** | `docs/mcp.md`、`protocol/mcp_package.json` | engine | 常駐ランタイムの入口 = nf serve（エンジン階の CLI 面）。本面は契約と用法文書のみを登録します。 |
| **図書館取り出し面** | `docs/agent/ROUTES.md`、`library/INDEX.md`、`library/ALIAS.md` | asset | 番号によるアドレッシング + ミラールーティング。蔵書本体は資産階に属し、本面は「どう見つけるか」だけを担います。 |

### 検証縦断（四階を貫く。層ではない）

| 件 | 落点 | 既存の判定 |
|---|---|---|
| **verify** | `verify.sh` | check27 |
| **conformance** | `protocol/conformance_report.json` | check35 |
| **audit** | `results/audit` | check36 |
| **receipts** | `protocol/RECEIPTS.json` | check35 |
| **attest** | `docs/attest.md` | check33 |
| **provenance** | `05_资产库/provenance.json` | check23 |

> 本区は `nf layers --write` が描画します。手での変更は禁止。真源 = `protocol/LAYERS.json`。
<!-- nf:layers:end -->

## 五つの規律（判定は `desktop/src/core/layer_model.py` の L1–L10）

- **依存は下向きのみ**：契約はいかなる階にも依存しません。資産は契約のみに依存します。エンジンは契約と資産に依存します（読み取り専用）。出口はエンジンに依存します。
- **階をまたぐのはインターフェース面のみ**：`02 §8` の登録項目、`protocol.yaml`、資産の来歴台帳、CLI 命令面——これらが約束です；
  それ以外（モジュール本文、core 内部関数）は実装面に属し、自由に書き換えられます。
- **入口は真源ではない**：入口は差し替え可能です（端シェル → 端末もその一例）。いかなる階も入口件を真源としたり、逆方向に依存したりしてはなりません。
- **退役は一等市民**：ある階の退役は「能力の再配分 → 入口の補完 → 判定の改定 + 記録 + 作者による裁定」の三手順を必ず踏みます。
- **縦断は帰属に関与しない**：`results/audit/**`、`protocol/RECEIPTS.json` などの証跡と派生物は `derived` リストで免除され、
  暗黙の取り決めには頼りません。
