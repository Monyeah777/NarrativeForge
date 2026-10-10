# NFA-L 容器分发（零成本）

零第三方 Python 依赖：镜像只装 Python 标准库 + NF 引擎源码；仓库真源用卷挂载，
镜像本身不含内容，因此可离线、可复现。

## 构建

    docker build -f packaging/nfal/Dockerfile -t nfal .      # 上下文必须是仓库根（COPY 为根相对路径）

云端零成本构建：.github/workflows/docker-nfal.yml（push 改动 packaging/nfal 或 nfal 引擎件即 build + 冒烟，不推注册表）。

## 运行

    docker run --rm -v "$PWD":/repo nfal --root /repo build 03_管线库/P01_标准管线.md --no-tokens
    docker run --rm -v "$PWD":/repo nfal --root /repo check "WorldState.time.day >= 30"
    docker run --rm -v "$PWD":/repo nfal --root /repo eval 03_管线库/P01_标准管线.md --state state.json

真源缺 PyYAML 时，管线围栏回退到零依赖子集解析（见 core.nfal._fence_pipeline），
所以镜像无需 pip install 也能读管线。

## 零成本分发面

- 本机：上述 docker run 即用；
- 免费托管：可与既有 packaging/hf-space 同法上 HF Space 免费层，或推 Docker Hub 公开层；
- 模块入口：python -m core.nfal_cli（容器 ENTRYPOINT 即它）。
