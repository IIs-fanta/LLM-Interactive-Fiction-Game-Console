@echo off
echo 启动大语言模型文字冒险游戏...
echo.

python llm_adventure_game.py

if %errorlevel% neq 0 (
    echo.
    echo 启动失败！请确保已安装所有依赖：
    echo install.bat
    echo.
    pause
) 