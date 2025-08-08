import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading
import queue
import json
import markdown2
import dashscope
from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role
import re
import os

class LLMAdventureGame:
    """
    一个基于大语言模型的文字冒险游戏GUI应用（最终版）。
    能够处理AI返回的纯文本格式，自动提取故事和选项。
    """
    def __init__(self, master):
        self.master = master
        self.master.title("陈狗大语言模型文字冒险游戏 (最终版)")
        self.master.geometry("1200x900")
        self.master.minsize(1000, 800)
        self.master.configure(bg="#f0f0f0")

        # --- 游戏状态变量 ---
        self.story_history = ""  # 存储完整的故事历史，作为AI的记忆
        self.last_player_choice = "" # 存储玩家上一次的选择，用于重试
        self.current_options = [] # 存储当前可用的选项
        self.last_ai_response = "" # 存储AI的原始响应，用于调试
        self.current_model = "qwen-turbo"  # 当前使用的模型名称
        self.paragraph_min_chars = 300 # 段落最小字数
        self.paragraph_max_chars = 500 # 段落最大字数
        self.setup_collapsed = False  # 设置区域是否收起

        # --- 异步处理队列 ---
        self.llm_queue = queue.Queue()

        # --- 创建UI界面 ---
        self.setup_ui()
        
        # --- 启动队列检查循环 ---
        self.master.after(100, self.check_llm_queue)

    def save_config(self):
        """保存当前配置到文件。"""
        try:
            config = {
                'api_key': self.api_key_entry.get().strip(),
                'host': self.host_entry.get().strip(),
                'model': self.model_entry.get().strip(),
                'length_range': self.length_entry.get().strip(),
                'story_type': self.story_type_entry.get().strip(),
                'option_style': self.option_style_entry.get().strip(),
                'story_bg': self.story_bg_text.get("1.0", tk.END).strip()
            }
            
            with open('game_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", "配置已保存到 game_config.json 文件")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{str(e)}")

    def load_config(self):
        """从文件加载配置。"""
        try:
            if not os.path.exists('game_config.json'):
                messagebox.showwarning("警告", "没有找到配置文件 game_config.json")
                return
            
            with open('game_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 加载配置到界面
            if 'api_key' in config:
                self.api_key_entry.delete(0, tk.END)
                self.api_key_entry.insert(0, config['api_key'])
            
            if 'host' in config:
                self.host_entry.delete(0, tk.END)
                self.host_entry.insert(0, config['host'])
            
            if 'model' in config:
                self.model_entry.delete(0, tk.END)
                self.model_entry.insert(0, config['model'])
            
            if 'length_range' in config:
                self.length_entry.delete(0, tk.END)
                self.length_entry.insert(0, config['length_range'])
            
            if 'story_type' in config:
                self.story_type_entry.delete(0, tk.END)
                self.story_type_entry.insert(0, config['story_type'])
            
            if 'option_style' in config:
                self.option_style_entry.delete(0, tk.END)
                self.option_style_entry.insert(0, config['option_style'])
            
            if 'story_bg' in config:
                self.story_bg_text.delete("1.0", tk.END)
                self.story_bg_text.insert(tk.END, config['story_bg'])
            
            messagebox.showinfo("成功", "配置已从 game_config.json 文件加载")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败：{str(e)}")

    def setup_ui(self):
        """初始化并布局所有UI组件。"""
        main_frame = tk.Frame(self.master, padx=10, pady=10, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=0)
        main_frame.rowconfigure(1, weight=6)
        main_frame.rowconfigure(2, weight=2)
        main_frame.rowconfigure(3, weight=0)

        # --- 1. 设置区域 ---
        setup_frame = tk.LabelFrame(main_frame, text="游戏设置", padx=10, pady=10, bg="#f0f0f0", font=("Helvetica", 12))
        setup_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # 设置区域内容框架
        self.setup_content_frame = tk.Frame(setup_frame, bg="#f0f0f0")
        self.setup_content_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.setup_content_frame, text="API-KEY（找陈狗要）:", bg="#f0f0f0", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.api_key_entry = tk.Entry(self.setup_content_frame, width=50, show="*", font=("Helvetica", 10))
        self.api_key_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(self.setup_content_frame, text="自定义Host:", bg="#f0f0f0", font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.host_entry = tk.Entry(self.setup_content_frame, width=50, font=("Helvetica", 10))
        self.host_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.host_entry.insert(0, "https://dashscope.aliyuncs.com")  # 默认host

        tk.Label(self.setup_content_frame, text="输入模型:", bg="#f0f0f0", font=("Helvetica", 10)).grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.model_entry = tk.Entry(self.setup_content_frame, width=50, font=("Helvetica", 10))
        self.model_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.model_entry.insert(0, "qwen-turbo")  # 默认模型

        tk.Label(self.setup_content_frame, text="单段字数范围:", bg="#f0f0f0", font=("Helvetica", 10)).grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.length_entry = tk.Entry(self.setup_content_frame, width=50, font=("Helvetica", 10))
        self.length_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        self.length_entry.insert(0, "800-1000")  # 默认段落长度范围

        tk.Label(self.setup_content_frame, text="故事类型:", bg="#f0f0f0", font=("Helvetica", 10)).grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.story_type_entry = tk.Entry(self.setup_content_frame, width=50, font=("Helvetica", 10))
        self.story_type_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        self.story_type_entry.insert(0, "末世/爽文/悬疑/（自己输入）")

        tk.Label(self.setup_content_frame, text="选项风格:", bg="#f0f0f0", font=("Helvetica", 10)).grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.option_style_entry = tk.Entry(self.setup_content_frame, width=50, font=("Helvetica", 10))
        self.option_style_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=5)
        self.option_style_entry.insert(0, "爽文/激进（也是自己输入）")

        tk.Label(self.setup_content_frame, text="故事背景设定:", bg="#f0f0f0", font=("Helvetica", 10)).grid(row=6, column=0, sticky="nw", padx=5, pady=5)
        self.story_bg_text = scrolledtext.ScrolledText(self.setup_content_frame, height=5, wrap=tk.WORD, font=("Helvetica", 10))
        self.story_bg_text.grid(row=6, column=1, sticky="ew", padx=5, pady=5)
        self.story_bg_text.insert(tk.END, "（这个也自己写）")
        
        self.setup_content_frame.columnconfigure(1, weight=1)

        # 按钮区域
        button_frame = tk.Frame(setup_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # 配置管理按钮
        config_frame = tk.Frame(button_frame)
        config_frame.pack(side=tk.LEFT, padx=5)
        
        self.save_config_button = tk.Button(config_frame, text="保存配置", command=self.save_config, font=("Helvetica", 9), bg="#2196F3", fg="white", relief=tk.FLAT, padx=8, pady=3)
        self.save_config_button.pack(side=tk.LEFT, padx=2)
        
        self.load_config_button = tk.Button(config_frame, text="加载配置", command=self.load_config, font=("Helvetica", 9), bg="#FF9800", fg="white", relief=tk.FLAT, padx=8, pady=3)
        self.load_config_button.pack(side=tk.LEFT, padx=2)
        
        # 折叠按钮
        self.toggle_setup_button = tk.Button(button_frame, text="收起设置", command=self.toggle_setup, font=("Helvetica", 9), bg="#607D8B", fg="white", relief=tk.FLAT, padx=8, pady=3)
        self.toggle_setup_button.pack(side=tk.LEFT, padx=5)
        
        self.start_button = tk.Button(button_frame, text="开始 / 重置游戏", command=self.start_game, font=("Helvetica", 10, "bold"), bg="#4CAF50", fg="white", relief=tk.FLAT, padx=10, pady=5)
        self.start_button.pack(side=tk.RIGHT, padx=5)
        
        self.debug_button = tk.Button(button_frame, text="显示AI原始响应", command=self.show_debug_info, font=("Helvetica", 10), bg="#FF9800", fg="white", relief=tk.FLAT, padx=10, pady=5)
        self.debug_button.pack(side=tk.RIGHT, padx=5)

        # --- 2. 故事显示区域 ---
        story_frame = tk.LabelFrame(main_frame, text="故事进展", padx=10, pady=10, bg="#f0f0f0", font=("Helvetica", 12))
        story_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        story_frame.columnconfigure(0, weight=1)
        story_frame.rowconfigure(0, weight=1)
        
        self.story_display = scrolledtext.ScrolledText(story_frame, wrap=tk.WORD, font=("Helvetica", 11), bg="white", fg="#333")
        self.story_display.pack(fill=tk.BOTH, expand=True)
        self.story_display.insert(tk.END, "请先设置好API-KEY和故事背景，然后点击\"开始游戏\"。\n\n")

        # --- 3. 选项显示区域 ---
        options_frame = tk.LabelFrame(main_frame, text="当前选项", padx=10, pady=10, bg="#f0f0f0", font=("Helvetica", 12))
        options_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        options_frame.columnconfigure(0, weight=1)
        options_frame.rowconfigure(0, weight=1)
        
        self.options_display = scrolledtext.ScrolledText(options_frame, height=8, wrap=tk.WORD, font=("Helvetica", 10), bg="#f8f9fa", fg="#333")
        self.options_display.pack(fill=tk.BOTH, expand=True)
        self.options_display.insert(tk.END, "选项将在这里显示...\n")

        # --- 4. 选择输入区域 ---
        choice_frame = tk.LabelFrame(main_frame, text="你的选择", padx=10, pady=10, bg="#f0f0f0", font=("Helvetica", 12))
        choice_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        choice_frame.columnconfigure(0, weight=1)
        
        tk.Label(choice_frame, text="请输入选项编号 (1-4):", bg="#f0f0f0", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        
        self.choice_entry = tk.Entry(choice_frame, width=10, font=("Helvetica", 12), justify=tk.CENTER)
        self.choice_entry.pack(side=tk.LEFT, padx=5)
        self.choice_entry.bind('<Return>', self.submit_choice)
        
        self.submit_button = tk.Button(choice_frame, text="确认选择", command=self.submit_choice, font=("Helvetica", 10), bg="#2196F3", fg="white", relief=tk.FLAT, padx=10, pady=5)
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        # 禁用选择输入，直到游戏开始
        self.choice_entry.config(state=tk.DISABLED)
        self.submit_button.config(state=tk.DISABLED)

    def toggle_setup(self):
        """切换设置区域的显示状态。"""
        if self.setup_collapsed:
            # 展开设置
            self.setup_content_frame.pack(fill=tk.BOTH, expand=True)
            self.toggle_setup_button.config(text="收起设置")
            self.setup_collapsed = False
        else:
            # 收起设置
            self.setup_content_frame.pack_forget()
            self.toggle_setup_button.config(text="展开设置")
            self.setup_collapsed = True

    def start_game(self):
        """当玩家点击"开始/重置游戏"时触发。"""
        api_key = self.api_key_entry.get().strip()
        host = self.host_entry.get().strip()
        model_name = self.model_entry.get().strip()
        story_bg = self.story_bg_text.get("1.0", tk.END).strip()
        length_range_text = self.length_entry.get().strip()
        story_type = self.story_type_entry.get().strip()
        option_style = self.option_style_entry.get().strip()

        if not api_key or not story_bg:
            messagebox.showerror("错误", "API-KEY 和 故事背景 不能为空！")
            return

        if not model_name:
            messagebox.showerror("错误", "请输入模型名称！")
            return

        if not host:
            messagebox.showerror("错误", "请输入Host地址！")
            return

        # 解析长度范围（形如 "300-500"）
        self.paragraph_min_chars, self.paragraph_max_chars = 300, 500
        try:
            if '-' in length_range_text:
                _min, _max = length_range_text.split('-', 1)
                self.paragraph_min_chars = max(50, int(_min))
                self.paragraph_max_chars = max(self.paragraph_min_chars + 50, int(_max))
        except Exception:
            # 保留默认值
            pass
        # 估算可生成的最大token数（中文1字符≈1 token，给出富余）
        # 为故事正文与四个选项预留空间：上限×2 + 200
        self.max_new_tokens = int(self.paragraph_max_chars * 2.0 + 200)
        # 安全上限，避免超出模型限制
        self.max_new_tokens = max(256, min(self.max_new_tokens, 8192))

        dashscope.api_key = api_key
        # 设置自定义host
        dashscope.base_http_client.base_url = host
        self.current_model = model_name  # 保存当前使用的模型
        self.story_type = story_type or ""
        self.option_style = option_style or ""

        parts = ["## 故事背景\n", story_bg]
        if self.story_type:
            parts.append(f"\n\n## 故事类型\n{self.story_type}")
        if self.option_style:
            parts.append(f"\n\n## 选项风格\n{self.option_style}")
        parts.append("\n\n")
        self.story_history = "".join(parts)

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

        system_prompt = f"""
你是一位才华横溢、充满想象力的文字冒险游戏AI。你的任务是：
1. 根据玩家的选择和已有的故事，生成一段生动、具体的后续情节（大约{self.paragraph_min_chars}-{self.paragraph_max_chars}字，尽量写满范围上限，细节丰富、包含感官描写与动作）。若未达到最少字数{self.paragraph_min_chars}，请继续扩写，不要提前开始列出选项。
2. 在情节的结尾，为玩家提供四个风格迥异、导向完全不同剧情分支的行动选项。
3. 故事类型偏好：{self.story_type if hasattr(self, 'story_type') and self.story_type else '不限'}。
4. 选项风格要求：{self.option_style if hasattr(self, 'option_style') and self.option_style else '清晰互斥、差异明显'}。

请按照以下格式返回：
1. 首先写一段故事情节
2. 然后写"### 行动选项"
3. 接着列出四个选项，每个选项用"**选项标题**-选项描述"的格式

示例格式：
随着晨星号缓缓降落在X-17星球表面，你透过驾驶舱的窗户向外望去，只见一片奇异而迷人的景象。这颗星球的地表覆盖着五彩斑斓的植物，远处连绵起伏的山脉反射出不寻常的光芒，仿佛整个世界都被某种神秘力量所笼罩。飞船降落带来的震动逐渐平息后，你意识到必须采取行动了———————不仅要确保自己和船员的安全，还要尽快找到修复飞船的方法。

### 行动选项

**探索周围环境**-你决定先检查一下飞船降落点附近的区域，看看是否能找到任何有用的资源或线索。虽然未知总是伴随着危险，但直觉告诉你，了解这片土地的秘密可能是解决问题的关键所在。

**启动紧急信号发射器**-考虑到情况危急，你认为最明智的选择是立即激活晨星号上的紧急求救信号发射装置，希望有人能够接收到你的求助信息，并前来救援。不过这样做也可能吸引到一些不必要的注意。

**尝试自行修理飞船**-凭借着多年积累下来的机械知识，你觉得或许自己就能够解决当前遇到的问题。于是，你准备打开飞船的引擎舱盖，亲自检查能量核心损坏的具体原因，并寻找可能存在的修复方案。

**与本地生物交流**-在降落过程中，你注意到不远处有一群外形奇特的生物正在好奇地观察着你们。尽管不知道它们是否友好，但也许这些原住民能提供关于这个星球以及如何获得帮助的信息。因此，你打算尝试接近并尝试与之沟通。
"""
        
        threading.Thread(target=self._call_llm_in_thread, args=(system_prompt, prompt), daemon=True).start()

    def _call_llm_in_thread(self, system_prompt, user_prompt):
        """在后台线程中实际调用API，防止UI卡死。"""
        try:
            messages = [
                {"role": Role.SYSTEM, "content": system_prompt},
                {"role": Role.USER, "content": user_prompt},
            ]
            response = Generation.call(
                model=self.current_model,
                messages=messages,
                result_format='message',
                max_tokens=getattr(self, 'max_new_tokens', 1024),
                max_length=getattr(self, 'max_new_tokens', 1024),
                top_p=0.9
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
                # 兼容两种返回格式：text 与 message
                text_payload = None
                try:
                    # 旧版 text
                    text_payload = response_data.output.text
                except Exception:
                    pass
                if not text_payload:
                    try:
                        choices = getattr(response_data.output, 'choices', None)
                        if choices and len(choices) > 0:
                            first_choice = choices[0]
                            message_obj = first_choice['message'] if isinstance(first_choice, dict) else getattr(first_choice, 'message', None)
                            if message_obj:
                                if isinstance(message_obj, dict):
                                    text_payload = message_obj.get('content')
                                else:
                                    text_payload = getattr(message_obj, 'content', None)
                    except Exception:
                        text_payload = None
                if text_payload:
                    self.process_llm_response(text_payload)
                else:
                    error_msg = f"API请求成功但未能解析到文本内容。\n原始数据: {getattr(response_data, 'output', None)}"
                    self.handle_api_error(error_msg)
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
        """解析LLM返回的文本，并更新UI。"""
        # 保存AI的原始响应用于调试
        self.last_ai_response = text_response
        
        try:
            # 使用新的文本解析器
            story_part, options = self.parse_text_response(text_response)
            
            # 更新故事历史
            self.story_history += story_part
            
            # 更新显示
            self.update_story_display()
            
            # 更新选项
            self.current_options = options
            self.update_options_display()
            
            self.toggle_controls(is_generating=False)

        except Exception as e:
            # 改进的错误处理
            error_msg = f"AI返回的内容无法解析。\n错误: {e}\n\n原始响应:\n{text_response}"
            messagebox.showwarning("解析错误", error_msg)
            
            # 将原始响应添加到故事历史中
            self.story_history += f"\n\n---\n\n**[系统警告：AI响应无法解析，以下为原始输出]**\n\n{text_response}\n\n"
            self.update_story_display()
            
            # 清空选项
            self.current_options = []
            self.update_options_display()
            
            self.toggle_controls(is_generating=False)

    def parse_text_response(self, text_response):
        """解析AI返回的纯文本响应，提取故事和选项。"""
        # 清理响应文本
        text = text_response.strip()
        
        # 查找"### 行动选项"或类似的分隔符
        option_markers = [
            "### 行动选项",
            "### 选项",
            "### 选择",
            "行动选项：",
            "选项：",
            "选择："
        ]
        
        story_part = ""
        options = []
        
        # 尝试找到选项部分
        option_start = -1
        for marker in option_markers:
            option_start = text.find(marker)
            if option_start != -1:
                break
        
        if option_start != -1:
            # 分离故事和选项
            story_part = text[:option_start].strip()
            options_text = text[option_start:].strip()
            
            # 提取选项
            options = self.extract_options_from_text(options_text)
        else:
            # 如果没有找到明确的选项标记，尝试其他方法
            story_part = text
            options = self.extract_options_from_text(text)
        
        # 验证结果
        if not story_part:
            raise ValueError("无法提取故事内容")
        
        if len(options) != 4:
            raise ValueError(f"选项数量不正确，期望4个，实际{len(options)}个")
        
        return story_part, options

    def extract_options_from_text(self, text):
        """从文本中提取选项。"""
        options = []
        
        # 方法1：查找"**选项标题**-描述"格式
        pattern1 = r'\*\*([^*]+)\*\*-([^\n]+)'
        matches1 = re.findall(pattern1, text)
        
        if len(matches1) >= 4:
            for title, desc in matches1[:4]:
                options.append(f"{title}-{desc}")
            return options
        
        # 方法2：查找数字编号的选项
        pattern2 = r'(\d+)[\.、]\s*([^\n]+)'
        matches2 = re.findall(pattern2, text)
        
        if len(matches2) >= 4:
            for num, desc in matches2[:4]:
                options.append(desc.strip())
            return options
        
        # 方法3：查找"选项X："格式
        pattern3 = r'选项\s*(\d+)[：:]\s*([^\n]+)'
        matches3 = re.findall(pattern3, text)
        
        if len(matches3) >= 4:
            for num, desc in matches3[:4]:
                options.append(desc.strip())
            return options
        
        # 方法4：按行分割，查找可能的选项
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # 排除太短的行
                # 检查是否包含选项关键词
                if any(keyword in line for keyword in ['**', '选项', '选择', '决定']):
                    options.append(line)
                    if len(options) >= 4:
                        break
        
        # 如果还是不够4个，用最后几行作为选项
        if len(options) < 4:
            lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 10]
            for line in lines[-4:]:
                if line not in options:
                    options.append(line)
                    if len(options) >= 4:
                        break
        
        return options[:4]  # 确保最多返回4个选项

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

if __name__ == "__main__":
    root = tk.Tk()
    app = LLMAdventureGame(root)
    root.mainloop()