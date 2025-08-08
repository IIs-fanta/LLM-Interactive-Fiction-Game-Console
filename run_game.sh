#!/bin/bash

echo "启动大语言模型文字冒险游戏..."
echo

python3 llm_adventure_game.py

if [ $? -ne 0 ]; then
    echo
    echo "启动失败！请确保已安装所有依赖："
    echo "./install.sh"
    echo
fi 