@echo off
echo 正在安装大语言模型文字冒险游戏依赖（简化版）...
echo.

echo 检查Python版本...
python --version
if %errorlevel% neq 0 (
    echo 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo.
echo 正在安装依赖包...
pip install -r requirements_simple.txt

if %errorlevel% equ 0 (
    echo.
    echo 安装完成！现在可以运行游戏了：
    echo python llm_adventure_game_simple.py
) else (
    echo.
    echo 安装失败，请检查网络连接或手动安装依赖
)

echo.
pause 