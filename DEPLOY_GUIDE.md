# Mac开发 -> Windows EXE 部署指南

## 🎯 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **GitHub Actions** | 免费、自动化、可靠 | 需要GitHub仓库 | ⭐⭐⭐⭐⭐ |
| Docker + Wine | 本地构建 | 复杂、不稳定 | ⭐⭐ |
| 虚拟机 | 完全兼容 | 资源消耗大 | ⭐⭐⭐ |
| 交叉编译 | 快速 | 兼容性问题 | ⭐⭐ |

## 🚀 推荐方案：GitHub Actions（已配置）

### 使用步骤：

1. **推送代码到GitHub**：
   ```bash
   git add .
   git commit -m "添加DNF自动刷图工具"
   git push origin main
   ```

2. **自动构建**：
   - GitHub会自动在Windows环境中构建
   - 完成后在Actions页面下载exe文件

3. **手动触发构建**：
   - 进入GitHub仓库
   - 点击 Actions -> Build Windows EXE -> Run workflow

4. **创建发布版本**：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   - 会自动创建Release并包含完整的zip包

## 🐳 备选方案一：Docker + Wine

创建Dockerfile：
```dockerfile
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip wine xvfb

WORKDIR /app
COPY . .

RUN pip3 install -r requirements.txt
RUN pip3 install -r build_requirements.txt

CMD ["python3", "-m", "PyInstaller", "--onefile", "dnf_bot.py"]
```

使用方法：
```bash
docker build -t dnf-builder .
docker run -v $(pwd)/dist:/app/dist dnf-builder
```

## 💻 备选方案二：虚拟机

### 1. 安装虚拟机软件
- **VMware Fusion** (推荐，性能好)
- **Parallels Desktop** (Mac优化好)
- **VirtualBox** (免费)

### 2. 安装Windows虚拟机
```bash
# 下载Windows 11 ISO
# 在虚拟机中安装Python和依赖
# 共享Mac文件夹到虚拟机
```

### 3. 在虚拟机中打包
```cmd
pip install -r requirements.txt
pip install -r build_requirements.txt
pyinstaller --onefile --console --name "DNF自动刷图" dnf_bot.py
```

## 📦 方案三：使用构建服务

### 1. AppVeyor（免费CI/CD）
```yaml
# appveyor.yml
version: 1.0.{build}
image: Visual Studio 2019
platform: x64

install:
  - python -m pip install --upgrade pip
  - pip install -r requirements.txt
  - pip install -r build_requirements.txt

build_script:
  - pyinstaller --onefile dnf_bot.py

artifacts:
  - path: dist\*.exe
```

### 2. 本地交叉编译（实验性）
```bash
# 安装CrossEnv
pip install crossenv

# 创建Windows环境
python -m crossenv /path/to/windows/python venv-cross
source venv-cross/bin/activate
cross-pip install pyinstaller

# 构建（可能有兼容性问题）
cross-pyinstaller --onefile dnf_bot.py
```

## 🎯 最佳实践

### 推荐工作流程：

1. **在Mac上开发**：
   ```bash
   # 正常开发和测试
   python dnf_bot.py
   ```

2. **推送到GitHub**：
   ```bash
   git add .
   git commit -m "更新功能"
   git push
   ```

3. **自动构建Windows版本**：
   - GitHub Actions自动触发
   - 5-10分钟后下载exe

4. **传输到Windows电脑**：
   - 直接从GitHub下载
   - 或通过网盘、邮件等方式

### 开发技巧：

```bash
# 创建开发脚本
echo '#!/bin/bash
git add .
git commit -m "自动提交: $(date)"
git push
echo "已推送，等待GitHub Actions构建..."' > deploy.sh

chmod +x deploy.sh
./deploy.sh
```

## 🔧 自动化脚本

创建一键部署脚本：

```bash
#!/bin/bash
# auto-deploy.sh

echo "🚀 开始自动部署..."

# 检查是否有未提交的更改
if [[ -n $(git status -s) ]]; then
    echo "📝 发现更改，正在提交..."
    git add .
    git commit -m "Auto deploy: $(date '+%Y-%m-%d %H:%M:%S')"
fi

# 推送到GitHub
echo "📤 推送到GitHub..."
git push origin main

echo "✅ 部署完成！"
echo "🔗 请访问 GitHub Actions 查看构建进度："
echo "   https://github.com/你的用户名/仓库名/actions"
echo ""
echo "⏱️  预计5-10分钟后可下载Windows exe文件"
```

这样您就可以在Mac上愉快地开发，然后自动生成Windows版本的exe文件了！
