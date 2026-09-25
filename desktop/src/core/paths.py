"""仓库内路径包含性判据（`validate_path` 的唯一实现点）。

**为什么单独成模块**：`AGENTS.md` 与 `CONTRIBUTING.md` 都把「路径逃逸被 `validatePath`
拦截」写成既定事实，但仓库里**此前没有任何 `validatePath`**——唯一含逃逸判据的是
`asset_ledger` 内部的私有 `_safe_join`（只覆盖资产台账一个面）。文档承诺的控制没有真实
载体，等于给出**虚假保证**：照文档行事的 agent 会以为 `../../x` 一定被拦，从而省掉自己的
校验。本模块把该承诺落成可复用、可测的一等原语，并把资产台账的私有实现收敛到这里
（单一真相源）。

**作用边界（不得含糊）**：这里是**仓库内组件之间**的包含性判据——防的是「内容/参数里夹带
的路径把读写带出既定根目录」。进程级沙箱、工具调用越权拦截属宿主 harness 的职责，
NF 既不声称也无法在自身代码里实现工具级沙箱；文档须同样如实表述。

纪律：纯标准库；错误消息带修复指引（对齐 purity_scan R4）。
"""
from __future__ import annotations

import os
import tempfile


class PathEscapeError(ValueError):
    """路径逃逸既定根目录（修复指引：改用根内相对路径，去掉绝对路径与 `..` 段）。"""


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
    if ".." in text.replace("\\", "/").split("/"):
        raise PathEscapeError("路径不得含 `..` 段：%s（修复指引：改用根内相对路径）" % text)
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
