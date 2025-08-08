# 游戏配置文件示例
# 复制此文件为 config.py 并根据需要修改

# AI模型配置
AI_MODEL = 'qwen-max'  # 可选: 'qwen-max', 'qwen-plus', 'qwen-turbo'

# 游戏界面配置
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
WINDOW_TITLE = "大语言模型文字冒险游戏"

# 默认故事背景
DEFAULT_STORY_BACKGROUND = """
你是一位经验丰富的星际探险家，驾驶着名为"晨星号"的飞船。
在一次穿越未知星系时，飞船的能量核心突然发生故障，你被迫紧急降落在一颗代号为X-17的陌生星球上。
飞船的扫描显示，这颗星球的大气可以呼吸，但充满了未知的能量读数。
你的任务是：找到修复飞船的方法，或者寻找一线生机。
"""

# AI提示词配置
SYSTEM_PROMPT = """
你是一位才华横溢、充满想象力的文字冒险游戏AI。你的任务是：
1. 根据玩家的选择和已有的故事，生成一段生动、具体的后续情节（大约150-250字）。
2. 在情节的结尾，为玩家提供四个风格迥异、导向完全不同剧情分支的行动选项。
3. 你的回答必须是严格的JSON格式，包含两个键：'story'（字符串，包含新生成的故事，请使用Markdown语法来丰富表现力）和'options'（一个包含四个字符串的列表）。
"""

# 界面样式配置
COLORS = {
    'background': '#f0f0f0',
    'button_primary': '#4CAF50',
    'button_secondary': '#2196F3',
    'text_primary': '#333333',
    'text_secondary': '#555555'
}

# 字体配置
FONTS = {
    'title': ('Helvetica', 12, 'bold'),
    'body': ('Helvetica', 10),
    'button': ('Helvetica', 10, 'bold')
}

# 游戏设置
GAME_SETTINGS = {
    'max_story_length': 10000,  # 故事历史最大长度（字符数）
    'queue_check_interval': 100,  # 队列检查间隔（毫秒）
    'enable_auto_scroll': True,  # 是否自动滚动到最新内容
    'enable_retry_on_error': True,  # 是否在错误时提供重试选项
} 