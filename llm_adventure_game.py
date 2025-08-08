import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading
import queue
import json
import markdown2
from tk_html_widgets import HTMLLabel
import dashscope
from dashscope import Generation

class LLMAdventureGame:
    """
    一个基于大语言模型的文字冒险游戏GUI应用。
    """
    def __init__(self, master):
        self.master = master
        self.master.title("大语言模型文字冒险游戏 (主用：阿里云百炼)")
        self.master.geometry("1000x800")
        self.master.configure(bg="#f0f0f0")

        # --- 游戏状态变量 ---
        self.story_history = ""  # 存储完整的故事历史，作为AI的记忆
        self.last_player_choice = "" # 存储玩家上一次的选择，用于重试

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

        self.start_button = tk.Button(setup_frame, text="开始 / 重置游戏", command=self.start_game, font=("Helvetica", 10, "bold"), bg="#4CAF50", fg="white", relief=tk.FLAT, padx=10, pady=5)
        self.start_button.grid(row=2, column=1, sticky="e", padx=5, pady=10)

        # --- 2. 故事显示区域 ---
        story_frame = tk.LabelFrame(main_frame, text="故事进展", padx=10, pady=10, bg="#f0f0f0", font=("Helvetica", 12))
        story_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.story_display = HTMLLabel(story_frame, background="white", padx=10, pady=10)
        self.story_display.pack(fill=tk.BOTH, expand=True)
        self.story_display.set_html("<p style='font-family: sans-serif; font-style: italic; color: #555;'>请先设置好API-KEY和故事背景，然后点击\"开始游戏\"。</p>")

        # --- 3. 玩家选项区域 ---
        options_frame = tk.LabelFrame(main_frame, text="你的选择", padx=10, pady=10, bg="#f0f0f0", font=("Helvetica", 12))
        options_frame.pack(fill=tk.X)
        
        self.option_buttons = []
        for i in range(4):
            button = tk.Button(options_frame, text=f"选项 {i+1}", state=tk.DISABLED, wraplength=220, justify=tk.LEFT, font=("Helvetica", 10), bg="#2196F3", fg="white", relief=tk.FLAT, padx=8, pady=8)
            button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
            self.option_buttons.append(button)

    def start_game(self):
        """当玩家点击"开始/重置游戏"时触发。"""
        api_key = self.api_key_entry.get().strip()
        story_bg = self.story_bg_text.get("1.0", tk.END).strip()

        if not api_key or not story_bg:
            messagebox.showerror("错误", "API-KEY 和 故事背景 不能为空！")
            return

        dashscope.api_key = api_key

        self.story_history = f"## 故事背景\n\n{story_bg}\n\n"
        self.update_story_display("游戏初始化中，正在为您生成开篇情节...")
        self.toggle_controls(is_generating=True)

        self.generate_next_segment(initial_prompt=self.story_history)

    def make_choice(self, choice_index):
        """当玩家点击一个选项按钮时触发。"""
        chosen_option_text = self.option_buttons[choice_index].cget('text')
        self.last_player_choice = chosen_option_text # 记录选择，以备重试
        
        self.story_history += f"\n\n**我的选择是：** *{chosen_option_text}*\n\n---\n\n"
        
        self.update_story_display(f"你选择了：'{chosen_option_text}'。AI正在思考接下来会发生什么...")
        self.toggle_controls(is_generating=True)

        self.generate_next_segment(player_choice=chosen_option_text)

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
例如：
{
  "story": "你环顾四周，发现自己身处一片奇异的荧光森林中。高大的蘑菇状植物散发着柔和的蓝光，空气中弥漫着泥土和花蜜的混合气息。不远处传来潺潺的水声，而另一边则似乎有某种生物在低吼。",
  "options": [
    "走向发出水声的地方，寻找水源。",
    "小心翼翼地朝着低吼声的方向前进，探明究竟。",
    "检查最近的荧光植物，看看是否能分析出其成分。",
    "回到坠毁的飞船残骸，看看能否找到可用的工具。"
  ]
}
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
        # 提供一个重试选项
        for btn in self.option_buttons:
            btn.config(state=tk.DISABLED, text="")
        retry_button = self.option_buttons[0]
        retry_button.config(
            text="出错了，点击重试刚刚的选择", 
            state=tk.NORMAL,
            command=self.retry_last_action
        )

    def retry_last_action(self):
        """让玩家可以重试上一次失败的请求。"""
        self.update_story_display("正在重试...")
        self.toggle_controls(is_generating=True)
        self.generate_next_segment(player_choice=self.last_player_choice)

    def process_llm_response(self, text_response):
        """解析LLM返回的JSON，并更新UI。"""
        try:
            # 尝试从可能包含额外文本的响应中提取JSON
            json_start = text_response.find('{')
            json_end = text_response.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                raise json.JSONDecodeError("未在响应中找到有效的JSON对象。", text_response, 0)
            
            json_str = text_response[json_start:json_end]
            data = json.loads(json_str)

            new_story_part = data['story']
            options = data['options']

            if not isinstance(new_story_part, str) or not (isinstance(options, list) and len(options) == 4):
                raise ValueError("JSON格式不正确，缺少'story'或'options'键，或'options'非4元素列表。")

            self.story_history += new_story_part
            self.update_story_display()
            for i, option_text in enumerate(options):
                self.option_buttons[i].config(text=option_text, command=lambda i=i: self.make_choice(i))
            
            self.toggle_controls(is_generating=False)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            messagebox.showwarning("解析错误", f"AI返回的数据格式不规范，无法解析。\n错误: {e}\n\n将显示原始文本。")
            self.story_history += f"\n\n---\n\n**[系统警告：AI响应格式错误，以下为原始输出]**\n\n```\n{text_response}\n```"
            self.update_story_display()
            self.toggle_controls(is_generating=False)

    def update_story_display(self, loading_text=None):
        """更新故事显示区域，将Markdown转换为HTML并渲染。"""
        if loading_text:
            content = f"<h2 style='font-family: sans-serif; color: #333;'>{loading_text}</h2>"
        else:
            html_content = markdown2.markdown(self.story_history, extras=["fenced-code-blocks", "tables", "spoiler"])
            content = f"""
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.7; color: #333; }}
                h1, h2, h3 {{ color: #000; border-bottom: 1px solid #eee; padding-bottom: 5px;}}
                p {{ margin-bottom: 1em; }}
                i {{ color: #555; }}
                b, strong {{ color: #000; }}
                hr {{ border: 0; border-top: 2px solid #eee; margin: 2em 0; }}
                code {{ background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: "Courier New", Courier, monospace;}}
                pre > code {{ display: block; padding: 10px; border-radius: 5px;}}
            </style>
            {html_content}
            """
        
        self.story_display.set_html(content)
        # 使用JS滚动到底部，确保最新内容可见
        self.story_display.page.run_javascript("window.scrollTo(0, document.body.scrollHeight);")

    def toggle_controls(self, is_generating):
        """切换控件的可用状态，提供视觉反馈。"""
        state = tk.DISABLED if is_generating else tk.NORMAL
        for btn in self.option_buttons:
            btn.config(state=state)
        
        self.start_button.config(state=state)
        if is_generating:
            self.master.config(cursor="watch")
        else:
            self.master.config(cursor="")

if __name__ == "__main__":
    root = tk.Tk()
    app = LLMAdventureGame(root)
    root.mainloop() 