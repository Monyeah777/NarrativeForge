#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📚 NF 云端代收站 · Gitee 前端轮询入库（Y12′ 扩展 · 2026-09-07 · 零治理开放投稿）

背景：投稿的「写入口」此前只在 GitHub Issues——国内用户进不去 GitHub 就无法投稿。
本脚本把投稿入口搬到 Gitee Issues（国内可达），由 GitHub Actions 定时轮询拉取：
  投稿人（任何人，零治理）→ Gitee 开 Issue（标题【NF投稿】+ 粘贴全文）
  → 本脚本每 10 分钟醒来 → Gitee API 拉 open 投稿 → 同一入库核心（净化/空壳拒收/
    36进制编号/小写键查重/ALIAS 重建）→ git 提交推双端（origin + gitee）
  → Gitee Issue 回评双端链接 → 关闭 Issue（state=closed = 天然幂等，处理过的不再拉取）。

与 GitHub 前端（library_ingest.py）的差异：
  - 数据源 = Gitee API v5（不是 GitHub 事件推送的 env）
  - 零治理：不校验投稿人白名单（作者拍板「烂就烂，出事拉黑」）
  - 入库注记头标注「来源：Gitee Issue #N」（防重/可追溯）
  - 回评与关闭走 Gitee API；git push 双端（gitee 用 GITEE_TOKEN 子令牌）

本地调试：设 DRY_RUN=1 只改工作区不提交/不调 API/不推远端。
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import date
from glob import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 复用 GitHub 前端的纯函数（36进制 / 文件名解析 / 存量扫描 / ALIAS 重建）
from library_ingest import (to_b36, parse_nfname, scan_existing, rebuild_alias,
                            SEG_RE)

GITEE_OWNER = 'monyeah777'
GITEE_REPO = 'narrative-forge'
GH_REPO = os.environ.get('REPO', 'Monyeah777/NarrativeForge')
TOKEN = os.environ.get('GITEE_TOKEN', '')
DRY = os.environ.get('DRY_RUN', '') == '1'
MAX_SEG = 16

# 模板残留说明短语（与 GitHub 前端同一套——投稿人 = 蠢用户，机器兜底）
FILLER_PATS = ('如 校园情感世界', '作品名，同时', '可选，一句话', '可选，编号',
               '编号规则', '从这里开始粘贴', '两者都填', '填了就必须',
               '把 AI 产物全文整篇粘贴到这条线下面', '此占位行务必删掉')


def fail(msg):
    print('❌ ' + msg)
    sys.exit(1)


def clean_val(v):
    """模板残留净化：说明文字/括号示例一律视为未填。"""
    v = v.strip()
    if not v:
        return ''
    if v.startswith(('（', '(')):
        return ''
    for pat in FILLER_PATS:
        if v.startswith(pat):
            return ''
    return v


def gitee_api(path, params=None, method='GET'):
    """Gitee OpenAPI v5 调用（统一注入 access_token）。"""
    base = f'https://gitee.com/api/v5{path}'
    p = dict(params or {})
    p['access_token'] = TOKEN
    if method == 'GET':
        url = f"{base}?{urllib.parse.urlencode(p)}"
        req = urllib.request.Request(url, method='GET')
    else:
        req = urllib.request.Request(base, data=urllib.parse.urlencode(p).encode(),
                                     method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f'⚠ Gitee API HTTP {e.code}: {body}')
        if e.code == 401:
            fail('GITEE_TOKEN 无效或权限不足（需 issues 读写 + 仓库推送）')
        return None
    except Exception as e:
        print(f'⚠ Gitee API 异常: {e}')
        return None


def gitee_comment(number, text):
    """Gitee Issue 评论。"""
    if DRY:
        print(f'[DRY] Gitee 评论 #{number}')
        return
    gitee_api(f'/repos/{GITEE_OWNER}/{GITEE_REPO}/issues/{number}/comments',
              {'body': text}, method='POST')


def gitee_close(number):
    """Gitee Issue 关闭（state=closed → 下次轮询不再拉取 = 幂等）。"""
    if DRY:
        print(f'[DRY] Gitee 关闭 #{number}')
        return
    gitee_api(f'/repos/{GITEE_OWNER}/{GITEE_REPO}/issues/{number}',
              {'state': 'closed'}, method='PATCH')


def fetch_open_submissions():
    """拉取全部 open 投稿 Issue（标题【NF投稿】），按创建时间升序（旧稿先入 = 序号稳定）。"""
    issues = []
    page = 1
    while True:
        batch = gitee_api(
            f'/repos/{GITEE_OWNER}/{GITEE_REPO}/issues',
            {'state': 'open', 'sort': 'created', 'direction': 'asc',
             'page': page, 'per_page': 100})
        if batch is None:
            return issues
        if not batch:
            break
        issues += batch
        if len(batch) < 100:
            break
        page += 1
    return [i for i in issues if i.get('title', '').startswith('【NF投稿】')]


def already_processed(number):
    """幂等防重：注记头已含「来源：Gitee Issue #N」= 已入库过（上次成功入库但关闭失败的重试场景）。"""
    for f in glob('library/NF-*.md'):
        try:
            with open(f, encoding='utf-8') as fh:
                head = fh.read(300)
        except OSError:
            continue
        if f'来源：Gitee Issue #{number}' in head:
            return True
    return False


def git(*args):
    print('$ git', *args)
    if not DRY:
        subprocess.run(['git', *args], check=True)


def process(issue):
    """处理单条 Gitee 投稿 Issue（入库核心，与 GitHub 前端同规）。"""
    number = issue.get('number')
    title_raw = issue.get('title', '')
    body = issue.get('body', '') or ''
    author = (issue.get('user') or {}).get('login', 'unknown')
    print(f'── 处理 Gitee Issue #{number}（作者 {author}）')

    if already_processed(number):
        print(f'  ⏭ 已入库过（防重），仅尝试关闭')
        gitee_close(number)
        return

    if not body.strip():
        gitee_comment(number, '⚠️ Issue 正文为空——请按模板粘贴产物全文后再提交。')
        gitee_close(number)
        return

    def clean_val_(v):
        return clean_val(v)

    meta = {}
    body_main = body
    if '\n---' in body:
        head, _, rest = body.partition('\n---')
        body_main = rest.lstrip('\n')
        for line in head.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'^(.+?)\s*[:：]\s*(.*)$', line)
            if m:
                meta[m.group(1).strip()] = m.group(2).strip()
    else:
        m = re.match(r'^#\s+(.+)$', body, re.M)
        if m:
            meta['标题'] = m.group(1).strip()

    # 空壳检测：正文区残留模板占位行 = 没清理模板（Issue #1 实测翻车现场）
    if ('从这里开始粘贴产物全文' in body_main
            or '把 AI 产物全文整篇粘贴到这条线下面' in body_main
            or '此占位行务必删掉' in body_main):
        gitee_comment(number, '⚠️ 正文里还留着模板的占位提示行——请删掉它，并把 AI 产出的完整内容整篇粘贴进来，重新开题提交。')
        gitee_close(number)
        print('  ✋ 正文区空壳（残留模板占位行），已拒绝并关闭')
        return

    title = clean_val_(meta.get('标题', '')) or re.sub(r'^【NF投稿】\s*', '', title_raw).strip() or f'投稿 #{number}'
    topic = clean_val_(meta.get('形态/领域自述') or meta.get('形态') or '') or '未标注'
    one_line = clean_val_(meta.get('一句话') or '') or '（见文件）'
    seg1 = clean_val_(meta.get('档位词', ''))
    seg2 = clean_val_(meta.get('自定义段', ''))

    # 段位配对 + 字符/长度校验
    if bool(seg1) != bool(seg2):
        gitee_comment(number, '⚠️ 档位词与自定义段必须**都填或都不填**。请按模板规则重新开题。')
        gitee_close(number)
        print('  ✋ 段位不配对，已拒绝并关闭')
        return
    if seg1 and (not SEG_RE.match(seg1) or not SEG_RE.match(seg2)):
        gitee_comment(number, '⚠️ 档位词/自定义段仅允许字母数字、各 ≤16 字符、不含连字符。请修正后重新开题。')
        gitee_close(number)
        print('  ✋ 段位字符非法，已拒绝并关闭')
        return

    groups, _ = scan_existing()
    key = (seg1, seg2) if seg1 else None
    if key not in groups and seg1:
        # 新前缀：查大小写近似冲突（小写键全馆唯一）
        low_key = (seg1.lower(), seg2.lower())
        near = []
        for f in sorted(glob('library/NF-*.md')):
            p = parse_nfname(os.path.basename(f)[:-3])
            if p and p[0] is not None and (p[0].lower(), p[1].lower()) == low_key:
                near.append(os.path.basename(f)[:-3])
        if near:
            hint = '、'.join(near[:3])
            gitee_comment(number, f'⚠️ 档位段+自定义段与现有条目仅大小写不同（{hint}）——小写键全馆唯一，请更换拼写后重新开题。')
            gitee_close(number)
            print('  ✋ 前缀小写键撞车，已拒绝并关闭')
            return

    nums = groups.get(key, [])
    next_n = (max(nums) + 1) if nums else 1
    seq_s = to_b36(next_n)
    nfid = f'NF-{seg1}-{seg2}-{seq_s}' if seg1 else f'NF-{seq_s}'
    fname = f'library/{nfid}.md'
    today = date.today().isoformat()
    print(f'  编号分配: {nfid} → {fname}')

    # 写文件（含入库注记头，标注 Gitee 来源）
    header = (
        f'> 📚 **NF 云端图书馆条目 {nfid}** · 入库 {today} · 投稿人：{author} · 来源：Gitee Issue #{number}\n'
        f'> 形态/领域：{topic} · 一句话：{one_line}\n'
        f'> 本文为社区投稿副本，版权归投稿人；引用/衍生请注明来源；如需下架请联系作者。\n'
        f'> 自包含声明：本文件自带「是什么 + 怎么用」，AI 单文件即可正确使用。\n\n---\n\n'
    )
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(header + body_main.rstrip() + '\n')
    print(f'  已写入 {fname}（{len(body_main)} 字符）')

    # 更新 INDEX 登记表
    with open('library/INDEX.md', encoding='utf-8') as f:
        index = f.read()
    lines = index.split('\n')
    last_row = -1
    for i, ln in enumerate(lines):
        if re.match(r'^\|\s*NF-', ln):
            last_row = i
    new_row = f'| {nfid} | {title} | {topic} | {author} | {today} | {one_line} |'
    if last_row >= 0:
        lines.insert(last_row + 1, new_row)
    else:
        lines.append(new_row)
    with open('library/INDEX.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'  INDEX 已插入: {new_row}')

    # 重建 ALIAS（复用 GitHub 前端实现；REPO env 需已设置）
    rebuild_alias()

    # 提交推送双端 + 回评 + 关闭
    if DRY:
        print('  [DRY] 跳过提交/推送/回评/关闭（检查 git diff 后还原即可）')
        return
    git('config', 'user.name', 'NF Library Bot')
    git('config', 'user.email', 'nf-bot@users.noreply.github.com')
    git('add', fname, 'library/INDEX.md', 'library/ALIAS.md')
    git('commit', '-m', f'lib(Y12): Gitee 云端代收 {nfid} 自动入库（Gitee Issue #{number}，投稿人 {author}）')
    # Gitee push（子令牌注入 remote；避免令牌进 commit 相关输出仅本机可见）
    git('remote', 'set-url', 'gitee',
        f'https://{GITEE_OWNER}:{TOKEN}@gitee.com/{GITEE_OWNER}/{GITEE_REPO}.git')
    git('push', 'gitee', 'HEAD:main')
    git('remote', 'set-url', 'gitee',
        f'https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}.git')  # 用完即卸令牌
    git('push', 'origin', 'HEAD:main')

    form = ''
    reply = (
        f'✅ **云端代收成功——已入库 {nfid}**《{title}》\n\n'
        f'随时可用链接召回运行（说「运行 {nfid}」即可）：\n'
        f'- Gitee（国内直连）：`https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}/raw/main/library/{nfid}.md`\n'
        f'- GitHub：`https://raw.githubusercontent.com/{GH_REPO}/main/library/{nfid}.md`\n\n'
        f'> 💡 给任意 AI 的启动句：请读取上面的链接，按文档执行。\n'
        f'> 🔤 若 AI 报编号时大小写拿不准：让它读 `library/ALIAS.md` 转译（编号全小写化后匹配）。\n'
        f'> ⚠ 若内容不合规（非原创/未授权/缺自包含可运行性），联系作者下架。'
    )
    gitee_comment(number, reply)
    gitee_close(number)
    print(f'  ✅ 入库完成 {nfid}（Gitee Issue #{number} 已回评并关闭）')


def main():
    if not TOKEN:
        fail('缺少 GITEE_TOKEN 环境变量')
    print(f'🔍 轮询 Gitee（{GITEE_OWNER}/{GITEE_REPO}）开放投稿…')
    subs = fetch_open_submissions()
    print(f'  发现 {len(subs)} 条待处理投稿')
    for issue in subs:
        try:
            process(issue)
        except Exception as e:
            print(f'  ⚠ Issue #{issue.get("number")} 处理异常: {e}')
    print('✅ 本轮轮询结束')


if __name__ == '__main__':
    main()
