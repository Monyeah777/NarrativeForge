// 路径与缓存目录解析（无第三方依赖）。
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const PACKAGE_ROOT = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
export const PAYLOAD_DIR = path.join(PACKAGE_ROOT, 'payload');
export const MANIFEST_NAME = 'payload-manifest.json';

// 平台缓存根：Windows 用 LOCALAPPDATA，其余用 XDG_CACHE_HOME 或 ~/.cache。
export function cacheRoot(env = process.env) {
  if (env.NARRATIVEFORGE_CACHE) return path.resolve(env.NARRATIVEFORGE_CACHE);
  if (process.platform === 'win32' && env.LOCALAPPDATA) {
    return path.join(env.LOCALAPPDATA, 'narrativeforge', 'cache');
  }
  if (env.XDG_CACHE_HOME) return path.join(env.XDG_CACHE_HOME, 'narrativeforge');
  return path.join(os.homedir(), '.cache', 'narrativeforge');
}

export function payloadHome(manifest, env = process.env) {
  return path.join(cacheRoot(env), manifest.package_version + '-' + manifest.tree_sha256.slice(0, 12));
}

// 从 cwd 向上找 NF 仓库根（verify.sh + scripts/nf.py 双命中才算）。
export function findRepoRoot(start, fs) {
  let dir = path.resolve(start);
  for (;;) {
    if (fs.existsSync(path.join(dir, 'verify.sh')) && fs.existsSync(path.join(dir, 'scripts', 'nf.py'))) {
      return dir;
    }
    const up = path.dirname(dir);
    if (up === dir) return null;
    dir = up;
  }
}
