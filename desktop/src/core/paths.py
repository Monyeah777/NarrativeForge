"""仓库内路径包含性判据（`validate_path` 的唯一实现点）。

**为什么单独成模块**：`AGENTS.md` 与 `CONTRIBUTING.md` 都把「路径逃逸被 `validatePath`
拦截」写成既定事实，但仓库里**此前没有任何 `validatePath`**——唯一含逃逸判据的是
`asset_ledger` 内部的私有 `_safe_join`（只覆盖资产台账一个面）。文档承诺的控制没有真实
载体，等于给出**虚假保证**：照文档行事的 agent 会以为 `../../x` 一定被拦，从而省掉自己的
校验。本模块把该承诺落成可复用、可测的一等原语，并把资产台账的私有实现收敛到这里
（单一真相源）。

**与参数面同源**：词法判据（控制字符 / `..` 段 / 盘符写法 / 备用数据流）由本模块的
`path_syntax_issue` 单点定义，`core.trust_boundary` 的 MCP 参数面直接调它——避免「同一套
包含性判据」两处各写一份后宽窄分叉（2026-10-01 实测：备用数据流 `x.md:hidden` 与控制字符
`ok\x00bad` 此前**只有参数面拒、账本面放行**，且两套判据的对账样本集恰好没覆盖这两类）。

**作用边界（不得含糊）**：这里是**仓库内组件之间**的包含性判据——防的是「内容/参数里夹带
的路径把读写带出既定根目录」。进程级沙箱、工具调用越权拦截属宿主 harness 的职责，
NF 既不声称也无法在自身代码里实现工具级沙箱；文档须同样如实表述。

纪律：纯标准库；错误消息带修复指引（对齐 purity_scan R4）。
"""
from __future__ import annotations

import os
import re
import tempfile


class PathEscapeError(ValueError):
    """路径逃逸既定根目录（修复指引：改用根内相对路径，去掉绝对路径与 `..` 段）。"""


#: 盘符相对写法（`C:foo`）：Windows 独有的一种**不是绝对路径**的越界写法——
#: `ntpath.join("D:\\repo", "C:foo") == "C:foo"`，于是同一个值在 D 盘仓上会落到 C 盘进程
#: 当前目录、在 C 盘仓上又会「看起来没问题」（本机 cwd 恰在 C 盘 ⇒ 老判据放行）。
#: 口径：根内相对路径**不带盘符**，带盘符一律拒（与 `core.trust_boundary` 的参数面同源）。
_DRIVE_RELATIVE = re.compile(r"^[A-Za-z]:(?![\\/])")

#: 控制字符（\t \n \r 之外的 C0/C1 与 DEL）：文件名里出现即形状非法——Windows API 会静默
#: 截断到 NUL 之前、POSIX 直接 `ValueError: embedded null byte`，两种都不是「可核验的产出」。
_CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
#: `..` 段（两种分隔符都算）：唯一能把路径带出既定根目录的词法形态。
_TRAVERSAL = re.compile(r"(^|[\\/])\.\.([\\/]|$)")
#: NTFS 备用数据流（`文件.md:流`）：同名文件的**隐藏流**，可绕过按扩展名/文件名建的允许集。
_ADS = re.compile(r"\.[A-Za-z0-9]{1,8}:[^\\/\s]")
#: Windows 保留设备名（`CON`/`NUL`/`COM1`…，可带扩展名）：这些名字指向**设备**而非文件——
#: 以写模式打开 `…\NUL` 会「成功」但不落盘（静默丢数据），`CON` 甚至接控制台。跨平台统一拒
#: （与盘符/备用数据流同口径：同一字符串在任何平台不许有第二种落点语义）。
_RESERVED_DEVICE = re.compile(
    r"(?i)(^|[\\/])(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.[^\\/]*)?($|[\\/])")


def path_syntax_issue(text: str) -> str:
    """根内相对标识符的**词法判据**（单一出处）→ 问题描述；合规返回空串。

    与 `core.trust_boundary.relative_path_issue`（MCP 参数面 / 取件面）同源：后者改调本函数，
    `validate_path` 也调本函数。绝对路径写法由调用方各自判定——`validate_path` 认
    `os.path.isabs` + `allow_absolute`，参数面另把 `~` 也算绝对（取件面更严，见
    `test_trust_boundary` 的 `extra_strict` 登记）。
    """
    if _CONTROL.search(text):
        return "含控制字符"
    if _TRAVERSAL.search(text) or _DRIVE_RELATIVE.match(text):
        return "含越界路径写法（../ 段 / 绝对路径 / 盘符写法如 C:foo）"
    if _ADS.search(text):
        return "含备用数据流写法（`文件:流` 形态）"
    if _RESERVED_DEVICE.search(text):
        return "含 Windows 保留设备名写法（CON/NUL/COM1 等指向设备而非文件）"
    return ""


def contained(root: str, target: str) -> bool:
    """`target` 解析后是否落在 `root` 内（含 `root` 自身）。两端先 realpath 归一。"""
    r = os.path.realpath(str(root))
    t = target if os.path.isabs(str(target)) else os.path.join(r, str(target))
    t = os.path.realpath(t)
    return t == r or t.startswith(r + os.sep)


def validate_path(root: str, rel: str, *, allow_absolute: bool = False) -> str:
    """校验 `rel` 落在 `root` 内 → 返回根内绝对路径；否则抛 `PathEscapeError`。

    `allow_absolute=True` 只放行「绝对路径的写法」，**不放行**落到根外的目标——
    包含性判据在任何写法下一律成立。
    """
    text = str(rel or "")
    if not text.strip():
        raise PathEscapeError("路径为空（修复指引：给出根内相对路径，如 assets/A1.md）")
    if os.path.isabs(text) and not allow_absolute:
        raise PathEscapeError("不接受绝对路径：%s（修复指引：改用根内相对路径）" % text)
    issue = path_syntax_issue(text)
    if issue:
        raise PathEscapeError("%s：%s（修复指引：改用根内相对路径——勿用 `..` 段 / 盘符写法如 "
                              "C:foo / `文件:流` 备用数据流写法，并去掉不可见控制字符）"
                              % (issue, text))
    full = os.path.realpath(os.path.join(os.path.realpath(str(root)), text))
    if not contained(root, full):
        raise PathEscapeError("路径逃逸根目录：%s（修复指引：目标须落在 %s 内）"
                             % (text, root))
    return full


def guard_recursive_delete_target(raw: str, *, root: str, default: str,
                                  label: str = "目标") -> str:
    """校验「即将被**递归删除**的目录」落点 → 返回 realpath；灾难性落点一律拒绝。

    为什么单列一条判据：`shutil.rmtree` 类调用不可逆，而落点常常来自环境变量/参数
    （渗透实证 F-10：自检脚本把 `NF_TEST_HOME` 原样当递归删除目标，`=~`/`=<仓库根>`/`=/`
    即静默删除主目录/仓库/盘根）。**只拦灾难性落点，不拦正当用途**：拒绝指向文件系统根、
    用户主目录或其上级、`root` 或其上级、系统临时目录本身或其上级。

    `raw` 为空 → 返回 `default`（调用方给的专用目录）。
    """
    text = str(raw or "").strip()
    if not text:
        return default
    full = os.path.realpath(text)

    def covers(outer: str, inner: str) -> bool:
        """outer 是否等于 inner 或是它的上级目录（即删 outer 会波及 inner）。"""
        return inner == outer or inner.startswith(outer + os.sep)

    why = ""
    if os.path.dirname(full) == full:
        why = "文件系统根目录"
    elif covers(full, os.path.realpath(os.path.expanduser("~"))):
        why = "用户主目录或其上级目录"
    elif covers(full, os.path.realpath(str(root))):
        why = "仓库根目录或其上级目录"
    elif covers(full, os.path.realpath(tempfile.gettempdir())):
        why = "系统临时目录本身或其上级目录"
    if why:
        raise PathEscapeError(
            "拒绝把 %s=%s 当递归删除目标：它指向%s——该操作不可逆。"
            "（修复指引：指向专用临时目录，如 %s）" % (label, text, why, default))
    return full
