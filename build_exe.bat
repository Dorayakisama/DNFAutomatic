@echo off
setlocal

cd /d "%~dp0"
python -m PyInstaller --noconfirm --clean build.spec

echo.
echo Build finished. Check the dist folder for DNF_Auto_Down_Rank_Tool.exe
