#!/bin/bash

echo "🚀 DNF自动刷图工具 - 自动部署脚本"
echo "================================"

# 检查是否在git仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ 错误: 当前目录不是git仓库"
    echo "请先运行: ./setup_repo.sh 初始化仓库"
    exit 1
fi

# 检查是否有GitHub remote
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "❌ 错误: 没有配置GitHub远程仓库"
    echo "请先运行: ./setup_repo.sh 初始化仓库"
    exit 1
fi

# 检查是否有未提交的更改
if [[ -n $(git status -s) ]]; then
    echo "📝 发现未提交的更改，正在提交..."
    git add .
    
    # 获取提交信息
    read -p "请输入提交信息 (默认: Auto deploy $(date '+%Y-%m-%d %H:%M:%S')): " commit_msg
    if [[ -z "$commit_msg" ]]; then
        commit_msg="Auto deploy $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    git commit -m "$commit_msg"
    echo "✅ 已提交更改"
else
    echo "ℹ️  没有未提交的更改"
fi

# 推送到GitHub
echo "📤 正在推送到GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ 推送成功！"
    
    # 获取仓库信息
    remote_url=$(git remote get-url origin)
    repo_url=${remote_url%.git}
    repo_url=${repo_url/git@github.com:/https://github.com/}
    
    echo ""
    echo "🔗 GitHub Actions构建链接:"
    echo "   https://github.com/lllanlll/dnf_automate/actions"
    echo ""
    echo "⏱️  预计5-10分钟后可下载Windows exe文件"
    echo "📥 下载地址: https://github.com/lllanlll/dnf_automate/actions (点击最新的workflow run)"
    echo ""
    echo "💡 提示: 也可以创建release版本获得更好的下载体验:"
    echo "   git tag v1.0.0 && git push origin v1.0.0"
    
else
    echo "❌ 推送失败，请检查网络连接和仓库权限"
    exit 1
fi
