# S1 入口：Docker Space（零第三方 Python 依赖，与 NF「只用标准库」纪律一致）。
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    NF_AUTOSTART=0 \
    PORT=7860

WORKDIR /app
COPY nf/ /app/nf/
COPY server.py /app/server.py

EXPOSE 7860
CMD ["python", "server.py"]
