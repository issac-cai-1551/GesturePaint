import time
from pathlib import Path

class CommandResult:
    def __init__(self, success, message, data=None):
        self.success = success    # 执行是否成功
        self.message = message    # 用户反馈信息
        self.data = data          # 额外数据


class GestureCommands:
    def __init__(self,canvas_manager,brush_engine):
        self.current_filename = None
        self.command_map={
            "Open_Palm":self.clear_canvas,
            "Closed_Fist":self.undo_last_action,
            "Victory":self.save_drawing,
            "Thumb_Up":self.increase_brush_size,
            "Thumb_Down":self.decrease_brush_size,
            "Pointing_Up":self.start_drawing,
            "ILoveYou":self.change_face_source
        }
        self.canvas_manager = canvas_manager
        self.brush_engine= brush_engine
        self.last_command_time = {}  # 防抖处理
        self.command_cooldown = 1.0  # 命令冷却时间

        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        assets_dir = project_root / "assets" / "avatar_sticker"

        self.face_sources = [
            str(assets_dir / "img1.png"),
            str(assets_dir / "img2.png"),
            str(assets_dir / "img3.png"),
            str(assets_dir / "img4.jpeg"),
            str(assets_dir / "img5.webp"),
            str(assets_dir / "img6.webp"),
            str(assets_dir / "img7.webp"),
            None
        ]

        self.current_face_source_index = 4
        self.face_source_size=len(self.face_sources)
        self.current_face_source = self.face_sources[self.current_face_source_index]



    def change_brush_color(self):
        self.brush_engine.change_brush_color()
    def change_brush_size(self):
        self.brush_engine.change_brush_size()

    def execute_command(self,gesture_name,hand_landmarks=None):
        # 防抖处理：避免重复触发
        current_time = time.time()
        if (gesture_name in self.last_command_time and
                current_time - self.last_command_time[gesture_name] < self.command_cooldown):
            return None

        if gesture_name in self.command_map:
            # 执行命令
            result = self.command_map[gesture_name](hand_landmarks)
            self.last_command_time[gesture_name] = current_time

            # 提供用户反馈
            self.provide_feedback(result, gesture_name)
            return result

        return None

    def provide_feedback(self, result, gesture_name):
        """提供用户反馈（简化版）"""
        if result and result.success:
            print(f"✓ {result.message}")
        else:
            error_msg = result.message if result else "未知命令"
            print(f"✗ {error_msg}")

    def clear_canvas(self, landmarks=None):
        """清空画布命令"""
        try:
            self.canvas_manager.clear_canvas()
            return CommandResult(True, "画布已清空")
        except Exception as e:
            return CommandResult(False, f"清空失败: {str(e)}")

    def undo_last_action(self, landmarks=None):
        """撤销上一步"""
        if hasattr(self.canvas_manager, 'undo'):
            success = self.canvas_manager.undo()
            message = "已撤销" if success else "无法撤销"
            return CommandResult(success, message)
        return CommandResult(False, "撤销功能未实现")

    def increase_brush_size(self, landmarks=None):
        """增大笔刷"""
        current_size = self.brush_engine.brush.size
        new_size = min(50, current_size + 2)
        self.brush_engine.change_size(new_size)
        return CommandResult(True, f"笔刷大小: {new_size}")

    def save_drawing(self, landmarks=None):
        """保存绘画"""
        filename = f"drawing_{int(time.time())}"
        success = self.canvas_manager.save_canvas(filename)  # 假设save_canvas返回布尔值
        if success:
            self.current_filename = filename
            return CommandResult(True, f"已保存: {filename}", filename)
        else:
            return CommandResult(False, "保存失败")

    def decrease_brush_size(self, landmarks=None):
        """减小笔刷"""
        current_size = self.brush_engine.brush.size
        new_size = max(1, current_size - 2)
        self.brush_engine.change_size(new_size)
        return CommandResult(True, f"笔刷大小: {new_size}")

    def start_drawing(self, landmarks=None):
        """开始绘画（上指手势）"""
        return CommandResult(True, "开始绘画")

    def change_face_source(self,landmarks=None):
        self.current_face_source_index += 1
        if self.current_face_source_index >= self.face_source_size:
            self.current_face_source_index = 0
        self.current_face_source = self.face_sources[self.current_face_source_index]
        return CommandResult(True, "已切换源头像")

