#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📚 NF 云端代收站 · 入库机器人 V2（Y12′ · 2026-09-07 · 编号 v0.4 制式）
由 .github/workflows/library-ingest.yml 调用（Issue 标题以【NF投稿】开头时触发）。

编号制式（v0.4 定稿，见 .rivet/plans/Y线自审与重制方案_草案_v0.4_2026-09-07.md）：
  完整形 NF-<档位段>-<自定义段>-<36进制序号>   例 NF-WORLDCAMPUS-Monyeah777-1
  默认形 NF-<36进制序号>（不填档位/自定义）      例 NF-1
  36进制：每位字符集 0-9 + A-Z（数字排完上字母），从 1 起、无前导零、不定长、低位满进位；
          同前缀（档位段+自定义段相同，默认形自成一前缀组）各自计数。
硬约束：
  - 档位/自定义段各 ≤16 字符、仅 [A-Za-z0-9]、不含连字符；要填就都填，否则默认形
  - 前缀小写键全馆唯一（禁止仅大小写不同的前缀并存 → 转译无歧义）
  - 入馆唯一硬标准 = 自包含可召回（引用式不再收；机器不审内容，作者把关）
流程：白名单校验 → 解析元信息 → 分配编号 → 写文件 → 更新 INDEX → 重建 ALIAS → git 提交推送 → Issue 回评双端链接 → 关闭 Issue。
本地调试：设 DRY_RUN=1 只改工作区不提交/不调 API。
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

ALLOWED = {'monyeah777'}
GITEE_OWNER = 'monyeah777'
GITEE_REPO = 'narrative-forge'
B36 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
MAX_SEG = 16
SEG_RE = re.compile(r'^[A-Za-z0-9]{1,%d}$' % MAX_SEG)


def fail(msg):
    print('❌ ' + msg)
    sys.exit(1)


def to_b36(n):
    """十进制 → 36进制字符串（n>=1，无前导零）。"""
    if n <= 0:
        n = 1
    s = ''
    while n > 0:
        n, r = divmod(n, 36)
        s = B36[r] + s
    return s


def from_b36(s):
    return int(s, 36)


def parse_nfname(name):
    """解析文件名（去 .md）→ (档位段|None, 自定义段|None, 序号str)；不合法返回 None。"""
    m = re.match(r'^NF-([A-Za-z0-9]+)-([A-Za-z0-9]+)-([0-9A-Z]+)$', name)
    if m:
        return (m.group(1), m.group(2), m.group(3))
    m = re.match(r'^NF-([0-9A-Z]+)$', name)
    if m:
        return (None, None, m.group(1))
    return None


def scan_existing():
    """扫描 library/NF-*.md → {前缀key: [序号int,...]}。key：完整形=(档位,自定义)，默认形=None。"""
    groups = {}
    prefixes = set()
    for f in glob('library/NF-*.md'):
        base = os.path.basename(f)[:-3]
        p = parse_nfname(base)
        if p is None:
            print(f'⚠ 跳过无法解析的现有文件: {base}')
            continue
        seg1, seg2, seq = p
        key = (seg1, seg2) if seg1 is not None else None
        groups.setdefault(key, []).append(from_b36(seq))
        prefixes.add((seg1.lower(), seg2.lower()) if seg1 is not None else None)
    return groups, prefixes


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


def rebuild_alias():
    """全量重建 library/ALIAS.md（大小写转译表）。从文件系统扫描，保证与实况一致。"""
    rows = []
    for f in sorted(glob('library/NF-*.md')):
        base = os.path.basename(f)[:-3]
        p = parse_nfname(base)
        if p is None:
            continue
        rows.append((
            base.lower(),
            base,
            f'https://raw.githubusercontent.com/{REPO}/main/library/{base}.md'
        ))
    lines = [
        '# 📖 大小写转译表（ALIAS）· AI 专用',
        '',
        '> **用法**：拿不准编号大小写时 → 先把编号**全小写化** → 在「小写键」列匹配 → '
        '用「真实编号」列拼链接取件。',
        f'> 取件基底（GitHub）：`https://raw.githubusercontent.com/{REPO}/main/library/`'
        '（国内镜像 Gitee：`https://gitee.com/monyeah777/narrative-forge/raw/main/library/`，规则相同）。',
        '> 本表由云端代收站机器人自动维护（每次入库全量重建）；人工通道入库请同步补录。',
        '',
        '| 小写键 | 真实编号 | GitHub raw 链接 |',
        '|---|---|---|',
    ]
    for low, real, url in rows:
        lines.append(f'| {low} | {real} | {url} |')
    with open('library/ALIAS.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'ALIAS 已重建：{len(rows)} 条')


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
    def clean_val(v):
        """模板残留净化：说明文字/括号示例一律视为未填（投稿人 = 蠢用户，机器兜底）。"""
        v = v.strip()
        if not v:
            return ''
        if v.startswith(('（', '(')):
            return ''
        for pat in ('如 校园情感世界', '作品名，同时', '可选，一句话', '可选，编号',
                    '编号规则', '从这里开始粘贴', '两者都填', '填了就必须'):
            if v.startswith(pat):
                return ''
        return v

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
        m = re.match(r'^#\s+(.+)$', BODY, re.M)
        if m:
            meta['标题'] = m.group(1).strip()

    # 空壳检测：正文区残留模板占位提示行 = 没清理模板/没粘产物全文（Issue #1 实测翻车现场）
    if ('从这里开始粘贴产物全文' in body_main
            or '把 AI 产物全文整篇粘贴到这条线下面' in body_main
            or '此占位行务必删掉' in body_main):
        comment('⚠️ 正文里还留着模板的占位提示行「（从这里开始粘贴产物全文…）」——请删掉它，并把 AI 产出的完整内容整篇粘贴进来，重新开题提交。')
        close_issue()
        print('正文区空壳（残留模板占位行），已拒绝并关闭')
        sys.exit(0)

    raw_title = clean_val(meta.get('标题', ''))
    title = raw_title or re.sub(r'^【NF投稿】\s*', '', TITLE).strip() or f'投稿 #{N}'
    topic = clean_val(meta.get('形态/领域自述') or meta.get('形态') or '') or '未标注'
    one_line = clean_val(meta.get('一句话') or '') or '（见文件）'
    seg1 = clean_val(meta.get('档位词', ''))
    seg2 = clean_val(meta.get('自定义段', ''))

    # ---- 3. 校验档位/自定义段 + 分配编号 ----
    if bool(seg1) != bool(seg2):
        comment('⚠️ 档位词与自定义段必须**都填或都不填**（两者都填 = 完整形 `NF-档位词-自定义段-序号`；都不填 = 默认形 `NF-序号`）。请按模板规则重新开题。')
        close_issue()
        print('段位不配对，已拒绝并关闭')
        sys.exit(0)
    if seg1:
        if not SEG_RE.match(seg1) or not SEG_RE.match(seg2):
            comment('⚠️ 档位词/自定义段仅允许字母数字、各 ≤16 字符、不含连字符（连字符是段分隔符）。请修正后重新开题。')
            close_issue()
            print('段位字符非法，已拒绝并关闭')
            sys.exit(0)

    groups, _ = scan_existing()
    key = (seg1, seg2) if seg1 else None
    if key not in groups and seg1:
        # 新前缀：查大小写近似冲突（前缀小写键全馆唯一，禁止仅大小写不同并存）
        low_key = (seg1.lower(), seg2.lower())
        near = []
        for f in sorted(glob('library/NF-*.md')):
            p = parse_nfname(os.path.basename(f)[:-3])
            if p and p[0] is not None and (p[0].lower(), p[1].lower()) == low_key:
                near.append(os.path.basename(f)[:-3])
        if near:
            hint = '、'.join(near[:3])
            comment(f'⚠️ 档位段+自定义段与现有条目仅大小写不同（{hint}）——为保转译表无歧义，前缀小写键必须全馆唯一。请更换档位词/自定义段拼写后重新开题。')
            close_issue()
            print('前缀小写键撞车，已拒绝并关闭')
            sys.exit(0)

    nums = groups.get(key, [])
    next_n = (max(nums) + 1) if nums else 1
    seq = to_b36(next_n)
    nfid = f'NF-{seg1}-{seg2}-{seq}' if seg1 else f'NF-{seq}'
    fname = f'library/{nfid}.md'
    today = date.today().isoformat()
    print(f'编号分配: {nfid}（前缀 {key}，第 {next_n} 件，36进制序号 {seq}）→ {fname}')

    # ---- 4. 写入产物文件（含入库注记头）----
    header = (
        f'> 📚 **NF 云端图书馆条目 {nfid}** · 入库 {today} · 投稿人：{AUTHOR} · 来源：Issue #{N}\n'
        f'> 形态/领域：{topic} · 一句话：{one_line}\n'
        f'> 本文为社区投稿副本，版权归投稿人；引用/衍生请注明来源；如需下架请联系作者。\n'
        f'> 自包含声明：本文件自带「是什么 + 怎么用」，AI 单文件即可正确使用。\n\n---\n\n'
    )
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(header + body_main.rstrip() + '\n')
    print(f'已写入 {fname}（{len(body_main)} 字符）')

    # ---- 5. 更新 INDEX 登记表（最后一个数据行后插入）----
    with open('library/INDEX.md', encoding='utf-8') as f:
        index = f.read()
    lines = index.split('\n')
    last_row = -1
    for i, ln in enumerate(lines):
        if re.match(r'^\|\s*NF-', ln):
            last_row = i
    new_row = f'| {nfid} | {title} | {topic} | {AUTHOR} | {today} | {one_line} |'
    if last_row >= 0:
        lines.insert(last_row + 1, new_row)
    else:
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

    # ---- 6. 重建 ALIAS（全量）----
    rebuild_alias()

    # ---- 7. 提交推送 ----
    if DRY:
        print('[DRY] 跳过提交/推送/回评（检查 git diff 后还原即可）')
        return
    git('config', 'user.name', 'NF Library Bot')
    git('config', 'user.email', 'nf-bot@users.noreply.github.com')
    git('add', fname, 'library/INDEX.md', 'library/ALIAS.md')
    git('commit', '-m', f'lib(Y12): 云端代收 {nfid} 自动入库（Issue #{N}，投稿人 {AUTHOR}）')
    git('push', 'origin', 'HEAD:main')

    # ---- 8. 回评 + 关闭 ----
    form = f'`NF-{seg1}-{seg2}-…`（档位+自定义完整形）' if seg1 else '默认形 `NF-…`'
    reply = (
        f'✅ **云端代收成功——已入库 {nfid}**《{title}》\n\n'
        f'随时可用链接召回运行（说「运行 {nfid}」即可）：\n'
        f'- GitHub：`https://raw.githubusercontent.com/{REPO}/main/library/{nfid}.md`\n'
        f'- 国内镜像（Gitee · 无需梯子）：`https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}/raw/main/library/{nfid}.md`\n\n'
        f'> 💡 给任意 AI 的启动句：请读取上面的链接，按文档执行。\n'
        f'> 🔤 若 AI 报编号时大小写拿不准：让它读 `library/ALIAS.md` 转译（编号全小写化后匹配）。\n'
        f'> ⚠ 若内容不合规（非原创/未授权/缺自包含可运行性），联系作者下架。'
    )
    comment(reply)
    close_issue()
    print(f'✅ 入库完成 {nfid}（Issue #{N} 已回评并关闭）')


if __name__ == '__main__':
    main()