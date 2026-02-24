# dialog_manager.py
import pygame
from enum import Enum
from pathlib import Path
import sys
from src.features.custom_dialog import OptionDialog, InputDialog, ArtResultDialog, CustomDialog


class DialogState(Enum):
    INACTIVE = 0
    SAVE_CONFIRM = 1
    PROMPT_INPUT = 2
    STYLE_SELECT = 3
    STYLE_INPUT = 4
    ART_RESULT = 5


class DialogManager:
    """对话框管理器"""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = DialogState.INACTIVE
        self.current_dialog = None
        self.callback = None
        self.prompt_callback = None  # 新加这一行
        self.saved_filename = ""
        self.stored_prompt = ""  # 新增：存储输入的prompt
        self.stored_style = ""  # 新增：存储选择的风格

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
        
        from src.features.custom_dialog import ArtResultDialog
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
        self.stored_prompt = ""  # 重置
        self.stored_style = ""  # 重置

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

    # def show_style_select(self, styles, callback):
    #     """显示风格选择对话框"""
    #     self.state = DialogState.STYLE_SELECT
    #     self.callback = callback
    #     self.stored_style = ""
    #
    #     # 创建选项对话框
    #     dialog_rect = pygame.Rect(0, 0, 550, 400)
    #     dialog_rect.center = (self.screen_width // 2, self.screen_height // 2)
    #
    #     from src.features.custom_dialog import OptionDialog
    #     self.current_dialog = OptionDialog(
    #         dialog_rect,
    #         "创作风格选择",
    #         "请选择一个你喜欢的艺术风格:",
    #         styles,
    #         self.font_path,
    #         12,
    #         columns=2
    #     )
    #     self.current_dialog.show()

        # self.callback = callback
    def show_style_select(self, styles, callback):
        print("[DEBUG] show_style_select: start")
        try:
            print("[DEBUG] show_style_select: setting state")
            self.state = DialogState.STYLE_SELECT
            self.callback = callback
            self.stored_style = ""
            print("[DEBUG] show_style_select: state set")

            print("[DEBUG] show_style_select: creating rect")
            dialog_rect = pygame.Rect(0, 0, 550, 400)
            dialog_rect.center = (self.screen_width // 2, self.screen_height // 2)
            print(f"[DEBUG] show_style_select: rect={dialog_rect}")

            print("[DEBUG] show_style_select: importing OptionDialog")
            from src.features.custom_dialog import OptionDialog
            print("[DEBUG] show_style_select: OptionDialog imported")

            print("[DEBUG] show_style_select: creating OptionDialog instance")
            self.current_dialog = OptionDialog(
                dialog_rect,
                "创作风格选择",
                "请选择一个你喜欢的艺术风格:",
                styles,
                self.font_path,
                12,
                columns=2
            )
            print("[DEBUG] show_style_select: OptionDialog created")

            print("[DEBUG] show_style_select: calling show()")
            self.current_dialog.show()
            print("[DEBUG] show_style_select: show() completed")
        except Exception as e:
            print(f"[DEBUG] show_style_select EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

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

    # def handle_event(self, event):
    #     """处理对话框事件"""
    #     if not self.current_dialog or not self.current_dialog.visible:
    #         return False
    #     result = None
    #     if isinstance(event,pygame.event.EventType):
    #         result = self.current_dialog.handle_event(event)
    #     # 处理voice调用,此时event的是字典，存储信息
    #     elif isinstance(event, dict):
    #         result = event["result"]
    #
    #
    #     if result:
    #         if self.state == DialogState.SAVE_CONFIRM:
    #             if result == "OK":
    #                 # 用户确认进行艺术化创作
    #                 # styles = [
    #                 #     "masterpiece oil painting",
    #                 #     "beautiful watercolor art",
    #                 #     "professional digital artwork",
    #                 #     "fantasy concept art",
    #                 #     "minimalist line art",
    #                 #     "surreal dreamlike painting",
    #                 #     "elegant ink drawing",
    #                 #     "school style",
    #                 #     '自定义'
    #                 # ]
    #                 # self.show_style_select(styles, self.callback)
    #                 self.show_prompt_input_dialog()
    #             else:
    #                 # 用户取消，关闭对话框
    #                 self.close_dialog()
    #                 if self.callback:
    #                     self.callback(False, None)
    #
    #         elif self.state == DialogState.PROMPT_INPUT:
    #             if hasattr(self.current_dialog, "input_text"):
    #                 prompt = self.current_dialog.input_text
    #             if result == "OK":
    #                 self.close_dialog()
    #                 if self.callback:
    #                     self.callback(False, prompt)
    #                 styles = [
    #                     "masterpiece oil painting",
    #                     "beautiful watercolor art",
    #                     "professional digital artwork",
    #                     "fantasy concept art",
    #                     "minimalist line art",
    #                     "surreal dreamlike painting",
    #                     "elegant ink drawing",
    #                     "school style",
    #                     '自定义'
    #                 ]
    #                 self.show_style_select(styles, self.callback)
    #             elif result == "Cancel":
    #                 self.close_dialog()
    #                 if self.callback:
    #                     self.callback(False, None)
    #             elif result == "INPUT":
    #                 if isinstance(event,dict):
    #                     self.current_dialog.insert_text(event["content"])
    #
    #         elif self.state == DialogState.STYLE_SELECT:
    #             if result == "OK":
    #                 # 用户选择了风格
    #                 selected_style = None
    #                 if hasattr(self.current_dialog, 'selected_style'):
    #                     selected_style = self.current_dialog.selected_style
    #                 elif hasattr(self.current_dialog, 'result'):
    #                     selected_style = self.current_dialog.result
    #                 self.close_dialog()
    #                 # 如果选择是自定义
    #                 if selected_style == "自定义":
    #                     self.show_style_input_dialog()
    #                 else:
    #                     if self.callback:
    #                         if selected_style == "无":
    #                             self.callback(True, None)
    #                         else:
    #                             self.callback(True, selected_style)
    #             elif result == "CANCEL":
    #                 # 用户取消风格选择
    #                 self.close_dialog()
    #                 if self.callback:
    #                     self.callback(False, None)
    #         #添加自定义输入
    #         elif self.state == DialogState.STYLE_INPUT:
    #             if hasattr(self.current_dialog, 'input_text'):
    #                 style = self.current_dialog.input_text
    #             if result == "OK":
    #                 self.close_dialog()
    #                 if self.callback:
    #                     self.callback(True, style)
    #             elif result == "CANCEL":
    #                 self.close_dialog()
    #                 if self.callback:
    #                     self.callback(False, None)
    #             elif result == "INPUT":
    #                 if isinstance(event,dict):
    #                     self.current_dialog.insert_text(event["content"])
    #     return True
    # def handle_event(self, event):
    #     """处理对话框事件（最终稳定版）"""
    #     try:
    #         if not self.current_dialog or not self.current_dialog.visible:
    #             return False
    #
    #         result = None
    #         handled = False
    #
    #         # 1. 处理Pygame原生事件（输入框核心）
    #         if isinstance(event, pygame.event.EventType):
    #             result = self.current_dialog.handle_event(event)
    #             # 输入类事件标记为已处理，但不关闭对话框
    #             if event.type in [pygame.TEXTINPUT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION]:
    #                 handled = True
    #             else:
    #                 handled = (result is not None)
    #
    #         # 2. 处理语音自定义事件（字典格式）
    #         elif isinstance(event, dict):
    #             result = event.get("result", "").strip().upper()  # 统一转大写，避免大小写问题
    #             content = event.get("content", "")
    #
    #             # 语音输入文本
    #             if result == "INPUT" and hasattr(self.current_dialog, "insert_text"):
    #                 self.current_dialog.insert_text(content)
    #                 handled = True
    #             # 语音清空
    #             elif result == "CLEAR" and hasattr(self.current_dialog, "clear_text"):
    #                 self.current_dialog.clear_text()
    #                 handled = True
    #             # 语音回退
    #             elif result == "BACKSPACE" and hasattr(self.current_dialog, "back_text"):
    #                 self.current_dialog.back_text()
    #                 handled = True
    #             # 语音确认
    #             elif result == "OK" :
    #                 # 模拟点击确认按钮
    #                 self.current_dialog.hide()
    #                 result = "OK"
    #                 handled = True
    #             # 语音取消
    #             elif result == "CANCEL":
    #                 # 模拟点击取消按钮
    #                 self.current_dialog.hide()
    #                 result = "CANCEL"
    #                 handled = True
    #             else:
    #                 handled = (result != "")
    #
    #         # 3. 核心逻辑：状态跳转 + 数据传递
    #         if result:
    #             # 统一转大写，避免 Cancel/CANCEL 不一致
    #             result = result.upper() if isinstance(result, str) else result
    #
    #             # 保存确认 → 输入Prompt
    #             if self.state == DialogState.SAVE_CONFIRM:
    #                 if result == "OK":
    #                     self.show_prompt_input_dialog(self.callback)
    #                 else:
    #                     self.close_dialog()
    #                     if self.callback:
    #                         self.callback(False, None, None)  # 传3个参数：是否转换、风格、prompt
    #
    #             # Prompt输入 → 风格选择（关键：保存prompt）
    #             elif self.state == DialogState.PROMPT_INPUT:
    #                 # 确保能拿到输入框内容
    #                 self.stored_prompt = self.current_dialog.input_text if hasattr(self.current_dialog,
    #                                                                                "input_text") else ""
    #                 if result == "OK":
    #                     self.close_dialog()
    #                     # 风格选择列表
    #                     styles = [
    #                         "masterpiece oil painting",
    #                         "beautiful watercolor art",
    #                         "professional digital artwork",
    #                         "fantasy concept art",
    #                         "minimalist line art",
    #                         "surreal dreamlike painting",
    #                         "elegant ink drawing",
    #                         "school style",
    #                         '自定义'
    #                     ]
    #                     self.show_style_select(styles, self.callback)
    #                 elif result == "CANCEL":
    #                     self.close_dialog()
    #                     if self.callback:
    #                         self.callback(False, None, None)
    #
    #             # 风格选择 → 自定义风格/最终回调（关键：关联prompt）
    #             # 原代码中 STYLE_SELECT 分支替换为这个
    #             elif self.state == DialogState.STYLE_SELECT:
    #                 if result == "OK":
    #                     self.stored_style = None
    #                     if hasattr(self.current_dialog, 'selected_style'):
    #                         self.stored_style = self.current_dialog.selected_style
    #                     elif hasattr(self.current_dialog, 'result'):
    #                         self.stored_style = self.current_dialog.result
    #
    #                     self.close_dialog()
    #                     # 选择自定义 → 输入风格
    #                     if self.stored_style == "自定义":
    #                         self.show_style_input_dialog()
    #                     else:
    #                         # 最终回调：传 转换状态、风格、prompt
    #                         if self.callback:
    #                             self.callback(True, self.stored_style, self.stored_prompt)
    #                 elif result == "CANCEL":
    #                     self.close_dialog()
    #                     if self.callback:
    #                         self.callback(False, None, None)
    #             # 自定义风格输入 → 最终回调（关联prompt）
    #             elif self.state == DialogState.STYLE_INPUT:
    #                 self.stored_style = self.current_dialog.input_text if hasattr(self.current_dialog, 'input_text') else ""
    #                 if result == "OK":
    #                     self.close_dialog()
    #                     # 最终回调：传 转换状态、自定义风格、之前输入的prompt
    #                     if self.callback:
    #                         self.callback(True, self.stored_style, self.stored_prompt)
    #                 elif result == "CANCEL":
    #                     self.close_dialog()
    #                     if self.callback:
    #                         self.callback(False, None, None)
    #
    #         return handled
    #     except:
    #         print("对话框事件出错")
    #         return False
    def handle_event(self, event):
        print(f"[DialogManager] >>> handle_event called, state={self.state}, event type={type(event)}")
        try:
            if not self.current_dialog or not self.current_dialog.visible:
                print("[DialogManager] No active dialog, returning False")
                return False

            dialog_result = None
            voice_result = None
            handled = False

            # 1. 处理 Pygame 原生事件
            if isinstance(event, pygame.event.EventType):
                print(f"[DialogManager] Pygame event type: {event.type}")
                dialog_result = self.current_dialog.handle_event(event)
                handled = dialog_result is not None
                print(f"[DialogManager] Pygame result: {dialog_result}")

            # 2. 处理语音字典事件
            elif isinstance(event, dict):
                print(f"[DialogManager] Voice event dict: {event}")
                cmd = event.get("result", "").strip().upper()
                content = event.get("content", "")
                print(f"[DialogManager] Voice cmd: {cmd}, content: {content}")

                if cmd == "INPUT" and hasattr(self.current_dialog, "insert_text"):
                    self.current_dialog.insert_text(content)
                    print("[DialogManager] Inserted text")
                    return True
                elif cmd == "CLEAR" and hasattr(self.current_dialog, "clear_text"):
                    self.current_dialog.clear_text()
                    print("[DialogManager] Cleared text")
                    return True
                elif cmd == "BACKSPACE" and hasattr(self.current_dialog, "back_text"):
                    self.current_dialog.back_text()
                    print("[DialogManager] Backspace")
                    return True
                elif cmd == "OK":
                    voice_result = "OK"
                    handled = True
                    print("[DialogManager] Voice OK")
                elif cmd == "CANCEL":
                    voice_result = "CANCEL"
                    handled = True
                    print("[DialogManager] Voice CANCEL")
                else:
                    print("[DialogManager] Unknown voice command, returning False")
                    return False

            # 3. 通用状态机逻辑
            result = dialog_result if dialog_result is not None else voice_result
            if result:
                print(f"[DialogManager] Processing result: {result}, current state: {self.state}")
                result = result.upper() if isinstance(result, str) else result

                # 保存确认 → 输入Prompt
                if self.state == DialogState.SAVE_CONFIRM:
                    print("[DialogManager] In SAVE_CONFIRM state")
                    if result == "OK":
                        print("[DialogManager] OK -> showing prompt input dialog")
                        self.show_prompt_input_dialog(self.callback)
                    else:
                        print("[DialogManager] CANCEL -> closing dialog")
                        self.close_dialog()
                        if self.callback:
                            self.callback(False, None, None)

                # Prompt输入 → 风格选择
                elif self.state == DialogState.PROMPT_INPUT:
                    print("[DialogManager] In PROMPT_INPUT state")
                    self.stored_prompt = self.current_dialog.input_text if hasattr(self.current_dialog,
                                                                                   "input_text") else ""
                    print(f"[DialogManager] Stored prompt: {self.stored_prompt}")
                    if result == "OK":
                        print("[DialogManager] OK -> closing prompt, going to style select")
                        self.close_dialog()
                        styles = [
                            "masterpiece oil painting",
                            "beautiful watercolor art",
                            "professional digital artwork",
                            "fantasy concept art",
                            "minimalist line art",
                            "surreal dreamlike painting",
                            "elegant ink drawing",
                            "school style",
                            '自定义'
                        ]
                        self.show_style_select(styles, self.callback)
                    elif result == "CANCEL":
                        print("[DialogManager] CANCEL -> closing dialog")
                        self.close_dialog()
                        if self.callback:
                            self.callback(False, None, None)

                # 风格选择
                elif self.state == DialogState.STYLE_SELECT:
                    print("[DialogManager] In STYLE_SELECT state")
                    if result == "OK":
                        self.stored_style = None
                        if hasattr(self.current_dialog, 'selected_style'):
                            self.stored_style = self.current_dialog.selected_style
                        elif hasattr(self.current_dialog, 'result'):
                            self.stored_style = self.current_dialog.result
                        print(f"[DialogManager] Selected style: {self.stored_style}")

                        self.close_dialog()
                        if self.stored_style == "自定义":
                            print("[DialogManager] Custom style -> show style input")
                            self.show_style_input_dialog()
                        else:
                            print("[DialogManager] Fixed style -> callback with style and prompt")
                            if self.callback:
                                self.callback(True, self.stored_style, self.stored_prompt)
                    elif result == "CANCEL":
                        print("[DialogManager] CANCEL -> closing dialog")
                        self.close_dialog()
                        if self.callback:
                            self.callback(False, None, None)

                # 风格输入
                elif self.state == DialogState.STYLE_INPUT:
                    print("[DialogManager] In STYLE_INPUT state")
                    self.stored_style = self.current_dialog.input_text if hasattr(self.current_dialog,
                                                                                  'input_text') else ""
                    print(f"[DialogManager] Stored custom style: {self.stored_style}")
                    if result == "OK":
                        print("[DialogManager] OK -> callback with style and prompt")
                        self.close_dialog()
                        if self.callback:
                            self.callback(True, self.stored_style, self.stored_prompt)
                    elif result == "CANCEL":
                        print("[DialogManager] CANCEL -> closing dialog")
                        self.close_dialog()
                        if self.callback:
                            self.callback(False, None, None)

            print(f"[DialogManager] Returning handled={handled}")
            return handled
        except Exception as e:
            print(f"[DialogManager] EXCEPTION in handle_event: {e}")
            import traceback
            traceback.print_exc()
            return False
    def show_style_input_dialog(self):
        self.state = DialogState.STYLE_INPUT
        # 创建选项对话框
        dialog_rect = pygame.Rect(0, 0, 550, 400)
        dialog_rect.center = (self.screen_width // 2, self.screen_height // 2)
        
        from src.features.custom_dialog import InputDialog
        self.current_dialog = InputDialog(
            dialog_rect,
            "创作风格自定义",
            "请说出一个你喜欢的艺术风格:",
            "",
            self.font_path,
            12
        )
        self.current_dialog.show()

    # def show_prompt_input_dialog(self):
    #     self.state = DialogState.PROMPT_INPUT
    #     # 创建选项对话框
    #     dialog_rect = pygame.Rect(0, 0, 700, 300)
    #     dialog_rect.center = (self.screen_width // 2, self.screen_height // 2)
    #     #
    #     from src.features.custom_dialog import InputDialog
    #     self.current_dialog = InputDialog(
    #         dialog_rect,
    #         "prompt输入",
    #         "请输入艺术图片生成的提示词:",
    #         "High quality, detailed, sharp focus, beautiful composition, cinematic lighting, masterpiece, ultra-detailed, clean and clear",
    #         self.font_path,
    #         12
    #     )
    #     self.current_dialog.show()
    def show_prompt_input_dialog(self, callback=None):  # 加参数
        self.state = DialogState.PROMPT_INPUT
        self.callback = callback

        dialog_rect = pygame.Rect(0, 0, 700, 300)
        dialog_rect.center = (self.screen_width // 2, self.screen_height // 2)

        from src.features.custom_dialog import InputDialog
        self.current_dialog = InputDialog(
            dialog_rect,
            "prompt输入",
            "请输入艺术图片生成的提示词:",
            "High quality, detailed, sharp focus, beautiful composition, cinematic lighting, masterpiece, ultra-detailed, clean and clear",
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