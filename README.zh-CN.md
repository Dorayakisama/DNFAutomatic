# DNFAutomatic

[English](README.md) | [简体中文](README.zh-CN.md)

DNFAutomatic 是一个用于 DNF 重复段位匹配操作的桌面自动化工具。它通过屏幕截图、图像识别和模拟鼠标输入来执行固定流程。使用前，用户需要先打开游戏、设置正确分辨率，并进入对应的游戏页面。

本项目完全由 Codex 通过 vibe coding 构建完成。

## 项目简介

- 使用 `tkinter` 构建桌面界面
- 基于模板匹配的图像识别
- 支持段位比较与循环自动化流程
- 内置运行日志控制台与手动停止功能
- 支持使用 PyInstaller 打包为 Windows 可执行文件
- 支持在 Windows 下自动以管理员权限重新启动

## 重要说明

- 本工具不会修改游戏文件，也不会修改游戏内存。
- 本工具依赖屏幕识别与模拟手动输入。
- 运行过程中请保持游戏窗口可见，且不要被其他窗口遮挡。
- `resource/` 目录中的图像资源是自动化识别所必需的。

## 主要功能

- 在中文界面中选择目标段位
- 设置达到目标段位后继续执行的额外场数
- 在主窗口中启动和停止自动化
- 支持用户自定义终止快捷键
- 在内置控制台中查看运行日志
- 可打包为 Windows `.exe` 程序

## 段位映射

内部逻辑使用英文键值，界面显示中文名称：

- `Bronze 4` -> `青铜4`
- `Silver 1` -> `白银1`
- `Silver 2` -> `白银2`
- `Silver 3` -> `白银3`
- `Silver 4` -> `白银4`
- `Gold 1` -> `黄金1`
- `Gold 2` -> `黄金2`
- `Gold 3` -> `黄金3`
- `Gold 4` -> `黄金4`
- `Platinum` -> `白金`
- `Diamond` -> `钻石`

## 项目结构

```text
DNFAutomatic/
├─ app.py
├─ build.spec
├─ build_exe.bat
├─ requirements.txt
├─ dnf_tool/
│  ├─ constants.py
│  ├─ models.py
│  ├─ services/
│  │  ├─ automation.py
│  │  ├─ controller.py
│  │  ├─ hotkey.py
│  │  └─ vision.py
│  └─ ui/
│     └─ main_window.py
└─ resource/
   ├─ icon.ico
   ├─ rank_image/
   └─ sys_image/
```

## 运行要求

- Windows
- 推荐 Python 3.13
- 依赖包：
  - `opencv-python`
  - `Pillow`
  - `PyAutoGUI`
  - `PyInstaller`（用于打包）

## 从源码运行

安装依赖：

```powershell
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

启动程序：

```powershell
python app.py
```

## 打包为可执行文件

使用项目自带脚本：

```powershell
build_exe.bat
```

或者直接运行 PyInstaller：

```powershell
python -m PyInstaller --noconfirm --clean build.spec
```

生成的可执行文件位于：

```text
dist/DNF_Auto_Down_Rank_Tool.exe
```

## 分发方式

如果你要把程序发给其他用户，请同时提供：

- `DNF_Auto_Down_Rank_Tool.exe`
- 完整的 `resource/` 文件夹

它们应当保持在同一目录结构下。

## 资源文件

自动化识别依赖以下目录中的模板图像：

- `resource/rank_image/`
- `resource/sys_image/`

具体文件名和段位映射说明请查看 [resource/README.md](resource/README.md)。

## 打包说明

- 可执行文件启动时会请求管理员权限。
- 程序打包图标使用 `resource/icon.ico`。
- 运行时窗口图标也在界面启动逻辑中进行了配置。

## 仓库说明

本仓库及其实现内容完全由 Codex 通过 vibe coding 完成，包括：

- 界面构建
- 自动化流程实现
- 图像识别整合
- 打包配置
- 项目文档与仓库整理
