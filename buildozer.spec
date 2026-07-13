[app]
title = Curling Demo
package.name = curlingdemo
package.domain = org.demo.curling

source.dir = .
source.include_exts = py,png,jpg,ttf,otf,ttc

version = 1.0

# 依赖：让 p4a 稳定版 recipe 决定 python 具体版本（带 android 补丁），仅锁 kivy。
requirements = python3,kivy==2.3.0

orientation = portrait
fullscreen = 0

# 无需特殊权限
android.permissions =

# 目标/最低 API
# minapi 必须 >= 26：CPython 的 grpmodule.c 依赖 setgrent/getgrent/endgrent，
# 这些函数在 Android bionic 中自 API 26 起才引入，低于 26 会编译报错。
android.api = 34
android.minapi = 26

# 锁定 NDK 版本：默认的 r28c 移除了 clang 旧选项，会导致 hostpython/kivy 编译失败。
# r25b 是 python-for-android 官方推荐且验证稳定的版本。
android.ndk = 25b

# 支持的架构
android.archs = arm64-v8a, armeabi-v7a

# 允许云端自动接受 SDK 许可
android.accept_sdk_license = True

# 锁定 python-for-android 到稳定 release，避免 master 分支的前沿破损
# （latest 会用 Python 3.14 宿主 + 损坏的 pip vendored 库）。
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
