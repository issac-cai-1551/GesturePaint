# dialog_manager.py
import pygame
from enum import Enum
from pathlib import Path


class DialogState(Enum):
    INACTIVE = 0
    SAVE_CONFIRM = 1
    STYLE_SELECT = 2
    STYLE_DIY = 3


class DialogManager:
    """对话框管理器"""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = DialogState.INACTIVE
        self.current_dialog = None
        self.callback = None
        self.saved_filename = ""

        # 字体路径
        project_root = Path(__file__).parent.parent.parent
        self.font_path = project_root / "assets" / "fonts" / "SourceHanSansSC-Regular.otf"

        if self.font_path.exists():
            self.title_font = pygame.font.Font(str(self.font_path), 24)
            self.button_font = pygame.font.Font(str(self.font_path), 20)
        else:
            self.title_font = pygame.font.SysFont(None, 24)
            self.button_font = pygame.font.SysFont(None, 20)

        # 颜色定义
        self.colors = {
            'background': (255, 255, 255),
            'border': (0, 0, 0),
            'title_bar': (70, 130, 180),
            'title_text': (255, 255, 255),
            'message_text': (0, 0, 0),
            'button_normal': (200, 200, 200),
            'button_hover': (220, 220, 220),
            'button_text': (0, 0, 0),
            'overlay': (0, 0, 0, 128)  # 半透明黑色
        }

    def show_art_result(self, original_path, generated_path, prompt):
        """显示艺术创作结果对话框"""
        self.state = DialogState.ART_RESULT
        
        # 创建结果展示对话框
        dialog_rect = pygame.Rect(0, 0, 900, 600)
        dialog_rect.center = (self.screen_width // 2, self.screen_height // 2)
        
        from src.features.art_result_dialog import ArtResultDialog
        self.current_dialog = ArtResultDialog(
            dialog_rect,
            original_path,
            generated_path,
            prompt,
            self.font_path
        )
        self.current_dialog.show()
        # 结果展示不需要回调，关闭即可
        self.callback = None

    def show_save_confirm(self, filename, callback):
        """显示保存确认对话框"""
        self.state = DialogState.SAVE_CONFIRM
        self.saved_filename = filename
        self.callback = callback

        # 创建确认对话框
        dialog_rect = pygame.Rect(0, 0, 500, 200)
        dialog_rect.center = (self.screen_width // 2, self.screen_height // 2)

        from src.features.custom_dialog import CustomDialog
        self.current_dialog = CustomDialog(
            dialog_rect,
            "保存成功",
            f"图片已保存为: {filename}.png\n是否进行艺术化创作?",
            self.font_path,
            16
        )
        self.current_dialog.show()

    def show_style_select(self, styles, callback):
        """显示风格选择对话框"""
        self.state = DialogState.STYLE_SELECT

        # 创建选项对话框
        dialog_rect = pygame.Rect(0, 0, 550, 400)
        dialog_rect.center = (self.screen_width // 2, self.screen_height // 2)

        from src.features.custom_dialog import OptionDialog
        self.current_dialog = OptionDialog(
            dialog_rect,
            "创作风格选择",
            "请选择一个你喜欢的艺术风格:",
            styles,
            self.font_path,
            12,
            columns=2
        )
        self.current_dialog.show()

        self.callback = callback

    def update(self):
        """更新对话框状态"""
        if self.current_dialog:
            self.current_dialog.update()

    def draw(self, screen):
        """绘制对话框"""
        if self.current_dialog and self.current_dialog.visible:
            # 绘制半透明背景遮罩
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill(self.colors['overlay'])
            screen.blit(overlay, (0, 0))

            # 绘制对话框
            self.current_dialog.draw(screen)

    def handle_event(self, event):
        """处理对话框事件"""
        if not self.current_dialog or not self.current_dialog.visible:
            return False
        result = None
        if isinstance(event,pygame.event.EventType):
            result = self.current_dialog.handle_event(event)
        # 处理voice调用,此时event的是字典，存储信息
        elif isinstance(event, dict):
            result = event["result"]


        if result:
            if self.state == DialogState.SAVE_CONFIRM:
                if result == "OK":
                    # 用户确认进行艺术化创作
                    styles = [
                        "masterpiece oil painting",
                        "beautiful watercolor art",
                        "professional digital artwork",
                        "fantasy concept art",
                        "minimalist line art",
                        "surreal dreamlike painting",
                        "vibrant pop art style",
                        "elegant ink drawing",
                        'DIY'
                    ]
                    self.show_style_select(styles, self.callback)
                else:
                    # 用户取消，关闭对话框
                    self.close_dialog()
                    if self.callback:
                        self.callback(False, None)

            elif self.state == DialogState.STYLE_SELECT:
                if result == "OK":
                    # 用户选择了风格
                    selected_style = None
                    if hasattr(self.current_dialog, 'selected_style'):
                        selected_style = self.current_dialog.selected_style
                    elif hasattr(self.current_dialog, 'result'):
                        selected_style = self.current_dialog.result
                    self.close_dialog()
                    # 如果选择是自定义
                    if selected_style == "DIY":
                        self.show_input_dialog()
                    elif self.callback:
                        self.callback(True, selected_style)
                elif result == "CANCEL":
                    # 用户取消风格选择
                    self.close_dialog()
                    if self.callback:
                        self.callback(False, None)
            #添加自定义输入
            elif self.state == DialogState.STYLE_DIY:
                if hasattr(self.current_dialog, 'input_text'):
                    style = self.current_dialog.input_text
                if result == "OK":
                    self.close_dialog()
                    if self.callback:
                        self.callback(True, style)
                elif result == "CANCEL":
                    self.close_dialog()
                    if self.callback:
                        self.callback(False, None)
                elif result == "INPUT":
                    if isinstance(event,dict):
                        self.current_dialog.insert_text(event["content"])
        return True

    def show_input_dialog(self):
        self.state = DialogState.STYLE_DIY
        # 创建选项对话框
        dialog_rect = pygame.Rect(0, 0, 550, 400)
        dialog_rect.center = (self.screen_width // 2, self.screen_height // 2)
    #
        from src.features.custom_dialog import InputDialog
        self.current_dialog = InputDialog(
            dialog_rect,
            "创作风格自定义",
            "请说出一个你喜欢的艺术风格:",
            "默认",
            self.font_path,
            12
        )
        self.current_dialog.show()


    def close_dialog(self):
        """关闭对话框"""
        if self.current_dialog:
            self.current_dialog.hide()
        self.current_dialog = None
        self.state = DialogState.INACTIVE

    def is_active(self):
        """检查对话框是否激活"""
        return self.state != DialogState.INACTIVE and self.current_dialog and self.current_dialog.visible