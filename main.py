import os
# 必须在导入任何其他库之前设置，否则可能无效
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


from pathlib import Path
import pygame
import cv2
import numpy as np
import sys
import time
import threading
import queue
from PIL import Image

# from src.features.smart_voice_controller import SmartVoiceController
# from src.features.voice_ui import VoiceUI
from src.utils.SuppressStderr import SuppressStderr
from src.core.gesture_detector import GestureDetector
from src.core.canvas_manager import CanvasManager
from src.core.brush_engine import BrushEngine
from src.features.face_detector import FaceDetector
from src.features.face_swapper import FaceSwapper
from src.features.gesture_commands import GestureCommands
from src.utils.visualizer import Visualizer
from src.utils.coordinates import CoordinateMapper
from src.features.custom_dialog import CustomDialog,OptionDialog
from src.features.doodle_to_art_system import DoodleToArtConverter
from src.features.dialog_manager import DialogManager, DialogState
from src.features.voice_recognition import RealtimeVoiceController


import sys
import traceback

def global_excepthook(exc_type, exc_value, exc_traceback):
    print("="*50)
    print("UNCAUGHT EXCEPTION:")
    print(f"Type: {exc_type}")
    print(f"Value: {exc_value}")
    traceback.print_tb(exc_traceback)
    print("="*50)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = global_excepthook

class AirPaintingApp:
    def __init__(self):
        # 初始化Pygame

        pygame.init()
        pygame.key.start_text_input()#实现中文输入

        # 屏幕设置
        self.screen_width = 1600
        self.screen_height = 900
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("手势控制空气绘画系统")




        # 颜色定义
        self.colors = {
            'background': (240, 240, 240),
            'panel': (220, 220, 220),
            'text': (50, 50, 50),
            'highlight': (70, 130, 180),
            'pause_overlay': (0, 0, 0, 128)  # 半透明黑色
        }

        # 布局参数
        self.camera_width = 640
        self.camera_height = 480
        self.canvas_width = 600
        self.canvas_height = 400
        self.panel_width = 100

        # 修改
        self.cursor_layer = pygame.Surface((self.canvas_width, self.canvas_height), flags=pygame.SRCALPHA) #启用透明通道

        # 状态变量
        self.running = True
        self.drawing_active = False
        self.last_point = None
        self.current_gesture = None
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.5  # 手势冷却时间（秒）

        # 新增
        self.is_paused = False
        self.dialog_manager = DialogManager(self.screen_width, self.screen_height)
        self.last_camera_surface = None

        # 最近保存的图片文件
        self.last_save_filename = None
        
        # 艺术生成任务管理
        self.processing_tasks = [] # 存储所有任务状态，用于UI显示
        self.task_queue = queue.Queue() # 任务队列
        # 启动后台处理线程
        threading.Thread(target=self.art_worker, daemon=True).start()

        # 语音识别相关
        self.voice_controller = RealtimeVoiceController(
            on_result_callback=self.handle_voice_command
        )
        self.voice_active = False
        self.voice_thread = None

        # 语音显示特效状态
        self.voice_display_text = ""
        self.voice_display_timer = 0
        self.voice_visual_flash = 0  # 视觉闪烁特效计时器
        self.voice_command_executed = False  # 是否刚刚执行了命令（用于触发特效）

        # 新增特效状态
        self.active_effect = None
        self.special_brush = False

        # 字体
        self.font = pygame.font.SysFont('simhei', 24)
        self.small_font = pygame.font.SysFont('simhei', 18)

        # 图标
        self.load_gesture_icons()

        # 创建必要的目录
        self.create_directories()

        # 帧率控制
        self.clock = pygame.time.Clock()
        self.fps = 40
        # 初始化模块
        self.init_modules()



    def init_modules(self):
        """初始化所有系统模块"""
        try:
            # 初始化手势检测器
            model_path = "models/gesture_recognizer.task"
            if not os.path.exists(model_path):
                print(f"警告: 模型文件 {model_path} 不存在")
                # 这里可以添加下载默认模型的逻辑
            
            # 使用SuppressStderr屏蔽MediaPipe初始化时的底层日志
            with SuppressStderr():
                self.gesture_detector = GestureDetector(model_path)


            # 初始化画布管理器
            self.canvas_manager = CanvasManager(self.canvas_width, self.canvas_height)

            # 初始化笔刷引擎
            self.brush_engine = BrushEngine()

            # 初始化手势命令系统
            self.gesture_commands = GestureCommands(self.canvas_manager, self.brush_engine)

            # 初始化坐标转换器
            self.coord_transformer = CoordinateMapper(
                self.camera_width, self.camera_height,
                self.canvas_width, self.canvas_height
            )

            # 初始化可视化器
            self.visualizer = Visualizer(self.screen, self.font, self.small_font)

            # 初始化换脸系统
            self.face_swapper = FaceSwapper(self.gesture_commands.current_face_source)


            # 初始化摄像头
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("错误: 无法打开摄像头")
                self.running = False
            else:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)

            # 启动语音控制系统
            self.toggle_voice_control()

            print("系统初始化完成")

        except Exception as e:
            print(f"初始化失败: {str(e)}")
            self.running = False

    def create_directories(self):
        """创建必要的目录"""
        directories = ["assets/saved_drawings", "models", "logs"]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"创建目录: {directory}")

    def handle_events(self):
        """处理Pygame事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # 先传递事件给对话框，不直接return
            dialog_handled = False
            if self.dialog_manager.is_active():
                dialog_handled = self.dialog_manager.handle_event(event)
                # 即使对话框处理了事件，也要继续处理TEXTINPUT（输入框需要）
                if dialog_handled and event.type not in [pygame.TEXTINPUT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    continue  # 仅跳过非输入类事件

            # 非对话框激活时处理键盘
            if not self.dialog_manager.is_active() and event.type == pygame.KEYDOWN:
                self.handle_keyboard(event.key)

    def handle_keyboard(self, key):
        """处理键盘输入"""
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_c:
            # 清空画布
            self.canvas_manager.clear_canvas()
            print("画布已清空")
        elif key == pygame.K_s:
            # 保存画布
            filename = f"drawing_{int(time.time())}"
            self.save_drawing_with_dialog()
            print(f"画布已保存: {filename}")
        elif key == pygame.K_1:
            self.brush_engine.change_color('red')
            print("笔刷颜色: 红色")
        elif key == pygame.K_2:
            self.brush_engine.change_color('blue')
            print("笔刷颜色: 蓝色")
        elif key == pygame.K_3:
            self.brush_engine.change_color('green')
            print("笔刷颜色: 绿色")
        elif key == pygame.K_4:
            self.brush_engine.change_color('black')
            print("笔刷颜色: 黑色")
        elif key == pygame.K_PLUS or key == pygame.K_EQUALS:
            # 增大笔刷
            current_size = self.brush_engine.brush.size
            self.brush_engine.change_size(current_size + 2)
            print(f"笔刷大小: {self.brush_engine.brush.size}")
        elif key == pygame.K_MINUS:
            # 减小笔刷
            current_size = self.brush_engine.brush.size
            self.brush_engine.change_size(current_size - 2)
            print(f"笔刷大小: {self.brush_engine.brush.size}")
        elif key == pygame.K_v:  # V键切换语音控制
            self.toggle_voice_control()

    def save_drawing_with_dialog(self):
        """保存画布并显示对话框"""
        try:
            # 暂停手势识别
            self.is_paused = True

            # 保存图片
            filename = f"drawing_{int(time.time())}"
            success = self.canvas_manager.save_canvas(filename)

            if success:
                self.last_save_filename = filename
                # 显示确认对话框
                self.dialog_manager.show_save_confirm(
                    filename,
                    self.on_dialog_finished
                )
            else:
                print("保存失败")
                self.is_paused = False

        except Exception as e:
            print(f"保存失败: {e}")
            self.is_paused = False

    def on_dialog_finished(self, convert_art, style=None, prompt=None):
        """对话框完成回调"""

        print("✅ 成功收到：")
        print("style =", style)
        print("prompt =", prompt)

        # 恢复手势识别
        self.is_paused = False

        if convert_art:
            # 创建新任务
            filename = f"assets/saved_drawings/{self.dialog_manager.saved_filename}.png"
            
            new_task = {
                "id": int(time.time() * 1000),
                "filename": self.dialog_manager.saved_filename,
                "full_path": filename,
                "style": style,
                "prompt": prompt,
                "progress": 0,
                "status": "等待处理...",
                "thumbnail": None,
                "finished": False,
                "remove_time": 0
            }
            
            # 加载缩略图
            try:
                if os.path.exists(filename):
                    img = pygame.image.load(filename).convert()
                    new_task["thumbnail"] = pygame.transform.scale(img, (100, 66))
            except Exception as e:
                print(f"加载缩略图失败: {e}")

            # 添加到列表和队列
            self.processing_tasks.append(new_task)
            self.task_queue.put(new_task)

    def art_worker(self):
        """后台处理线程：串行处理生成任务"""
        converter = None
        while True:
            try:
                # 获取任务
                task = self.task_queue.get()
                
                # 如果还没有加载模型，先加载
                if converter is None:
                    task["status"] = "正在加载AI模型(首次运行较慢)..."
                    try:
                        converter = DoodleToArtConverter()
                    except Exception as e:
                        print(f"模型加载失败: {e}")
                        task["status"] = "模型加载失败"
                        task["finished"] = True
                        task["remove_time"] = time.time() + 5
                        self.task_queue.task_done()
                        continue

                # 执行任务
                self.run_art_generation_task(converter, task)
                self.task_queue.task_done()
                
            except Exception as e:
                print(f"Worker error: {e}")

    def run_art_generation_task(self, converter, task):
        """执行单个艺术生成任务"""
        filename = task["full_path"]
        style = task["style"]
        prompt = task["prompt"]
        
        try:
            # 定义进度回调
            def progress_callback(progress, status):
                task["progress"] = progress
                task["status"] = status
                
            doodle_img = Image.open(filename)
            creations, processed_doodle = converter.auto_generate_from_doodle(
                doodle_img, 
                num_creations=1, 
                style=style,
                prompt=prompt,
                progress_callback=progress_callback
            )

            # 获取保存的路径，不显示plt窗口
            saved_paths = converter.save_and_display_results(processed_doodle, creations, show_plot=False)
            print(f"艺术化转换完成，风格: {style}")
            
            task["status"] = "完成"
            task["progress"] = 100
            task["finished"] = True
            task["remove_time"] = time.time() + 5 # 5秒后消失

            # 将结果路径存入任务对象，供主线程显示
            if saved_paths and saved_paths.get('creations'):
                task["result_paths"] = {
                    "original": saved_paths['original'],
                    "generated": saved_paths['creations'][0]
                }
                task["needs_display"] = True
            
        except Exception as e:
            print(f"艺术化转换失败: {e}")
            task["status"] = f"失败: {str(e)[:15]}..."
            task["finished"] = True
            task["remove_time"] = time.time() + 5

    def process_camera_frame(self):
        """处理摄像头帧并进行手势识别"""
        ret, frame = self.cap.read()
        if not ret:
            print("无法读取摄像头帧")
            return None, None

        # 水平翻转帧（镜像效果）
        frame = cv2.flip(frame, 1)
        
        # 只有在未暂停时才进行手势识别
        if not self.is_paused:
            self.gesture_detector.recognize_gesture(frame)
            gesture_info = self.gesture_detector.get_gesture_info()

            swapped_frame=self.face_swapper.detect_and_swap(frame,self.gesture_commands.current_face_source)
            if swapped_frame is not None:
                frame=swapped_frame


        else:
            # 暂停时，不进行手势识别，但仍然返回一个空的gesture_info
            gesture_info = None


        self.cursor_layer.fill((0, 0, 0, 0))
        # 在帧上绘制手势信息
        if gesture_info:
            frame=self.visualizer.draw_landmarks(frame, gesture_info)
            # frame = self.gesture_detector.draw_landmarks_and_gesture(frame, gesture_info)
            frame=self.visualizer.draw_gesture_info(frame, gesture_info)

            if gesture_info['landmarks']:
                landmarks=gesture_info['landmarks'][0]
                index_tip=landmarks[8]
                canvas_x,canvas_y=self.coord_transformer.camera_to_canvas(index_tip["x"],index_tip["y"])
                frame=self.visualizer.draw_brush(self.brush_engine.brush.color,
                                                 self.brush_engine.brush.size+20,canvas_x+self.camera_width,canvas_y+self.camera_height,self.cursor_layer,frame)

                # 修改
                self.screen.blit(self.cursor_layer, (0, 0))



        else:
            # 如果暂停，在画面上显示"PAUSED"
            if self.is_paused:
                cv2.putText(frame, "PAUSED", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)



        return frame, gesture_info

    def process_gesture_commands(self, gesture_info):
        """处理手势命令"""
        if not gesture_info or not gesture_info['gesture']:
            return

        current_time = time.time()
        gesture = gesture_info['gesture'][0]
        gesture_name = gesture['category_name']

        # 手势冷却时间检查
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return

        # 执行手势命令
        result = self.gesture_commands.execute_command(gesture_name)
        if result:
            self.last_gesture_time = current_time
            self.current_gesture = gesture_name
            print(f"手势命令: {gesture_name} -> {result.message}")


            if gesture_name == "Victory" and not self.is_paused and not self.dialog_manager.is_active():
                self.save_drawing_with_dialog()


    def process_drawing(self, gesture_info):
        """处理绘画逻辑"""
        if not gesture_info or not gesture_info['gesture'] or not gesture_info['landmarks'] or \
                gesture_info['gesture'][0] is None:
            self.drawing_active = False
            self.last_point = None
            return

        gesture = gesture_info['gesture'][0]
        landmarks = gesture_info['landmarks'][0]

        # 获取食指指尖坐标（绘画点）
        index_tip = landmarks[8]
        canvas_x, canvas_y = self.coord_transformer.camera_to_canvas(
            index_tip['x'], index_tip['y']
        )

        current_point = (canvas_x, canvas_y)

        if gesture['category_name'] == 'Pointing_Up':
            # 上指手势 - 开始/继续绘画
            if not self.drawing_active:
                # 开始新线条
                self.drawing_active = True
                self.canvas_manager.draw_point(canvas_x, canvas_y, self.brush_engine.brush)
            elif self.last_point:
                # 连接前后点形成连续线条
                self.canvas_manager.draw_line(self.last_point, current_point, self.brush_engine.brush)

            self.last_point = current_point
        else:
            # 其他手势 - 停止绘画
            self.drawing_active = False
            self.last_point = None

    def convert_cv2_to_pygame(self, frame):
        """将OpenCV帧转换为Pygame表面"""
        # 水平翻转图像（镜像效果）
        frame = cv2.flip(frame, 1)  # 1表示水平翻转
        # 转换颜色空间 BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 旋转和转置以适应Pygame坐标系统
        frame_rgb = np.rot90(frame_rgb)
        # 创建Pygame表面
        return pygame.surfarray.make_surface(frame_rgb)

    def load_gesture_icons(self):
        """加载手势图标资源"""
        icons_config = {
            "Victory": ["assets/icons/victory.png", (self.camera_width + self.canvas_width + 60, 265)],
            "Closed_Fist": ["assets/icons/closed_fist.png", (self.camera_width + self.canvas_width + 60, 240)],
            "Open_Palm": ["assets/icons/open_arm.png", (self.camera_width + self.canvas_width + 60, 215)],
            "Pointing_UP": ["assets/icons/pointing_up.png", (self.camera_width + self.canvas_width + 60, 190)],
            "Thumb_Up": ["assets/icons/thumb_up.png", (self.camera_width + self.canvas_width + 60, 290)],
            "Thumb_Down": ["assets/icons/thumb_down.png", (self.camera_width + self.canvas_width + 60, 315)],
            "ILoveYou": ["assets/icons/finger_heart.png", (self.camera_width + self.canvas_width + 60, 340)],
        }
        
        self.gesture_icons_data = {}
        for name, (path, pos) in icons_config.items():
            try:
                if os.path.exists(path):
                    print(f"正在加载图标: {name} ({path})...")
                    image = pygame.image.load(path).convert_alpha()
                    scaled_image = pygame.transform.scale(image, (20, 20))
                    self.gesture_icons_data[name] = (scaled_image, pos)
                    print(f"成功加载: {name}")
                else:
                    print(f"警告: 图标文件不存在 {path}")
            except Exception as e:
                print(f"加载图标失败 {name}: {e}")


    def draw_ui(self):
        """绘制用户界面"""
        # 清屏
        self.screen.fill(self.colors['background'])

        # 绘制摄像头区域背景
        pygame.draw.rect(self.screen, (0, 0, 0), (20, 20, self.camera_width, self.camera_height))

        # 绘制画布区域背景
        pygame.draw.rect(self.screen, (122, 255, 255),
                         (self.camera_width + 40, 250, self.canvas_width, self.canvas_height))

        # 绘制控制面板背景
        panel_x = self.camera_width + self.canvas_width + 60
        pygame.draw.rect(self.screen, self.colors['panel'],
                         (panel_x, 20, self.panel_width, self.screen_height - 40))

        # 绘制分隔线
        pygame.draw.line(self.screen, (200, 200, 200),
                         (self.camera_width + 30, 0),
                         (self.camera_width + 30, self.screen_height), 2)
        pygame.draw.line(self.screen, (200, 200, 200),
                         (panel_x - 10, 0),
                         (panel_x - 10, self.screen_height), 2)

        # 绘制标题
        title = self.font.render("手势控制空气绘画系统", True, self.colors['text'])
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 10))

        # 绘制控制面板内容
        y_offset = 40
        panel_texts = [
            "控制面板",
            "-------------",
            f"笔刷颜色: {self.get_color_name()}",
            f"笔刷大小: {self.brush_engine.brush.size}",
            "",
            "手势命令:",
            "  上指: 绘画",
            "  张开手掌: 清空",
            "  握拳: 撤销",
            "  胜利手势: 保存",
            "  大拇指朝上: 增大笔刷",
            "  大拇指朝下: 减小笔刷",
            "  比心手势：切换源头像",
            "",
            "键盘快捷键:",
            "- ESC: 退出",
            "- C: 清空画布",
            "- S: 保存画布",
            "- 1-4: 切换颜色",
            "- +/-: 调整大小",
             "-------------",
            "语音指令:",
            "  说'保存'等: 保存",
            "  说'清空'等: 清空",
            "  说'红色/蓝色'等: 换色",
            "  说'大点/小点'等: 粗细",
            "  说'撤销'等: 撤销",
            "  说'暂停/恢复'等: 控制",
            "-------------",
            "一次最多显示三个任务"
        ]

        for text in panel_texts:
            if text:
                text_surface = self.small_font.render(text, True, self.colors['text'])
                self.screen.blit(text_surface, (panel_x + 10, y_offset))
            y_offset += 25

        if hasattr(self, 'gesture_icons_data'):
            for _, (icon_surface, pos) in self.gesture_icons_data.items():
                self.screen.blit(icon_surface, pos)

        # 绘制状态信息
        gesture_map = {
            "Pointing_Up": "上指(绘画)",
            "Open_Palm": "张开手掌(清空)",
            "Closed_Fist": "握拳(撤销)",
            "Victory": "胜利手势(保存)",
            "Thumb_Up": "大拇指上(变大)",
            "Thumb_Down": "大拇指下(变小)",
            "ILoveYou": "比心(切换头像)",
            "None": "无"
        }
        display_gesture = gesture_map.get(self.current_gesture, self.current_gesture or "无")

        status_text = f"状态: {'绘画中' if self.drawing_active else '待机'} | 手势: {self.current_gesture or '无'}"
        status_surface = self.small_font.render(status_text, True, self.colors['text'])
        self.screen.blit(status_surface, (20, self.camera_height + 40))

        # 绘制语音命令面板
        # if self.voice_active:
        #      self.draw_voice_panel()

        # 绘制语音动态显示文本
        current_time = time.time()
        # 1. 绘制识别结果及视觉反馈
        if self.voice_display_text and current_time - self.voice_display_timer < 3.0:  # 显示3秒
            # 计算文字宽度及背景
            text_surf = self.font.render(f"语音: {self.voice_display_text}", True, (255, 255, 255))
            padding = 10
            width = text_surf.get_width() + padding * 2
            height = text_surf.get_height() + padding * 2

            # 显示在屏幕顶部中间略下方
            x = (self.screen_width - width) // 2
            y = 80

            # 动态背景（正在识别时为黄色，识别完成为绿色）
            # 由于没有is_listening状态，这里简单用时间判断
            bg_color = (0, 180, 0, 180)  # 绿色半透明

            # 绘制圆角背景
            s = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(s, bg_color, (0, 0, width, height), border_radius=10)
            self.screen.blit(s, (x, y))
            self.screen.blit(text_surf, (x + padding, y + padding))

        # 2. 绘制命令触发时的全屏闪烁特效
        if current_time - self.voice_visual_flash < 0.2:  # 闪烁持续0.2秒
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            color = (50, 255, 50, 100) if self.voice_command_executed else (100, 100, 255, 60)
            overlay.fill(color)
            self.screen.blit(overlay, (0, 0))

        # 绘制艺术生成任务列表
        # 检查是否有任务需要显示结果
        for task in self.processing_tasks:
            if task.get("finished") and task.get("needs_display"):
                # 触发结果展示对话框
                self.dialog_manager.show_art_result(
                    task["result_paths"]["original"],
                    task["result_paths"]["generated"],
                    task["prompt"]
                )
                task["needs_display"] = False # 标记为已显示

        # 清理已完成并超时的任务
        current_time = time.time()
        self.processing_tasks = [t for t in self.processing_tasks if not (t["finished"] and current_time > t["remove_time"])]

        if self.processing_tasks:
            panel_height = 110
            panel_width = 400
            base_x = 20
            base_y = self.screen_height - panel_height - 10
            
            # 倒序遍历，最新的显示在最下面（或者最上面，这里选择堆叠显示）
            # 假设最多显示3个，避免遮挡太多
            visible_tasks = self.processing_tasks[:3]
            
            for index, task in enumerate(visible_tasks):
                # 计算每个面板的位置，向上堆叠
                # 倒序索引，让最新的(index=len-1)显示在最下面(base_y)
                panel_y = base_y - (index * (panel_height + 10))
                panel_x = base_x
                
                # 背景
                pygame.draw.rect(self.screen, (245, 245, 245), (panel_x, panel_y, panel_width, panel_height))
                pygame.draw.rect(self.screen, (200, 200, 200), (panel_x, panel_y, panel_width, panel_height), 1)
                
                # 缩略图
                if task["thumbnail"]:
                    self.screen.blit(task["thumbnail"], (panel_x + 10, panel_y + 10))
                
                # 文本信息
                text_x = panel_x + 120
                title_surf = self.small_font.render("艺术创作任务", True, (0, 0, 0))
                self.screen.blit(title_surf, (text_x, panel_y + 10))
                
                name_surf = self.small_font.render(f"文件: {task['filename']}", True, (100, 100, 100))
                self.screen.blit(name_surf, (text_x, panel_y + 35))
                
                style_surf = self.small_font.render(f"风格: {task['style']}", True, (100, 100, 100))
                self.screen.blit(style_surf, (text_x, panel_y + 55))
                
                status_color = (0, 120, 215) if not task["finished"] else (0, 200, 0)
                status_surf = self.small_font.render(f"进度: {task['status']}", True, status_color)
                self.screen.blit(status_surf, (text_x, panel_y + 75))
                
                # 进度条
                bar_width = panel_width - 130
                bar_height = 6
                bar_x = text_x
                bar_y = panel_y + 100
                
                # 进度条背景
                pygame.draw.rect(self.screen, (220, 220, 220), (bar_x, bar_y, bar_width, bar_height))
                # 进度条前景
                progress_width = int(bar_width * (task["progress"] / 100))
                pygame.draw.rect(self.screen, status_color, (bar_x, bar_y, progress_width, bar_height))

    def get_color_name(self):
        """获取当前颜色的名称"""
        color = self.brush_engine.brush.color
        for name, value in self.brush_engine.colors.items():
            if value == color:
                return name
        return "自定义"

    def update_display(self, camera_frame):
        """更新显示"""
        # 绘制UI框架
        self.draw_ui()

        # 显示摄像头画面
        if camera_frame is not None:
            camera_surface = self.convert_cv2_to_pygame(camera_frame)
            self.screen.blit(camera_surface, (20, 20))

            # 如果暂停，显示半透明遮罩
            if self.is_paused:
                pause_overlay = pygame.Surface((self.camera_width, self.camera_height), pygame.SRCALPHA)
                pause_overlay.fill(self.colors['pause_overlay'])
                self.screen.blit(pause_overlay, (20, 20))

                # 显示"暂停"文字
                pause_text = self.font.render("系统暂停", True, (255, 255, 255))
                pause_rect = pause_text.get_rect(center=(20 + self.camera_width // 2,
                                                         20 + self.camera_height // 2))
                self.screen.blit(pause_text, pause_rect)

        # 显示画布
        canvas_surface = self.canvas_manager.canvas
        self.screen.blit(canvas_surface, (self.camera_width + 40, 250))

        #显示笔刷预览
        self.visualizer.draw_brush_preview(self.brush_engine.brush,(self.camera_width+20+self.canvas_width//2,100))

        # 更新显示
        pygame.display.flip()

        # 绘制对话框（如果有）
        if self.dialog_manager.is_active():
            self.dialog_manager.draw(self.screen)
            pygame.display.flip()  # 确保对话框立即显示

    def handle_voice_command(self, text, start_time, end_time, is_final=True):
        """统一处理语音命令（防崩溃版）"""
        import threading
        print(f"[Voice] Current thread: {threading.current_thread().name}", flush=True)

        if text is None:
            return

        # 更新显示文本
        self.voice_display_text = text
        self.voice_display_timer = time.time()

        # 只有在最终结果时才进行命令处理
        if not is_final:
            return

        text = text.lower().strip()
        command_found = False

        state = self.dialog_manager.state
        event = {}  # 初始化空事件

        try:
            print(f"[Voice] state={state}, text='{text}'")
            # 将语音输入根据输入框状态分为4种情况
            if state == DialogState.INACTIVE:
                # 控制类命令
                if any(cmd in text for cmd in ["保存", "存下来", "保存画布"]):
                    self.save_drawing_with_dialog()
                    command_found = True

                    self.trigger_voice_feedback(is_command=True)
                    return
                elif any(cmd in text for cmd in ["暂停", "停止", "等一下"]):
                    self.is_paused = True
                    print("系统已暂停")
                    command_found = True
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif any(cmd in text for cmd in ["恢复", "继续", "开始"]):
                    self.is_paused = False
                    print("系统已恢复")
                    command_found = True
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif any(cmd in text for cmd in ["清空", "清除", "重置"]):
                    self.canvas_manager.clear_canvas()
                    print("画布已清空")
                    command_found = True
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif any(cmd in text for cmd in ["撤销", "回退", "上一步"]):
                    self.canvas_manager.undo()
                    print("已撤销")
                    command_found = True
                    self.trigger_voice_feedback(is_command=True)
                    return

                # 笔刷控制
                elif "红色" in text:
                    self.brush_engine.change_color('red')
                    print("笔刷切换为红色")
                    command_found = True
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif "蓝色" in text:
                    self.brush_engine.change_color('blue')
                    print("笔刷切换为蓝色")
                    command_found = True
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif "绿色" in text:
                    self.brush_engine.change_color('green')
                    print("笔刷切换为绿色")
                    command_found = True
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif "黑色" in text:
                    self.brush_engine.change_color('black')
                    print("笔刷切换为黑色")
                    command_found = True
                    self.trigger_voice_feedback(is_command=True)
                    return

                # 笔刷大小
                elif any(cmd in text for cmd in ["大点", "粗点", "增大", "变大", "变粗"]):
                    current = self.brush_engine.brush.size
                    self.brush_engine.change_size(min(50, current + 5))
                    print(f"笔刷增大到 {self.brush_engine.brush.size}")
                    command_found = True
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif any(cmd in text for cmd in ["小点", "细点", "减小", "变小", "变细"]):
                    current = self.brush_engine.brush.size
                    self.brush_engine.change_size(max(1, current - 5))
                    print(f"笔刷减小到 {self.brush_engine.brush.size}")
                    command_found = True
                    self.trigger_voice_feedback(is_command=True)
                    return
                return

            elif state == DialogState.SAVE_CONFIRM:
                if any(cmd in text for cmd in ["保存", "存下来", "保存画布", "确定", "确认"]):
                    event["result"] = "OK"
                    print("确定保存")
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    print("[Voice] Returned from dialog_manager, now returning")
                    return
                elif any(cmd in text for cmd in ["暂停", "停止", "取消"]):
                    event["result"] = 'CANCEL'
                    print("保存已取消")
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                return

            elif state == DialogState.PROMPT_INPUT:
                if any(cmd in text for cmd in ["保存", "存下来", "确定", "确认"]):
                    event["result"] = "OK"
                    print("确定保存")
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    print("[Voice] Returned from dialog_manager, now returning")
                    return
                elif any(cmd in text for cmd in ["暂停", "停止", "取消"]):
                    event["result"] = 'CANCEL'
                    print("保存已取消")
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif any(cmd in text for cmd in ["清空", "全部删除"]):
                    event["result"] = 'CLEAR'
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif any(cmd in text for cmd in ["删除", "回退"]):
                    event["result"] = 'BACKSPACE'
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                else:
                    event["result"] = 'INPUT'
                    event["content"] = text
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
            elif state == DialogState.STYLE_SELECT:
                # 1. 语音直接选择具体风格（匹配风格列表）
                style_map = {
                    "油画": "masterpiece oil painting",
                    "水彩": "beautiful watercolor art",
                    "数字艺术": "professional digital artwork",
                    "概念艺术": "fantasy concept art",
                    "线描": "minimalist line art",
                    "超现实": "surreal dreamlike painting",
                    "水墨画": "elegant ink drawing",
                    "校园风": "school style",
                }
                selected_style = None
                for chinese, english in style_map.items():
                    if chinese in text or english.lower() in text:
                        selected_style = english
                        break

                if selected_style:
                    # 直接选中风格并确认
                    if hasattr(self.dialog_manager, 'current_dialog') and self.dialog_manager.current_dialog:
                        if hasattr(self.dialog_manager.current_dialog, 'selected_option'):
                            # 找到风格对应的索引
                            for idx, opt in enumerate(self.dialog_manager.current_dialog.options):
                                if opt == selected_style:
                                    self.dialog_manager.current_dialog.selected_option = idx
                                    self.dialog_manager.current_dialog.result = selected_style
                                    break
                    event["result"] = "OK"
                    print(f"语音选择风格: {selected_style}")
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif any(cmd in text for cmd in ["diy", "自定义"]):
                    # 语音直接选择DIY
                    if hasattr(self.dialog_manager, 'current_dialog') and self.dialog_manager.current_dialog:
                        if hasattr(self.dialog_manager.current_dialog, 'result'):
                            self.dialog_manager.current_dialog.result = "自定义"
                    event["result"] = "OK"
                    print("语音选择: 自定义")
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                # 2. 语音确认当前选中的风格
                elif any(cmd in text for cmd in ["保存", "存下来", "确定", "确认"]):
                    event["result"] = "OK"
                    print("确认选择风格")
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                # 3. 语音取消
                elif any(cmd in text for cmd in ["暂停", "停止", "取消"]):
                    event["result"] = 'CANCEL'
                    print("取消风格选择")
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                return

            elif state == DialogState.STYLE_INPUT:
                if any(cmd in text for cmd in ["保存", "存下来", "确定", "确认"]):
                    event["result"] = "OK"
                    print("确定保存")
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    print("[Voice] Returned from dialog_manager, now returning")
                    return
                elif any(cmd in text for cmd in ["暂停", "停止", "取消"]):
                    event["result"] = 'CANCEL'
                    print("保存已取消")
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif any(cmd in text for cmd in ["清空", "全部删除"]):
                    event["result"] = 'CLEAR'
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                elif any(cmd in text for cmd in ["删除", "回退"]):
                    event["result"] = 'BACKSPACE'
                    command_found = True
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return
                else:
                    event["result"] = 'INPUT'
                    event["content"] = text
                    self.dialog_manager.handle_event(event)
                    self.trigger_voice_feedback(is_command=True)
                    return

        except Exception as e:
            # 捕获所有异常，避免崩溃
            print(f"语音命令处理异常: {e}")
            import traceback
            traceback.print_exc()

    def trigger_voice_feedback(self, is_command=True):
        """触发语音反馈特效"""
        # 视觉特效：屏幕闪烁
        self.voice_visual_flash = time.time()
        self.voice_command_executed = is_command

        # 音效反馈（简单beep）
        try:
            import winsound
            if is_command:
                # 成功识别命令：高频短音
                winsound.Beep(1000, 150)
            else:
                # 普通输入：低频短音
                winsound.Beep(800, 100)
        except ImportError:
            # 非Windows环境或模块缺失
            pass
        except Exception:
            pass

    def toggle_voice_control(self):
        """切换语音控制状态"""
        if not self.voice_controller:
            print("语音识别器未初始化")
            return

        if not self.voice_active:
            try:
                # 在新线程中启动语音识别
                import threading
                self.voice_thread = threading.Thread(
                    target=self.voice_controller.start,
                    daemon=True
                )
                self.voice_thread.start()
                self.voice_active = True
                print("🔊 语音控制已启用")
            except Exception as e:
                print(f"启动语音控制失败: {e}")
                self.voice_active = False
        else:
            try:
                self.voice_controller.stop()
                self.voice_active = False
                print("🔇 语音控制已关闭")
            except Exception as e:
                print(f"关闭语音控制失败: {e}")

    def save_current_doodle(self):
        try:
            # 暂停手势识别
            self.is_paused = True

            # 保存图片
            filename = f"drawing_{int(time.time())}"
            success = self.canvas_manager.save_canvas(filename)

            if success:
                self.last_save_filename = filename
            else:
                print("保存失败")
                self.is_paused = False

        except Exception as e:
            print(f"保存失败: {e}")
            self.is_paused = False

    def run(self):
        """主循环"""
        print("启动手势控制空气绘画系统...")
        print("按ESC键退出程序")

        while self.running:
            # 处理事件
            self.handle_events()


            # 如果有活动对话框，只更新对话框
            if self.dialog_manager.is_active():
                # 绘制背景（但不更新摄像头）
                self.draw_ui()
                if hasattr(self, 'last_camera_surface'):
                    self.screen.blit(self.last_camera_surface, (20, 20))

                # 绘制对话框
                self.dialog_manager.draw(self.screen)

                pygame.display.flip()

                # DEBUG: 启动时直接显示对话框
                # self.debug_test_dialog()
            else:

                # 处理摄像头帧和手势识别
                camera_frame, gesture_info = self.process_camera_frame()

                if camera_frame is not None:
                    # 保存最后一帧用于对话框显示
                    self.last_camera_surface = self.convert_cv2_to_pygame(camera_frame)

                    # 只有在未暂停时才处理手势命令和绘画
                    if not self.is_paused:
                        self.process_gesture_commands(gesture_info)
                        self.process_drawing(gesture_info)

                    # 更新显示
                    self.update_display(camera_frame)

            # 控制帧率
            self.clock.tick(self.fps)

        self.cleanup()

    def cleanup(self):
        """清理资源"""
        print("正在退出程序...")
        if hasattr(self, 'cap'):
            self.cap.release()
        pygame.quit()
        sys.exit()


def main():
    app = AirPaintingApp()
    app.run()


if __name__ == "__main__":
    main()