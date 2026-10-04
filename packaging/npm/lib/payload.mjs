// payload 校验 + 首次运行解包（一次性、原子、带锁、带 sha256 校验，fail-closed）。
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { PAYLOAD_DIR, MANIFEST_NAME, payloadHome } from './paths.mjs';

export function readManifest() {
  const p = path.join(PAYLOAD_DIR, MANIFEST_NAME);
  if (!fs.existsSync(p)) {
    return { error: 'payload 未暂存：' + p + '（修复指引：在 packaging/npm 下跑 npm run stage）' };
  }
  try {
    return { manifest: JSON.parse(fs.readFileSync(p, 'utf8')) };
  } catch (e) {
    return { error: 'payload 清单不可解析：' + e.message };
  }
}

export function sha256File(p) {
  const h = crypto.createHash('sha256');
  h.update(fs.readFileSync(p));
  return h.digest('hex');
}

// 清单是 [{path, sha256}] 数组（不是对象键：路径可含 `+` 等合法字符）。
export function entriesOf(manifest) {
  return Array.isArray(manifest.files) ? manifest.files : [];
}

function byPath(a, b) { return a.path < b.path ? -1 : (a.path > b.path ? 1 : 0); }

// 逐文件核对清单 → 返回不一致清单（空数组 = 全绿）。
export function verifyTree(dir, manifest) {
  const bad = [];
  for (const e of entriesOf(manifest)) {
    const abs = path.join(dir, e.path);
    if (!fs.existsSync(abs)) { bad.push('missing:' + e.path); continue; }
    if (sha256File(abs) !== e.sha256) bad.push('digest:' + e.path);
  }
  return bad;
}

export function treeSha256(manifest) {
  const h = crypto.createHash('sha256');
  for (const e of entriesOf(manifest).slice().sort(byPath)) {
    h.update(e.path + '\u0000' + e.sha256 + '\n');
  }
  return h.digest('hex');
}

async function copyTree(src, dst) {
  await fsp.mkdir(dst, { recursive: true });
  const entries = await fsp.readdir(src, { withFileTypes: true });
  for (const ent of entries) {
    const s = path.join(src, ent.name);
    const d = path.join(dst, ent.name);
    if (ent.isDirectory()) await copyTree(s, d);
    else if (ent.isFile()) await fsp.copyFile(s, d);
  }
}

function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

// 首次运行把 payload 落到缓存目录；已存在且校验通过则直接复用（冷启动只解包一次）。
export async function ensurePayload(manifest, opts) {
  const options = opts || {};
  const home = payloadHome(manifest);
  const marker = path.join(home, '.nf-payload-ok');
  if (fs.existsSync(marker) && verifyTree(home, manifest).length === 0) return home;
  const lock = home + '.lock';
  await fsp.mkdir(path.dirname(lock), { recursive: true });
  const STALE_MS = 10 * 60 * 1000;
  for (let i = 0; i < 60; i += 1) {
    try {
      await fsp.mkdir(lock);
      break;
    } catch (e) {
      if (!e || e.code !== 'EEXIST') {
        throw new Error('解包锁目录创建失败：' + lock + '（' + ((e && e.code) || e) + '）（修复指引：检查缓存目录可写）');
      }
      // 陈旧锁回收：上一次进程被杀会留下锁目录。
      try {
        const st = await fsp.stat(lock);
        if (Date.now() - st.mtimeMs > STALE_MS) { await fsp.rm(lock, { recursive: true, force: true }); continue; }
      } catch (e2) { /* 锁刚被释放，下一轮重试 */ }
      if (i === 59) throw new Error('无法获取解包锁：' + lock + '（修复指引：删除该目录后重跑）');
      await sleep(500);
    }
  }
  try {
    if (fs.existsSync(marker) && verifyTree(home, manifest).length === 0) return home;
    const tmp = home + '.tmp-' + process.pid + '-' + Date.now();
    await fsp.rm(tmp, { recursive: true, force: true });
    await copyTree(PAYLOAD_DIR, tmp);
    const bad = verifyTree(tmp, manifest);
    if (bad.length) throw new Error('payload 校验失败（' + bad.length + ' 处）：' + bad.slice(0, 3).join(', '));
    await fsp.writeFile(path.join(tmp, '.nf-payload-ok'), manifest.tree_sha256 + '\n', 'utf8');
    await fsp.rm(home, { recursive: true, force: true });
    await fsp.rename(tmp, home);
    return home;
  } finally {
    await fsp.rm(lock, { recursive: true, force: true });
  }
}

// `nf install --dest <dir>`：把 payload 物化成一份真实工作树（供需要完整仓面的人）。
export async function materialize(manifest, dest, force) {
  if (fs.existsSync(dest) && !force) {
    const entries = await fsp.readdir(dest);
    if (entries.length) throw new Error('目标非空：' + dest + '（修复指引：加 --force 覆盖，或换空目录）');
  }
  await copyTree(PAYLOAD_DIR, dest);
  const bad = verifyTree(dest, manifest);
  if (bad.length) throw new Error('落盘校验失败（' + bad.length + ' 处）：' + bad.slice(0, 3).join(', '));
  return dest;
}
