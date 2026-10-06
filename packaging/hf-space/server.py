#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NinFenz Space（S1 在线 demo）—— 纯标准库 HTTP 服务，真跑 NF 门禁。

为什么不引 gradio：NF 全仓零第三方硬依赖，Space 侧也保持同一纪律；一个 stdlib HTTP
服务就能把「粘贴文本 → 跑真实门禁 → 看逐条结论」做完整，且本地可复现。

安全面（与仓库纪律一致）：argv 列表调用（无 shell）、输入体积上限、超时上限、
只读命令白名单（不接受任意子命令）。
"""
from __future__ import annotations

import html
import json
import os
import subprocess
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
NF_ROOT = Path(os.environ.get('NF_ROOT') or (BASE / 'nf'))
PY = os.environ.get('NF_PYTHON') or sys.executable
MAX_INPUT = 200_000
TIMEOUT_S = 180

#: 只读命令白名单：(键, 展示名, 说明, 是否需要输入)
MODES = (
    ('lint', '文档语义体检（nf lint）', '把文本当作待检 .md，跑仓库 lint 判据', True),
    ('stats', '自述数字核对（nf stats --check）', '校验 README/llms.txt 的数字与实算一致', False),
    ('conformance', '契约一致性（nf conformance）', '跑协议件 ↔ registry 的一致性判据', False),
    ('doctor', '只读体检（nf doctor）', '仓库级 16 项只读体检', False),
)


def _caps(argv: list) -> None:
    if len(argv) > 4000:
        raise ValueError('参数过多（修复指引：命令面只接受白名单子命令）')


def run_mode(mode: str, text: str = '') -> dict:
    """跑一条白名单只读命令 → {ok, mode, exit, seconds, command, output}。"""
    table = {m[0]: m for m in MODES}
    if mode not in table:
        return {'ok': False, 'mode': mode, 'exit': 2, 'seconds': 0.0, 'command': '',
                'output': '未知模式（修复指引：只接受 %s）' % ', '.join(table)}
    if not NF_ROOT.is_dir():
        return {'ok': False, 'mode': mode, 'exit': 3, 'seconds': 0.0, 'command': '',
                'output': 'Space 未装载 NF 树：%s（修复指引：跑 tools/stage-space.mjs）' % NF_ROOT}
    args = [PY, str(NF_ROOT / 'scripts' / 'nf.py')]
    needs_input = table[mode][3]
    tmp_path = None
    if needs_input:
        body = str(text or '')
        if len(body) > MAX_INPUT:
            return {'ok': False, 'mode': mode, 'exit': 2, 'seconds': 0.0, 'command': '',
                    'output': '输入过大（%d 字符 > %d）（修复指引：截断后再试）' % (len(body), MAX_INPUT)}
        fd, tmp_path = tempfile.mkstemp(prefix='_space_input_', suffix='.md', dir=str(NF_ROOT))
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(body)
        args += ['lint', os.path.basename(tmp_path)]
    else:
        args += mode.split() if mode != 'stats' else ['stats', '--check']
        if mode == 'conformance':
            args = [PY, str(NF_ROOT / 'scripts' / 'nf.py'), 'conformance']
        elif mode == 'doctor':
            args = [PY, str(NF_ROOT / 'scripts' / 'nf.py'), 'doctor']
    _caps(args)
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    env['NF_AUTOSTART'] = '0'
    t0 = time.time()
    try:
        p = subprocess.run(args, cwd=str(NF_ROOT), capture_output=True, text=True,
                           encoding='utf-8', errors='replace', env=env, timeout=TIMEOUT_S)
        out = (p.stdout or '') + (('\n' + p.stderr) if p.stderr else '')
        code = p.returncode
    except subprocess.TimeoutExpired:
        out = '超时（> %d s）（修复指引：缩小输入或改跑其他只读命令）' % TIMEOUT_S
        code = 124
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    return {'ok': code == 0, 'mode': mode, 'exit': code, 'seconds': round(time.time() - t0, 2),
            'command': ' '.join(['nf'] + args[2:]), 'output': out.strip()[:20000]}


PAGE = '''<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NinFenz Contract Gate</title>
<style>
 :root{--bg:#0e1116;--fg:#dfe3e9;--dim:#8a929f;--acc:#7ee2f0;--ok:#76cd82;--err:#eb7a7a;--line:#2a3040}
 body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.6 ui-monospace,Consolas,"MS Gothic",monospace}
 .wrap{max-width:1000px;margin:0 auto;padding:24px}
 h1{font-size:18px;margin:0 0 4px} .sub{color:var(--dim);margin:0 0 18px}
 textarea{width:100%;height:220px;background:#12161e;color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:10px;font:13px/1.5 inherit}
 select,button{background:#1a2030;color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit}
 button{cursor:pointer} button:hover{border-color:var(--acc)}
 pre{background:#0b0e14;border:1px solid var(--line);border-radius:8px;padding:12px;overflow:auto;max-height:460px;white-space:pre-wrap}
 .meta{color:var(--dim);margin:10px 0} .ok{color:var(--ok)} .err{color:var(--err)}
 .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:12px 0}
 code{color:var(--acc)}
</style></head><body><div class="wrap">
<h1>NinFenz · Contract Gate</h1>
<p class="sub">在浏览器里跑 <b>真实</b> 的 NF 只读门禁：粘贴一段内容 → 看逐条判据结论。本地/离线同源，MIT。</p>
<div class="row"><select id="mode"></select><button id="go">运行</button><span class="meta" id="hint"></span></div>
<textarea id="text" placeholder="粘贴要体检的 markdown（仅 lint 模式使用）"></textarea>
<div class="meta" id="meta">就绪</div>
<pre id="out">点击「运行」开始。</pre>
<p class="sub" style="margin-top:18px">完整 39 条门禁与离线复跑：<code>npx -y ninfenz install --dest ./nf &amp;&amp; cd nf &amp;&amp; bash verify.sh</code> · 仓库 <a style="color:var(--acc)" href="https://github.com/Monyeah777/NinFenz">Monyeah777/NinFenz</a></p>
</div><script>
const MODES=__MODES__;
const sel=document.getElementById('mode'),ta=document.getElementById('text'),hint=document.getElementById('hint');
MODES.forEach(m=>{const o=document.createElement('option');o.value=m[0];o.textContent=m[1];sel.appendChild(o)});
function sync(){const m=MODES.find(x=>x[0]===sel.value);ta.style.display=m[3]?'block':'none';hint.textContent=m[2]}
sel.oninput=sync;sync();
document.getElementById('go').onclick=async()=>{
 const meta=document.getElementById('meta'),out=document.getElementById('out');
 meta.textContent='运行中…';out.textContent='';
 try{const r=await fetch('/api/gate',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({mode:sel.value,text:ta.value})});const j=await r.json();
  meta.innerHTML='<span class="'+(j.ok?'ok':'err')+'">exit '+j.exit+'</span> · '+j.seconds+'s · <code>'+(j.command||'')+'</code>';
  out.textContent=j.output||'(无输出)';}catch(e){meta.textContent='请求失败：'+e;}};
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    server_version = 'nf-space/1'

    def log_message(self, fmt, *args):  # 静默：日志交给平台
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path not in ('/', '/index.html'):
            self._send(404, b'not found', 'text/plain; charset=utf-8')
            return
        modes = json.dumps([[m[0], m[1], m[2], m[3]] for m in MODES], ensure_ascii=False)
        page = PAGE.replace('__MODES__', modes)
        self._send(200, page.encode('utf-8'), 'text/html; charset=utf-8')

    def do_POST(self) -> None:
        if self.path != '/api/gate':
            self._send(404, b'not found', 'text/plain; charset=utf-8')
            return
        try:
            n = int(self.headers.get('Content-Length') or 0)
            if n > MAX_INPUT + 4096:
                self._send(413, json.dumps({'ok': False, 'exit': 2, 'seconds': 0.0,
                                            'command': '', 'output': '请求过大'}).encode('utf-8'),
                           'application/json; charset=utf-8')
                return
            payload = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
            result = run_mode(str(payload.get('mode') or 'stats'), str(payload.get('text') or ''))
        except Exception as exc:  # noqa: BLE001 - 任何解析失败都按用户输入问题回，不 500
            result = {'ok': False, 'mode': '', 'exit': 2, 'seconds': 0.0, 'command': '',
                      'output': '请求不可解析：%s（修复指引：JSON 形如 {"mode":"stats","text":""}）' % exc}
        self._send(200, json.dumps(result, ensure_ascii=False).encode('utf-8'),
                   'application/json; charset=utf-8')


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if '--selftest' in args:
        r = run_mode('stats')
        print(json.dumps(r, ensure_ascii=False, indent=1)[:1500])
        return 0 if r['exit'] in (0, 1) else 1
    port = int(os.environ.get('PORT') or (args[args.index('--port') + 1] if '--port' in args else 7860))
    srv = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    print('nf-space listening on :%d (NF_ROOT=%s)' % (port, NF_ROOT), flush=True)
    srv.serve_forever()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
