# NarrativeForge · ドキュメント生成工房（仕様駆動）

<!-- nf:locales --> 语言 / Languages：[中文](README.md) · [English](README.en.md) · **日本語**

[![ゲート ci-verify](https://github.com/Monyeah777/NarrativeForge/actions/workflows/ci-verify.yml/badge.svg)](https://github.com/Monyeah777/NarrativeForge/actions/workflows/ci-verify.yml)

**NF ターミナル（TUI）** —— 全画面の人間向け入口（標準ライブラリのみ）。メニューと各アクションは `nf` CLI の実コマンドの制御された呼び出し元です。キー操作は一流ターミナルの慣例に従います（`Tab` でパネル切替、`↑↓` で移動、`/` で絞り込み、`?` でキー一覧）。詳細は [tui/README.md](tui/README.md) を参照。

> MIT License · オリジナルのオープンソース · 派生・引用の際は出典を明記してください

NF は**コンテンツ契約層（content contract layer）**です——「AI が長文コンテンツを安定して産出する」ためのプロトコル・品質ゲート・資産基準を定義します。プロトコル自体はドメイン中立・モデル非依存です。

**別名と検索語**：NF · NarrativeForge · 叙事工坊 · コンテンツ契約層（content contract layer）· 仕様駆動のコンテンツ工場 · 長文生成プロトコル · 組立型コンテンツ生産 · モジュール／パイプライン／資産 · 品質ゲート · ドメインパック · MCP 接続。

**そうではないもの**：モデルではなく、プロンプトテンプレート集でもなく、特定ベンダーの SDK でもありません——プロトコル本体はドメイン中立・モデル非依存で、MCP は接続可能なプロトコルの一つにすぎません。

`bash verify.sh`（現在の基準値は下部の生成領域「品質証憑」行を参照） · `python scripts/nf.py --version`

## ⚡ AI / エージェントの方へ

- これは何か：仕様駆動のドキュメント工場。モジュール／パイプライン／資産を搭載 → 検証 → 出力。
- 入口チェーン：`AGENT_START.md`（着手）→ `AI_ROUTING.md`（経路選択）→ `DEEP_DIVE.md`（深く理解する）。
- 機械証憑：`bash verify.sh`（現在の基準値は下部の生成領域「品質証憑」行。`nf stats --write` が書き込みます）。機械向け入口一覧は `llms.txt`、英語入口は `README.en.md`、日本語入口は本ファイル \`README.ja.md\`（機読事実の一致は `check34` が常時検証）。
- 設計意図を知る：[DEEP_DIVE.md](DEEP_DIVE.md) を参照。

## クイックスタート

作者・開発者向け（5 分）：

1. `bash verify.sh`
2. `python scripts/nf.py shell`（対話ターミナル。シェル退役後の人間向け入口。詳細は `docs/terminal.md`）
3. `python scripts/nf.py demo`
4. `python scripts/nf.py --help`
5. `python scripts/nf.py doctor`
6. `python scripts/nf.py completion bash`

AI による組立：

1. `AGENT_START.md` を読む
2. `agent_组装指令包_v0.2.md` を読む（`v0.2.md` は同一ファイル）
3. 必要に応じて 01/02/06/07 と `community/` のパッケージを取得
4. 「完全版」を組み立て、`##7` のセルフチェックを通す
5. `nf assemble "<要件>" --build --dest <ディレクトリ>`（組立コマンド：単一ファイルの「完全版」を直接生成）
6. `nf assemble "<要件>" --check <out.md>`

### よくある質問（FAQ）

- **NF とは？** コンテンツ契約層です。「AI が長文を安定して産出する」ことをプロトコル＋品質ゲート＋資産基準として定義し、産出物を搭載可能・検証可能・再現可能にします。
- **NF は MCP サーバーですか？** 必須ではありません。プロトコルと資産はすべてプレーンテキストで、clone または直リンクで搭載できます。`nf serve` が追加で MCP 接続面を提供します。
- **対応モデルは？** モデル非依存です。テキストを読める AI ならどれでもプロトコルに従って組立・搭載できます。特定モデルや特定接続プロトコルに縛られません。
- **ネット接続は必須？** 不要です。リポジトリ自体が markdown 原稿です。`bash verify.sh` はローカルのみで完結し、オフラインで実行できます。
- **産出物の合格判定は？** 判定は内部チェーンのみ：verify ゲート（静的に検証可能）＋五次元の縦深自己評価＋実戦例。外部評価は品質の裏付けとして用いません。
- **引用方法は？** MIT ライセンス。引用時は出典を明記してください。機読メタデータはリポジトリ直下の引用ファイル（`CITATION.cff`）にあります。

## 機能と資産

<!-- nf:stats:begin -->
**公式コア**：13 モジュール · 3 パイプライン（P00 / P01 / P90） · コアプロトコル 01–07
**コミュニティ規模**：111 登録パッケージ · 363 資産ファイル · 101 概念グラフ · 100 ドメインパック／1200 細分類 · 標準カタログ 370 件（到達可能 332 ／ 不可達 38 · 機関 194 · 206 依存辺） · 標準バインディング 1200 件
**品質証憑**：verify v2.30 · check1-40 · PASS=72（bash verify.sh の単一入口。期待基準は quality_baseline.EXPECTED_*） · 所蔵 3 件

分层：data 148 · eng 38 · form 29 · gov 71 · iface 84 （標準カタログ layer 別）

> 本区は python scripts/nf.py stats --write が生成します（手改禁止）。口径と実算真源は protocol/repo_stats.json。
<!-- nf:stats:end -->

## プロトコルチェーンと文書ナビ

| 層 | 入口 |
|---|---|
| 方向 | `STRATEGY.md` |
| プロトコル | `01_核心协议.md` · `02_联动注册表.md` · `06_Agent执行协议.md` · `07_官方核心出厂与社区预设导航.md` · `protocol/WORLD_MODEL.md` |
| ライブラリ | `03_管线库/` · `04_模块库/` · `05_资产库/` |
| コミュニティ | `community/README.md` · `community/模板制作指令包.md` |
| AI | `AGENT_START.md` · `AI_ROUTING.md` · `DEEP_DIVE.md` |
| ツール | `docs/mcp.md` · `docs/terminal.md` · `docs/layers.md` · `docs/release.md` · `scripts/nf.py` · `tui/nf.py` · `verify.sh` |
| 接続面 | `integrations/README.md`（MCP / LSP / CLI / TUI / 図書館 / Skill / npm / Rust / .NET / A2A） |
| 書庫 | `library/INDEX.md` · `ROUTES.md` |

## バージョンブロック

| バージョン | 状態 |
|---|---|
| v2.11.0 | 現行（2026-09-10）· world_model 決定的抽象状態契約 + world_slots |
| v2.10.0 | 公開済み 2026-09-09 · 45 品質縦深 + 基盤層 A 群の収口 |
| v2.9.0 | 公開済み 2026-09-08 · STRATEGY + 43/44 随波 |
| v2.8.0 | 公開済み 2026-09-08 · 41/42 波 C 品質収口 |

詳細なバージョン履歴は `CHANGELOG.md` と `VERSION-MATRIX.md` を参照してください。
