# 冰壶赛道互动演示 - 安卓版

由原 matplotlib 桌面版（`interactive_curling_demo.py`）移植为 Kivy 应用，可打包成安卓 APK。

## 文件说明

| 文件 | 作用 |
|------|------|
| `main.py` | Kivy 主程序（入口，文件名不可改） |
| `buildozer.spec` | 安卓打包配置 |
| `.github/workflows/build.yml` | GitHub Actions 云端自动打包 APK |
| `requirements.txt` | 本地电脑测试用依赖 |

## 一、云打包 APK（推荐，无需 Linux）

1. 在 GitHub 上新建一个仓库（如 `curling-apk`）。
2. 把本目录所有文件（含 `.github` 文件夹）上传到该仓库的 `main` 分支。
   - 网页上传：New → uploading an existing file，把文件拖进去提交。
   - 或用 git：
     ```bash
     git init
     git add .
     git commit -m "init curling apk"
     git branch -M main
     git remote add origin https://github.com/你的用户名/curling-apk.git
     git push -u origin main
     ```
3. 推送后进入仓库的 **Actions** 标签页，会看到 “Build Android APK” 正在运行（首次约 15-25 分钟）。
4. 运行成功后，点进该次运行，在页面底部 **Artifacts** 里下载 `curling-apk.zip`，解压即得 `.apk`。
5. 把 APK 传到安卓手机安装（需在系统设置里允许“安装未知来源应用”）。

> 若没自动触发，可在 Actions 页面点 “Build Android APK” → “Run workflow” 手动触发。

## 二、本地电脑先预览效果（可选）

在 Windows 上先跑起来看界面（不是安卓，只是桌面预览）：

```bash
pip install -r requirements.txt
python main.py
```

## 三、说明

- 物理模拟逻辑与原版完全一致，只是去掉了 numpy，改为纯 Python，方便打包。
- 中文显示：安卓上会自动使用系统 CJK 字体；本地 Windows 会尝试用微软雅黑/黑体。
- 6 个滑竿分别对应：速度、旋转强度、初始角度、刷冰强度、冰面摩擦、冰面摆动性，拖动即实时重绘轨迹。
