# エディタ接続（LSP）
> 最后更新：2026-10-07 (last updated)

## これは何か

`nf lsp` は NF の LSP サーバーです（stdio、`Content-Length` フレーミング）：**診断 + ドメイン知能 + quickfix**。
診断は `nf lint` / `nf lint --prose` と同一の源から出ます。ドメイン記号表は `core/nf_language` から
供給されます（モジュール id / 資産キー / イベント名 / 層位 id / パイプライン id。すべて registry.json、
`machine_contract`、イベント登録表、ファイル面から派生し、第二の真源を作りません）。
**自らディスクへ書き込みません**——編集は `codeAction` を通じてのみクライアントへ渡します。

**受信リソース閘門**：1 メッセージ（ヘッダ行を含む）の上限は **8 MiB**。`Content-Length` が上限超過か負、
あるいはヘッダ行が改行されずに長すぎる場合は不正フレームと判定し、`-32700` を返して**サービスを継続**します
（MCP 面と同一の上限・同一の類の証拠）。

### 能力表

| 能力 | LSP メソッド | 説明 |
|---|---|---|
| 同期 | `initialize` → `textDocumentSync` | full-sync（openClose + save）。**増分同期はしない** |
| 診断 | `textDocument/publishDiagnostics` | 二つの源（`nf` 機械規則 / `nf-prose` 本文 lint）。各行・各列が実位置 |
| 修復 | `textDocument/codeAction` | `quickfix`：最小の行単位編集（再生検証に通らなければ全文置換へ後退） |
| 補完 | `textDocument/completion` | モジュール id / 資産キー / イベント名 / 層位 id / パイプライン id（前方一致補完） |
| ホバー | `textDocument/hover` | 記号メタデータ（モジュール名と掛載、イベントの発行者/購読者、資産の所属パッケージ……） |
| 定義ジャンプ | `textDocument/definition` | 参照 → 定義ファイル。**曖昧なら失敗クローズ**（推測しない。下の「境界」参照） |
| アウトライン | `textDocument/documentSymbol` | Markdown 見出し木（フェンスコードブロックは除外）。クライアント能力に応じ階層/平坦の二形態 |
| ワークスペース記号 | `workspace/symbol` | リポジトリ全域の記号検索（モジュール/資産/イベント/層位/パイプライン） |
| 折り畳み | `textDocument/foldingRange` | 見出しセクション（同レベル以上の次の見出しの直前まで）とコードフェンス。単一行の区間は返しません（クライアントが無視するため） |
| 参照 | `textDocument/references` | **登録済みの関係のみ**（イベント ↔ 発行/購読モジュール、モジュール ↔ マウント層、パイプライン ← 採用パッケージ）。各位置に why が付き、未登録なら空リスト——**全文検索はしません**（偽の参照を撒くため） |
| 位置エンコーディング | `positionEncoding` | `utf-16` 固定（LSP の既定口径。クライアントは必ず対応） |

## 三ステップ接続

第 1 步：設定を生成（**手写し不要**）——真源は同一のレンダラであり、下の三ブロックはその出力そのものです：

```bash
python scripts/nf.py lsp --print-config neovim     # emacs / helix も可
```

第 2 步：出力をエディタ設定へ貼り付けます（LSP クライアントは stdio。パスは**リポジトリの絶対パス**を指す）。
第 3 步：エディタを再起動し、リポジトリ内の任意の ``.md`` を開きます。

Neovim（`init.lua`）：

```lua
vim.lsp.start({
  name = "nf-lsp",
  cmd = { "python", "<リポジトリ絶対パス>/scripts/nf.py", "lsp" },
  root_dir = "<リポジトリ絶対パス>",
})
```

Emacs / eglot（`init.el`）：

```elisp
(with-eval-after-load 'eglot
  (add-to-list 'eglot-server-programs
               '(markdown-mode . ("python" "<リポジトリ絶対パス>/scripts/nf.py" "lsp"))))
```

Helix（`languages.toml`）：

```toml
[[language]]
name = "markdown"
language-servers = ["nf-lsp"]

[language-server.nf-lsp]
command = "python"
args = ["<リポジトリ絶対パス>/scripts/nf.py", "lsp"]
```

## 自己テスト（エディタ不要）

```bash
python -m unittest desktop.tests.test_lsp desktop.tests.test_lsp_hardening desktop.tests.test_nf_language -v
```

## 境界（正直な注記）

- **実エディタでのロード実測は未実施**（本機に VS Code / Neovim / Emacs / Helix がない）——プロトコル挙動は
  回帰テストと `check33` のエディタ面判据（能力宣言 / 診断位置 / didClose / 終了コード / ドメイン解決 /
  補完・ホバー・定義ジャンプ・アウトライン / 設定生成）で覆っています。エディタ側のロードは利用者に委ねます
  ——**本リポジトリは検証済みとは主張しません**。interop 他証チャネルの `lsp` 面は**未カード**です
  （追加には .NET 線 golden の同期が必要。前提は `results/audit/docs_audit-93-three-axis-adapters.md`）。
  それまで本文書は回填行を指しません。
- **VS Code 系の設定は生成しません**：その LSP クライアントは拡張宿主を必要とし、本リポジトリにはロード検証に
  使えるエディタがないため、未実測の拡張や設定を出しません（測っていない対応を主張しない）。組み込み LSP
  クライアントをもつエディタ（Neovim / Emacs / Helix）はそのまま接続できます。
- full-sync + 診断 + ドメイン知能 + quickfix + **構造化参照** + **折り畳み** のみ。増分同期・整形・意味的ハイライトはしません。
- **曖昧な識別子は定義ジャンプしない**：裸番号 `M10` は `通用:M10` と `生存:M10` の両方に属し、
  `P00` は層位と公式パイプラインの両方です。こうしたトークンはホバーで同名候補をすべて列挙し、
  定義ジャンプは失敗クローズ（どれか一つを選ばない）。
- **参照は全文検索ではありません**：`registry.json` に登録された関係だけが位置を返します。`P00` のような
  同名トークンでは層位とパイプライン両方の関係のヒットを（それぞれ why 付きで）並べ、一方を推測しません。
