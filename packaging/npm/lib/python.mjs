// Python 解释器探测与版本闸门（NF 要求 >= 3.11；探测顺序可被环境变量覆盖）。
import { spawnSync } from 'node:child_process';

export const MIN_PYTHON = [3, 11];

export function candidates(env = process.env) {
  const out = [];
  if (env.NINFENZ_PYTHON) out.push({ cmd: env.NINFENZ_PYTHON, pre: [] });
  if (process.platform === 'win32') out.push({ cmd: 'py', pre: ['-3'] });
  out.push({ cmd: 'python3', pre: [] });
  out.push({ cmd: 'python', pre: [] });
  return out;
}

export function probe(cand) {
  const code = 'import sys; print("%d.%d.%d" % sys.version_info[:3])';
  const r = spawnSync(cand.cmd, cand.pre.concat(['-c', code]), { encoding: 'utf8' });
  if (r.error || r.status !== 0 || !r.stdout) return null;
  const parts = String(r.stdout).trim().split('.').map(function (n) { return parseInt(n, 10); });
  if (parts.length < 2 || Number.isNaN(parts[0])) return null;
  return { cmd: cand.cmd, pre: cand.pre, version: parts };
}

export function atLeast(version, min) {
  for (let i = 0; i < min.length; i += 1) {
    const a = version[i] || 0;
    const b = min[i] || 0;
    if (a > b) return true;
    if (a < b) return false;
  }
  return true;
}

// fail-closed：找不到或版本过低都返回带修复指引的错误（绝不静默降级）。
export function findPython(env = process.env) {
  const seen = [];
  for (const cand of candidates(env)) {
    const found = probe(cand);
    if (!found) { seen.push(cand.cmd); continue; }
    if (!atLeast(found.version, MIN_PYTHON)) {
      return { error: 'Python ' + found.version.join('.') + ' 过低（需 >= ' + MIN_PYTHON.join('.') + '）：' + found.cmd
        + '（修复指引：装 Python ' + MIN_PYTHON.join('.') + '+ 后重跑；或用 NINFENZ_PYTHON 指定解释器）' };
    }
    return { python: found };
  }
  return { error: '未找到可用的 Python（试过：' + seen.join(', ') + '）'
    + '（修复指引：装 Python ' + MIN_PYTHON.join('.') + '+；Windows 可装 python.org 版或 py -3；'
    + '或用 NINFENZ_PYTHON 指定解释器路径）' };
}
