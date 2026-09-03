[app]
# 叙事工坊 · 模块组合器 Android 版（Kivy/KivyMD 壳 + 复用 desktop core）
title = 叙事工坊
package.name = narrativeforge
package.domain = org.narrativeforge
source.dir = .
source.include_exts = py,kv,json,md,txt,png,jpg,jpeg,ttf
version = 0.2.0
orientation = portrait
fullscreen = 0

# 纯 stdlib core 可复用；KivyMD 提供 Material 外观；plyer 提供文件选择/分享
requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer

# Android 权限：读写通过系统文件选择器(SAF)/分享 intent，无需全盘；保留基础存储权限兼容旧路径
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
# minapi 需 >=24：CPython 3.14 的 remote_debugging 模块调用 preadv/pwritev，
# Android bionic 自 API 24(Android 7.0) 起才在 <sys/uio.h> 声明这两个函数（API23 报 implicit declaration）
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

# debug 签名（MVP 阶段 sideload 安装；正式签名后续接入 keystore）
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1