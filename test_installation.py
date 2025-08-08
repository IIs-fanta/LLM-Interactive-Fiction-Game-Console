#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证大语言模型文字冒险游戏的依赖安装
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """测试模块导入"""
    try:
        importlib.import_module(module_name)
        print(f"✓ {package_name or module_name} 导入成功")
        return True
    except ImportError as e:
        print(f"✗ {package_name or module_name} 导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("大语言模型文字冒险游戏 - 依赖测试")
    print("=" * 50)
    print()
    
    # 测试Python版本
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 7:
        print(f"✓ Python版本 {python_version.major}.{python_version.minor}.{python_version.micro} 符合要求")
    else:
        print(f"✗ Python版本 {python_version.major}.{python_version.minor}.{python_version.micro} 不符合要求（需要3.7+）")
        return False
    
    print()
    
    # 测试必需模块
    required_modules = [
        ('tkinter', 'Tkinter'),
        ('dashscope', 'DashScope'),
        ('tk_html_widgets', 'tk_html_widgets'),
        ('markdown2', 'markdown2'),
        ('threading', 'Threading'),
        ('queue', 'Queue'),
        ('json', 'JSON'),
    ]
    
    all_passed = True
    for module_name, display_name in required_modules:
        if not test_import(module_name, display_name):
            all_passed = False
    
    print()
    print("=" * 50)
    
    if all_passed:
        print("🎉 所有依赖测试通过！可以运行游戏了。")
        print("运行命令：python llm_adventure_game.py")
        return True
    else:
        print("❌ 部分依赖测试失败，请安装缺失的依赖：")
        print("Windows: install.bat")
        print("Linux/macOS: ./install.sh")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 