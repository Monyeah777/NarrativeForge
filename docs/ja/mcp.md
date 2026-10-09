# NinFenz MCP 接続（`nf serve` · 40 総綱 v2.7 波A S1-E3 / X2）
> 最后更新：2026-09-30 (last updated)

> **状態**：公開化文書は基礎層 v2.7 とともに着地済み。**E3 プロトコル級ロード実測は 2026-09-08 に通過**（stdio JSON-RPC フレーム列の直測で五方法すべて緑、文末の記録を参照。P06 パイプラインの缺口二つ——閉じ ``` の欠落 / techdoc 宣言の欠落——を修復）。41 波C C7（2026-09-08）で読み取り専用 tools/prompts を開放（本機 stdio スモーク通過、docs/41_波C_C7_实测记录.md を参照）。**宿主型クライアント（Claude Desktop などの GUI ロード）は依然ユーザ側での追記を推奨**——README の MCP 宣言は現状維持（S13 ゲートは docs_external-validation-v2.7.md の規則に従い開放）、追記後に「正式化」を補う。

## これは何か

NF は MCP（Model Context Protocol）stdio サービス `nf serve` を提供します：

- 「MCP スナップショット」（`nf run --fmt mcp` が出力する `.json`）を JSON-RPC stdio セッション（改行区切り UTF-8 メッセージ）へ焼き込みます；
- **読み取り専用面**：`resources/list` + `resources/read`；41 波C C7（2026-09-08 裁決）で**読み取り専用 tools/prompts** を開放——`tools/list`+`tools/call`（library_search / registry_query / pipeline_ls / spec_ls）と `prompts/list`+`prompts/get`（assemble_guide ロードガイド）；書き込み経路のツールは実装せず、未知のツール/メソッドは拒否；
- **uri 許可リスト**：`resources/read` はスナップショットに登録済みの uri のみ受理し、未知の uri は `-32602 INVALID_PARAMS` を返します（ディレクトリ構造を漏らしません）；
- **プロトコル版 = dual-era**：modern `2026-07-28`（各リクエストの `_meta` が版を運び、交渉ハンドシェイクなし）+ legacy `2025-11-25`（`initialize` ハンドシェイク）が併存；未対応の版には `-32022` を返し、対応集合を列挙。版宣言に使う鍵は**規範鍵名** `_meta["io.modelcontextprotocol/protocolVersion"]`；別の鍵名（素の `protocolVersion` など）は**版宣言と見なさず**、サーバは legacy として扱い `-32022` を返しません（実測 2026-10-01）。歴史的対照は 33 号 A5 核查報告（G1/G2/G4 は消し込み済み）、現代口径の実証は規範 §Versioning / §Discovery を参照。

安全定位（C2 最小安全層）：読み取り専用 + 許可リスト——リポジトリ/コンテンツ庫の能力を agent の検索向けに**読み取り専用で露出**するのに適し、構造的に書き込み面を持ちません。

**入站資源ゲート**：1 メッセージの上限は **8 MiB**（超過時は `-32600` を返し**行末まで破棄**、セッションは中断しない）——
クライアントが改行を送らなくても流れ全体をサーバメモリへ流し込むことはできません；行の整列は崩れず、後続のメッセージは通常どおり処理されます。

## 三ステップ導入

### 1. スナップショット生成（**任意面**）

**既定の導入ではこの手順は不要**——`nf serve` は既定でリアルタイムリポジトリ面となり、第 2 步へ直接進みます。「ある回のアセンブリの
成果面」を固定したいときだけ、全链 CLI で `--fmt mcp` スナップショットを出力します（品質ゲートが PASS したときのみ産出。意味は verify 鉄則と同じ）：

```bash
python scripts/nf.py run \
  --pipeline community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md \
  --modules 技术文档类:M90,技术文档类:M97,技术文档类:M98,通用类:M00,通用类:M80 \
  --store <store 目录> --fmt mcp --dest <输出目录>
```

**題材鉄則**：MCP 出口はプロトコル/規則類（techdoc）のアセンブリのみを受け付けます——パイプラインは `Pipeline.structure.type` で `techdoc` を宣言する必要があり（P06 が範例）、叙事類のパイプライン（P04 軽混など）は一律拒否（誠実マッピング裁決、0 ファイル + warnings）。

**モジュールロードの説明**：`--seed` は公式核心（04_模块库 13 件、M90 を含む）+ キャンパス西洋ファンタジー軽混バンドルのみをロードし、**社区ドメインパック同梱のモジュールは覆いません**（M97/M98 は `community/技术文档域包/modules/` にあります）。P06 の全アセンブリには下のスクリプトで先に store をロードする必要があります；`--seed` は公式核心の組み合わせのデモ/自己テストにのみ適します（対応して `--store` を `--seed` に置き換えるだけ）。

```bash
python3 - <<'PY'
import sys, glob
sys.path.insert(0, 'desktop/src')
from core.storage import Store
from core.parser import parse_module
store = Store(home='<store 目录>')          # 真实装配目录
for f in sorted(glob.glob('04_模块库/*/*.md')):
    store.save_module(parse_module(open(f, encoding='utf-8').read()))
for f in sorted(glob.glob('community/技术文档域包/modules/*.md')):
    store.save_module(parse_module(open(f, encoding='utf-8').read()))
print(f'装载 {len(store.list_modules())} 模块 → {store.home}')
PY
```

### 2. サーバ起動

```bash
python scripts/nf.py serve                 # 默认路径：实时仓库面（无需快照，推荐 agent 密集调用）
python scripts/nf.py serve <快照 .json 路径>  # 或烧快照面（须先 `nf run --fmt mcp` 产快照）
```

stdio サービスは呼び出しプロセスのライフサイクルに沿って動作します（`Ctrl+C` で終了）。`nf run --fmt mcp` の産物を export_schema で検証することもできます（check19/22 が産物 shape を覆います）。

### 3. クライアント接続（標準 MCP クライアント）

MCP stdio をサポートする任意のクライアントで、`nf.py serve` を一つの server として宣言します（例は汎用 `mcpServers` 設定、Claude Desktop 系クライアントも同型）：

```json
{
  "mcpServers": {
    "ninfenz": {
      "command": "python",
      "args": ["<仓库绝对路径>/scripts/nf.py", "serve"]
    }
  }
}
```

（スナップショット面：`args` の末尾に `<快照 .json 绝对路径>` を補います。）

接続後、agent は次を呼べます：`resources/list` で資源を列挙 → `resources/read` で uri ごとに本文を取得——リアルタイムリポジトリ面は `nf://repo/...`（モジュール / 資産 / パイプライン / 館蔵 / パターン）を返し、スナップショット面はその回のアセンブリが登録した資源を返します。具体的な uri 集合は実際の `resources/list` の戻り値に従います。
41 波C C7 以降、agent は読み取り専用の検索ツールも呼べます：`pipeline_ls`（パイプライン一覧）/ `spec_ls`（プロトコルパック一覧）/ `registry_query`（モジュール+プロトコル検索）/ `library_search`（リポジトリ側知識ベース検索）、およびロードガイド prompt `assemble_guide`。44 以降はさらに**コンテンツチャネルツール**を開放：`module_read`（モジュール本文）/ `pipeline_read`（パイプライン本文）/ `asset_get`（資産本文）——「メタデータ検索」から「実質コンテンツの取得」へ格上げ（MCP resource/content 二段式を機制借用として実証適配、依然すべて読み取り専用）。データ源 = リポジトリの読み取り専用スキャン（03/04/community/docs/registry.json）、すべて読み取り専用、書き込み面なし。

## 能力表（mcp_runtime 実装と一対一対応）

| メソッド | 実装 | 説明 |
|---|---|---|
| `server/discover` | ✅ | modern 必須：`supportedVersions` / `capabilities` / `_meta.serverInfo` + `instructions`/`ttlMs` を一度に返す |
| `initialize` | ✅ | legacy ハンドシェイク：要求版が対応なら反響し、そうでなければ `2025-11-25` へフォールバック；`serverInfo` は自己記述（スナップショットファイルの最上位ではない） |
| `notifications/initialized` | ✅ 静黙 | 通知は id を持たず、応答しません |
| `ping` | ✅ | `{}` を返す |
| `resources/list` | ✅ | スナップショット登録資源の純メタデータ（text フィールドなし） |
| `resources/templates/list` | ✅ | RFC 6570 レベル1サブセットの資源テンプレート（library / pattern / module / pipeline / asset の5本）、実資源 uri の全被覆は check33 が断言 |
| `resources/read` | ✅ | 許可リスト uri → `contents[].text`；未知 uri → `-32602` |
| `tools/list` / `tools/call`（読み取り専用 · 検索面） | ✅ | 41 波C C7：library_search / registry_query / pipeline_ls / spec_ls（inputSchema は実在、すべて読み取り専用） |
| `tools/list` / `tools/call`（読み取り専用 · コンテンツチャネル） | ✅ | 44：module_read / pipeline_read / asset_get——モジュール/パイプライン/資産の本文実質内容を返す（メタデータだけではない） |
| `tools/list` のツール注釈 | ✅ | 10 ツールすべてが `annotations.readOnlyHint: true` を宣言（2026-10-08 以降）——「読み取り専用」は散文だけでなく、MCP クライアントが読み取り専用呼び出しを**自動許可**できます |
| `prompts/list` / `prompts/get` | ✅ | 41 波C C7：assemble_guide ロードガイドテンプレート（読み取り専用） |
| 書き込み経路ツール（未実装） | ❌ | 未知ツール → `-32602`；未知メソッド → `-32601`（読み取り専用安全層が構造的に書き込みを拒否） |

標準エラーコード：`-32700` 解析エラー / `-32600` 不正リクエスト / `-32601` メソッド不存在 / `-32602` パラメータ不正 / `-32603` 内部エラー；版交渉エラー `-32022`（`data.supported` / `data.requested`）。

## E3 実測記録（2026-09-08 · プロトコル級ロード実測通過）

| 日付 | クライアント | 結果（成功/失敗/差距） | 差距と修復 |
|---|---|---|---|
| 2026-09-08 | プロトコル級 stdio クライアント（MCP `2025-11-25` の JSON-RPC フレームで `nf serve` を直測、GUI 宿主ではない） | ✅ **五方法すべて緑**：`initialize`（プロトコル 2025-11-25 + serverInfo P06-mcp v0.1.0）→ `notifications/initialized` 静黙 → `ping` `{}` → `resources/list`（5 資源：M00/M97/M98/M80/M90）→ `resources/read`（`nf://P06/P40/术语管理-M97` の本文を完全に返却）→ `tools/list` `-32601 METHOD_NOT_FOUND` → 未知 uri `-32602` | P06 パイプラインの缺口 2 か所を修復：① ファイル末尾に閉じ ```` ``` ```` が欠落（56 行截断、パイプライン解析は静黙に None）；② `Pipeline.structure.type` に `techdoc` 宣言が欠落（既定 linear → IR.type=narrative → MCP 出口が拒否）。修復後は PASS 0/WARN 1/FAIL 0 で 5 資源スナップショットを産出し、実測通過。**追記待ち**：Claude Desktop 系 GUI 宿主のロード（ユーザ側で任意の追記） |

> 追記の原則：実ロード/呼び出しの結果であり、捏造しない。上の表は**プロトコル級の実セッション記録**（標準クライアントのフレーム列をプロセスへ直結して模擬）。GUI 宿主の追記後、これに基づき README 宣言を項目ごとに正式化し（S13）、fixture をテストライブラリへ沈殿させます（X1）。

## 関連

- 実装：`desktop/src/core/mcp_runtime.py`（ランタイム）/ `mcp_adapter.py`（エクスポート）/ `export_schema.py`（shape 検証）
- 核查基线：`results/audit/docs_audit-58-pending-items.md`（外部核験記録：MCP のキャッシュ可能な結果における鍵欠落の発見と修復）
- 出品材料（対外名称 / 一言 / カテゴリ / インストールと提出文案）：本文「出品材料」節（真源 = `protocol/mcp_package.json`）
- CLI 入口：`scripts/nf.py`（`run --fmt mcp` / `serve`）

## フレーム規律と構造制約（2026-09-21 増補、外部標準の吸収）

stdio transport の**実行可能な判定**（従来はコメントのみ、現在は check33 入り）：

1. **1 メッセージ 1 行** —— `encode_message()` はコンパクトな区切りでシリアライズし、メッセージ内に裸の改行を出してはなりません；
2. **行境界トラップのエスケープ** —— `U+2028` 行区切り / `U+2029` 段落区切り / `U+0085` NEL は、Unicode 改行
   境界で行を読むクライアントにとって改行と同義です（JSON 規範は裸の記述を許容）→ 出口では一律 `\uXXXX` にエスケープ；
3. **通知は応答行を書かない** —— `id` のないメッセージは処理後すぐ静黙（`encode_message(None) is None`）；
4. **JSON-RPC 2.0 §4 / §5** —— `params` が在场する場合 MUST 構造化（原始型 → `-32600`；
   配列 → `-32602`、本ランタイムは名前付き引数のみ受理）、`id` MUST 文字列/数値/null、
   **id が判定可能ならエラー応答は MUST 反響**（判定不能のときのみ `null`）。

自己テスト：`desktop/tests/test_mcp_runtime.py`（フレーム規律 3 例 + 構造制約 4 例）；
ゲート：`verify.sh` check33 の第 11/13 面。

**資源テンプレート面**（RFC 6570 の第一級サブセット）：`resources/templates/list` の 5 テンプレート（library /
pattern / module / pipeline / asset）は次を満たすこと——`{var}` の単純展開のみ（`{+id}` 演算子、
`{x*}` 爆発、接頭辞修飾は不可）、変数名は一意、波括弧は釣合い、クエリ文字列なし；さらに**すべての実資源 uri が
いずれかのテンプレートで覆われる**こと（テンプレート⇄読み取り面の一致、「列挙できるが取得できない」を防止）。実測：5 テンプレートすべて合法、
**実資源 uri の未覆いゼロ**（数はリポジトリの成長に従い、**ハードコードしない**：判定は
`desktop/tests/test_mcp_runtime.py::test_template_matches_real_uris`）；負例（演算子/重複名/疑問符/
空変数/不釣合い）は種類ごとに阻止可能。

**パラメータ准入（メソッド級）**：引数を持つ各メソッドは自身が宣言した鍵のみを認め、未宣言の鍵（`_` 接頭辞のプロトコル予約名を除く）
は一律 `-32602` + 修復指引——`resources/read` → `uri`、`prompts/get` → `name`（加えてプロトコル自带の任意 `arguments`：**出現は許すが空オブジェクトでなければならない**、多くのクライアントが常に付けてくる；非空なら「このテンプレートは引数を取らない」と明示）、`initialize` →
`protocolVersion` / `capabilities` / `clientInfo`（後二者はさらにオブジェクトであること）、`server/discover` → なし
（予約名のみ）。`resources/list` にはさらに二つの値域判定：`cursor` は非負整数文字列（前頁の
`nextCursor` をそのまま渡す）、`type` は語彙内（`module` / `pipeline` / `asset` / `library` / `pattern`）；`package` フィルタは**リスト項目の `package` フィールドの原値**（例：`三维与世界模型域包`、すなわち中文名そのもの）を使い、uri 内のパーセント符号化部分では**ない**——符号化形式を渡すと空表になります（実測 2026-10-01）。
以前は不正な `cursor` が静黙に 0 とされ、不正な `type` が静黙に空表を返し、未知の鍵が静黙に無視されていました（クライアントは
フィルタが効いたと誤認）——いずれも「正常に見える」誤答です。

## 出品材料（B 線パッケージ · 対外提出用）

> 真源 = `protocol/mcp_package.json`（機読）。本節はその**人読投影**：変更はまず真源を直し、次に
> `desktop/tests/test_mcp_packaging.py` が両所の逐項一致を断言します（漂移は FAIL）。

### 一、対外標識

| フィールド | 値 |
|---|---|
| 名称（Name） | `NinFenz Content Gate` |
| 一言（One-liner） | あらゆる AI agent に検証可能なコンテンツ規範と資産基盤を——まず契約を引き、それから筆を執る。 |
| カテゴリ（Category） | `content-creation` |
| 転送（Transport） | `stdio`（dual-era：modern `2026-07-28` + legacy `2025-11-25`） |
| 入口（Entry） | `python scripts/nf.py serve`（**既定 = リアルタイムリポジトリ面、スナップショット不要**）｜スナップショット面（任意）：`python scripts/nf.py run --fmt mcp` → `python scripts/nf.py serve <快照 .json>` |

### 二、インストール（三ステップ、コピペ可）

```bash
# ① 起服务（默认路径：实时仓库面，**不需要先产快照**）
python scripts/nf.py serve

# ② 可选：烧一份快照面（techdoc 装配才出 MCP；叙事类一律拒出 = 诚实映射）
python scripts/nf.py run \
  --pipeline community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md \
  --modules 技术文档类:M90,技术文档类:M97,技术文档类:M98,通用类:M00,通用类:M80 \
  --store <store 目录> --fmt mcp --dest <输出目录>
python scripts/nf.py serve <输出目录>/mcp.json

# ③ 客户端声明（标准 MCP stdio 客户端同构）
```

```json
{
  "mcpServers": {
    "ninfenz": {
      "command": "python",
      "args": ["<仓库绝对路径>/scripts/nf.py", "serve"]
    }
  }
}
```

> スナップショット面：`args` の末尾に `<输出目录>/mcp.json` を補うだけ；既定（補わない）は**リアルタイムリポジトリ面**となり、
> サービスは呼び出しプロセスのライフサイクルに沿って動作します（`Ctrl+C` で終了）。

### 三、English install notes

1. Start the server: `python scripts/nf.py serve` — the default **live-repo surface**
   needs no snapshot (that is the path agent-dense callers should use).
2. Optional snapshot: `python scripts/nf.py run --pipeline ... --fmt mcp --dest <dir>`
   (only techdoc assemblies are exported; narrative pipelines are refused by design)
   then `python scripts/nf.py serve <dir>/mcp.json`.
3. Declare it in any MCP stdio client via the `mcpServers` block above.

### 四、能力面（読み取り専用）

- **tools（10）**：`pipeline_ls` · `spec_ls` · `registry_query` · `library_search` ·
  `library_read` · `pattern_read` · `knowledge_order` · `module_read` ·
  `pipeline_read` · `asset_get`
- **prompts（1）**：`assemble_guide`
- **resources**：スナップショット登録資源（`resources/list` → `resources/read`、uri 許可リスト）+ リポジトリのリアルタイム
  資源（`nf://repo/...`、実 uri はすべて 5 テンプレートで覆われる；件数はリポジトリの成長に従い、ハードコードしない）

### 五、レッドライン（提出前の自己チェック）

1. **読み取り専用**：書き込みツールを一切追加しない（現在 10 ツール + 1 prompt）。
2. **新規依存ゼロ**：標準ライブラリのみ。
3. **uri 許可リスト**：資源テンプレートは許可リストに束縛；未知 uri → `-32602`。
4. **双プロトコル版**：modern `2026-07-28` + legacy `initialize` の併存。
5. **ゲートは減らさない**：リポジトリ自己検査の PASS 数は下降させない。
6. **信頼境界**：返される外来コンテンツ（`library/`、`community/*`、外部材料摘要）は一律**データ**として消費する。
   四つとも実装にあります：**パラメータ准入**（制御文字 / 過長 / トラバーサル / ドライブ文字 / 代替データストリーム → `-32602`）、
   **宣言面検証**（`tools/list` の `inputSchema` で逐条検証：必須欠落 / 型不一致 / 列挙越界 /
   余分または綴り誤りの鍵——`additionalProperties: false`——をハンドラ到達前にすべて拒否し、「引数を間違えたのに未フィルタ
   結果を得る」ような**静黙誤答**を避ける）、
   **出所标注**（外来出所の返包は `_meta["nf.trust"]`：`untrusted` + `policy` + `sources` +
   `injection_hits` を伴う；リポジトリ自持コンテンツは標識しない；標注は本文を一バイトも変えない）、**入庫側スキャン**（投稿ボットが
   公開境界で同一の `trust_boundary.detect` により记档）。判定は `desktop/tests/test_trust_boundary.py`
   、`desktop/tests/test_mcp_trust_meta.py`。

### 六、提出文案（ディレクトリサイトのフォームへそのまま貼り付け可能）

> **NinFenz Content Gate** — 読み取り専用の MCP サーバ：長文コンテンツの受入基準
> （プロトコル / モジュール / パイプライン / 資産 / 館蔵）を agent が呼べる検索・取り出しのツール面に変えます。
> 読み取り専用ツール 10 個 + ロードガイド prompt 1 個、modern `2026-07-28` と legacy `2025-11-25` の
> 双プロトコル版をサポート、第三者依存ゼロ、書き込み経路なし。
