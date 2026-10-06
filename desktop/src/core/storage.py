"""存储层：~/.NinFenz 目录管理（config/modules/assets/presets/cache）。目录结构（指令集 3.2）：

~/.NinFenz/
├── config.json          # 工具配置（管线选择、激活资产包）
├── modules/<分类>/<id_名称>/module.json + source.md
├── assets/<包名>/asset.json
├── presets/<预设名>.json
└── cache/community_index.json

NF_HOME 默认 ~/.NinFenz，可用环境变量 NARRATIVE_FORGE_HOME 覆盖（测试友好）。
"""
from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import subprocess  # nosec B404 - 只问 `git check-ignore`（argv 列表、无 shell）
from pathlib import Path
from typing import List, Optional

from .models import Module, AssetPack, Preset, now_str, fid_key
from . import paths as nf_paths

#: 文件名主干上限（字符）：给「截断 + 摘要后缀」留出余量，稳稳落在各文件系统 255 字节上限内。
MAX_FILE_STEM = 120

ENV_HOME = "NARRATIVE_FORGE_HOME"


def default_home() -> Path:
    env = os.environ.get(ENV_HOME)
    if env:
        return Path(env).expanduser()
    return Path.home() / ".NinFenz"


class Store:
    """对 NF_HOME 下所有本地数据的管理器。"""

    def __init__(self, home: Optional[Path | str] = None):
        # 落点闸门（渗透 F-11）：NF_HOME 可由 `--store` 或 `NARRATIVE_FORGE_HOME` 指到任何地方，
        # 而本类会在其下建目录、还会在 remove_module 里递归删除 ⇒ 盘根/主目录/仓库根/临时目录本体
        # 一律拒绝（那几种落点不会有人真想要，却会把 `~/modules` 之类建到不该在的地方）。
        repo_root = str(Path(__file__).resolve().parents[3])
        self.home = Path(nf_paths.guard_recursive_delete_target(
            str(home) if home else str(default_home()),
            root=repo_root, default=str(default_home()),
            label="NF_HOME（--store / %s）" % ENV_HOME))
        # 形状闸门（2026-09-30）：落点已存在但是**文件** ⇒ 立刻给可读错误。
        # 此前会落到 `_ensure_dirs()` 的 `mkdir` 上抛 WinError 183/EEXIST，冒到 CLI 兜底报
        # 「内部错误」并回吐机器绝对路径（用户问题被当成内部故障）。
        if self.home.exists() and not self.home.is_dir():
            raise ValueError("NF_HOME 落点是文件而非目录：%s（修复指引：`--store` /"
                             " `NARRATIVE_FORGE_HOME` 要给目录路径；该文件若确实要当 store，"
                             "请改名或移走后重试）" % self.home)
        # 仓内落点闸门（2026-10-01 探针）：`--store` 落在**仓库内**且**不在 .gitignore 覆盖面**时
        # 拒绝——本类会建 modules / assets / presets / cache 四个目录，未忽略的仓内落点直接变成
        # `git status` 里的未跟踪垃圾（与 `trace.json` / `档案.md` 那类残留同一类），还可能被误提交。
        # 仓库自己的约定是 `.rivet/scratch/…` 这类**已忽略**路径（既有用例正落在那儿），故只拦这一种。
        _in_repo_issue = self._in_repo_unignored_issue(repo_root)
        if _in_repo_issue:
            raise ValueError(_in_repo_issue)
        self.config_path = self.home / "config.json"
        self.modules_root = self.home / "modules"
        self.assets_root = self.home / "assets"
        self.presets_root = self.home / "presets"
        self.cache_root = self.home / "cache"
        self._ensure_dirs()

    def _in_repo_unignored_issue(self, repo_root: str) -> str:
        """落点在仓库内且未被 git 忽略 → 问题描述（否则空串；无 git / 非仓内一律放行）。"""
        try:
            home = self.home.resolve()
            root = Path(repo_root).resolve()
        except OSError:
            return ""
        if not home.is_relative_to(root):
            return ""
        exe = shutil.which("git")          # 绝对路径（同 attest.py 口径：裸名走 PATH 有 cwd 劫持面）
        if not exe:
            return ""                      # 没有 git：不拦（闸门只做加法）
        try:
            probe = subprocess.run(  # nosec B603  # noqa: S603 - argv 列表、无 shell、子命令固定
                                   [exe, "-C", str(root), "check-ignore", "-q", str(home)],
                                   capture_output=True, timeout=15)
        except (OSError, subprocess.SubprocessError):
            return ""                      # 没有 git / 调用失败：不拦（闸门只做加法）
        if probe.returncode == 0:
            return ""                      # 已忽略：仓库自己的 `.rivet/scratch/…` 约定
        return ("--store 落在**仓库内**且未被 .gitignore 覆盖：%s（修复指引：NF_HOME 是**用户态**"
                "工作区，会建 modules/assets/presets/cache 四个目录——请指到仓库外（缺省 = "
                "~/.NinFenz），或落到已有的忽略面（如 .rivet/scratch/<名字>）；"
                "确实要在仓库内长期存放，请先把该路径写进 .gitignore）" % self.home)

    # ---------- 基础 ----------
    def _ensure_dirs(self):
        for d in (self.home, self.modules_root, self.assets_root,
                  self.presets_root, self.cache_root):
            d.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, s: str) -> str:
        """文件名安全化（**有界**）。

        依据（2026-10-01 敌意输入普查）：此前只做字符替换、**不限长**，于是
        `nf preset save <4096 个字符>` 会拼出超过文件系统上限的文件名 ⇒ `open` 抛
        `[Errno 2] No such file or directory: '<NF_HOME>/presets/AAAA…'`，冒到 CLI 兜底报
        「✗ 内部错误」**且回吐机器绝对路径**（用户输入问题被框成内部故障）。
        现在：**超长即截断 + 挂原文摘要后缀**——确定性（同一个名字永远同一个文件名，查/删仍命中），
        且不同长名不会撞成同一个文件；逻辑名不受影响（JSON 里仍存原名，CLI 也照原样回显）。
        """
        safe = re.sub(r"[^\w\u4e00-\u9fff-]", "_", s).strip("_") or "unnamed"
        if len(safe) <= MAX_FILE_STEM:
            return safe
        tag = hashlib.sha256(str(s).encode("utf-8")).hexdigest()[:8]
        return "%s-%s" % (safe[:MAX_FILE_STEM - 9], tag)

    # ---------- config ----------
    def load_config(self) -> dict:
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:  # nosec B110/B112 —— 尽力而为：跳过不可读/不可解析项；该类缺口由对应门禁与 AUD-0016 静默跳过清单另行报出
                pass
        return {"pipeline": "P01", "asset_pack": "", "recent": []}

    def save_config(self, cfg: dict):
        self.config_path.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_config(self, key: str, default=None):
        return self.load_config().get(key, default)

    def set_config(self, key: str, value):
        cfg = self.load_config()
        cfg[key] = value
        self.save_config(cfg)

    # ---------- 模块库 ----------
    def module_dirs(self) -> List[Path]:
        """返回所有已安装模块的目录（每个模块一个文件夹）"""
        out: List[Path] = []
        if not self.modules_root.exists():
            return out
        for cat in sorted(self.modules_root.iterdir()):
            if cat.is_dir():
                for md in sorted(cat.iterdir()):
                    if md.is_dir() and (md / "module.json").exists():
                        out.append(md)
        return out

    def list_modules(self) -> List[Module]:
        mods = []
        for d in self.module_dirs():
            try:
                m = Module.from_json(
                    json.loads((d / "module.json").read_text(encoding="utf-8")))
                # source.md 缺失时回退到内嵌 source_md
                src = d / "source.md"
                if src.exists():
                    m.source_md = src.read_text(encoding="utf-8")
                mods.append(m)
            except Exception:  # 尽力而为：跳过不可读/不可解析项（该类缺口由对应门禁与 AUD-0016 静默跳过清单另行报出）  # nosec B112 —— 尽力而为：跳过不可读/不可解析项（对应门禁另报；见 AUD-0016）
                continue
        return mods

    def get_module(self, full_id: str) -> Optional[Module]:
        """按 full_id 取模块。类别前缀短名/长名均可（情感:M22 ↔ 情感类:M22）。"""
        key = fid_key(full_id)
        for m in self.list_modules():
            if fid_key(m.full_id) == key:
                return m
        return None

    def save_module(self, m: Module) -> Path:
        """保存/更新一个模块。目录: modules/<分类>/<id>_<名称>/"""
        if not m.id:
            raise ValueError("模块 id 不能为空——请先补模块 id 再保存")
        if ":" in m.id:  # 兼容带前缀传入
            cat, num = m.id.split(":", 1)
            m.category = m.category or cat
            m.id = num
        if not m.installed_at:
            m.installed_at = now_str()
        d = self.modules_root / self._safe_name(m.category) / \
            f"{self._safe_name(m.id)}_{self._safe_name(m.name)}"
        # 清理同 full_id 的旧目录（改名/重存遗留），避免双目录并存
        key = fid_key(m.full_id)
        for old in self.module_dirs():
            if old == d:
                continue
            try:
                om = Module.from_json(json.loads(
                    (old / "module.json").read_text(encoding="utf-8")))
            except Exception:  # 尽力而为：跳过不可读/不可解析项（该类缺口由对应门禁与 AUD-0016 静默跳过清单另行报出）  # nosec B112 —— 尽力而为：跳过不可读/不可解析项（对应门禁另报；见 AUD-0016）
                continue
            if fid_key(om.full_id) == key:
                import shutil          # 惰性：`import shutil` 子树 ~9 ms，而写/删路径很少走（实测）
                shutil.rmtree(old, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)
        (d / "module.json").write_text(
            json.dumps(m.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
        if m.source_md:
            (d / "source.md").write_text(m.source_md, encoding="utf-8")
        return d

    def remove_module(self, full_id: str) -> bool:
        """删除模块（清理所有同 full_id 目录）。"""
        key = fid_key(full_id)
        removed = False
        for d in list(self.module_dirs()):
            try:
                mm = Module.from_json(json.loads(
                    (d / "module.json").read_text(encoding="utf-8")))
            except Exception:  # 尽力而为：跳过不可读/不可解析项（该类缺口由对应门禁与 AUD-0016 静默跳过清单另行报出）  # nosec B112 —— 尽力而为：跳过不可读/不可解析项（对应门禁另报；见 AUD-0016）
                continue
            if fid_key(mm.full_id) == key:
                import shutil
                shutil.rmtree(d, ignore_errors=True)
                removed = True
        return removed

    def toggle_module(self, full_id: str) -> Optional[Module]:
        m = self.get_module(full_id)
        if m:
            m.enabled = not m.enabled
            self.save_module(m)
        return m

    # ---------- 资产包 ----------
    def list_asset_packs(self) -> List[AssetPack]:
        out: List[AssetPack] = []
        if not self.assets_root.exists():
            return out
        for d in sorted(self.assets_root.iterdir()):
            jf = d / "asset.json"
            if jf.exists():
                try:
                    a = AssetPack.from_json(
                        json.loads(jf.read_text(encoding="utf-8")))
                    a.source_dir = str(d)
                    out.append(a)
                except Exception:  # nosec B112 —— 尽力而为：跳过不可读/不可解析项（见 AUD-0016）
                    continue
        return out

    def get_asset_pack(self, name: str) -> Optional[AssetPack]:
        for a in self.list_asset_packs():
            if a.name == name:
                return a
        return None

    def save_asset_pack(self, a: AssetPack) -> Path:
        if not a.installed_at:
            a.installed_at = now_str()
        d = self.assets_root / self._safe_name(a.name)
        d.mkdir(parents=True, exist_ok=True)
        (d / "asset.json").write_text(
            json.dumps(a.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
        return d

    def remove_asset_pack(self, name: str) -> bool:
        a = self.get_asset_pack(name)
        if not a:
            return False
        d = self.assets_root / self._safe_name(a.name)
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        return True

    # ---------- 预设 ----------
    def list_presets(self) -> List[Preset]:
        out: List[Preset] = []
        if not self.presets_root.exists():
            return out
        for f in sorted(self.presets_root.glob("*.json")):
            try:
                out.append(Preset.from_json(
                    json.loads(f.read_text(encoding="utf-8"))))
            except Exception:  # nosec B112 —— 尽力而为：跳过不可读/不可解析项（见 AUD-0016）
                continue
        return out

    def save_preset(self, p: Preset) -> Path:
        if not p.created_at:
            p.created_at = now_str()
        f = self.presets_root / f"{self._safe_name(p.name)}.json"
        f.write_text(json.dumps(p.to_json(), ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return f

    def remove_preset(self, name: str) -> bool:
        f = self.presets_root / f"{self._safe_name(name)}.json"
        if f.exists():
            f.unlink()
            return True
        return False

    # ---------- 缓存 ----------
    def save_cache(self, key: str, data):
        (self.cache_root / f"{key}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_cache(self, key: str) -> Optional[dict]:
        f = self.cache_root / f"{key}.json"
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except Exception:  # 缓存坏件/缺件 ⇒ 无命中（等价于未缓存，重算即可）
                return None
        return None

    # ---------- 统计 ----------
    def stats(self) -> dict:
        return {
            "modules": len(self.list_modules()),
            "assets": len(self.list_asset_packs()),
            "presets": len(self.list_presets()),
        }
