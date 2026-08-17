# PC-Doctor-Lite 上传 GitHub + 自动打包指南

## 一、在 GitHub 上新建仓库

1. 打开 https://github.com/new
2. Repository name 填：`PC-Doctor-Lite`
3. 选 **Public**
4. **不要**勾选 "Add a README file"
5. 点 **Create repository**

## 二、把文件上传到 GitHub

### 方式 A：网页拖拽（最简单）

1. 打开你刚建的仓库页面
2. 点 **Add file → Upload files**
3. 把 `PC-Doctor-Lite` 文件夹里的**所有文件和文件夹**拖进去
4. Commit message 写 `Initial commit`
5. 点 **Commit changes**

### 方式 B：用 GitHub Desktop

1. 下载 https://desktop.github.com/ 并登录
2. File → Clone repository → 选你的 PC-Doctor-Lite
3. 把文件拷进本地仓库文件夹
4. 点 Commit → Push

### 方式 C：命令行

```bash
cd PC-Doctor-Lite
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/PC-Doctor-Lite.git
git push -u origin main
```

## 三、触发自动打包

1. 上传完文件后，进仓库页面
2. 点顶部 **Actions** 标签
3. 左侧选 **Build PC-Doctor-Lite EXE**
4. 点 **Run workflow** → 选 main 分支 → 点绿色 **Run workflow**
5. 等待 3~5 分钟

## 四、下载 exe

1. 构建完成后，页面显示绿色 ✅
2. 往下滚，右侧 **Artifacts** 区域出现 `PC-Doctor-Lite-EXE`
3. 点它下载 zip 包
4. 解压后就是 `PC-Doctor-Lite.exe` + 说明书 + 工具包

## 五、验证 exe

在一台 Windows 电脑上：
1. 解压 zip
2. 右键 `PC-Doctor-Lite.exe` → **以管理员身份运行**
3. 等待 10~30 秒，自动弹出 HTML 体检报告
4. 检查报告内容是否完整

## 六、上传后顺便做的事

- 在仓库页面点 ⭐ Star
- 仓库描述写：`A clean, local-only PC health check tool that generates an HTML report.`
- 加 Topic 标签：`pc-diagnostics` `system-info` `hardware-monitor`
