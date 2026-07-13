[app]
title = Curling Demo
package.name = curlingdemo
package.domain = org.demo.curling

source.dir = .
source.include_exts = py,png,jpg,ttf,otf,ttc

version = 1.0

# 只需 Python + Kivy（物理逻辑纯 Python，无需 numpy）
requirements = python3,kivy

orientation = portrait
fullscreen = 0

# 无需特殊权限
android.permissions =

# 目标/最低 API（留空使用 buildozer 默认，云端会自动下载对应 SDK/NDK）
android.api = 34
android.minapi = 24

# 支持的架构
android.archs = arm64-v8a, armeabi-v7a

# 允许云端自动接受 SDK 许可
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
