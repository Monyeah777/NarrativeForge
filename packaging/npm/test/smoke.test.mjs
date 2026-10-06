// 冒烟测试：清单自洽 + 版本快路径 + 帮助 + 真跑一条只读命令（有 Python 时）。
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { PACKAGE_ROOT, PAYLOAD_DIR } from '../lib/paths.mjs';
import { verifyTree, treeSha256 } from '../lib/payload.mjs';

const pkg = JSON.parse(fs.readFileSync(path.join(PACKAGE_ROOT, 'package.json'), 'utf8'));
const manifest = JSON.parse(fs.readFileSync(path.join(PAYLOAD_DIR, 'payload-manifest.json'), 'utf8'));
const REPO_ROOT = path.resolve(PACKAGE_ROOT, '..', '..');

test('payload 逐文件 sha256 与清单一致', function () {
  assert.deepEqual(verifyTree(PAYLOAD_DIR, manifest), []);
  assert.equal(treeSha256(manifest), manifest.tree_sha256);
  assert.ok(manifest.count > 100, 'payload 件数异常偏少：' + manifest.count);
});

test('--version 走快路径且与包版本一致', function () {
  const r = spawnSync(process.execPath, [path.join(PACKAGE_ROOT, 'bin', 'nf.mjs'), '--version'], { encoding: 'utf8' });
  assert.equal(r.status, 0);
  assert.equal(r.stdout.trim(), 'nf ' + pkg.version);
});

test('--help 打印用法', function () {
  const r = spawnSync(process.execPath, [path.join(PACKAGE_ROOT, 'bin', 'nf.mjs'), '--help'], { encoding: 'utf8' });
  assert.equal(r.status, 0);
  assert.match(r.stdout, /ninfenz install --dest/);
});

test('在已有检出上真跑一条只读命令', function () {
  const r = spawnSync(process.execPath, [path.join(PACKAGE_ROOT, 'bin', 'nf.mjs'), '--repo', REPO_ROOT, 'doctor'], { encoding: 'utf8' });
  if (r.status === 4) return; // 本机无 Python：环境问题，不算失败
  assert.equal(r.status, 0, r.stderr || r.stdout);
  assert.match(r.stdout + r.stderr, /doctor|体检|PASS/i);
});
