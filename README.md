# GesturePaint - 手势绘画与AI艺术生成

## 项目简介

GesturePaint 是一个结合手势识别和AI艺术生成的多功能绘画应用。用户可以通过手势控制和语音控制绘制涂鸦，然后使用AI模型将涂鸦转换为精美的艺术作品。

## 主要功能

1. **手势绘画**：通过摄像头识别手势进行绘画
2. **涂鸦转艺术**：使用Stable Diffusion和Img2ImgPipeline将简单涂鸦转换为高质量的多种风格（包含nju建筑风格）的艺术作品
3. **多种画笔**：支持不同粗细、颜色的画笔
4. **历史记录**：保存和查看绘画历史
5. **AI换脸**：使用mediapipe实现换脸功能
6. **语音控制**：使用百度云实时语音服务


## 技术栈

- **Python 3.9+**
- **PyGame** - GUI框架
- **OpenCV** - 图像处理和手势识别
- **MediaPipe** - 手势检测
- **PyTorch** - 深度学习框架
- **Transformers/Diffusers** - Hugging Face模型库
- **Stable Diffusion + ControlNet** - AI图像生成

## 安装步骤

### 1. 克隆项目
```bash
git clone https://github.com/123tan-ww/GesturePaint.git
cd GesturePaint
```

### 2. 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 下载模型文件
由于模型文件较大，请手动下载并放置在 `models/` 目录下：

1. BLIP图像描述模型
2. Stable Diffusion v1.5
3. ControlNet Scribble模型
4. gesture_recognizer模型

或运行提供的脚本自动下载。
```bash
python download_models.py
```

### 5. 运行应用
```bash
python main.py
```


## 使用说明

1. 启动应用程序
2. 通过摄像头使用手势绘制
3. 完成涂鸦后，点击"AI艺术生成"按钮
4. 选择/输入提示词和艺术风格，等待AI生成
5. 全程可用语音实时辅助绘画


## 贡献指南

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request



## 致谢

- [Hugging Face](https://huggingface.co/) - 提供优秀的AI模型
- [MediaPipe](https://google.github.io/mediapipe/) - 手势识别和面部识别方案
