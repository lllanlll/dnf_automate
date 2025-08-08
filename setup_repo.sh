#!/bin/bash

echo "🚀 DNF自动刷图工具 - 初始化并推送到独立仓库"
echo "============================================"

# 目标仓库地址
REPO_URL="https://github.com/lllanlll/dnf_automate.git"

# 进入dnf_bot目录
cd /Users/lan/Downloads/solana_rust/dnf_bot

echo "📁 当前目录: $(pwd)"

# 检查是否已经是git仓库
if [ -d ".git" ]; then
    echo "🔄 发现现有git仓库，正在重新初始化..."
    rm -rf .git
fi

# 初始化新的git仓库
echo "🆕 初始化新的git仓库..."
git init

# 添加远程仓库
echo "🔗 添加远程仓库..."
git remote add origin $REPO_URL

# 创建.gitignore文件
echo "📝 创建.gitignore文件..."
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temporary files
*.tmp
*.temp
EOF

# 添加所有文件
echo "📦 添加项目文件..."
git add .

# 提交
echo "💾 创建初始提交..."
git commit -m "🎮 初始提交: DNF自动刷图工具

✨ 功能特性:
- 🎯 自动识别并攻击怪物
- 💎 自动拾取掉落物品  
- 🚪 自动寻找并进入传送门
- 🎮 支持自定义按键设置
- ⚡ 实时屏幕识别
- 🔧 GitHub Actions自动打包Windows EXE

📋 项目结构:
- dnf_bot.py - 主程序
- config.py - 配置文件
- requirements.txt - Python依赖
- .github/workflows/build.yml - 自动构建配置
- deploy.sh - 一键部署脚本

🚀 使用方法:
1. 运行 python dnf_bot.py
2. F1开始/暂停，F2停止
3. 或推送到GitHub自动构建Windows EXE

⚠️ 注意: 仅供学习研究使用"

# 检查远程仓库是否存在内容
echo "🔍 检查远程仓库状态..."
if git ls-remote --exit-code --heads origin main > /dev/null 2>&1; then
    echo "⚠️  远程仓库已有内容，将强制推送覆盖"
    read -p "是否继续? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "❌ 已取消操作"
        exit 1
    fi
    
    # 强制推送
    echo "📤 强制推送到GitHub..."
    git push --force --set-upstream origin main
else
    # 正常推送
    echo "📤 推送到GitHub..."
    git push --set-upstream origin main
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 成功推送到独立仓库!"
    echo ""
    echo "🔗 仓库地址: $REPO_URL"
    echo "🔗 GitHub Actions: https://github.com/lllanlll/dnf_automate/actions"
    echo ""
    echo "⏱️  GitHub Actions将自动开始构建Windows EXE"
    echo "📥 5-10分钟后可在Actions页面下载exe文件"
    echo ""
    echo "🚀 后续开发流程:"
    echo "   1. 在此目录修改代码"
    echo "   2. 运行 ./deploy.sh 推送更新" 
    echo "   3. GitHub自动构建新版本"
    
    # 更新deploy.sh脚本中的仓库地址
    echo ""
    echo "🔧 更新部署脚本..."
    
else
    echo "❌ 推送失败，请检查:"
    echo "   1. 网络连接"
    echo "   2. GitHub仓库权限" 
    echo "   3. 仓库地址是否正确"
    exit 1
fi
