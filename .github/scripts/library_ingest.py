#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📚 NF 云端代收站 · 入库机器人（Y12, 2026-09-07）
由 .github/workflows/library-ingest.yml 调用（Issue 标题以【NF投稿】开头时触发）。

流程：作者白名单校验 → 解析正文元信息（--- 之前）→ 分配下一编号
    → 写入 library/NF-XXXX.md（含入库注记头）→ 更新 library/INDEX.md 登记表
    → git 提交推送 main → Issue 回评双端链接 → 关闭 Issue。

本地调试：设 DRY_RUN=1 只改工作区不提交/不调 API（检查 git diff 后还原即可）。
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date
from glob import glob

REPO = os.environ.get('REPO', '')
TOKEN = os.environ.get('GITHUB_TOKEN', '')
N = os.environ.get('ISSUE_NUMBER', '')
TITLE = os.environ.get('ISSUE_TITLE', '')
BODY = os.environ.get('ISSUE_BODY', '') or ''
AUTHOR = os.environ.get('ISSUE_AUTHOR', '')
DRY = os.environ.get('DRY_RUN', '') == '1'

# 作者白名单（防公开仓库被滥用开题灌库）
ALLOWED = {'monyeah777'}
GITEE_OWNER = 'monyeah777'
GITEE_REPO = 'narrative-forge'  # Gitee URL 路径（展示名 NarrativeForge）


def fail(msg):
    print('❌ ' + msg)
    sys.exit(1)


def api(path, data=None, method=None):
    if DRY:
        print(f'[DRY] API {method or ("POST" if data else "GET")} /{path}')
        return {}
    req = urllib.request.Request(
        f'https://api.github.com/repos/{REPO}{path}',
        data=json.dumps(data).encode() if data is not None else None,
        method=method,
        headers={
            'Authorization': f'token {TOKEN}',
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'NF-Library-Bot',
        })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print(f'API HTTP {e.code}: {e.read().decode()[:300]}')
        sys.exit(1)
    except Exception as e:
        print(f'API 异常: {e}')
        sys.exit(1)


def comment(text):
    api(f'/issues/{N}/comments', {'body': text})


def close_issue():
    api(f'/issues/{N}', {'state': 'closed'}, method='PATCH')


def git(*args):
    print('$ git', *args)
    if not DRY:
        subprocess.run(['git', *args], check=True)


def main():
    # ---- 1. 前置校验 ----
    if not TITLE.startswith('【NF投稿】'):
        print('非投稿标题，跳过')
        sys.exit(0)
    if AUTHOR.lower() not in ALLOWED:
        comment('⏳ 收到投稿意图，但云端代收站当前仅接受作者本人投稿（公开仓库白名单防滥用）。如需投稿请联系作者。')
        print('非作者投稿，已礼貌拒绝')
        sys.exit(0)
    if not BODY.strip():
        comment('⚠️ Issue 正文为空——请按模板粘贴产物全文后再提交。')
        sys.exit(0)

    # ---- 2. 解析元信息（--- 之前为元信息区，之后为产物全文）----
    meta = {}
    body_main = BODY
    if '\n---' in BODY:
        head, _, rest = BODY.partition('\n---')
        body_main = rest.lstrip('\n')
        for line in head.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'^(.+?)\s*[:：]\s*(.*)$', line)
            if m:
                meta[m.group(1).strip()] = m.group(2).strip()
    else:
        # 无元信息区：尝试从正文首行标题推断
        m = re.match(r'^#\s+(.+)$', BODY, re.M)
        if m:
            meta['标题'] = m.group(1).strip()

    title = meta.get('标题') or re.sub(r'^【NF投稿】\s*', '', TITLE).strip() or f'投稿 #{N}'
    topic = meta.get('题材') or meta.get('题材标签') or '未标注'
    level = meta.get('档位') or '自包含（投稿未标注，按可单文件运行处理）'
    one_line = meta.get('一句话') or '（见文件）'

    # ---- 3. 分配编号 ----
    files = glob('library/NF-*.md')
    nums = []
    for f in files:
        m = re.search(r'NF-(\d+)\.md$', f)
        if m:
            nums.append(int(m.group(1)))
    next_id = (max(nums) + 1) if nums else 1
    nfid = f'NF-{next_id:04d}'
    fname = f'library/{nfid}.md'
    today = date.today().isoformat()
    print(f'编号分配: {nfid} → {fname}')

    # ---- 4. 写入产物文件（含入库注记头）----
    header = (
        f'> 📚 **NF 云端图书馆条目 {nfid}** · 入库 {today} · 投稿人：{AUTHOR} · '
        f'来源：Issue #{N} · 档位：{level}\n'
        f'> 本文为社区投稿副本，版权归投稿人；引用/衍生请注明来源；如需下架请联系作者。\n'
        f'> ⚠ 若本文为引用式（运行需仓库配套模块/资产），AI 请勿脑补缺失内容。\n\n---\n\n'
    )
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(header + body_main.rstrip() + '\n')
    print(f'已写入 {fname}（{len(body_main)} 字符）')

    # ---- 5. 更新 INDEX 登记表（最后一个表格数据行后插入）----
    with open('library/INDEX.md', encoding='utf-8') as f:
        index = f.read()
    lines = index.split('\n')
    last_row = -1
    for i, ln in enumerate(lines):
        # 匹配登记表数据行：| NF-0001 | 或 | **NF-0001** |（编号可能加粗）
        if re.match(r'^\|\s*\*{0,2}NF-\d+\*{0,2}\s*\|', ln):
            last_row = i
    new_row = f'| {nfid} | {title} | {topic} | {level} | {AUTHOR} | {today} | {one_line} |'
    if last_row >= 0:
        lines.insert(last_row + 1, new_row)
    else:
        # 兜底：登记表区（## 登记表 之后、下一个 ## 之前）末尾追加，避免丢失
        print('⚠ 未匹配到登记表数据行，尝试定位登记表区追加')
        sec_start = -1
        for i, ln in enumerate(lines):
            if ln.startswith('## 登记表'):
                sec_start = i
            elif sec_start >= 0 and ln.startswith('## '):
                break
        if sec_start >= 0:
            lines.insert(sec_start + 1, new_row)
        else:
            print('⚠ 未找到登记表区，INDEX 未插入（人工补录）')
            lines.append(new_row)
    with open('library/INDEX.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'INDEX 已插入: {new_row}')

    # ---- 6. 提交推送 ----
    if DRY:
        print('[DRY] 跳过提交/推送/回评（检查 git diff 后还原即可）')
        return
    git('config', 'user.name', 'NF Library Bot')
    git('config', 'user.email', 'nf-bot@users.noreply.github.com')
    git('add', fname, 'library/INDEX.md')
    git('commit', '-m', f'lib(Y12): 云端代收 {nfid} 自动入库（Issue #{N}，投稿人 {AUTHOR}）')
    git('push', 'origin', 'HEAD:main')

    # ---- 7. 回评 + 关闭 ----
    reply = (
        f'✅ **云端代收成功——已入库 {nfid}**《{title}》\n\n'
        f'随时可用链接召回运行（说「运行 {nfid}」即可）：\n'
        f'- GitHub：`https://raw.githubusercontent.com/{REPO}/main/library/{nfid}.md`\n'
        f'- 国内镜像（Gitee · 无需梯子）：`https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}/raw/main/library/{nfid}.md`\n\n'
        f'> 💡 给任意 AI 的启动句：请读取上面的链接，按文档执行。\n'
        f'> ⚠ 若内容不合规（非原创/未授权/缺可运行性），联系作者下架。'
    )
    comment(reply)
    close_issue()
    print(f'✅ 入库完成 {nfid}（Issue #{N} 已回评并关闭）')


if __name__ == '__main__':
    main()
