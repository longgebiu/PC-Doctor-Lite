# PC-Doctor-Lite

> 一个不想当管家的电脑体检工具。纯本地运行，不联网、不弹窗、不捆绑。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE-THIRDPARTY.txt)

## ✨ 功能

- 🖥️ **硬件配置清单**：CPU / 内存 / 显卡 / 硬盘
- 🌡️ **实时温度监控**：CPU / 主板 / GPU，超温自动标红
- 💾 **磁盘空间检测**：带可视化进度条
- 🛡️ **蓝屏记录分析**：最近 5 次 dump 文件
- 📄 **HTML 报告生成**：双击即用，浏览器打开，可保存/打印

## 🚀 快速开始

### 方式一：GitHub Actions 自动打包（推荐）

详见 [README-UPLOAD.md](README-UPLOAD.md)

1. Fork / 上传到你的 GitHub 仓库
2. 点 **Actions** → **Build PC-Doctor-Lite EXE** → **Run workflow**
3. 等待 3~5 分钟，下载 Artifact 中的 zip

### 方式二：本地打包（需 Windows）

```cmd
build.bat
```

依赖：Python 3.10+ / pip / PowerShell

## 📋 使用方式

1. 右键 `PC-Doctor-Lite.exe` → **以管理员身份运行**
2. 等待 10~30 秒
3. 自动弹出 HTML 体检报告

## 📁 项目结构

```
PC-Doctor-Lite/
├── .github/workflows/build.yml   # GitHub Actions 自动打包
├── source/pc_doctor_lite.py     # 主程序（Python）
├── report-template/              # HTML 报告模板
├── tools/                       # 第三方工具（需手动下载）
├── README.txt                    # 用户使用说明
├── README-UPLOAD.md             # GitHub 上传指南
├── LICENSE-THIRDPARTY.txt       # 第三方许可证
├── 蓝屏代码速查表.md          # 附赠：12 个蓝屏代码人话版
├── 闲鱼上架文案.txt           # 闲鱼标题+主图+详情页
├── build.bat                    # Windows 一键打包
└── 项目结构.txt                # 目录说明
```

## ⚠️ 说明

- 本工具仅用于个人电脑健康检查
- 集成工具版权归原作者所有（详见 LICENSE-THIRDPARTY.txt）
- 虚拟商品，仅供个人学习使用

## 📜 许可证

主程序：闭源，仅供个人使用
第三方组件：见 LICENSE-THIRDPARTY.txt
