# DNFAutomatic

[English](README.md) | [简体中文](README.zh-CN.md)

DNFAutomatic is a desktop automation tool for repetitive DNF rank-match operations. It uses screen capture, image recognition, and simulated mouse input to automate a fixed workflow after the user has already opened the game, configured the correct resolution, and entered the proper in-game page.

This project was completely constructed by Codex using vibe coding.

## Overview

- Desktop UI built with `tkinter`
- Image recognition based on template matching
- Rank comparison and looped automation flow
- Runtime log console and manual stop controls
- Windows executable packaging with PyInstaller
- Built-in administrator relaunch support on Windows

## Important Notes

- This tool does not modify game files or game memory.
- It relies on screen recognition and simulated manual input.
- The game window should stay visible and unobstructed while the tool is running.
- The image resources in `resource/` are required for detection to work.

## Main Features

- Select target rank in Chinese UI labels
- Set extra runs after the target rank is reached
- Start and stop automation from the main window
- Configure a user-defined stop hotkey
- View runtime logs in the built-in console
- Package the project into a Windows `.exe`

## Rank Mapping

Internal logic uses English keys, while the UI shows Chinese labels:

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

## Project Structure

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

## Requirements

- Windows
- Python 3.13 recommended
- Installed packages:
  - `opencv-python`
  - `Pillow`
  - `PyAutoGUI`
  - `PyInstaller` for packaging

## Run From Source

Install dependencies:

```powershell
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

Start the app:

```powershell
python app.py
```

## Build Executable

Use the included build script:

```powershell
build_exe.bat
```

Or run PyInstaller directly:

```powershell
python -m PyInstaller --noconfirm --clean build.spec
```

The generated executable will be placed in:

```text
dist/DNF_Auto_Down_Rank_Tool.exe
```

## Distribution

To distribute the program, provide:

- `DNF_Auto_Down_Rank_Tool.exe`
- the full `resource/` folder

They should stay together in the same directory layout.

## Resource Files

The automation depends on template images stored in:

- `resource/rank_image/`
- `resource/sys_image/`

See [resource/README.md](resource/README.md) for the expected filenames and rank mappings.

## Packaging Notes

- The executable is configured to request administrator privileges on launch.
- The project uses `resource/icon.ico` for the packaged executable icon.
- Runtime window icon behavior is also configured in the UI startup logic.

## Repository Credit

This repository and its implementation were fully produced by Codex through vibe coding, including:

- UI construction
- automation workflow implementation
- image-recognition integration
- packaging setup
- project documentation and repo preparation
