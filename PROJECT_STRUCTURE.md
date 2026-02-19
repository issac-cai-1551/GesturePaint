# GesturePaint 项目结构说明

本项目是一个基于手势控制的空气绘画系统，集成了计算机视觉（MediaPipe）、生成式 AI（Stable Diffusion）和 Pygame 交互界面。

## 目录结构概览

```text
GesturePaint/
├── main.py                     # 程序主入口，负责初始化和主循环
├── config.yaml                 # 配置文件
├── requirements.txt            # Python 依赖列表
├── download_models.py          # 模型下载脚本
├── copy_models.py              # 模型复制脚本
├── assets/                     # 静态资源目录
│   ├── fonts/                  # 字体文件
│   ├── icons/                  # 图标资源
│   ├── saved_drawings/         # 保存的绘画作品
│   └── avatar_sticker/         # 头像贴纸资源
├── src/                        # 源代码目录
│   ├── core/                   # 核心功能模块
│   │   ├── brush_engine.py     # 笔刷引擎（颜色、大小、绘制逻辑）
│   │   ├── canvas_manager.py   # 画布管理器（图层、撤销/重做、保存）
│   │   └── gesture_detector.py # 手势检测器（基于 MediaPipe）
│   ├── features/               # 业务功能模块
│   │   ├── art_result_dialog.py   # 艺术创作结果展示对话框
│   │   ├── custom_dialog.py       # 自定义 UI 对话框基类
│   │   ├── dialog_manager.py      # 对话框管理器（统一管理弹窗）
│   │   ├── doodle_to_art_system.py # 涂鸦转艺术系统（Stable Diffusion + ControlNet）
│   │   ├── face_detector.py       # 人脸检测模块
│   │   ├── face_swapper.py        # 人脸替换/变脸模块
│   │   └── gesture_commands.py    # 手势命令映射与执行
│   └── utils/                  # 工具类模块
│       ├── config.py           # 配置加载工具
│       ├── coordinates.py      # 坐标映射工具（摄像头坐标 -> 屏幕坐标）
│       ├── visualizer.py       # 视觉可视化工具（绘制骨架、UI元素）
│       └── SuppressStderr.py   # 标准错误流拦截工具（用于屏蔽底层日志）
```

## 核心模块说明

### 1. 入口层 (Root)

- **main.py**: 系统的核心控制器。负责初始化 Pygame、OpenCV 摄像头、各个子模块，并维护主事件循环（Event Loop）。它协调手势识别、画布绘制和 UI 更新。

### 2. 核心层 (src/core)

- **gesture_detector.py**: 封装了 MediaPipe 的手势识别模型，提供实时的手部关键点检测和手势分类。
- **canvas_manager.py**: 管理虚拟画布的状态，包括像素数据的存储、笔迹的绘制、清空以及撤销操作。
- **brush_engine.py**: 定义笔刷的属性（颜色、粗细）和行为，支持动态调整。

### 3. 功能层 (src/features)

- **doodle_to_art_system.py**: 集成了 Stable Diffusion 和 ControlNet，负责将用户的简笔画（Doodle）转换为高质量的艺术画作。包含模型加载、推理和图像后处理。
- **gesture_commands.py**: 命令模式的实现。将识别到的手势（如"比心"、"握拳"）映射为具体的系统指令（如"切换头像"、"撤销"）。
- **face_swapper.py**: 实现基于人脸关键点的实时换脸功能，支持将摄像头中的人脸替换为预设的头像贴纸。
- **UI 系统 (dialog_*)**: 实现了一套基于 Pygame 的自定义 UI 系统，用于显示提示框、风格选择和结果展示，替代了阻塞式的系统弹窗。

### 4. 工具层 (src/utils)

- **coordinates.py**: 解决摄像头画面与屏幕画布之间的坐标变换问题，处理镜像翻转和比例缩放。
- **SuppressStderr.py**: 一个上下文管理器，用于在加载重型 AI 模型（如 TensorFlow/PyTorch）时屏蔽繁杂的底层 C++ 日志输出，保持控制台整洁。

## 数据流向

1. **输入**: 摄像头捕获每一帧图像 -> `main.py`
2. **处理**:
   - 图像传入 `gesture_detector.py` 获取手势信息。
   - 图像传入 `face_swapper.py` 进行人脸特效处理。
3. **交互**:
   - `gesture_commands.py` 根据手势判断意图（绘画、命令）。
   - 如果是绘画，坐标经 `coordinates.py` 转换后由 `brush_engine.py` 在 `canvas_manager.py` 上绘制。
4. **AI 生成**:
   - 用户触发保存/生成后，`doodle_to_art_system.py` 读取画布内容，调用本地模型生成艺术图。
5. **输出**:
   - `visualizer.py` 和 `dialog_manager.py` 将合成后的画面（摄像头+画布+UI）渲染到屏幕。
