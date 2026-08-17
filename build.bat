@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════════╗
echo ║       PC-Doctor-Lite Build Script          ║
echo ╚══════════════════════════════════════════╝
echo.

REM Check Python
python --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM Install dependencies
echo 📦 安装依赖...
pip install psutil wmi pywin32 pyinstaller
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

REM Clean previous builds
echo 🧹 清理旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "*.spec" del /q "*.spec"

REM Build EXE
echo 🔨 打包 EXE...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "PC-Doctor-Lite" ^
    --add-data "report-template;report-template" ^
    --hidden-import wmi ^
    --hidden-import pywin32 ^
    source\pc_doctor_lite.py

if %errorlevel% neq 0 (
    echo ❌ 打包失败
    pause
    exit /b 1
)

REM Package release zip
echo 📦 打包发布文件...
if not exist release mkdir release
copy "dist\PC-Doctor-Lite.exe" "release\" >nul
copy "README.txt" "release\" >nul
copy "LICENSE-THIRDPARTY.txt" "release\" >nul
copy "蓝屏代码速查表.md" "release\" >nul
if exist tools xcopy "tools" "release\tools\" /s /i /y >nul

REM Create zip (requires PowerShell)
powershell -command "Compress-Archive -Path 'release\*' -DestinationPath 'PC-Doctor-Lite-v1.0.zip' -Force"

echo.
echo ✅ 构建完成！
echo 📁 文件：PC-Doctor-Lite-v1.0.zip
echo.
echo 下一步：
echo   1. 下载 BlueScreenView 放到 tools\ 目录
echo   2. 下载 CrystalDiskInfo 便携版放到 tools\ 目录
echo   3. 双击 PC-Doctor-Lite.exe 测试
echo.
pause
