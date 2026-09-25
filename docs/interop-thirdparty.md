# 互操作性 · 他证通道（第三方可自跑）

> 本页由 `python scripts/interop_thirdparty_kit.py --emit` 生成，禁止手改。
> 定位：这些卡片是给**第三方**跑的，不冒充「本仓已他证」。回填表：`results/interop-thirdparty-status.md`。

## 两种证据，别混（分层）

- **上游判据校验（已有）**：`scripts/check_interop_schemas.py --fetch` 用上游官方 meta-schema 校导出面 → `results/interop-schema-validation.md`。
- **他证（本页）**：对端消费或官方验证器由第三方在其环境跑，结果回填状态表。未回填 = 未他证。

## 回填纪律

1. 六字段齐备才算一条他证：`tool_version` · `run_by` · `run_at` · `output_sha256` · `verdict` · `note`。
2. `output_sha256` 必须是被跑对象或输出的 sha256（不可用「看起来通过」代替）。
3. 标 `not-applicable` 的面**不计入他证通过数**，只说明为何不适用。

## 他证卡

### `mcp` · MCP 运行时（server/discover · tools/list）

- 种类：`peer-consumption`
- 对端：任意 MCP 客户端（Claude Desktop / mcp-inspector 等）
- 安装：对端自选；服务端：`python scripts/nf.py run --fmt mcp --dest out` 产出 mcp.json 快照
- 命令（原样）：`python scripts/nf.py serve out/mcp.json  然后由对端客户端调用 server/discover / tools/list / resources/list / prompts/list`
- 期望：对端能完成初始化并取到 4 类列表；应答通过官方 MCP 2026-07-28 schema
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `ccv3` · CCV3 角色卡（SillyTavern 侧消费）

- 种类：`peer-consumption`
- 对端：SillyTavern（或任何 CCV3 实现）
- 安装：对端自装；样本卡见 docs/external-validation-assets/
- 命令（原样）：`在对端导入样本卡 → 启动 → 记录是否可读、是否报错、首回合输出`
- 期望：导入不报错且角色卡字段被正确识别（spec=chara_card_v3 / spec_version=3.0）
- 相关产物：`docs/external-validation-assets/`
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `openapi` · OpenAPI 3.1 导出面

- 种类：`official-cli`
- 对端：openapi-spec-validator（官方生态校验器）
- 安装：pip install openapi-spec-validator
- 命令（原样）：`python -m openapi_spec_validator results/interop/openapi.json`
- 期望：退出码 0（无 ValidationError）
- 相关产物：`results/interop/openapi.json`
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `asyncapi` · AsyncAPI 3.0 导出面

- 种类：`official-cli`
- 对端：@asyncapi/cli（官方 CLI）
- 安装：npm i -g @asyncapi/cli
- 命令（原样）：`asyncapi validate results/interop/asyncapi.json`
- 期望：退出码 0，输出 “is valid”
- 相关产物：`results/interop/asyncapi.json`
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `sbom` · SPDX 3.x SBOM 导出面

- 种类：`official-cli`
- 对端：spdx-tools（SPDX 官方工具）
- 安装：pip install spdx-tools
- 命令（原样）：`pyspdxtools -i results/interop/sbom.json`
- 期望：退出码 0（解析通过）
- 相关产物：`results/interop/sbom.json`
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `cyclonedx` · CycloneDX 1.5 SBOM 导出面

- 种类：`official-cli`
- 对端：cyclonedx-cli（官方 CLI）
- 安装：下载 cyclonedx-cli 发行版（GitHub Releases）
- 命令（原样）：`cyclonedx validate --input-file results/interop/cyclonedx.json`
- 期望：BOM validated
- 相关产物：`results/interop/cyclonedx.json`
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `slsa` · SLSA v1.0 来源面（形状）

- 种类：`shape-only`
- 对端：slsa-verifier / CUE 工具链（官方）
- 安装：go install github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@latest
- 命令（原样）：`slsa-verifier version  # 并对照官方 CUE/Protobuf 定义核对形状`
- 期望：工具可得；形状与官方定义一致（本面**只证形状，不证构建来源**）
- 相关产物：`results/interop/slsa.json`
- 为何如此判定：SLSA v1.0 官方以 CUE / Protobuf 定义机器可读协议，不发布 JSON Schema；NF 导出面是契约形状而非真实构建证明，故本面判据止于形状一致。
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `intoto` · in-toto Statement 面（形状）

- 种类：`shape-only`
- 对端：in-toto（官方实现）
- 安装：pip install in-toto
- 命令（原样）：`python -c "import in_toto, json; s=json.load(open('results/interop/intoto.json',encoding='utf-8')); assert {'_type','subject','predicateType'} <= set(s)"`
- 期望：断言通过（Statement 必备键在位）
- 相关产物：`results/interop/intoto.json`
- 为何如此判定：in-toto 官方以 Markdown 规范发布 Statement，不提供 JSON Schema 文件；本面判据为必备键形状 + 官方文本核对。
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `vc` · W3C VC 2.0 凭证面（形状）

- 种类：`shape-only`
- 对端：W3C VC 数据模型校验库 / JSON-LD 处理器
- 安装：pip install pyld
- 命令（原样）：`python -c "import json; d=json.load(open('results/interop/vc.json',encoding='utf-8')); assert {'@context','type','credentialSubject'} <= set(d)"`
- 期望：断言通过（凭证必备键在位）
- 相关产物：`results/interop/vc.json`
- 为何如此判定：VC 2.0 以规范文本 + JSON-LD 上下文发布，无官方 JSON Schema；本面判据为必备键形状 + 上下文可取。
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `prov` · W3C PROV-O 溯源面（形状）

- 种类：`shape-only`
- 对端：PROV 工具链 / JSON-LD 处理器
- 安装：pip install pyld
- 命令（原样）：`python -c "import json; d=json.load(open('results/interop/prov.json',encoding='utf-8')); assert d"`
- 期望：断言通过；JSON-LD 上下文可解析
- 相关产物：`results/interop/prov.json`
- 为何如此判定：PROV-O 以本体 + 规范文本发布（官方 prov.jsonld 本轮实测 300/不可取），本面判据为形状 + 上下文解析。
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `a2a` · A2A Agent Card 面

- 种类：`not-applicable`
- 对端：A2A 客户端（如官方 SDK）
- 安装：对端自装
- 命令（原样）：`（本仓不提供 A2A 端点，无法对端消费）`
- 期望：—
- 相关产物：`results/interop/a2a.json`
- 为何如此判定：本仓只导出 Agent Card 形状、不运行 A2A 端点，故无法做对端消费；改由官方 .proto/文本核对形状（不判本面通过）。
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `c2pa` · C2PA 内容凭证面

- 种类：`not-applicable`
- 对端：c2pa-rs（官方实现）
- 安装：对端自装
- 命令（原样）：`（本仓不做 CBOR/JUMBF 容器封装）`
- 期望：—
- 相关产物：`results/interop/c2pa.json`
- 为何如此判定：C2PA 以容器封装为真值载体；本仓只做清单形状，不做容器，故他证不适用（保留为形状面）。
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `cid` · CID 已知向量面

- 种类：`official-cli`
- 对端：multiformats 参照实现 / 已知向量复算
- 安装：无需安装（sha256 + base32 复算）
- 命令（原样）：`python scripts/interop_thirdparty_kit.py --dry-run   # 内含 CID 已知向量复算（sha256("")）`
- 期望：复算出的 CIDv1 与 results/interop/cid.json 记录一致
- 相关产物：`results/interop/cid.json`
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

### `decisions` · 决策面（NF 自有形状）

- 种类：`not-applicable`
- 对端：—
- 安装：—
- 命令（原样）：`—`
- 期望：—
- 相关产物：`results/interop/decisions.json`
- 为何如此判定：决策面是 NF 自有形状，无外部对端与外部 schema；判据落在 check33（覆盖一致 / 内部边界声明 / 确定性），不属他证范围。
- 回填：请在 `results/interop-thirdparty-status.md` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。

