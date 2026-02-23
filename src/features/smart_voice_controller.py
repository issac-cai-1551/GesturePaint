"""
智能语音控制器 - 使用大模型理解自然语言
"""

import json
import threading
import queue
import time
import re
from typing import Dict, List, Optional, Any
import openai
import torch
from openai import OpenAI
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write


class SmartVoiceController:
    """智能语音控制器 - 使用大模型理解命令"""

    def __init__(self, main_app, config_path="config/api_config.json"):
        """
        初始化智能语音控制器

        参数:
            main_app: 主程序引用
            config_path: API配置文件路径
        """
        self.main_app = main_app
        self.is_active = False
        self.is_listening = False
        self.is_processing = False

        # 语音相关
        self.sample_rate = 16000
        self.duration = 3  # 每次录音时长（秒）
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.processing_thread = None

        # 命令历史
        self.command_history = []
        self.max_history = 10

        # 初始化大模型
        self.llm_client = None
        self.llm_config = self._load_config(config_path)
        self._init_llm()

        # 初始化本地语音识别（备选）
        self._init_local_asr()

        # 系统提示词
        self.system_prompt = self._create_system_prompt()

        print("🤖 智能语音控制器初始化完成")

    def _load_config(self, config_path):
        """加载API配置"""
        default_config = {
            "provider": "deepseek",  # deepseek, openai, local
            "api_key": "",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "local_model_path": "",
            "use_local": False
        }

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_config.update(config)
                return default_config
        except:
            print(f"⚠️  配置文件 {config_path} 不存在，使用默认配置")
            # 创建默认配置文件
            self._create_default_config(config_path)
            return default_config

    def _create_default_config(self, config_path):
        """创建默认配置文件"""
        default_config = {
            "provider": "deepseek",
            "api_key": "your-api-key-here",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "local_model_path": "",
            "use_local": False,
            "instructions": "请从以下地址获取API Key:",
            "deepseek_url": "https://platform.deepseek.com/api_keys",
            "openai_url": "https://platform.openai.com/api-keys"
        }

        import os
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

        print(f"📄 已创建配置文件: {config_path}")
        print("⚠️  请修改配置文件中的API Key")

    def _init_llm(self):
        """初始化大模型客户端"""
        if self.llm_config["use_local"]:
            self._init_local_llm()
        else:
            self._init_api_llm()

    def _init_api_llm(self):
        """初始化API大模型"""
        try:
            if self.llm_config["provider"] == "deepseek":
                self.llm_client = OpenAI(
                    api_key=self.llm_config["api_key"],
                    base_url=self.llm_config["base_url"]
                )
                print(f"✅ DeepSeek API 初始化成功")
            elif self.llm_config["provider"] == "openai":
                self.llm_client = OpenAI(
                    api_key=self.llm_config["api_key"]
                )
                print(f"✅ OpenAI API 初始化成功")
            else:
                raise ValueError(f"未知的提供商: {self.llm_config['provider']}")
        except Exception as e:
            print(f"❌ API初始化失败: {e}")
            print("⚠️  将使用本地规则匹配")
            self.llm_client = None

    def _init_local_llm(self):
        """初始化本地大模型"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch

            model_path = self.llm_config["local_model_path"]
            if not model_path:
                print("❌ 未指定本地模型路径")
                self.llm_client = None
                return

            print(f"正在加载本地模型: {model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )

            # 设置为评估模式
            self.model.eval()
            self.use_local_llm = True
            print("✅ 本地大模型加载成功")

        except Exception as e:
            print(f"❌ 本地大模型加载失败: {e}")
            print("⚠️  将使用API模式或规则匹配")
            self.llm_client = None
            self.use_local_llm = False

    def _init_local_asr(self):
        """初始化本地语音识别（备用）"""
        try:
            import speech_recognition as sr
            self.local_recognizer = sr.Recognizer()
            print("✅ 本地语音识别初始化成功")
        except:
            print("⚠️  本地语音识别初始化失败")
            self.local_recognizer = None

    def _create_system_prompt(self):
        """创建系统提示词"""
        return """你是一个智能绘画助手，负责将用户的语音指令转换为具体的绘画操作命令。

# 可用命令类型：
1. 画布控制(canvas_control)：
   - 保存画布 (save_canvas)
   - 清空画布 (clear_canvas)
   - 撤销操作 (undo)
   - 暂停系统 (pause)
   - 恢复系统 (resume)

2. 笔刷控制(brush_control)：
   - 切换颜色：红色、蓝色、绿色、黑色
   - 调整大小：增大笔刷、减小笔刷、设置为N(1-50)像素(如果未指明增大/减少多少，默认变化幅度为5像素）
   - 特效笔刷：火焰、彩虹、星空、霓虹、水彩

3. 创意生成(creative_generation)：
   - 根据描述生成绘画：prompt
   - 艺术化转换：将当前画作进行转换的prompt

4. 系统功能：
   - 切换摄像头
   - 切换人脸源
   - 显示帮助
   
你需要分析用户的语音，提取其中的指令，一段话语中可能包含多个指令，你需要以列表形式依次输出各个指令，每个指令的输出格式如下：

# 输出格式：
请以JSON格式返回，包含以下字段：
{
  "command": "命令类型",
  "action": "具体动作",
  "parameters": {},  // 参数
  "response": "给用户的友好回复",
  "confidence": 0.95 // 置信度 (0-1)
}

# 示例：
用户说："保存一下我的画"
输出：{
  "command": "canvas_control",
  "action": "save_canvas",
  "parameters": {},
  "response": "好的，已经为您保存画布",
  "confidence": 0.98
}

用户说："画一个红色的猫"
输出：{
  "command": "creative_generation",
  "action": "generate_painting",
  "parameters": {
    "prompt":"a red cat"
  },
  "response": "正在为您绘制一只红色的卡通猫",
  "confidence": 0.95
}

用户说："把笔刷调大一点"
输出：{
  "command": "brush_control",
  "action": "increase_size",
  "parameters": {"amount": 5},
  "response": "已增大笔刷大小",
  "confidence": 0.9
}


现在，请处理用户的语音指令："""

    def start(self):
        """启动智能语音控制"""
        if self.is_active:
            print("⚠️ 智能语音控制已启用")
            return

        self.is_active = True
        self.is_listening = True

        # 启动录音线程
        self.recording_thread = threading.Thread(target=self._recording_loop)
        self.recording_thread.daemon = True
        self.recording_thread.start()

        # 启动处理线程
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()

        print("🤖 智能语音控制已启用")

    def stop(self):
        """停止智能语音控制"""
        if not self.is_active:
            return

        self.is_active = False
        self.is_listening = False

        # 等待线程结束
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)

        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)

        print("🤖 智能语音控制已停止")

    def _recording_loop(self):
        """录音循环"""
        print("🎤 开始监听语音...")

        try:
            import pyaudio
            import wave
            import io

            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
            )

            while self.is_listening:
                # 录制音频
                frames = []
                for _ in range(0, int(self.sample_rate / 1024 * self.duration)):
                    if not self.is_listening:
                        break
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)

                if frames:
                    # 保存到内存中的WAV文件
                    wav_buffer = io.BytesIO()
                    with wave.open(wav_buffer, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                        wf.setframerate(self.sample_rate)
                        wf.writeframes(b''.join(frames))

                    # 重置指针并放入队列
                    wav_buffer.seek(0)
                    self.audio_queue.put(wav_buffer)

                # 短暂暂停，避免CPU占用过高
                time.sleep(0.1)

            # 清理
            stream.stop_stream()
            stream.close()
            p.terminate()

        except Exception as e:
            print(f"🎤 录音错误: {e}")

    def _processing_loop(self):
        """处理循环"""
        while self.is_active:
            try:
                # 从队列获取音频数据
                wav_buffer = self.audio_queue.get(timeout=0.5)

                # 识别语音
                text = self._recognize_speech(wav_buffer)

                if text and len(text.strip()) > 1:
                    print(f"🎤 识别到语音: {text}")

                    # 使用大模型理解命令
                    self.is_processing = True
                    command = self._understand_command(text)
                    self.is_processing = False

                    if command:
                        self._execute_command(command)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ 处理错误: {e}")
                self.is_processing = False

    def _recognize_speech(self, wav_buffer):
        """识别语音"""
        # 方法1: 使用本地识别（快速）
        if self.local_recognizer:
            try:
                import speech_recognition as sr

                # 使用speech_recognition识别
                with sr.AudioFile(wav_buffer) as source:
                    audio = self.local_recognizer.record(source)
                    text = self.local_recognizer.recognize_google(audio, language='zh-CN')
                    return text
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"本地识别失败: {e}")

        # 方法2: 使用大模型API的语音识别（如果有）
        # 这里可以集成OpenAI Whisper等

        return None

    def _understand_command(self, text):
        """使用大模型理解命令"""
        # 先尝试简单的规则匹配（快速）
        simple_command = self._simple_rule_match(text)
        if simple_command:
            return simple_command

        # 使用大模型理解（复杂命令）
        if self.llm_client or self.use_local_llm:
            try:
                return self._llm_understand(text)
            except Exception as e:
                print(f"大模型理解失败: {e}")

        # 回退到规则匹配
        return self._advanced_rule_match(text)

    def _simple_rule_match(self, text):
        """简单规则匹配（快速响应）"""
        text = text.lower().strip()

        # 保存相关
        if any(word in text for word in ["保存", "存下来", "保存画布"]):
            return {
                "command": "canvas_control",
                "action": "save_canvas",
                "parameters": {},
                "response": "好的，正在保存画布",
                "confidence": 0.95
            }

        # 清空相关
        if any(word in text for word in ["清空", "清除", "重置", "干净"]):
            return {
                "command": "canvas_control",
                "action": "clear_canvas",
                "parameters": {},
                "response": "已清空画布",
                "confidence": 0.95
            }

        # 颜色切换
        color_map = {
            "红色": "red",
            "蓝色": "blue",
            "绿色": "green",
            "黑色": "black",
            "黄色": (255, 255, 0),
            "紫色": (128, 0, 128),
            "白色": (255, 255, 255)
        }

        for color_cn, color_val in color_map.items():
            if color_cn in text:
                return {
                    "command": "brush_control",
                    "action": "change_color",
                    "parameters": {"color": color_val},
                    "response": f"已切换为{color_cn}",
                    "confidence": 0.9
                }

        return None

    def _llm_understand(self, text):
        """使用大模型理解命令"""
        try:
            if self.use_local_llm and hasattr(self, 'model'):
                # 本地大模型
                return self._local_llm_predict(text)
            elif self.llm_client:
                # API大模型
                return self._api_llm_predict(text)
        except Exception as e:
            print(f"大模型预测错误: {e}")

        return None

    def _local_llm_predict(self, text):
        """本地大模型预测"""
        prompt = f"{self.system_prompt}\n用户说：{text}\n输出："

        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = inputs.to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 提取JSON部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                command = json.loads(json_match.group())
                return command
            except:
                pass

        return None

    def _api_llm_predict(self, text):
        """API大模型预测"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"用户说：{text}"}
            ]

            response = self.llm_client.chat.completions.create(
                model=self.llm_config["model"],
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            command = json.loads(content)
            return command

        except json.JSONDecodeError:
            print(f"JSON解析失败: {content}")
        except Exception as e:
            print(f"API调用失败: {e}")

        return None

    def _advanced_rule_match(self, text):
        """高级规则匹配（回退方案）"""
        text = text.lower().strip()

        # 笔刷大小
        size_match = re.search(r'(\d+)[\s个]?像素', text)
        if size_match:
            size = int(size_match.group(1))
            return {
                "command": "brush_control",
                "action": "set_size",
                "parameters": {"size": size},
                "response": f"已设置笔刷大小为{size}像素",
                "confidence": 0.9
            }

        # 增大减小
        if any(word in text for word in ["大点", "粗点", "增大", "调大"]):
            return {
                "command": "brush_control",
                "action": "increase_size",
                "parameters": {"amount": 5},
                "response": "已增大笔刷",
                "confidence": 0.85
            }

        if any(word in text for word in ["小点", "细点", "减小", "调小"]):
            return {
                "command": "brush_control",
                "action": "decrease_size",
                "parameters": {"amount": 5},
                "response": "已减小笔刷",
                "confidence": 0.85
            }

        # 创意生成检测
        creative_words = ["画一个", "创作", "生成", "绘制", "制作", "画幅"]
        if any(word in text for word in creative_words):
            # 提取主题
            theme = "抽象画"
            for word in creative_words:
                if word in text:
                    parts = text.split(word)
                    if len(parts) > 1:
                        theme = parts[1].strip()
                        break

            return {
                "command": "creative_generation",
                "action": "generate_painting",
                "parameters": {
                    "subject": theme,
                    "style": "油画"
                },
                "response": f"正在为您创作: {theme}",
                "confidence": 0.8
            }

        return None

    def _execute_command(self, command):
        """执行命令"""
        if not command:
            return

        print(f"🤖 执行命令: {command['action']}")
        print(f"   回复: {command['response']}")

        # 添加到历史
        self.command_history.append(command)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)

        # 根据命令类型执行
        cmd_type = command.get("command", "")
        action = command.get("action", "")
        params = command.get("parameters", {})

        try:
            if cmd_type == "canvas_control":
                self._execute_canvas_control(action, params)
            elif cmd_type == "brush_control":
                self._execute_brush_control(action, params)
            elif cmd_type == "creative_generation":
                self._execute_creative_generation(action, params)
            elif cmd_type == "system_control":
                self._execute_system_control(action, params)
            else:
                print(f"未知命令类型: {cmd_type}")
        except Exception as e:
            print(f"执行命令失败: {e}")

    def _execute_canvas_control(self, action, params):
        """执行画布控制命令"""
        if action == "save_canvas":
            self.main_app.save_drawing_with_dialog()
        elif action == "clear_canvas":
            self.main_app.canvas_manager.clear_canvas()
        elif action == "undo":
            if hasattr(self.main_app.canvas_manager, 'undo'):
                self.main_app.canvas_manager.undo()
        elif action == "pause":
            self.main_app.is_paused = True
        elif action == "resume":
            self.main_app.is_paused = False

    def _execute_brush_control(self, action, params):
        """执行笔刷控制命令"""
        if action == "change_color":
            color = params.get("color")
            if isinstance(color, str):
                self.main_app.brush_engine.change_color(color)
            elif isinstance(color, (tuple, list)):
                self.main_app.brush_engine.brush.color = color
        elif action == "set_size":
            size = params.get("size", 5)
            self.main_app.brush_engine.change_size(size)
        elif action == "increase_size":
            amount = params.get("amount", 5)
            current = self.main_app.brush_engine.brush.size
            self.main_app.brush_engine.change_size(min(50, current + amount))
        elif action == "decrease_size":
            amount = params.get("amount", 5)
            current = self.main_app.brush_engine.brush.size
            self.main_app.brush_engine.change_size(max(1, current - amount))

    def _execute_creative_generation(self, action, params):
        """执行创意生成命令"""
        if action == "generate_painting":
            subject = params.get("subject", "抽象画")
            style = params.get("style", "油画")

            # 保存当前画布
            filename = f"drawing_{int(time.time())}"
            success = self.main_app.canvas_manager.save_canvas(filename)

            if success:
                # 构建提示词
                prompt = f"{subject}, {style}"

                # 添加到艺术生成任务
                new_task = {
                    "id": int(time.time() * 1000),
                    "filename": filename,
                    "full_path": f"assets/saved_drawings/{filename}.png",
                    "style": style,
                    "prompt": prompt,
                    "progress": 0,
                    "status": "等待处理...",
                    "thumbnail": None,
                    "finished": False,
                    "remove_time": 0
                }

                # 添加到主程序队列
                self.main_app.processing_tasks.append(new_task)
                self.main_app.task_queue.put(new_task)

    def _execute_system_control(self, action, params):
        """执行系统控制命令"""
        if action == "toggle_camera":
            print("切换摄像头（待实现）")
        elif action == "toggle_face_source":
            self.main_app.gesture_commands.change_face_source()
            print("已切换人脸源")

    def get_status(self):
        """获取控制器状态"""
        return {
            "active": self.is_active,
            "listening": self.is_listening,
            "processing": self.is_processing,
            "history_count": len(self.command_history)
        }

    def get_recent_commands(self, count=5):
        """获取最近的命令"""
        return self.command_history[-count:]