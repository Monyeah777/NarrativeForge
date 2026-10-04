"""取证脚本：用 sys.addaudithook 记录 conformance 构建期间所有 open/scandir 路径，
判定 `engine/rust/**` 是否真被任何契约读取（把「我造成的漂移」与「并发会话造成的漂移」分开）。

只读：本脚本不写任何仓库文件，仅向标准输出打印结论。
"""
import sys
from pathlib import Path

root = Path(".").resolve()
sys.path.insert(0, str(root / "desktop" / "src"))

opened = []
scanned = []


def hook(event, args):
    if event == "open":
        try:
            opened.append(str(args[0]))
        except Exception:
            pass
    elif event in ("os.scandir", "os.listdir"):
        try:
            scanned.append(str(args[0]))
        except Exception:
            pass


sys.addaudithook(hook)

from core import conformance_report as cr  # noqa: E402

doc = cr.run(str(root))


def norm(p):
    return p.replace("\\", "/")


allpaths = [norm(p) for p in opened + scanned]
engine_rust = sorted({p for p in allpaths if "/engine/rust" in p})
engine_any = sorted({p for p in allpaths if "/engine/" in p})

print("audit: open=%d scandir=%d" % (len(opened), len(scanned)))
print("verdict=%s root=%s" % (doc.get("verdict"), doc.get("root")))
print("engine/rust 命中: %d" % len(engine_rust))
for p in engine_rust[:20]:
    print("    RUST>", p)
print("engine/ 命中: %d" % len(engine_any))
for p in engine_any[:20]:
    print("    ENG >", p)
