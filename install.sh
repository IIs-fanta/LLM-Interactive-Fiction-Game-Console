#!/bin/bash

echo "正在安装大语言模型文字冒险游戏依赖..."
echo

echo "检查Python版本..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误：未找到Python，请先安装Python 3.7+"
    exit 1
fi

echo
echo "正在安装依赖包..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo
    echo "安装完成！现在可以运行游戏了："
    echo "python3 llm_adventure_game.py"
else
    echo
    echo "安装失败，请检查网络连接或手动安装依赖"
fi

echo 