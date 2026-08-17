# PC-Doctor-Lite Release Build Script (PowerShell)
# Run on Windows with Administrator privileges

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       PC-Doctor-Lite Release Builder      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "📋 Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "   $pythonVersion" -ForegroundColor Green

# Step 2: Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install psutil wmi pywin32 pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Step 3: Clean
Write-Host ""
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
Get-ChildItem "*.spec" -ErrorAction SilentlyContinue | Remove-Item -Force

# Step 4: Build EXE
Write-Host ""
Write-Host "🔨 Building EXE with PyInstaller..." -ForegroundColor Yellow
pyinstaller `
    --onefile `
    --windowed `
    --name "PC-Doctor-Lite" `
    --add-data "report-template;report-template" `
    --hidden-import wmi `
    --hidden-import pywin32 `
    "source/pc_doctor_lite.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}

# Step 5: Package release
Write-Host ""
Write-Host "📦 Packaging release..." -ForegroundColor Yellow
$releaseDir = "release"
if (Test-Path $releaseDir) { Remove-Item -Recurse -Force $releaseDir }
New-Item -ItemType Directory -Path $releaseDir | Out-Null

Copy-Item "dist\PC-Doctor-Lite.exe" "$releaseDir\" -Force
Copy-Item "README.txt" "$releaseDir\" -Force
Copy-Item "LICENSE-THIRDPARTY.txt" "$releaseDir\" -Force
Copy-Item "蓝屏代码速查表.md" "$releaseDir\" -Force
if (Test-Path "tools") { Copy-Item "tools" "$releaseDir\" -Recurse -Force }

$zipName = "PC-Doctor-Lite-v1.0.zip"
if (Test-Path $zipName) { Remove-Item $zipName -Force }
Compress-Archive -Path "$releaseDir\*" -DestinationPath $zipName -Force

Write-Host ""
Write-Host "✅ Build complete!" -ForegroundColor Green
Write-Host "📁 Output: $zipName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Download BlueScreenView → put in tools\" 
Write-Host "  2. Download CrystalDiskInfo portable → put in tools\"
Write-Host "  3. Test by double-clicking PC-Doctor-Lite.exe"
Write-Host ""
