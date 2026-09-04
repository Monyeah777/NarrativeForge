[app]
# 叙事工坊 · 模块组合器 Android 版（Kivy/KivyMD 壳 + 复用 desktop core）
title = 叙事工坊
package.name = narrativeforge
package.domain = org.narrativeforge
source.dir = .
# CJK 字体 fonts/NotoSansSC-Regular.otf（思源黑体 SC）需随包打入，otf 必须列入
source.include_exts = py,kv,json,md,txt,png,jpg,jpeg,ttf,otf
# v0.3.3：打包 CJK 字体（fonts/NotoSansSC-Regular.otf）修复 Android 全中文 notdef 沙漏占位
version = 0.3.3
orientation = portrait
fullscreen = 0

# 纯 stdlib core 可复用；KivyMD 提供 Material 外观；plyer 提供文件选择/分享
requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer

# Android 权限：读写通过系统文件选择器(SAF)/分享 intent，无需全盘；保留基础存储权限兼容旧路径
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
# NDK 固定 r25b（clang 14，2022-09）：Kivy 2.3.0 cgl_backend/cgl_gl.pyx 把
# glShaderSource 函数指针声明为 const GLchar **（4563 行赋值处），而 NDK r26+
# （clang 16+）GLES2/gl2.h 声明为 const GLchar *const *；clang 16 起把
# -Wincompatible-function-pointer-types 从 warning 升级为默认 error →
# cgl_gl.c:4563 编译判死（第 9 轮 CI 崩溃点）。r25b(clang14) 仅报 warning，
# 与 Kivy 2.3.0 发布时代（2023-02）p4a 官方 NDK 组合一致；p4a #3180 仍兼容。
android.ndk = 25b
# minapi 需 >=24：CPython 3.14 的 remote_debugging 模块调用 preadv/pwritev，
# Android bionic 自 API 24(Android 7.0) 起才在 <sys/uio.h> 声明这两个函数（API23 报 implicit declaration）
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

# debug 签名（MVP 阶段 sideload 安装；正式签名后续接入 keystore）
android.private_storage = True
# p4a 使用 CI 预制的 patched 克隆（p4a.source_dir 模式，buildozer 不 clone/reset/clean）：
#   - workflow 先 clone develop 并 reset --hard 到 2025-10-08 的 #3180
#     （6b66944a2f51e0c848c7ac51e04a771324067ecc）再打入 android/p4a_disable_grp.patch
#   - #3180：默认 CPython 3.11.13（kivy==2.3.0 的 Cython 预生成 C 代码只兼容到 3.12
#     私有 API；3.13 移除 _PyList_Extend/_PyGen_SetStopIterationValue，3.14 将
#     _PyLong_AsByteArray 扩为 6 参，均导致 kivy 编译判死）+ 已支持 NDK r28c
#   - 补丁：在 python3 recipe configure_args 注入 ac_cv_func_getgrgid(_r)=no，
#     使 CPython 3.11 的 grp 模块判定降为 missing 跳过编译（bionic 无 getgrent/
#     setgrent/endgrent，grpmodule.c 一编译必挂；3.14 起上游才补 getgrent 检查）
#   - 注入必须走 configure_args（命令行参数）：p4a arch.get_env() 从零构建 env
#     白名单（仅透传 HOME/PATH/CCACHE_*），workflow 里 export 的变量到不了 configure
# 注意：路径为 GitHub hosted runner 的绝对路径（HOME=/home/runner），
#       与 workflow 预制步骤的 clone 目标必须一致。
p4a.source_dir = /home/runner/p4a
[buildozer]
log_level = 2
warn_on_root = 1