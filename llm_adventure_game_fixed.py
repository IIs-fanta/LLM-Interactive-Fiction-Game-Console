import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading
import queue
import json
import markdown2
import dashscope
from dashscope import Generation
import re

class LLMAdventureGame:
    """
    一个基于大语言模型的文字冒险游戏GUI应用（修复版）。
    使用数字输入选择选项，更可靠的AI响应解析。
    """
    def __init__(self, master):
        self.master = master
        self.master.title("大语言模型文字冒险游戏 (修复版)")
        self.master.geometry("1000x800")
        self.master.configure(bg="#f0f0f0")

        # --- 游戏状态变量 ---
        self.story_history = ""  # 存储完整的故事历史，作为AI的记忆
        self.last_player_choice = "" # 存储玩家上一次的选择，用于重试
        self.current_options = [] # 存储当前可用的选项
        self.last_ai_response = "" # 存储AI的原始响应，用于调试

        # --- 异步处理队列 ---
        self.llm_queue = queue.Queue()

        # --- 创建UI界面 ---
        self.setup_ui()
        
        # --- 启动队列检查循环 ---
        self.master.after(100, self.check_llm_queue)

    def setup_ui(self):
        """初始化并布局所有UI组件。"""
        main_frame = tk.Frame(self.master, padx=10, pady=10, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 1. 设置区域 ---
        setup_frame = tk.LabelFrame(main_frame, text="游戏设置", padx=10, pady=10, bg="#f0f0f0", font=("Helvetica", 12))
        setup_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(setup_frame, text="阿里云API-KEY:", bg="#f0f0f0", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.api_key_entry = tk.Entry(setup_frame, width=50, show="*", font=("Helvetica", 10))
        self.api_key_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(setup_frame, text="故事背景设定:", bg="#f0f0f0", font=("Helvetica", 10)).grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self.story_bg_text = scrolledtext.ScrolledText(setup_frame, height=5, wrap=tk.WORD, font=("Helvetica", 10))
        self.story_bg_text.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.story_bg_text.insert(tk.END, "你是一位经验丰富的星际探险家，驾驶着名为\"晨星号\"的飞船。在一次穿越未知星系时，飞船的能量核心突然发生故障，你被迫紧急降落在一颗代号为X-17的陌生星球上。飞船的扫描显示，这颗星球的大气可以呼吸，但充满了未知的能量读数。你的任务是：找到修复飞船的方法，或者寻找一线生机。")
        
        setup_frame.columnconfigure(1, weight=1)

        # 按钮区域
        button_frame = tk.Frame(setup_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.start_button = tk.Button(button_frame, text="开始 / 重置游戏", command=self.start_game, font=("Helvetica", 10, "bold"), bg="#4CAF50", fg="white", relief=tk.FLAT, padx=10, pady=5)
        self.start_button.pack(side=tk.RIGHT, padx=5)
        
        self.debug_button = tk.Button(button_frame, text="显示AI原始响应", command=self.show_debug_info, font=("Helvetica", 10), bg="#FF9800", fg="white", relief=tk.FLAT, padx=10, pady=5)
        self.debug_button.pack(side=tk.RIGHT, padx=5)

        # --- 2. 故事显示区域 ---
        story_frame = tk.LabelFrame(main_frame, text="故事进展", padx=10, pady=10, bg="#f0f0f0", font=("Helvetica", 12))
        story_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.story_display = scrolledtext.ScrolledText(story_frame, wrap=tk.WORD, font=("Helvetica", 11), bg="white", fg="#333")
        self.story_display.pack(fill=tk.BOTH, expand=True)
        self.story_display.insert(tk.END, "请先设置好API-KEY和故事背景，然后点击\"开始游戏\"。\n\n")

        # --- 3. 选项显示区域 ---
        options_frame = tk.LabelFrame(main_frame, text="当前选项", padx=10, pady=10, bg="#f0f0f0", font=("Helvetica", 12))
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.options_display = scrolledtext.ScrolledText(options_frame, height=8, wrap=tk.WORD, font=("Helvetica", 10), bg="#f8f9fa", fg="#333")
        self.options_display.pack(fill=tk.BOTH, expand=True)
        self.options_display.insert(tk.END, "选项将在这里显示...\n")

        # --- 4. 选择输入区域 ---
        choice_frame = tk.LabelFrame(main_frame, text="你的选择", padx=10, pady=10, bg="#f0f0f0", font=("Helvetica", 12))
        choice_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(choice_frame, text="请输入选项编号 (1-4):", bg="#f0f0f0", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        
        self.choice_entry = tk.Entry(choice_frame, width=10, font=("Helvetica", 12), justify=tk.CENTER)
        self.choice_entry.pack(side=tk.LEFT, padx=5)
        self.choice_entry.bind('<Return>', self.submit_choice)
        
        self.submit_button = tk.Button(choice_frame, text="确认选择", command=self.submit_choice, font=("Helvetica", 10), bg="#2196F3", fg="white", relief=tk.FLAT, padx=10, pady=5)
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        # 禁用选择输入，直到游戏开始
        self.choice_entry.config(state=tk.DISABLED)
        self.submit_button.config(state=tk.DISABLED)

    def start_game(self):
        """当玩家点击"开始/重置游戏"时触发。"""
        api_key = self.api_key_entry.get().strip()
        story_bg = self.story_bg_text.get("1.0", tk.END).strip()

        if not api_key or not story_bg:
            messagebox.showerror("错误", "API-KEY 和 故事背景 不能为空！")
            return

        dashscope.api_key = api_key

        self.story_history = f"## 故事背景\n\n{story_bg}\n\n"
        self.current_options = []
        self.update_story_display("游戏初始化中，正在为您生成开篇情节...")
        self.toggle_controls(is_generating=True)

        self.generate_next_segment(initial_prompt=self.story_history)

    def submit_choice(self, event=None):
        """处理玩家的选择输入。"""
        try:
            choice_text = self.choice_entry.get().strip()
            if not choice_text:
                messagebox.showwarning("警告", "请输入选项编号！")
                return
            
            choice_num = int(choice_text)
            if choice_num < 1 or choice_num > 4:
                messagebox.showwarning("警告", "请输入1-4之间的数字！")
                return
            
            if choice_num > len(self.current_options):
                messagebox.showwarning("警告", f"当前只有{len(self.current_options)}个选项！")
                return
            
            # 获取选择的选项文本
            chosen_option = self.current_options[choice_num - 1]
            self.make_choice(chosen_option)
            
            # 清空输入框
            self.choice_entry.delete(0, tk.END)
            
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的数字！")

    def make_choice(self, chosen_option):
        """处理玩家的选择。"""
        self.last_player_choice = chosen_option # 记录选择，以备重试
        
        self.story_history += f"\n\n**我的选择是：** *{chosen_option}*\n\n---\n\n"
        
        self.update_story_display(f"你选择了：'{chosen_option}'。AI正在思考接下来会发生什么...")
        self.toggle_controls(is_generating=True)

        self.generate_next_segment(player_choice=chosen_option)

    def generate_next_segment(self, initial_prompt=None, player_choice=None):
        """准备prompt并开启线程调用LLM。"""
        if initial_prompt:
            prompt = f"这是文字冒险游戏的开篇，请根据以下背景，生成第一段引人入胜的故事情节和四个截然不同的行动选项。故事背景：\n\n{initial_prompt}"
        else:
            # 这就是核心：将整个故事历史作为"精简的全篇故事走向"发给AI
            prompt = f"""
以下是目前为止的完整故事情节（这是我们的记忆）：
---
{self.story_history}
---
玩家刚刚做出的选择是："{player_choice}"

请基于以上所有内容，继续推进故事，并提供四个新的、截然不同的行动选项。
"""

        system_prompt = """
你是一位才华横溢、充满想象力的文字冒险游戏AI。你的任务是：
1. 根据玩家的选择和已有的故事，生成一段生动、具体的后续情节（大约150-250字）。
2. 在情节的结尾，为玩家提供四个风格迥异、导向完全不同剧情分支的行动选项。
3. 你的回答必须是严格的JSON格式，包含两个键：'story'（字符串，包含新生成的故事，请使用Markdown语法来丰富表现力）和'options'（一个包含四个字符串的列表）。

重要：你的回答必须是一个有效的JSON对象，不能包含任何其他文本。不要添加解释、注释或其他内容。

示例格式：
{
  "story": "你环顾四周，发现自己身处一片奇异的荧光森林中。高大的蘑菇状植物散发着柔和的蓝光，空气中弥漫着泥土和花蜜的混合气息。不远处传来潺潺的水声，而另一边则似乎有某种生物在低吼。",
  "options": [
    "走向发出水声的地方，寻找水源。",
    "小心翼翼地朝着低吼声的方向前进，探明究竟。",
    "检查最近的荧光植物，看看是否能分析出其成分。",
    "回到坠毁的飞船残骸，看看能否找到可用的工具。"
  ]
}

请严格按照这个格式返回JSON，不要添加任何其他内容。
"""
        
        threading.Thread(target=self._call_llm_in_thread, args=(system_prompt, prompt), daemon=True).start()

    def _call_llm_in_thread(self, system_prompt, user_prompt):
        """在后台线程中实际调用API，防止UI卡死。"""
        try:
            # 推荐使用qwen-max或qwen-plus模型以获得更好的故事创作能力
            response = Generation.call(
                model='qwen-max',
                system_prompt=system_prompt,
                prompt=user_prompt,
                result_format='text' # 我们要求它返回纯文本（JSON字符串）
            )
            self.llm_queue.put(response)
        except Exception as e:
            self.llm_queue.put({"error": str(e)})

    def check_llm_queue(self):
        """每100ms检查一次队列，看是否有LLM的返回结果。"""
        try:
            response_data = self.llm_queue.get_nowait()
            
            if "error" in response_data:
                self.handle_api_error(response_data['error'])
            elif response_data.status_code == 200:
                self.process_llm_response(response_data.output.text)
            else:
                error_msg = f"API请求失败\n状态码: {response_data.status_code}\n信息: {response_data.message}"
                self.handle_api_error(error_msg)

        except queue.Empty:
            pass # 队列为空，什么都不做
        finally:
            self.master.after(100, self.check_llm_queue)
    
    def handle_api_error(self, error_message):
        """统一处理API调用失败的情况。"""
        messagebox.showerror("API 调用失败", f"与AI通信时发生错误：\n{error_message}")
        self.toggle_controls(is_generating=False)

    def retry_last_action(self):
        """让玩家可以重试上一次失败的请求。"""
        self.update_story_display("正在重试...")
        self.toggle_controls(is_generating=True)
        self.generate_next_segment(player_choice=self.last_player_choice)

    def process_llm_response(self, text_response):
        """解析LLM返回的JSON，并更新UI。"""
        # 保存AI的原始响应用于调试
        self.last_ai_response = text_response
        
        try:
            # 使用新的解析器
            data = self.parse_ai_response(text_response)
            
            new_story_part = data['story']
            options = data['options']

            # 更新故事历史
            self.story_history += new_story_part
            
            # 更新显示
            self.update_story_display()
            
            # 更新选项
            self.current_options = options
            self.update_options_display()
            
            self.toggle_controls(is_generating=False)

        except Exception as e:
            # 改进的错误处理
            error_msg = f"AI返回的数据格式不规范，无法解析。\n错误: {e}\n\n原始响应:\n{text_response}"
            messagebox.showwarning("解析错误", error_msg)
            
            # 将原始响应添加到故事历史中
            self.story_history += f"\n\n---\n\n**[系统警告：AI响应格式错误，以下为原始输出]**\n\n{text_response}\n\n"
            self.update_story_display()
            
            # 清空选项
            self.current_options = []
            self.update_options_display()
            
            self.toggle_controls(is_generating=False)

    def update_story_display(self, loading_text=None):
        """更新故事显示区域，将Markdown转换为纯文本显示。"""
        if loading_text:
            self.story_display.delete(1.0, tk.END)
            self.story_display.insert(tk.END, f"{loading_text}\n\n")
        else:
            # 将Markdown转换为纯文本显示
            try:
                # 简单的Markdown到纯文本转换
                text_content = self.story_history
                # 移除Markdown标记
                text_content = text_content.replace('**', '').replace('*', '').replace('#', '').replace('---', '\n---\n')
                self.story_display.delete(1.0, tk.END)
                self.story_display.insert(tk.END, text_content)
            except Exception as e:
                # 如果转换失败，直接显示原始内容
                self.story_display.delete(1.0, tk.END)
                self.story_display.insert(tk.END, self.story_history)
        
        # 滚动到底部
        self.story_display.see(tk.END)

    def update_options_display(self):
        """更新选项显示区域。"""
        self.options_display.delete(1.0, tk.END)
        
        if not self.current_options:
            self.options_display.insert(tk.END, "暂无可用选项...\n")
            return
        
        for i, option in enumerate(self.current_options, 1):
            self.options_display.insert(tk.END, f"{i}. {option}\n")
        
        self.options_display.see(tk.END)

    def toggle_controls(self, is_generating):
        """切换控件的可用状态，提供视觉反馈。"""
        if is_generating:
            self.choice_entry.config(state=tk.DISABLED)
            self.submit_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            self.master.config(cursor="watch")
        else:
            self.choice_entry.config(state=tk.NORMAL)
            self.submit_button.config(state=tk.NORMAL)
            self.start_button.config(state=tk.NORMAL)
            self.master.config(cursor="")
            # 聚焦到输入框
            self.choice_entry.focus()

    def show_debug_info(self):
        """显示AI的原始响应，以便调试。"""
        if self.last_ai_response:
            messagebox.showinfo("AI原始响应", f"AI的原始响应:\n\n{self.last_ai_response}")
        else:
            messagebox.showwarning("AI原始响应", "没有可显示的AI原始响应。")

    def parse_ai_response(self, text_response):
        """更强大的AI响应解析器"""
        # 清理响应文本
        cleaned_response = text_response.strip()
        
        # 尝试多种解析方法
        methods = [
            # 方法1：直接解析
            lambda: json.loads(cleaned_response),
            
            # 方法2：提取JSON部分
            lambda: self._extract_json_part(cleaned_response),
            
            # 方法3：修复常见的JSON格式问题
            lambda: self._fix_and_parse_json(cleaned_response),
            
            # 方法4：尝试解析为Python字典格式
            lambda: self._parse_python_dict(cleaned_response)
        ]
        
        for i, method in enumerate(methods):
            try:
                data = method()
                if self._validate_response_data(data):
                    return data
            except Exception as e:
                print(f"解析方法{i+1}失败: {e}")
                continue
        
        raise ValueError("所有解析方法都失败了")

    def _extract_json_part(self, text):
        """提取文本中的JSON部分"""
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("未找到JSON对象")
        
        json_str = text[json_start:json_end]
        return json.loads(json_str)

    def _fix_and_parse_json(self, text):
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
            return self._extract_json_part(text)

    def _parse_python_dict(self, text):
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

    def _validate_response_data(self, data):
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

if __name__ == "__main__":
    root = tk.Tk()
    app = LLMAdventureGame(root)
    root.mainloop() 