import os
import sys

# 添加项目根目录到Python路径，方便导入
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 设置本地模型路径
os.environ['HF_HOME'] = ''
os.environ['HUGGINGFACE_HUB_CACHE'] = ''
os.environ['TRANSFORMERS_CACHE'] = ''

import os

# 设置HuggingFace缓存目录
cache_dir = "E:/huggingface_cache"
os.makedirs(cache_dir, exist_ok=True)
os.environ['TRANSFORMERS_CACHE'] = cache_dir
os.environ['HF_HOME'] = cache_dir
os.environ['HUGGINGFACE_HUB_CACHE'] = cache_dir

# 禁用代理（如果有网络问题）
os.environ['NO_PROXY'] = '*'
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

import torch
import cv2
import numpy as np
import warnings

# 忽略diffusers的FutureWarning，因为新版API(callback_on_step_end)和环境还不兼容我没法改
warnings.filterwarnings("ignore", category=FutureWarning)

from datetime import datetime
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
# 🔥 修改这里：移除ControlNet，使用Img2ImgPipeline
from diffusers import StableDiffusionImg2ImgPipeline  # 移除ControlNet相关导入
from pathlib import Path
from transformers import BlipProcessor, BlipForConditionalGeneration


class DoodleToArtConverter:
    def __init__(self):
        """
        初始化涂鸦转艺术模型，使用本地模型文件
        """
        # 获取当前文件所在目录
        current_file = Path(__file__).resolve()

        # 计算模型路径（项目根目录的models文件夹）
        models_dir = current_file.parent.parent.parent / "models"

        # 设置各个模型的具体路径
        sd_model_path = models_dir / "stable-diffusion-v1-5"
        # 🔥 移除ControlNet路径，因为不再需要
        # blip_model_path = models_dir / "blip-image-captioning-base"

        # self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # print(f"使用设备: {self.device}")
        if torch.cuda.is_available():
            self.device = "cuda"
            print(f"✅ CUDA可用，使用GPU: {torch.cuda.get_device_name(0)}")
            print(
                f"GPU内存: {torch.cuda.memory_allocated(0) / 1024 ** 3:.2f}GB / {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.2f}GB")
        else:
            self.device = "cpu"
            print("⚠ 警告: CUDA不可用，将使用CPU（会很慢）")

        print(f"项目根目录: {current_file.parent.parent.parent}")
        print(f"模型目录: {models_dir}")

        # 检查模型是否存在
        self._check_models_exist(sd_model_path)  # 🔥 移除ControlNet参数

        # print("加载图像理解模型...")
        # # 从本地加载BLIP模型
        # self.caption_processor = BlipProcessor.from_pretrained(
        #     str(blip_model_path),
        #     use_fast=True,
        #     local_files_only=True
        # )
        # self.caption_model = BlipForConditionalGeneration.from_pretrained(
        #     str(blip_model_path),
        #     local_files_only=True
        # ).to(self.device)
        # print("✓ BLIP模型加载成功")

        print("加载Stable Diffusion模型（Img2Img）...")
        # 🔥 修改这里：使用Img2ImgPipeline而不是ControlNet
        self.pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            str(sd_model_path),
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
            local_files_only=True
        )
        print("✓ Stable Diffusion Img2Img模型加载成功")

        # 🔥 加载训练好的LoRA模型
        print("加载LoRA模型...")
        lora_model_path = models_dir / "lora" / "my_university_style.safetensors"
        if lora_model_path.exists():
            try:
                # 加载LoRA权重
                self.pipe.load_lora_weights(
                    str(lora_model_path.parent),  # 文件夹路径
                    weight_name=lora_model_path.name  # 文件名
                )
                print(f"✅ LoRA模型加载成功: {lora_model_path.name}")

                # 设置LoRA权重（0.5-1.5之间调整）
                # 0.8是一个温和的权重，不会覆盖太多原始内容
                self.pipe.set_adapters(["my_university_style"], adapter_weights=[0.8])
            except Exception as e:
                print(f"⚠ LoRA加载失败: {e}")
                print("⚠ 将使用基础模型（无学校风格）")
        else:
            print("⚠ 未找到LoRA模型文件，将使用基础模型")

        self.trigger_word = "nanjing_university"  # 🔥 替换为你的实际触发词

        self.pipe = self.pipe.to(self.device)

        # 输出目录 - 指向 assets/auto_doodle_art
        self.output_dir = current_file.parent.parent.parent / "assets" / "auto_doodle_art"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 启用内存优化
        if self.device == "cuda":
            self.pipe.enable_attention_slicing()
            try:
                self.pipe.enable_xformers_memory_efficient_attention()
                print("✓ 已启用xformers内存优化")
            except:
                print("⚠ xformers不可用，使用标准注意力")

        print("✓ 所有模型加载完成，准备就绪！")

    def _check_models_exist(self, sd_path):  # 🔥 移除ControlNet参数
        """检查模型文件是否存在"""
        paths_to_check = [
            (sd_path, "Stable Diffusion v1.5")
        ]

        all_exist = True
        for path, name in paths_to_check:
            if path.exists():
                print(f"✓ {name} 模型存在于: {path}")

                # 列出主要文件
                model_files = list(path.rglob("*.bin")) + list(path.rglob("*.safetensors"))
                if model_files:
                    print(f"  找到模型文件: {len(model_files)} 个")
                else:
                    print(f"  ⚠ 未找到模型权重文件")
            else:
                print(f"✗ {name} 模型不存在于: {path}")
                all_exist = False

        if not all_exist:
            print("\n请按以下步骤操作:")
            print("1. 确保已下载模型到缓存目录 (E:/huggingface_cache)")
            print("2. 运行复制脚本将模型复制到项目models目录")
            print("3. 或者手动复制:")
            # print(
            #     "   - BLIP: E:/huggingface_cache/models--Salesforce--blip-image-captioning-base/snapshots/xxx 到 models/blip-image-captioning-base/")
            print(
                "   - Stable Diffusion: E:/huggingface_cache/models--runwayml--stable-diffusion-v1-5/snapshots/xxx 到 models/stable-diffusion-v1-5/")
            raise FileNotFoundError("模型文件不存在，请先下载并复制模型到项目目录")

    def auto_generate_from_doodle(self, doodle_image, num_creations=6, style=None,
                                  prompt="High quality, detailed, sharp focus, beautiful composition, cinematic lighting, masterpiece, ultra-detailed, clean and clear",
                                  progress_callback=None):
        """
        完全自动化：从涂鸦到多种创意作品
        """
        print("开始自动化创意生成流程...")
        if progress_callback:
            progress_callback(0, "开始初始化...")

        # # 1. 分析涂鸦内容
        # print("步骤1: 分析涂鸦内容...")
        # if progress_callback:
        #     progress_callback(5, "正在分析涂鸦内容...")
        # prompt = self.auto_analyze_doodle(doodle_image)

        #1.处理需求并生成最终的prompt
        print("处理需求并生成最终的prompt...")
        if progress_callback:
            progress_callback(5, "正在处理需求并生成最终的prompt...")

        if style == "school style":
            final_prompt=f"{self.trigger_word},{prompt}"
        else:
            if style == None:
                final_prompt=prompt
            else:
                final_prompt=f"{prompt},{style}"
        # 如果你想要调整触发词的权重，可以这样写：
        # enhanced_prompt = f"({trigger_word}:1.2), {style_enhanced_prompt}"

        # 🔥 修改这里：不再需要线稿预处理
        # 2. 直接使用原始涂鸦作为输入图像
        print("步骤2: 准备输入图像...")
        if progress_callback:
            progress_callback(10, "正在准备输入图像...")

        # 预处理涂鸦：调整大小并转换为RGB
        if isinstance(doodle_image, str):
            input_image = Image.open(doodle_image).convert("RGB")
        else:
            input_image = doodle_image.convert("RGB")

        # 调整图像大小到标准尺寸（如512x512）
        target_size = (512, 512)
        input_image = input_image.resize(target_size, Image.Resampling.LANCZOS)

        # 3. 生成多种创意变体
        print("步骤3: 生成创意作品...")
        creations = []

        for i in range(num_creations):
            print(f"  生成作品 {i + 1}/{num_creations}...")
            if progress_callback:
                progress_callback(10 + int(90 * i / num_creations), f"正在生成作品 {i + 1}/{num_creations}...")


            generator = torch.Generator(device=self.device).manual_seed(i * 1000)

            # 定义内部回调函数来更新进度，每完成一步调用一次call_back
            def pipe_callback(step, timestep, latents):
                if progress_callback:
                    # 总步数为50，与num_inference_steps保持一致
                    total_steps = 50
                    # 计算当前生成的进度 (0-1)
                    current_gen_progress = step / total_steps
                    # 映射到总进度 (0-100)
                    base_progress = 10 + int(90 * i / num_creations)
                    step_progress = int(90 * current_gen_progress / num_creations)
                    # 更新进度情况
                    progress_callback(base_progress + step_progress, f"正在绘制... {int(current_gen_progress * 100)}%")

            # 🔥 修改这里：使用Img2Img管道
            # strength参数控制对原始图像的保留程度：0.0=完全保留，1.0=完全重绘
            # 建议从0.5-0.8开始尝试
            image = self.pipe(
                prompt=final_prompt,
                image=input_image,  # 🔥 直接使用原始涂鸦，不需要线条提取
                negative_prompt="Blurry, low resolution, pixelated, distorted, ugly, disfigured, text, watermark, signature, messy, noisy",
                guidance_scale=7.5,
                generator=generator,
                num_inference_steps=50,  # 可以适当增加步数以获得更好效果
                strength=0.7,  # 🔥 关键参数：控制重绘强度
                callback=pipe_callback,
                callback_steps=1
            ).images[0]

            creations.append((image, final_prompt))

        if progress_callback:
            progress_callback(100, "生成完成！")

        return creations, input_image  # 🔥 返回原始图像而不是处理后的线稿

    def auto_analyze_doodle(self, doodle_image):
        """自动分析涂鸦内容"""
        if isinstance(doodle_image, str):
            image = Image.open(doodle_image).convert("RGB")
        else:
            image = doodle_image.convert("RGB")

        inputs = self.caption_processor(image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            caption_ids = self.caption_model.generate(**inputs, max_length=30, num_beams=3)

        description = self.caption_processor.decode(caption_ids[0], skip_special_tokens=True)

        # 基础质量增强
        enhanced = f"{description}, high quality, detailed, artistic"

        return enhanced

    # def add_style(self, prompt, style):
    #     return f"{prompt}, {style}"

    def save_and_display_results(self, original_doodle, creations):
        """保存和显示结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        session_dir = self.output_dir / f"art_{timestamp}"
        session_dir.mkdir(exist_ok=True)

        # 创建展示图
        fig, axes = plt.subplots(2, (len(creations) + 1) // 2, figsize=(15, 10))
        axes = axes.flatten()

        # 显示原始涂鸦
        axes[0].imshow(original_doodle)
        axes[0].set_title("Original Doodle")
        axes[0].axis('off')

        # 显示生成的作品
        for i, (img, prompt) in enumerate(creations):
            axes[i + 1].imshow(img)
            axes[i + 1].set_title(f"Creation {i + 1}")
            axes[i + 1].axis('off')

            # 保存单个作品
            creation_path = session_dir / f"{timestamp}_creation_{i + 1}.png"
            img.save(creation_path)

        # 保存原始涂鸦
        original_path = session_dir / f"{timestamp}_original.png"
        original_doodle.save(original_path)

        # 保存提示词信息
        prompts_path = session_dir / f"{timestamp}_prompts.txt"
        with open(prompts_path, "w") as f:
            for i, (_, prompt) in enumerate(creations):
                f.write(f"Creation {i + 1}: {prompt}\n")

        plt.tight_layout()
        plt.show()

        print(f"所有作品已保存到: {self.output_dir}")
        print(f"时间戳: {timestamp}")


def main():
    converter = DoodleToArtConverter()
    doodle_img = Image.open("E:/GesturePaint/assets/saved_drawings/drawing_1763901950.png")
    creations, processed_doodle = converter.auto_generate_from_doodle(doodle_img, num_creations=1,style=None)

    converter.save_and_display_results(processed_doodle, creations)


if __name__ == "__main__":
    main()