# NarrativeForge 快速开始

## 安装本 skill

外部用户可通过 Codex 的 skill 安装器从 GitHub 安装：

```bash
scripts/install-skill-from-github.py \
  --repo Monyeah777/NarrativeForge \
  --path skills/narrativeforge
```

也可以把 `skills/narrativeforge/` 目录复制到 `$CODEX_HOME/skills/`。

## 准备仓库

```bash
git clone https://github.com/Monyeah777/NarrativeForge.git
cd NarrativeForge
python scripts/nf.py --version
python scripts/nf.py doctor
```

需要完整验收门禁时，用支持 Bash 的终端执行：

```bash
bash verify.sh
```

## 最快跑通

```bash
python scripts/nf.py demo
python scripts/nf.py market --list
python scripts/nf.py asset ls
python scripts/nf.py module ls
python scripts/nf.py worldmodel --walk
```

## 不克隆仓库的 AI 装配路径

1. 读 `AGENT_START.md` 确认装配师角色。
2. 读 `agent_组装指令包_v0.2.md` 获取取货顺序、选件铁律、八段骨架、`##7` 自检。
3. 从仓库 raw 文件读取协议层 01/02/06/07 与 `community/*` 所需包。
4. 交付单文件完整版 `.md`，并明确来源与缺口。

如无法访问文件，不要假装抓取；向用户要缺失原文或如实标注缺口。
