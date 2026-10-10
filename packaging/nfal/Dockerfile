# NFA-L 容器（零第三方 Python 依赖 —— 与 core 同纪律；镜像即分发单元）。
# 零成本分发：任意带 Docker 的机器 docker run 即用；无需 pip install、无需联网。
# 构建上下文 = **仓库根**（下面 COPY 是根相对路径）：
#   docker build -f packaging/nfal/Dockerfile -t nfal .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONPATH=/app/desktop/src

WORKDIR /app
COPY desktop/src /app/desktop/src

# 仓库真源（world_slots / event_registry / schema / 模块）按卷挂载，不进镜像：
#   docker run --rm -v "$PWD":/repo nfal --root /repo build 03_管线库/P01_标准管线.md
VOLUME ["/repo"]
WORKDIR /repo

ENTRYPOINT ["python", "-m", "core.nfal_cli"]
CMD ["--help"]
