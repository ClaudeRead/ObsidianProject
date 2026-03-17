#!/bin/bash

echo "Obsidian 讲义生成器 - 启动脚本"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.6或更高版本"
    exit 1
fi

# 检查是否在虚拟环境中
echo "正在检查依赖..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "依赖安装失败"
        exit 1
    fi
fi

# 运行应用
echo "启动Obsidian讲义生成器..."
echo "Obsidian仓库路径: obsidian_repo"
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""

python3 app.py