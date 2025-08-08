@echo off
echo 启动大语言模型文字冒险游戏（最终版）...
echo.

python llm_adventure_game_final.py

if %errorlevel% neq 0 (
    echo.
    echo 启动失败！请确保已安装所有依赖：
    echo install_simple.bat
    echo.
    pause
) 