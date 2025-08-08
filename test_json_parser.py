#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON解析器功能
"""

import json
import re

def parse_ai_response(text_response):
    """更强大的AI响应解析器"""
    # 清理响应文本
    cleaned_response = text_response.strip()
    
    # 尝试多种解析方法
    methods = [
        # 方法1：直接解析
        lambda: json.loads(cleaned_response),
        
        # 方法2：提取JSON部分
        lambda: extract_json_part(cleaned_response),
        
        # 方法3：修复常见的JSON格式问题
        lambda: fix_and_parse_json(cleaned_response),
        
        # 方法4：尝试解析为Python字典格式
        lambda: parse_python_dict(cleaned_response)
    ]
    
    for i, method in enumerate(methods):
        try:
            data = method()
            if validate_response_data(data):
                print(f"解析方法{i+1}成功")
                return data
        except Exception as e:
            print(f"解析方法{i+1}失败: {e}")
            continue
    
    raise ValueError("所有解析方法都失败了")

def extract_json_part(text):
    """提取文本中的JSON部分"""
    json_start = text.find('{')
    json_end = text.rfind('}') + 1
    if json_start == -1 or json_end == 0:
        raise ValueError("未找到JSON对象")
    
    json_str = text[json_start:json_end]
    return json.loads(json_str)

def fix_and_parse_json(text):
    """修复常见的JSON格式问题"""
    # 移除可能的markdown代码块标记
    if text.startswith('```json'):
        text = text[7:]
    if text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    
    # 清理文本
    text = text.strip()
    
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 如果失败，尝试提取JSON部分
        return extract_json_part(text)

def parse_python_dict(text):
    """尝试解析Python字典格式"""
    # 查找类似Python字典的格式
    pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(pattern, text)
    
    if matches:
        # 尝试将Python字典转换为JSON
        dict_str = matches[0]
        # 替换单引号为双引号
        dict_str = dict_str.replace("'", '"')
        return json.loads(dict_str)
    
    raise ValueError("未找到有效的字典格式")

def validate_response_data(data):
    """验证响应数据的格式"""
    if not isinstance(data, dict):
        return False
    
    if 'story' not in data or 'options' not in data:
        return False
    
    if not isinstance(data['story'], str):
        return False
    
    if not isinstance(data['options'], list) or len(data['options']) != 4:
        return False
    
    for option in data['options']:
        if not isinstance(option, str):
            return False
    
    return True

def test_parser():
    """测试解析器"""
    test_cases = [
        # 标准JSON
        '''{
  "story": "你环顾四周，发现自己身处一片奇异的荧光森林中。",
  "options": [
    "走向发出水声的地方，寻找水源。",
    "小心翼翼地朝着低吼声的方向前进，探明究竟。",
    "检查最近的荧光植物，看看是否能分析出其成分。",
    "回到坠毁的飞船残骸，看看能否找到可用的工具。"
  ]
}''',
        
        # 带markdown代码块的JSON
        '''```json
{
  "story": "你环顾四周，发现自己身处一片奇异的荧光森林中。",
  "options": [
    "走向发出水声的地方，寻找水源。",
    "小心翼翼地朝着低吼声的方向前进，探明究竟。",
    "检查最近的荧光植物，看看是否能分析出其成分。",
    "回到坠毁的飞船残骸，看看能否找到可用的工具。"
  ]
}
```''',
        
        # Python字典格式
        '''{
  'story': '你环顾四周，发现自己身处一片奇异的荧光森林中。',
  'options': [
    '走向发出水声的地方，寻找水源。',
    '小心翼翼地朝着低吼声的方向前进，探明究竟。',
    '检查最近的荧光植物，看看是否能分析出其成分。',
    '回到坠毁的飞船残骸，看看能否找到可用的工具。'
  ]
}''',
        
        # 带额外文本的JSON
        '''这是一个AI生成的响应：

{
  "story": "你环顾四周，发现自己身处一片奇异的荧光森林中。",
  "options": [
    "走向发出水声的地方，寻找水源。",
    "小心翼翼地朝着低吼声的方向前进，探明究竟。",
    "检查最近的荧光植物，看看是否能分析出其成分。",
    "回到坠毁的飞船残骸，看看能否找到可用的工具。"
  ]
}

希望这个响应符合要求。'''
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}:")
        print("-" * 50)
        try:
            result = parse_ai_response(test_case)
            print("解析成功!")
            print(f"故事: {result['story'][:50]}...")
            print(f"选项数量: {len(result['options'])}")
            for j, option in enumerate(result['options']):
                print(f"  选项{j+1}: {option[:30]}...")
        except Exception as e:
            print(f"解析失败: {e}")

if __name__ == "__main__":
    test_parser() 