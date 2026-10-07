# リリース編成（release）
> ⛔ 操作指示：本ファイルはリリース方針の**人読投影**です。機読真源は `protocol/release_policy.json`（`protocol/schema/release.schema.json` で検証）、機検前置は check38 の `release_gate` 子スキャンです。読んだら実行してください。
> 最后更新：2026-10-05 (last updated)

## これが解決するもの

リリース作業は以前 4 か所に散っていました——`nf release`（事前健診）、`scripts/release_freeze.sh`（golden master スナップショット）、`scripts/bump_verify.sh`（版ラベル差替）、手作業チェックリスト。**順序**と**前置**は文章と記憶の中だけにありました。ここで同種の一流プロジェクトから二つの仕組みを取り込みました：**設定即契約**（方針を `protocol/release_policy.json` + JSON Schema に、release-please の `$schema` 方式に倣う）と**変更エントリ収集**（`changes/unreleased/*.md`、changesets に倣う）。

```bash
python scripts/nf.py release --plan          # 順序付き計画（コマンド / 産物 / 判定）
python scripts/nf.py release --plan --json   # 機読計画
python scripts/nf.py release                 # 事前健診（verify + 被覆率 + e2e + レポート鮮度）
python scripts/nf.py release --json          # 決定的な証跡摘要（読み取り専用）
python scripts/nf.py release --freeze --apply --by <承認者> --note "<波の説明>"
                                             # 凍結チェーンを順に実行（既定は dry-run）
```

## 凍結チェーン

順序は逆にできません（`decisions/ADR-0005-新增NET引擎线.md` と PO-0001 事故の教訓）：内容確定 → 一致性レポート再計算 → 内容バインド承認 → プロトコル層レシート再署名。

1. `python scripts/nf.py conformance --write`（`protocol/conformance_report.json` を生成、`conformant` 必須）
2. `nf approve protocol/conformance_report.json --by <承認者> --note <説明>`（内容バインド。対象が変われば即失効）
3. `python scripts/nf.py receipts --scope protocol --write`（プロトコル層レシート単根 + 派生面を更新）

レシートは**内容変更の後に最後**走らせます。そうでなければ単根が古いバイトを覆います。館蔵内容を変えた場合は `nf library receipts --write` も必要です。

## 版の三面

三か所の登録が宙に浮いてはいけません（再計算口径は `core/quality_baseline.py` と VERSION-MATRIX 自身の双方向検証）：

| 面 | 真源 | リリース時の操作 |
|---|---|---|
| `CHANGELOG.md` | 最新節 `## [X.Y.Z]` | 未公開 → 公開済みにし、PASS 基準を記録 |
| `docs/meta/VERSION-MATRIX.md` | 版 × 方案 × 能力の行 | 一行追加（版 / 日付状態 / 方案 / 能力） |
| `README.md` 版ブロック | 「現行」行 | 現行行を新版へ移す |

`bash verify.sh` が全量ゲートの単一入口です。`PASS` の期待値は宣言（`quality_baseline.EXPECTED_*`）であり、本文には書きません。

## Golden Master

```bash
bash scripts/release_freeze.sh vX.Y.Z
```

産物 = `.release-frozen/<tag>/sha256.manifest`（`01_核心协议.md` / `02_联动注册表.md` / `06_Agent执行协议.md` / `07_官方核心出厂与社区预设导航.md` / `verify.sh` + `desktop/src/core/*.py`）+ `sig-fingerprint.txt`（`nf sig --verify` 知識指紋）。スナップショットは**歴史的事実**で現状に追従しません。構造不完全（件類欠落 / 摘要が空）は `release_gate` 子スキャンが赤にします。

## 変更エントリ

変更を着地させるとき `changes/unreleased/` に一条書きます（`type:` + `note:`、語彙は `CONTRIBUTING §1` と同じ）。リリース時に `nf changelog` が版節を**生成**し（決定的・各項は条目か規約的コミットに遡及可能）、`--write` で CHANGELOG へ挿入して条目を `changes/<version>/` へ归档します：

```bash
python scripts/nf.py changelog --version X.Y.Z --date YYYY-MM-DD          # プレビュー（リリース PR の原生的等価物）
python scripts/nf.py changelog --version X.Y.Z --date YYYY-MM-DD --write  # 挿入 + 归档
```

規則と理由は `changes/README.md`。判据は check38 の `release_gate` 子スキャン。

## 境界（宣伝しない）

- 本機構は `verify.sh` を**代替しません**：ゲート緑は前提であり、品質の宣伝ではありません。
- 計画は**編成**であり証明ではありません：`--apply` は既存コマンドを順に呼ぶだけで、書き込み意味を追加しません。
- `git tag` は人が実行します（本機構はコマンドと判定だけを与える）——打標は不可逆で、自動実行面には入れません。
