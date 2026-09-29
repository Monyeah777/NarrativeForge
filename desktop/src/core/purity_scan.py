"""42 M3：架构纯度体检（verify check27 · 文档级 grep 断言族）。

每波收口前跑纯度体检，首批四规则（文档级，纯 stdlib）：

R1 层级越界/端壳残留：协议真相源（01/02）不得再出现 android/APK/src/ui/Kivy
    （APK 线裁决 #16 移除后的残留扫描）。
R2 私货/可变物：协议层文档（01/02/06/07）不得出现机器不可复现内容
    （绝对盘符路径 / 临时目录 / TODO-FIXME-XXX-TBD 占位）。
R3 冗余标题：同文档内重复章节标题（同一标题文本出现 >1 次）。
R4 错误信息即微型文档：desktop/src/core 全部 raise 消息须含修复/指引语
    （应为/先/请/须/必填/参考/示例/§ 等动作或出处词——标准批 A #12）。
R5 import 面越界：desktop/src/core + scripts 的第三方 import 面必须**登记**——
    只许 stdlib / 本地模块 / HARD_ALLOW 登记的硬依赖；其余第三方必须**软导入**
    （try/except ImportError 守卫）且在 SOFT_IMPORTS 登记理由；已退役端壳的存量残留
    在 IMPORT_RESIDUE 登记（**WARN 挂账**，带裁决指针，不判死但不得隐身）。
    （内部差距：CONTRIBUTING §4.2「core 零第三方依赖」是成文红线，此前**零判据**。）
R6 危险 sink 面：desktop/src/core + scripts 不得出现**动态执行 / shell 命令 / 不安全
    反序列化 / **不可逆的递归删除**（eval / exec / __import__ / os.system / os.popen /
    subprocess(shell=True) / pickle.load(s) / marshal.loads / yaml.load /
    shutil.rmtree / os.remove / os.rmdir，以及**方法名类**的 `x.unlink()`——确需使用须在
    SINK_ALLOW 登记并写明理由
    （放行可审计；list 参数调用 subprocess 不受限）。
    （内部差距：安全兜底此前**零判据**——NF 只靠人读与本仓之外的 linter；实测 sink 面
    仅 1 处受控 `__import__`，故本条落地即零返工。）
    2026-09-24 渗透 F-10 补：递归删除面此前**不在类目内**，于是 `NF_TEST_HOME=~`
    驱动的静默 `shutil.rmtree` 无判据可拦。现纳入类目（基线 1→5，放行点在册可审计）。
R7 抽象阶梯归属与越界：`protocol/LAYERS.json` 是阶梯唯一真源，语义判据实现在
    `core/layer_model.py`（L1 真源在位 / L2 归属互斥 / L3 接口面子集 / L4 依赖向下无环 /
    L5 入口非真源 / L6 引擎不反向 import 入口 / L7 退役阶不被依赖 / L8 判据可解析 /
    L9 豁免诚实 / L10 生成区==实时渲染）。本规则只做**接线**：把阶梯体检的 issues 汇入
    纯度报告——落地依据是端壳退役的教训（一阶可以整体退役，当时零判据，只能事后补）。
    分工遵 ADR-0003：形状类断言进 protocol/assertions.json，语义判据留代码。

check27 自身用变异注入验证捕获力（mutation testing：test_purity_scan 对
每规则注入典型违规样本，断言可被捕获——「check 的 check」）。
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
import sys
from core import conformance_scan as csc
from core import disk_cache

#: 协议真相源 + 导航文档（R1/R2/R3 作用域）
PROTO_DOCS = ("01_核心协议.md", "02_联动注册表.md",
              "06_Agent执行协议.md", "07_官方核心出厂与社区预设导航.md")

_END_SHELL = re.compile(r"(?i)(android|APK|src/ui|Kivy)")
_PRIVATE = re.compile(r"[A-Za-z]:\\|/tmp/|/Users/|/home/|TODO|FIXME|XXX|TBD")

#: R1–R3 的**逐件**事实缓存（键 = 该件正文的 sha256）：`(端壳残留, 私货/可变物, 重复标题)`。
#: 依据（实测 2026-09-29）：R1–R3 每次扫描都要把 4 份协议文档 `splitlines()` **三遍**、逐行跑
#: 三个正则（`01_核心协议.md` 是长文，这笔实测占 `purity_scan._scan_impl` 的一半以上）；而这
#: 三个事实只是**该件正文**的纯函数——改任何别的件（模块库、协议件、文档）时这一整笔应当为零。
#: 纪律同 `layer_model._entry_imports` / 本模块 `_facts_for`：键即内容，值里**不含路径**。
_DOC_FACTS_CACHE: dict = {}
_DOC_FACTS_MAX = 64


def _doc_facts(text: str):
    """一份协议文档的 R1–R3 事实：`(端壳命中, 私货命中, 重复标题)`（行号 + 已截断正文 / 标题）。

    等价性由 `test_purity_scan.DocFactsTest` 守着：用**未缓存的参考实现**（原先那三段
    「三遍 `splitlines()` + 逐行正则」原样搬进测试）在真仓库 4 份文档与合成样本上逐字段比对。
    """
    key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    hit = _DOC_FACTS_CACHE.get(key)
    if hit is not None:
        return hit
    shell, private, seen = [], [], {}
    for i, ln in enumerate(text.splitlines(), 1):     # `splitlines` 只做一遍（过去三遍）
        if _END_SHELL.search(ln):
            shell.append((i, ln.strip()[:80]))
        if _PRIVATE.search(ln):
            private.append((i, ln.strip()[:80]))
        m = _HEAD.match(ln)
        if m:
            seen.setdefault(m.group(1).strip(), []).append(i)
    got = (tuple(shell), tuple(private),
           tuple((t, tuple(v)) for t, v in seen.items() if len(v) > 1))
    if len(_DOC_FACTS_CACHE) >= _DOC_FACTS_MAX:
        _DOC_FACTS_CACHE.clear()
    _DOC_FACTS_CACHE[key] = got
    return got

#: R5 硬依赖白名单（**登记**的第三方硬 import：允许直接 import）
HARD_ALLOW = {
    "yaml": "PyYAML（仓库既有依赖；check16/28 同源解析，见 CONTRIBUTING §4.2 例外）",
}
#: R5 软导入登记（第三方可选依赖：必须 try/except ImportError 守卫 + 写明理由）
SOFT_IMPORTS = {
    "jsonschema": "IDL 标准实现交叉验证（可选对照；缺依赖则跳过该面）",
    "PySide6": "CCV3 卡面占位图写入（缺依赖须给明确修复指引，不得裸 ImportError）",
    "laya": "决策层本地服务（scripts/serve_decision_model.py）的模型运行时；软导入 + 缺依赖给修复指引",
}
#: R5 存量残留（**WARN 挂账**：确有理由保留的存量违规，须带裁决/文档指针；不判死但不得隐身）
#: 空表即"零残留"。注意本扫描按**文件系统**取件（与 verify 其它 check 同口径）——
#: 未入库的本地副本同样会被扫到，故"仓库干净"不等于"工作目录干净"。
#: 2026-09-20：唯一一项残留（`scripts/` 下端壳自检旧脚本，属 `.git/info/exclude` 的本地旧副本）
#: 经作者裁决删除，登记随之清空。
IMPORT_RESIDUE: dict = {}
#: 扫描作用域含 `.github/scripts`——那是**唯一处理远程不可信输入**（Issue 标题/正文）
#: 且持有写权限令牌的代码。此前只在 core + scripts 取件，等于把最高风险的入口
#: 排除在 R5/R6 之外（渗透实证：同一份含 os.system / subprocess(shell=True) 的文件
#: 放 scripts/ 被拦、放 .github/scripts/ 命中 0 条）。
IMPORT_SCAN = ("desktop/src/core/*.py", "scripts/*.py", ".github/scripts/*.py")

#: R6 危险 sink（AST 级；键 = 规范化调用名）+ CWE 对齐（外部缺陷类型编码，便于跨工具对账）
DANGEROUS_CALLS = {
    "eval": "CWE-95 动态执行（输入可注入）",
    "exec": "CWE-95 动态执行（输入可注入）",
    "__import__": "CWE-470 动态导入（须证明模块名非用户输入）",
    "os.system": "CWE-78 shell 命令（改用 subprocess 列表参数）",
    "os.popen": "CWE-78 shell 管道（改用 subprocess 列表参数）",
    "pickle.load": "CWE-502 不安全反序列化（可执行任意代码）",
    "pickle.loads": "CWE-502 不安全反序列化（可执行任意代码）",
    "marshal.loads": "CWE-502 不安全反序列化",
    "yaml.load": "CWE-502 非安全 YAML 载入（改用 yaml.safe_load）",
    "shutil.rmtree": "CWE-73 递归删除外部可控路径（须证明落点非主目录/仓库根/盘根）",
    "os.remove": "CWE-73 删除外部可控路径（须证明来源不可被外部左右）",
    "os.rmdir": "CWE-73 删除外部可控目录",
}
#: **方法名类 sink**：`x.unlink()` 与 `os.remove` 同险（都是"删一个文件"），但它们被调者的名字
#: 随接收者变（`old.unlink` / `p.unlink` / `f.unlink` …）——按整串匹配会**整类漏掉**。
#: 故这一类按**方法名**匹配，放行键也用方法名（`<文件基名>:unlink`），不随变量名漂移。
#: 落地依据（2026-09 实测）：本仓 core 里当时有 **6 处 `.unlink()`**，全部一路绿灯穿过 R6——
#: 与 F-10「递归删除面此前不在类目内」是同一类缺口。
METHOD_SINKS = {
    "unlink": "CWE-73 删除外部可控文件（`Path.unlink` 等价 `os.remove`，同样须证明来源不可被外部左右）",
}
#: R6 已登记放行（键 = "<文件基名>:<调用名>"；放行须可审计）
SINK_ALLOW = {
    "regression_score.py:__import__":
        "模块名取自内部常量表 SIGNAL_SPECS（非用户输入），用于按名调用既有扫描器",
    "e2e_desktop_headless.py:shutil.rmtree":
        "自检专用临时 home 的清理；落点已由 _resolve_test_home 拒绝主目录/仓库根/盘根（见 F-10）",
    "storage.py:shutil.rmtree":
        "模块仓内「同 full_id 旧目录」清理；路径由 Store._safe_name 拼装且限于 modules_root 之下",
    "watch.py:os.rmdir":
        "监听机制自检的临时目录清理：该目录由本模块 tempfile.mkdtemp 现建（路径不来自外部输入），"
        "且**非递归**——真出现意外子树时 rmdir 会拒绝，而不是把它一并抹掉",
    "disk_cache.py:unlink":
        "缓存裁剪：落点在 <NF_HOME>/cache/<tag>/ 之下，文件名是本模块自己算的 sha256（非外部输入），"
        "且只删超出保留份数的旧条目（按 mtime 排序）",
    "domain_pack.py:unlink":
        "域包工厂的陈旧件清理：只在目标包自己的 modules/ 与 pipelines/ 内、且文件名令牌匹配该包代码，"
        "删的是本轮未列入 planned 的旧产物（可复算，删旧即安全）",
    "pack_combo.py:unlink":
        "组合包改号残留清理：只在目标包自己的 pipelines/ 内、且文件名形如 P\\d{2,3} 且不等于本轮管线号",
    "storage.py:unlink":
        "Preset 删除（remove_preset）：路径由 Store._safe_name 拼装且限于 presets_root 之下",
    "watch.py:unlink":
        "监听机制自检自建临时目录内的探针件（probe.txt）清理；路径不来自外部输入",
}
_HEAD = re.compile(r"^#{1,6}\s+(.*?)\s*$")
_ACTION = re.compile(
    r"(应|须|先|必填|必需|必须|请|建议|参考|查看|运行|执行|使用|改用|替换|修复|"
    r"补齐|重新|重跑|更正|核对|检查|可选|选项|列表|注册|示例|格式|参见|见|按|需|"
    r"选择|可用|如|缺少|缺|期望|修正|§|文档|帮助|重试|再)")


#: R4–R6 的文本预筛：无 raise / import / try / shell / 任一危险调用名 → 三类事实必然为空，
#: 连 parse 都不必做（判据等价：AST 里出现的名字必然在源码文本里出现）。
_NEEDS_AST = re.compile(
    r"raise|import|try|shell|"
    + "|".join(re.escape(c.rsplit(".", 1)[-1]) for c in sorted(DANGEROUS_CALLS)))


def _try_guards_import(node: ast.Try) -> bool:
    """该 try 是否兜住了导入失败（ImportError / ModuleNotFoundError / Exception / 裸 except）。"""
    for h in node.handlers:
        if h.type is None:
            return True
        if isinstance(h.type, ast.Name) and h.type.id in (
                "ImportError", "ModuleNotFoundError", "Exception"):
            return True
        if isinstance(h.type, ast.Tuple):
            names = {e.id for e in h.type.elts if isinstance(e, ast.Name)}
            if names & {"ImportError", "ModuleNotFoundError", "Exception"}:
                return True
    return False


#: AST 事实缓存：键 = **文件文本本身**（内容不变 ⇒ 事实必然相同；内容一改键就变）。
#: 与围栏 YAML 缓存（conformance_scan._FENCE_CACHE）、引用度普查缓存同一条纪律：
#: 键即内容，所以**不存在陈旧风险**，可以放心在常驻进程里长期复用。
_FACTS_CACHE: dict = {}
_FACTS_CACHE_MAX = 4096


def _facts_for(text: str):
    """文本 → R4–R6 事实（预筛不中即 None）；**两层**按内容缓存（进程内 + 持久）。

    持久层（`core.disk_cache`，键里还含代码面 + 运行时）：一次冷进程 `evaluate` 里 AST 解析
    134–235 份 core/scripts 源码约 **0.98 s**，新进程从此免付。键＝文本的 sha256 ⇒ 键即内容，
    无陈旧面；读回按 `_packed_ok` 校验形状并把元组/集合**还原成原类型**（保证与现算逐位相等，
    有往返判据守着）。
    """
    if text in _FACTS_CACHE:
        return _FACTS_CACHE[text]
    dkey = disk_cache.key("ast-facts", hashlib.sha256(text.encode("utf-8")).hexdigest(),
                              code_modules=("core.purity_scan",))
    packed = disk_cache.load("ast-facts", dkey, validate=_packed_ok)
    got = _unpack_facts(packed) if packed is not None else _FACTS_READ_MISS
    if got is _FACTS_READ_MISS:
        got = None
        if _NEEDS_AST.search(text):
            try:
                got = _ast_facts(ast.parse(text))
            except SyntaxError:
                got = None
        # 每份源码一条 ⇒ 上限按「进程内事实缓存」同一量级给（默认 16 会让它反复抖动）
        disk_cache.store("ast-facts", dkey, _pack_facts(got), keep=_FACTS_CACHE_MAX)
    if len(_FACTS_CACHE) >= _FACTS_CACHE_MAX:
        _FACTS_CACHE.clear()
    _FACTS_CACHE[text] = got
    return got


#: 持久层未命中的哨兵（`None` 本身是**合法结果**：预筛不中 / 语法错，两者都要能落盘）
_FACTS_READ_MISS = object()


def _pack_facts(facts):
    """事实 → 可 JSON 的载荷（元组/集合统一成列表，并记下「命中与否」）。"""
    if facts is None:
        return {"hit": False, "facts": None}
    raises, guarded, modules, sinks = facts
    return {"hit": True, "facts": [[list(x) for x in raises], sorted(guarded),
                                   [list(x) for x in modules], [list(x) for x in sinks]]}


def _packed_ok(value) -> bool:
    """载荷形状校验：不符即当未命中（半截/串味的文件一律重算）。"""
    return (isinstance(value, dict) and set(value) == {"hit", "facts"}
            and isinstance(value["hit"], bool)
            and (value["facts"] is None
                 or (isinstance(value["facts"], list) and len(value["facts"]) == 4)))


def _unpack_facts(value):
    """载荷 → 事实：**逐类型还原**（元组回元组、集合回集合），保证与现算结果相等。"""
    if not value["hit"]:
        return None
    raises, guarded, modules, sinks = value["facts"]
    return ([(int(a), str(b)) for a, b in raises],
            {int(x) for x in guarded},
            [(str(a), int(b)) for a, b in modules],
            [(int(a), str(b), bool(c)) for a, b, c in sinks])


def _ast_facts(tree: ast.AST) -> tuple:
    """**一次** `ast.walk` 取齐 R4–R6 全部事实（判据与分次遍历逐条等价）。

    效率（实测）：同一棵树过去被 walk **四遍**——R4 的 raise 消息 1 遍、R5 的守卫 import
    行号 1 遍、R5 的顶层模块 1 遍、R6 的危险 sink 1 遍；`nf conformance` 里 AST 面因此
    独占约 **7.7 s**（约 210 万次节点访问）。合流后每份文件只 walk 一遍。

    返回 `(raise 消息, 守卫 import 行号集, 顶层模块, 危险调用节点)`；各自的**产出顺序**
    与原来那次独立遍历完全一致（同一次 walk 顺序）。
    """
    raises: list = []
    guarded: set = set()
    modules: list = []
    sinks: list = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and node.exc.args:
            arg = node.exc.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                raises.append((node.lineno, arg.value))
            elif isinstance(arg, ast.JoinedStr):
                parts = [v.value for v in arg.values
                         if isinstance(v, ast.Constant) and isinstance(v.value, str)]
                raises.append((node.lineno, "".join(parts)))
        elif isinstance(node, ast.Import):
            modules += [(a.name.split(".")[0], node.lineno) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules.append((node.module.split(".")[0], node.lineno))
        elif isinstance(node, ast.Try) and _try_guards_import(node):
            for sub in node.body:
                for n2 in ast.walk(sub):
                    if isinstance(n2, (ast.Import, ast.ImportFrom)):
                        guarded.add(n2.lineno)
        elif isinstance(node, ast.Call):
            # 危险 sink 候选在这里就**摘成可序列化的三元组**（行号 / 被调名 / 是否 shell=True）：
            # 判据与原来"拿着 AST 节点到 R6 再 unparse"逐条等价（有等价性判据守着），
            # 但结果成了纯数据 ⇒ 整份事实可以按内容落盘，新进程不必再解析这 235 份源码。
            sinks.append((node.lineno, ast.unparse(node.func),
                          any(kw.arg == "shell" and isinstance(kw.value, ast.Constant)
                              and kw.value.value is True for kw in node.keywords)))
    return raises, guarded, modules, sinks


def _is_local(mod: str, root: str) -> bool:
    if mod == "core":
        return True
    for base in (os.path.join(root, "desktop", "src", "core"), os.path.join(root, "scripts"),
                 os.path.join(root, ".github", "scripts")):
        if os.path.exists(os.path.join(base, mod + ".py")):
            return True
    return False


def patterns(root: str = ".") -> tuple:
    """`scan()` 的输入面：自身读的面（代码 / 协议文档 / 判据脚本）+ **R7 阶梯面**。

    为什么带上阶梯面：本函数把 `layer_model.scan()` 的结果并进 issues ⇒ 阶梯的输入也是本函数的
    输入，漏了它就会出现「改资产却不重算纯度」的陈旧。
    """
    own = OWN_PATTERNS
    try:
        from core import layer_model as _lm
        return tuple(dict.fromkeys(own + tuple(_lm.patterns(root))))
    except Exception:                                    # noqa: BLE001 - 面取不全就别缓存
        return own


#: **自有面**（本模块自己读的那些件）：代码 / 协议文档 / 判据脚本。
OWN_PATTERNS = ("01_核心协议.md", "02_联动注册表.md", "06_Agent执行协议.md",
                "07_官方核心出厂与社区预设导航.md", "protocol/*.json", "verify.sh",
                "desktop/src/**/*.py", "scripts/**/*", ".github/scripts/*.py")


def scan(root: str = ".") -> tuple:
    """纯度体检（R1–R7）。派生结果按**输入内容指纹**缓存（输入面见 `patterns()`，很宽）。

    宽面只在常驻语料层在位时走缓存（`require_resident=True`）——理由见 `layer_model.scan`。

    **键的取法（2026-09-29 改，实测）**：过去直接把 `patterns(root)`（自有面 + 阶梯面，54 条）
    交给 `memo_pair` 枚举一遍，而 `layer_model.scan()` 内部又把**同一张阶梯面**（45 条）枚举第二遍
    ⇒ 一次 `nf_score` 白花 ~10 ms。现在把两张面**各自的指纹组合**成键，并把阶梯面指纹**传给**
    `layer_model.scan(_fp=...)`：覆盖面与旧口径完全相同（自有面 ∪ 阶梯面），只枚举一次。
    """
    if not csc.resident_active():
        # **冷进程**：`memo_pair` 反正不会走缓存（宽面在冷进程里宁可不算，见 `layer_model.scan`），
        # 那就**连指纹都别取**——否则这一改会把冷进程推慢 ~250 ms（实测踩过）。
        return _scan_impl(root)
    try:
        from core import layer_model as _lm
        layer_fp = _lm.face_fingerprint(root)
    except Exception:                                    # noqa: BLE001 - 取不出就退回整面
        return csc.memo_pair("purity-scan", patterns(root), _scan_impl, root,
                             require_resident=True, code_modules=("core.purity_scan",))
    own_fp = csc.face_fingerprint(root, OWN_PATTERNS)
    fp = hashlib.sha256(("%s\x00%s" % (own_fp, layer_fp)).encode("utf-8")).hexdigest()
    return csc.memo_pair("purity-scan", patterns(root), lambda r: _scan_impl(r, layer_fp), root,
                         require_resident=True, code_modules=("core.purity_scan",), fp=fp)


def _scan_impl(root: str = ".", _layer_fp: str = None) -> tuple:
    """真算（未命中缓存时走这里）；`_layer_fp` 由 `scan()` 传下来，避免走两次阶梯面。"""
    issues = []
    stats = {"docs": 0, "raises": 0, "imports": 0, "import_residue": []}
    # R1/R2/R3：协议层文档
    for name in PROTO_DOCS:
        path = os.path.join(root, name)
        if not os.path.exists(path):
            continue
        text = csc.read_text_cached(path)          # 共享语料读：一次只读调用内同件只读一遍
        stats["docs"] += 1
        shell_hits, private_hits, dup_titles = _doc_facts(text)   # 键即内容：没改就不重扫
        if name in ("01_核心协议.md", "02_联动注册表.md"):
            for i, ln in shell_hits:
                issues.append("%s:%d 端壳/APK 残留：%s" % (name, i, ln))
        for i, ln in private_hits:
            issues.append("%s:%d 私货/可变物：%s" % (name, i, ln))
        for title, lines in dup_titles:
            issues.append("%s 重复标题「%s」：行 %s"
                          % (name, title, ",".join(map(str, lines))))
    # R4：错误信息审计（desktop/src/core/*.py）
    # R4/R5/R6 共用一份「读 + parse + walk」：同一批 core/*.py 过去被 R4 与 R5 各自 parse
    # 一遍、同一棵树被 walk 四遍（见 `_ast_facts`）。
    # 缓存分两层，判据都是「键即内容」：
    #   ① 本次扫描内按**路径**缓存（省重复读盘）；
    #   ② 跨调用按**文件文本**缓存（`_facts_for`）——文本没变 ⇒ 事实必然相同，文本一变键就变，
    #      因此**不存在陈旧风险**，可以在常驻进程（nf daemon）里长期复用，
    #      把「每次跑 score/verify 都重解析 247 份 .py」的成本摊掉。
    facts_cache: dict = {}

    def _facts(fpath: str):
        if fpath in facts_cache:
            return facts_cache[fpath]
        try:
            text = csc.read_text_cached(fpath)     # 同上（L6 与这里的 core/*.py 是同一批件）
        except OSError:
            facts_cache[fpath] = None
            return None
        got = _facts_for(text)
        facts_cache[fpath] = got
        return got

    core_dir = os.path.join(root, "desktop", "src", "core")
    if os.path.isdir(core_dir):
        for fname in sorted(os.listdir(core_dir)):
            if not fname.endswith(".py"):
                continue
            facts = _facts(os.path.join(core_dir, fname))
            if facts is None:
                continue
            for lineno, msg in facts[0]:
                stats["raises"] += 1
                if msg and not _ACTION.search(msg):
                    issues.append("%s:%d raise 消息缺修复指引：%s"
                                  % (fname, lineno, msg[:60]))
    # R5：import 面（core + scripts 的第三方依赖须登记；软导入才可免硬依赖）
    import glob as _glob
    for rel_pat in IMPORT_SCAN:
        for f in sorted(_glob.glob(os.path.join(root, rel_pat))):
            rel = os.path.relpath(f, root).replace("\\", "/")
            facts = _facts(f)
            if facts is None:
                continue
            _raises, guarded, modules, sinks = facts
            residue = IMPORT_RESIDUE.get(rel)
            for mod, lineno in modules:
                if mod in sys.stdlib_module_names or _is_local(mod, root):
                    continue
                stats["imports"] += 1
                if mod in HARD_ALLOW:
                    continue
                if mod in SOFT_IMPORTS:
                    if lineno not in guarded:
                        msg = ("%s:%d 第三方 %s 未软导入（须 try/except ImportError 守卫；"
                               "登记理由：%s）" % (rel, lineno, mod, SOFT_IMPORTS[mod]))
                        (stats["import_residue"] if residue else issues).append(
                            "%s（%s）" % (msg, residue) if residue else msg)
                    continue
                msg = ("%s:%d 第三方 import 未登记：%s（修复指引：改为软导入并在 purity_scan.SOFT_IMPORTS "
                       "登记理由，或加入 HARD_ALLOW；端壳残留则登记 IMPORT_RESIDUE）" % (rel, lineno, mod))
                (stats["import_residue"] if residue else issues).append(
                    "%s（%s）" % (msg, residue) if residue else msg)
            # R6：危险 sink 面（同一次 AST 遍历复用同一份事实）
            for lineno, call, shell_true in sinks:
                flags = []                      # (展示名, 放行键名)——方法类 sink 的键名用方法名
                if call in DANGEROUS_CALLS:
                    flags.append((call, call))
                method = call.rsplit(".", 1)[-1]
                if method in METHOD_SINKS:
                    flags.append((method, method))
                if shell_true:
                    flags.append(("subprocess(shell=True)", "subprocess"))
                for name, key_name in flags:
                    stats["sinks"] = stats.get("sinks", 0) + 1
                    key = "%s:%s" % (os.path.basename(f), key_name)
                    if key in SINK_ALLOW:
                        continue
                    issues.append("%s:%d 危险 sink %s（%s）——确需使用须在 purity_scan.SINK_ALLOW "
                                  "登记理由（修复指引：改用安全等价物，或登记后写明为何不可注入）"
                                  % (rel, lineno, name,
                                     DANGEROUS_CALLS.get(call)
                                     or METHOD_SINKS.get(method)
                                     or "shell=True 命令注入面"))
    # R6 自洽面（登记表自身的判据）：每个 sink 类目须带 CWE 对齐（跨工具对账用缺陷类型编码），
    # 且 SINK_ALLOW 的每个放行键必须指向一个已登记 sink——放行不能凭空出现。
    for call, desc in sorted({**DANGEROUS_CALLS, **METHOD_SINKS}.items()):
        if not re.match(r"^CWE-\d+ ", desc):
            issues.append("危险 sink 类目缺 CWE 对齐：%s（修复指引：在 purity_scan.DANGEROUS_CALLS "
                          "的说明前加 `CWE-<nnn> `，便于外部扫描器按缺陷类型对账）" % call)
    for key in sorted(SINK_ALLOW):
        sink = key.rsplit(":", 1)[-1]
        if sink not in DANGEROUS_CALLS and sink not in METHOD_SINKS and sink != "subprocess":
            issues.append("SINK_ALLOW 放行键指向未登记 sink：%s（修复指引：删除放行，"
                          "或先在 DANGEROUS_CALLS 登记该 sink 类目）" % key)
    # R7：抽象阶梯归属与越界（真源 protocol/LAYERS.json；语义判据在 core/layer_model.py）
    try:
        from core import layer_model as _lm
        if os.path.isfile(os.path.join(root, _lm.DECL_REL)):
            _ladder_issues, _ladder_stats = _lm.scan(root, _fp=_layer_fp)
            stats["layers"] = _ladder_stats
            issues += _ladder_issues
        else:
            # 合成树（单测）通常无阶梯件：缺件不在这里判死——缺席由断言表
            # `layers-declaration-in-place`（json_value 命中"目标件不存在"）+ 规范性名单
            # （modeling.verify_normative 断言 norm 件存在）+ RECEIPTS 覆盖面三处另判，不静默。
            stats["layers"] = {"skipped": "缺 %s（另由断言表与规范性名单判）" % _lm.DECL_REL}
    except Exception as _exc:
        issues.append("R7 阶梯体检不可用：%s（修复指引：核对 protocol/LAYERS.json 与 "
                      "desktop/src/core/layer_model.py 后可读性）" % _exc)
    return issues, stats
