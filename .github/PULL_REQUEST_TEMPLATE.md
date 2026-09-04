## 改动域（勾选）
- [ ] 协议层（01–07 / 08 / 09 方案）——是否触发 01 §7 V2 bump：是 / 否
- [ ] 代码层 desktop/src/core —— 是否已跑 `bash scripts/sync_android.sh`：是 / 否
- [ ] 代码层 desktop/（非 core）/ android / scripts
- [ ] 社区领域包 community/
- [ ] 工程治理（ROADMAP / CHANGELOG / CONTRIBUTING / .github / verify.sh）

## 门禁自检（提交前全过）
- [ ] `bash verify.sh` → PASS / WARN / FAIL
- [ ] `cd desktop && python3 -m unittest discover -s tests -q` → Ran N tests
- [ ] `python3 -m compileall -q desktop/src android/app scripts`
- [ ] 改 desktop/src/core 已跑 `bash scripts/sync_android.sh`（如适用）
- [ ] CHANGELOG [Unreleased] 已回填本次变更

## 变更摘要
（一句话 + 关键文件列表）

## 关联 Issue
Fixes # / Closes #
