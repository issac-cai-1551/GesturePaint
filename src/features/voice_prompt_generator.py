# voice_prompt_generator.py
class VoicePromptGenerator:
    def __init__(self):
        self.style_keywords = {
            "油画": "masterpiece oil painting",
            "水彩": "beautiful watercolor art",
            "数字艺术": "professional digital artwork",
            "奇幻": "fantasy concept art",
            "极简": "minimalist line art",
            "超现实": "surreal dreamlike painting",
            "波普": "vibrant pop art style",
            "水墨": "elegant ink drawing",
            "印象派": "impressionist painting style",
            "赛博朋克": "cyberpunk neon style"
        }

        self.quality_enhancers = [
            "highly detailed", "4K resolution", "trending on artstation",
            "beautiful lighting", "cinematic", "professional"
        ]

    def generate_from_voice(self, voice_text):
        """从语音生成AI提示词"""
        import random

        # 提取关键信息
        prompt = voice_text

        # 检测并应用风格关键词
        style = None
        for chinese, english in self.style_keywords.items():
            if chinese in voice_text:
                style = english
                prompt = prompt.replace(chinese, "")
                break

        # 如果没有指定风格，随机选择一个
        if not style:
            style = random.choice(list(self.style_keywords.values()))

        # 增强提示词质量
        enhancer = random.choice(self.quality_enhancers)

        # 最终提示词格式
        final_prompt = f"{prompt}, {style}, {enhancer}"

        return final_prompt, style