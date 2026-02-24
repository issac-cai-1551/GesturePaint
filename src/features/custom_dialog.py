import pygame
import os
from pathlib import Path
import sys

class CustomDialog:
    def __init__(self, rect, title, message, font_path=None, font_size=14):
        """
        自定义对话框类

        参数:
            rect: 对话框位置和大小 (pygame.Rect)
            title: 对话框标题
            message: 对话框消息内容
            font_path: 字体文件路径
            font_size: 字体大小
        """
        self.rect = rect
        self.title = title
        self.message = message
        self.visible = False
        self.result = None

        # 颜色定义
        self.colors = {
            'background': (255, 255, 255),
            'border': (0, 0, 0),
            'title_bar': (0, 120, 215),
            'title_text': (255, 255, 255),
            'message_text': (0, 0, 0),
            'button_normal': (200, 200, 200),
            'button_hover': (220, 220, 220),
            'button_text': (0, 0, 0)
        }

        # 加载字体
        self.load_fonts(font_path, font_size)

        # 创建按钮
        self.create_buttons()

        # 文本换行
        self.message_lines = self.wrap_text(message, self.message_font, self.rect.width - 40)

    def load_fonts(self, font_path, font_size):
        """加载字体"""
        try:
            if font_path and os.path.exists(font_path):
                self.title_font = pygame.font.Font(font_path, font_size + 2)  # 标题字体稍大
                self.message_font = pygame.font.Font(font_path, font_size+5)
                self.button_font = pygame.font.Font(font_path, font_size)
            else:
                self.title_font = pygame.font.SysFont(None, font_size + 2)
                self.message_font = pygame.font.SysFont(None, font_size)
                self.button_font = pygame.font.SysFont(None, font_size)
        except Exception as e:
            print(f"字体加载失败: {e}")
            # 使用默认字体
            self.title_font = pygame.font.SysFont(None, font_size + 2)
            self.message_font = pygame.font.SysFont(None, font_size)
            self.button_font = pygame.font.SysFont(None, font_size)

    def create_buttons(self):
        """创建对话框按钮"""
        button_width, button_height = 80, 30
        button_y = self.rect.y + self.rect.height - 40

        # 确认按钮
        self.ok_button_rect = pygame.Rect(
            self.rect.x + self.rect.width - 180,
            button_y,
            button_width,
            button_height
        )

        # 取消按钮
        self.cancel_button_rect = pygame.Rect(
            self.rect.x + self.rect.width - 90,
            button_y,
            button_width,
            button_height
        )

        # 按钮状态
        self.ok_hovered = False
        self.cancel_hovered = False

    def wrap_text(self, text, font, max_width):
        """将文本换行以适应最大宽度，支持显式换行符"""
        lines = []
        # 1. 首先按显式换行符分割段落
        paragraphs = text.split('\n')

        for paragraph in paragraphs:
            # 2. 对每个段落进行自动换行处理
            words = paragraph.split(' ')
            current_line = []

            for word in words:
                # 测试当前行加上新单词后的宽度
                test_line = ' '.join(current_line + [word])
                test_width, _ = font.size(test_line)

                if test_width <= max_width:
                    current_line.append(word)
                else:
                    # 如果当前行不为空，则添加到行列表中
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]

            # 添加最后一行
            if current_line:
                lines.append(' '.join(current_line))

        return lines

    def show(self):
        """显示对话框"""
        self.visible = True
        self.result = None

    def hide(self):
        """隐藏对话框"""
        self.visible = False

    def draw(self, surface):
        """绘制对话框"""
        if not self.visible:
            return

        # 绘制对话框背景
        pygame.draw.rect(surface, self.colors['background'], self.rect)
        pygame.draw.rect(surface, self.colors['border'], self.rect, 2)

        # 绘制标题栏
        title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 30)
        pygame.draw.rect(surface, self.colors['title_bar'], title_rect)
        pygame.draw.rect(surface, self.colors['border'], title_rect, 1)

        # 绘制标题
        title_surf = self.title_font.render(self.title, True, self.colors['title_text'])
        title_pos = (self.rect.x + 10, self.rect.y + 5)
        surface.blit(title_surf, title_pos)

        # 绘制消息文本
        for i, line in enumerate(self.message_lines):
            msg_surf = self.message_font.render(line, True, self.colors['message_text'])
            msg_pos = (self.rect.x + 20, self.rect.y + 35 + i * 25)
            surface.blit(msg_surf, msg_pos)

        # 绘制按钮
        ok_color = self.colors['button_hover'] if self.ok_hovered else self.colors['button_normal']
        cancel_color = self.colors['button_hover'] if self.cancel_hovered else self.colors['button_normal']

        # 确认按钮
        pygame.draw.rect(surface, ok_color, self.ok_button_rect)
        pygame.draw.rect(surface, self.colors['border'], self.ok_button_rect, 2)
        ok_text = self.button_font.render('确认', True, self.colors['button_text'])
        ok_text_pos = ok_text.get_rect(center=self.ok_button_rect.center)
        surface.blit(ok_text, ok_text_pos)

        # 取消按钮
        pygame.draw.rect(surface, cancel_color, self.cancel_button_rect)
        pygame.draw.rect(surface, self.colors['border'], self.cancel_button_rect, 2)
        cancel_text = self.button_font.render('取消', True, self.colors['button_text'])
        cancel_text_pos = cancel_text.get_rect(center=self.cancel_button_rect.center)
        surface.blit(cancel_text, cancel_text_pos)

    def handle_event(self, event):
        """处理事件"""
        if not self.visible:
            return None

        # 更新按钮悬停状态
        mouse_pos = pygame.mouse.get_pos()
        self.ok_hovered = self.ok_button_rect.collidepoint(mouse_pos)
        self.cancel_hovered = self.cancel_button_rect.collidepoint(mouse_pos)

        # 处理鼠标点击事件
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.ok_button_rect.collidepoint(event.pos):
                self.result = "OK"
                self.hide()
                return "OK"
            elif self.cancel_button_rect.collidepoint(event.pos):
                self.result = "CANCEL"
                self.hide()
                return "CANCEL"

        return None

    def update(self):
        """更新对话框状态（可用于动画等）"""
        # 可以在这里添加动画效果
        pass


class OptionDialog(CustomDialog):
    """支持选项按钮的自定义对话框"""

    def __init__(self, rect, title, message, options, font_path=None, font_size=12, columns=2):
        """
        参数:
            rect: 对话框位置和大小
            title: 对话框标题
            message: 对话框消息
            options: 选项列表
            font_path: 字体路径
            font_size: 字体大小
            columns: 网格布局的列数
        """
        super().__init__(rect, title, message, font_path, font_size)

        self.options = options
        self.selected_option = None
        self.columns = columns
        self.option_rects = []

        # 创建选项按钮
        self.create_option_buttons()

    def create_option_buttons(self):
        """创建选项按钮 - 使用网格布局"""
        option_height = 35
        option_spacing = 10
        option_margin = 20

        # 计算每列的宽度
        column_width = (self.rect.width - 2 * option_margin) // self.columns

        # 计算行数
        rows = (len(self.options) + self.columns - 1) // self.columns

        # 计算起始Y坐标，确保内容在对话框内居中
        total_height = rows * option_height + (rows - 1) * option_spacing
        start_y = self.rect.y + 80 + (self.rect.height - 150 - total_height) // 2

        for i, option in enumerate(self.options):
            # 计算行和列
            row = i // self.columns
            col = i % self.columns

            # 计算位置
            x = self.rect.x + option_margin + col * column_width
            y = start_y + row * (option_height + option_spacing)

            # 创建选项按钮矩形
            option_rect = pygame.Rect(
                x + 5,  # 添加一点内边距
                y,
                column_width - 10,  # 减去内边距
                option_height
            )
            self.option_rects.append(option_rect)

    def draw(self, surface):
        """绘制选项对话框"""
        if not self.visible:
            return

        # 调用父类的绘制方法
        super().draw(surface)

        # 绘制选项按钮
        for i, (option, rect) in enumerate(zip(self.options, self.option_rects)):
            # 判断是否选中
            is_selected = (self.selected_option == i)
            option_color = self.colors['button_hover'] if is_selected else self.colors['button_normal']

            pygame.draw.rect(surface, option_color, rect)
            pygame.draw.rect(surface, self.colors['border'], rect, 2)

            # 绘制选项文本 - 自动换行
            wrapped_text = self.wrap_option_text(option, self.message_font, rect.width - 10)
            for j, line in enumerate(wrapped_text):
                option_surf = self.message_font.render(line, True, self.colors['button_text'])
                option_pos = option_surf.get_rect(center=(rect.centerx, rect.y + 10 + j * 15))
                surface.blit(option_surf, option_pos)

    def wrap_option_text(self, text, font, max_width):
        """将选项文本换行以适应按钮宽度"""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            # 测试当前行加上新单词后的宽度
            test_line = ' '.join(current_line + [word])
            test_width, _ = font.size(test_line)

            if test_width <= max_width:
                current_line.append(word)
            else:
                # 如果当前行不为空，则添加到行列表中
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        # 添加最后一行
        if current_line:
            lines.append(' '.join(current_line))

        # 如果行数超过2行，截断并添加省略号
        if len(lines) > 2:
            lines = lines[:2]
            if len(lines[1]) > 3:
                lines[1] = lines[1][:-3] + "..."
            else:
                lines[1] = "..."

        return lines

    def handle_event(self, event):
        """处理选项对话框事件"""
        if not self.visible:
            return None

        # 处理选项点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected_option = i
                    self.result = self.options[self.selected_option]

        # 处理按钮点击
        result = super().handle_event(event)
        if result == "OK" and self.selected_option is not None:
            self.result = self.options[self.selected_option]
        elif result == "OK" and self.selected_option is None:
            # 如果没有选择选项，不关闭对话框
            self.result = None
            return None

        return result


from pygame.locals import *


# class InputDialog(CustomDialog):
#     def __init__(self, rect, title, message="", default_text="", font_path=None, font_size=14):
#         """
#         支持中文输入的自定义输入对话框
#
#         参数:
#             rect: 对话框位置和大小 (pygame.Rect)
#             title: 对话框标题
#             message: 提示信息
#             default_text: 默认文本
#             font_path: 字体文件路径
#             font_size: 字体大小
#         """
#         # 计算合适的高度，留出输入框空间
#         rect.height = max(rect.height, 150)
#         super().__init__(rect, title, message, font_path, font_size)
#
#         # 输入框相关属性
#         self.input_text = default_text
#         self.cursor_visible = True
#         self.cursor_timer = 0
#         self.cursor_blink_interval = 500  # 光标闪烁间隔（毫秒）
#         self.cursor_position = len(self.input_text)  # 光标位置
#
#         # 输入框矩形
#         self.input_rect = pygame.Rect(
#             self.rect.x + 20,
#             self.rect.y + 60,
#             self.rect.width - 40,
#             30
#         )
#
#         # 颜色定义（新增输入框颜色）
#         self.colors.update({
#             'input_bg': (240, 240, 240),
#             'input_border': (100, 100, 100),
#             'input_border_focus': (0, 120, 215),
#             'cursor': (0, 0, 0)
#         })
#
#         # 输入状态
#         self.input_active = True
#         self.input_focus = True
#
#         # 文本滚动相关
#         self.text_offset = 0
#         self.caret_offset = 0
#
#         # 重新计算消息换行（考虑输入框位置）
#         if message:
#             self.message_lines = self.wrap_text(message, self.message_font, self.rect.width - 40)
#             # 调整输入框位置
#             message_height = len(self.message_lines) * 25
#             self.input_rect.y = self.rect.y + 50 + message_height
#             # 调整按钮位置 (恢复原来的间距)
#             self.ok_button_rect.y = self.input_rect.y + 50
#             self.cancel_button_rect.y = self.input_rect.y + 50
#         else:
#             # 如果没有消息，向上移动输入框
#             self.input_rect.y = self.rect.y + 50
#             self.ok_button_rect.y = self.input_rect.y + 50
#             self.cancel_button_rect.y = self.input_rect.y + 50
#
#         # 底部说明文字
#         self.bottom_tips = [
#             "语音指令:",
#             "说 '清空' -> 清空  |  说 '删除' -> 回退",
#             "说 '确认' -> 提交  |  说 '取消' -> 关闭"
#         ]
#
#         # 增加对话框高度以容纳底部文字
#         self.rect.height += 60
#
#     def draw(self, surface):
#         """绘制对话框"""
#         if not self.visible:
#             return
#
#         # 调用父类的绘制方法
#         super().draw(surface)
#
#         # 绘制消息文本（如果有）
#         for i, line in enumerate(self.message_lines):
#             msg_surf = self.message_font.render(line, True, self.colors['message_text'])
#             msg_pos = (self.rect.x + 20, self.rect.y + 35 + i * 25)
#             surface.blit(msg_surf, msg_pos)
#
#         # 绘制输入框
#         border_color = self.colors['input_border_focus'] if self.input_focus else self.colors['input_border']
#         pygame.draw.rect(surface, self.colors['input_bg'], self.input_rect)
#         pygame.draw.rect(surface, border_color, self.input_rect, 2)
#
#         # 绘制底部说明文字 (在按钮下方)
#         if hasattr(self, 'bottom_tips'):
#             # 寻找合适的字体大小
#             tip_font = self.message_font
#             tip_start_y = self.ok_button_rect.bottom + 15
#
#             for i, tip in enumerate(self.bottom_tips):
#                 tip_surf = tip_font.render(tip, True, (120, 120, 120))
#                 # 居中显示
#                 tip_x = self.rect.centerx - tip_surf.get_width() // 2
#                 surface.blit(tip_surf, (tip_x, tip_start_y + i * 20))
#
#         # 创建用于文本渲染的表面
#         text_surface = pygame.Surface((self.input_rect.width - 4, self.input_rect.height - 4), pygame.SRCALPHA)
#
#         # 渲染文本
#         font = self.message_font
#         text_color = self.colors['message_text']
#
#         # 计算可见文本部分
#         visible_text = self.input_text
#
#         temp_text = self.input_text
#
#         # 渲染文本
#         text_img = font.render(temp_text, True, text_color)
#
#         # 计算文本位置（考虑滚动）
#         text_x = 4 - self.text_offset
#         text_y = (self.input_rect.height - text_img.get_height()) // 2
#
#         # 绘制文本到文本表面
#         text_surface.blit(text_img, (text_x, text_y))
#
#         # 绘制光标
#         if self.input_focus and self.cursor_visible:
#             # 计算光标位置
#
#             text_before_cursor = self.input_text[:self.cursor_position]
#
#             cursor_x = font.size(text_before_cursor)[0] - self.text_offset
#
#             # 确保光标在可见区域内
#             if cursor_x < 0:
#                 self.text_offset += cursor_x
#                 cursor_x = 0
#             elif cursor_x > self.input_rect.width - 10:
#                 self.text_offset += cursor_x - (self.input_rect.width - 10)
#                 cursor_x = self.input_rect.width + 10
#
#             cursor_rect = pygame.Rect(cursor_x, 2, 2, self.input_rect.height - 8)
#             pygame.draw.rect(text_surface, self.colors['cursor'], cursor_rect)
#
#
#
#         # 将文本表面绘制到主表面
#         surface.blit(text_surface, (self.input_rect.x + 2, self.input_rect.y + 2))
#
#     def handle_event(self, event):
#         """处理事件"""
#         if not self.visible:
#             return None
#
#         # 更新按钮悬停状态
#         mouse_pos = pygame.mouse.get_pos()
#         self.ok_hovered = self.ok_button_rect.collidepoint(mouse_pos)
#         self.cancel_hovered = self.cancel_button_rect.collidepoint(mouse_pos)
#
#         # 处理鼠标点击
#         if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
#             if self.input_rect.collidepoint(event.pos):
#                 self.input_focus = True
#                 # 计算点击位置对应的光标位置
#                 self.update_cursor_position_from_mouse(event.pos)
#                 return "INPUT"
#             elif self.ok_button_rect.collidepoint(event.pos):
#                 self.result = self.input_text
#                 self.hide()
#                 return "OK"
#             elif self.cancel_button_rect.collidepoint(event.pos):
#                 self.result = None
#                 self.hide()
#                 return "CANCEL"
#             else:
#                 self.input_focus = False
#
#         # 处理键盘输入（仅在输入框获得焦点时）
#         if self.input_focus:
#             if event.type == pygame.KEYDOWN:
#                 # 处理特殊键
#                 if event.key == pygame.K_RETURN:
#                     self.result = self.input_text
#                     self.hide()
#                     return "OK"
#                 elif event.key == pygame.K_ESCAPE:
#                     self.result = None
#                     self.hide()
#                     return "CANCEL"
#                 elif event.key == pygame.K_BACKSPACE:
#                     self.back_text()
#                 elif event.key == pygame.K_DELETE:
#                     if self.cursor_position < len(self.input_text):
#                         self.input_text = (self.input_text[:self.cursor_position] +
#                                            self.input_text[self.cursor_position + 1:])
#                 else:
#                     # 不处理其他按键，等待TEXTINPUT事件
#                     pass
#
#             # 处理文本输入事件
#             elif event.type == pygame.TEXTINPUT:
#                 # 插入普通文本
#                 self.insert_text(event.text)
#
#             # 处理按钮点击
#             result = super().handle_event(event)
#             if result == "OK":
#                 self.result = self.input_text
#                 # 如果没有选择选项，不关闭对话框
#             return result
#
#
#
#     def insert_text(self, text):
#         """插入文本到当前光标位置"""
#         self.input_text = (self.input_text[:self.cursor_position] +
#                                text +
#                                self.input_text[self.cursor_position:])
#         self.cursor_position += len(text)
#
#     def clear_text(self):
#         self.input_text = ""
#         self.cursor_position = 0
#
#     def back_text(self):
#         if self.cursor_position > 0:
#             # 删除光标前的字符
#             self.input_text = (self.input_text[:self.cursor_position - 1] +
#                                self.input_text[self.cursor_position:])
#             self.cursor_position -= 1
#
#     def update_cursor_position_from_mouse(self, mouse_pos):
#         """根据鼠标点击位置更新光标位置"""
#         # 计算相对于输入框的位置
#         rel_x = mouse_pos[0] - self.input_rect.x - 2 + self.text_offset
#
#         # 找到最接近的字符位置
#         font = self.message_font
#         current_width = 0
#         best_position = 0
#         min_distance = float('inf')
#
#         for i in range(len(self.input_text) + 1):
#             # 计算到当前位置的距离
#             distance = abs(rel_x - current_width)
#             if distance < min_distance:
#                 min_distance = distance
#                 best_position = i
#
#             if i < len(self.input_text):
#                 # 计算下一个字符的宽度
#                 char_width = font.size(self.input_text[i])[0]
#                 current_width += char_width
#
#         self.cursor_position = best_position
#
#     def update(self):
#         """更新对话框状态"""
#         # 更新光标闪烁
#         current_time = pygame.time.get_ticks()
#         if current_time - self.cursor_timer > self.cursor_blink_interval:
#             self.cursor_visible = not self.cursor_visible
#             self.cursor_timer = current_time
#
#         # 确保文本滚动正确
#         self.ensure_cursor_visible()
#
#     def ensure_cursor_visible(self):
#         """确保光标在可见区域内"""
#         if not self.input_focus:
#             return
#
#         font = self.message_font
#         text_before_cursor = self.input_text[:self.cursor_position]
#         cursor_x = font.size(text_before_cursor)[0]
#
#         # 检查光标是否在可见区域外
#         if cursor_x < self.text_offset:
#             self.text_offset = cursor_x
#         elif cursor_x > self.text_offset + self.input_rect.width - 10:
#             self.text_offset = cursor_x - self.input_rect.width + 10
#
#     def show(self):
#         """显示对话框"""
#         super().show()
#         self.input_focus = True
#         self.cursor_visible = True
#         self.cursor_timer = pygame.time.get_ticks()
class InputDialog(CustomDialog):
    def __init__(self, rect, title, message="", default_text="", font_path=None, font_size=14):
        """
        支持项目集成的鲁棒版输入对话框（修复中文/键盘输入问题）
        """
        rect.height = max(rect.height, 220)
        super().__init__(rect, title, message, font_path, font_size)

        # 输入框核心属性
        self.input_text = default_text
        self.cursor_visible = True
        self.cursor_timer = pygame.time.get_ticks()
        self.cursor_blink_interval = 500
        self.cursor_position = len(self.input_text)

        # 输入框矩形
        self.input_rect = pygame.Rect(
            self.rect.x + 20,
            self.rect.y + 60,
            self.rect.width - 40,
            30
        )

        # 颜色扩展
        self.colors.update({
            'input_bg': (240, 240, 240),
            'input_border': (100, 100, 100),
            'input_border_focus': (0, 120, 215),
            'cursor': (0, 0, 0)
        })

        # 输入状态（强化焦点管理）
        self.input_focus = False  # 初始不获取焦点，避免抢占项目事件
        self.is_active = False    # 标记对话框是否处于激活状态

        # 文本滚动
        self.text_offset = 0

        # 重新计算布局
        if message:
            self.message_lines = self.wrap_text(message, self.message_font, self.rect.width - 40)
            message_height = len(self.message_lines) * 25
            self.input_rect.y = self.rect.y + 50 + message_height
        else:
            self.input_rect.y = self.rect.y + 50

        # 按钮位置（固定）
        self.ok_button_rect.y = self.input_rect.y + 40
        self.cancel_button_rect.y = self.input_rect.y + 40

        # 底部提示
        self.bottom_tips = [
            "语音指令:",
            "说 '清空' -> 清空  |  说 '删除' -> 回退",
            "说 '确认' -> 提交  |  说 '取消' -> 关闭"
        ]

        # 新增：设置文本输入区域（关键）
        pygame.key.start_text_input()
        pygame.key.set_text_input_rect(self.input_rect)  # 绑定输入框区域

        # 修复光标初始位置
        self.cursor_position = len(self.input_text)
        self.text_offset = 0

    def show(self):
        """显示对话框（关键：激活时才启用文本输入）"""
        super().show()
        self.is_active = True
        self.input_focus = True  # 显示时自动获取焦点
        self.cursor_visible = True
        self.cursor_timer = pygame.time.get_ticks()
        # 强制启用文本输入（兼容不同系统）
        pygame.key.start_text_input()
        # 限定文本输入区域（提升输入法兼容性）
        pygame.key.set_text_input_rect(self.input_rect)

    def hide(self):
        """隐藏对话框（关键：释放文本输入资源）"""
        super().hide()
        self.is_active = False
        self.input_focus = False
        try:
            pygame.key.stop_text_input()
        except Exception:
            pass  # 防止重复停止导致崩溃

    def handle_event(self, event):
        """
        强化版事件处理（兼容项目多事件源）
        注意：项目中需确保将 ALL 事件传递给此方法
        """
        if not self.visible:
            return None

        # 1. 基础按钮悬停更新（不依赖焦点）
        mouse_pos = pygame.mouse.get_pos()
        self.ok_hovered = self.ok_button_rect.collidepoint(mouse_pos)
        self.cancel_hovered = self.cancel_button_rect.collidepoint(mouse_pos)

        # 2. 鼠标事件处理（优先级最高）
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 点击输入框：获取焦点
            if self.input_rect.collidepoint(event.pos):
                self.input_focus = True
                self.update_cursor_position_from_mouse(event.pos)
                pygame.key.start_text_input()  # 重新激活输入
                pygame.key.set_text_input_rect(self.input_rect)
                return "INPUT_FOCUS"
            # 点击确认/取消按钮
            elif self.ok_button_rect.collidepoint(event.pos):
                self.result = self.input_text
                self.hide()
                return "OK"
            elif self.cancel_button_rect.collidepoint(event.pos):
                self.result = None
                self.hide()
                return "CANCEL"
            # 点击其他区域：失去焦点
            else:
                self.input_focus = False

        # 3. 仅当输入框激活且有焦点时，处理键盘/文本输入
        if self.is_active and self.input_focus:
            # 处理键盘按键
            if event.type == pygame.KEYDOWN:
                # 回车/ESC 直接触发确认/取消
                if event.key == pygame.K_RETURN:
                    self.result = self.input_text
                    self.hide()
                    return "OK"
                elif event.key == pygame.K_ESCAPE:
                    self.result = None
                    self.hide()
                    return "CANCEL"
                # 退格/删除
                elif event.key == pygame.K_BACKSPACE:
                    self.back_text()
                    return "BACKSPACE"
                elif event.key == pygame.K_DELETE:
                    if self.cursor_position < len(self.input_text):
                        self.input_text = self.input_text[:self.cursor_position] + self.input_text[self.cursor_position+1:]
                    return "DELETE"
                # 光标移动
                elif event.key == pygame.K_LEFT:
                    self.cursor_position = max(0, self.cursor_position - 1)
                    self.ensure_cursor_visible()
                    return "CURSOR_LEFT"
                elif event.key == pygame.K_RIGHT:
                    self.cursor_position = min(len(self.input_text), self.cursor_position + 1)
                    self.ensure_cursor_visible()
                    return "CURSOR_RIGHT"
                # 全选（新增实用功能）
                elif event.key == pygame.K_a and (event.mod & pygame.KMOD_CTRL):
                    self.cursor_position = len(self.input_text)
                    return "SELECT_ALL"

            # 处理文本输入（核心：优先处理 TEXTINPUT，兼容中文）
            elif event.type == pygame.TEXTINPUT:
                # 过滤控制字符（避免无效输入）
                if event.text.isprintable():
                    self.insert_text(event.text)
                    self.ensure_cursor_visible()
                    return "TEXT_INPUT"

        # 4. 最后处理父类事件（避免冲突）
        return super().handle_event(event)

    # 保留 insert_text/back_text/update_cursor_position_from_mouse/ensure_cursor_visible/update/draw 方法
    # （这些方法与上一版一致，无需修改）
    def insert_text(self, text):
        self.input_text = self.input_text[:self.cursor_position] + text + self.input_text[self.cursor_position:]
        self.cursor_position += len(text)

    def back_text(self):
        if self.cursor_position > 0:
            self.input_text = self.input_text[:self.cursor_position-1] + self.input_text[self.cursor_position:]
            self.cursor_position -= 1
            self.ensure_cursor_visible()

    def clear_text(self):
        """清空输入框文本"""
        self.input_text = ""
        self.cursor_position = 0
        self.text_offset = 0  # 重置滚动偏移

    def update_cursor_position_from_mouse(self, mouse_pos):
        rel_x = mouse_pos[0] - self.input_rect.x - 2 + self.text_offset
        font = self.message_font
        current_width = 0
        best_position = 0
        min_distance = float('inf')

        for i in range(len(self.input_text) + 1):
            distance = abs(rel_x - current_width)
            if distance < min_distance:
                min_distance = distance
                best_position = i
            if i < len(self.input_text):
                current_width += font.size(self.input_text[i])[0]

        self.cursor_position = best_position
        self.ensure_cursor_visible()

    def ensure_cursor_visible(self):
        if not self.input_focus:
            return
        font = self.message_font
        text_before_cursor = self.input_text[:self.cursor_position]
        cursor_x = font.size(text_before_cursor)[0]

        if cursor_x < self.text_offset:
            self.text_offset = max(0,cursor_x)
        elif cursor_x > self.text_offset + self.input_rect.width - 10:
            self.text_offset = cursor_x - (self.input_rect.width - 10)
            self.text_offset = max(0,self.text_offset)

    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.cursor_timer > self.cursor_blink_interval:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time
        self.ensure_cursor_visible()

    def draw(self, surface):
        if not self.visible:
            return

        # 绘制对话框背景/标题（简化版，避免与父类冲突）
        pygame.draw.rect(surface, self.colors['background'], self.rect)
        pygame.draw.rect(surface, self.colors['border'], self.rect, 2)
        title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 30)
        pygame.draw.rect(surface, self.colors['title_bar'], title_rect)
        pygame.draw.rect(surface, self.colors['border'], title_rect, 1)
        title_surf = self.title_font.render(self.title, True, self.colors['title_text'])
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 5))

        # 绘制消息文本
        for i, line in enumerate(self.message_lines):
            msg_surf = self.message_font.render(line, True, self.colors['message_text'])
            surface.blit(msg_surf, (self.rect.x + 20, self.rect.y + 35 + i * 25))

        # 绘制输入框
        border_color = self.colors['input_border_focus'] if self.input_focus else self.colors['input_border']
        pygame.draw.rect(surface, self.colors['input_bg'], self.input_rect)
        pygame.draw.rect(surface, border_color, self.input_rect, 2)

        # 绘制输入文本和光标
        text_surface = pygame.Surface((self.input_rect.width - 4, self.input_rect.height - 4), pygame.SRCALPHA)
        font = self.message_font
        text_img = font.render(self.input_text, True, self.colors['message_text'])
        text_x = 4 - self.text_offset
        text_y = (self.input_rect.height - text_img.get_height()) // 2
        text_surface.blit(text_img, (text_x, text_y))

        # 绘制光标
        if self.input_focus and self.cursor_visible:
            text_before_cursor = self.input_text[:self.cursor_position]
            cursor_x = font.size(text_before_cursor)[0] - self.text_offset
            cursor_x = max(0, min(cursor_x, self.input_rect.width - 6))
            cursor_rect = pygame.Rect(cursor_x, 2, 2, self.input_rect.height - 8)
            pygame.draw.rect(text_surface, self.colors['cursor'], cursor_rect)
        surface.blit(text_surface, (self.input_rect.x + 2, self.input_rect.y + 2))

        # 绘制按钮
        ok_color = self.colors['button_hover'] if self.ok_hovered else self.colors['button_normal']
        cancel_color = self.colors['button_hover'] if self.cancel_hovered else self.colors['button_normal']
        pygame.draw.rect(surface, ok_color, self.ok_button_rect)
        pygame.draw.rect(surface, self.colors['border'], self.ok_button_rect, 2)
        ok_text = self.button_font.render('确认', True, self.colors['button_text'])
        surface.blit(ok_text, ok_text.get_rect(center=self.ok_button_rect.center))

        pygame.draw.rect(surface, cancel_color, self.cancel_button_rect)
        pygame.draw.rect(surface, self.colors['border'], self.cancel_button_rect, 2)
        cancel_text = self.button_font.render('取消', True, self.colors['button_text'])
        surface.blit(cancel_text, cancel_text.get_rect(center=self.cancel_button_rect.center))

        # 绘制底部提示
        if hasattr(self, 'bottom_tips'):
            tip_font = self.message_font
            tip_start_y = self.ok_button_rect.bottom + 15
            for i, tip in enumerate(self.bottom_tips):
                tip_surf = tip_font.render(tip, True, (120, 120, 120))
                tip_x = self.rect.centerx - tip_surf.get_width() // 2
                surface.blit(tip_surf, (tip_x, tip_start_y + i * 18))



class ArtResultDialog(CustomDialog):
    def __init__(self, rect, original_path, generated_path, prompt, font_path=None):
        # 调用父类初始化，标题为"艺术创作完成"，消息为空（因为我们自己绘制图片）
        super().__init__(rect, "艺术创作完成", "", font_path, 16)

        self.prompt = prompt

        # 加载图片
        try:
            self.original_image = pygame.image.load(original_path).convert_alpha()
            self.generated_image = pygame.image.load(generated_path).convert_alpha()
        except Exception as e:
            print(f"加载结果图片失败: {e}")
            # 创建占位图
            self.original_image = pygame.Surface((200, 200))
            self.original_image.fill((200, 200, 200))
            self.generated_image = pygame.Surface((200, 200))
            self.generated_image.fill((200, 200, 200))

        # 计算图片显示区域
        # 假设对话框宽度足够，我们在中间留出箭头位置
        # 图片大小设为 350x350 (根据对话框大小调整)
        img_size = (350, 350)
        self.original_image = pygame.transform.scale(self.original_image, img_size)
        self.generated_image = pygame.transform.scale(self.generated_image, img_size)

        # 箭头
        if font_path:
            self.arrow_font = pygame.font.Font(font_path, 40)
        else:
            self.arrow_font = pygame.font.SysFont("arial", 40)
        self.arrow_surf = self.arrow_font.render("->", True, (0, 0, 0))

        # 调整按钮位置到最下方
        button_y = self.rect.y + self.rect.height - 40
        self.ok_button_rect.y = button_y
        # 只需要确认按钮，隐藏取消按钮
        self.cancel_button_rect.width = 0
        self.cancel_button_rect.x = -100  # 移出屏幕

        # 居中确认按钮
        self.ok_button_rect.centerx = self.rect.centerx

    def _wrap_text(self, text, font, max_width):
        """
        将文本按最大宽度自动换行
        :param text: 要换行的文本
        :param font: 使用的字体
        :param max_width: 最大显示宽度
        :return: 换行后的文本行列表
        """
        words = text.split(' ')
        lines = []
        current_line = ''

        for word in words:
            # 测试当前行加上这个单词的宽度
            test_line = current_line + word + ' '
            test_width = font.size(test_line)[0]

            if test_width <= max_width or not current_line:
                # 如果宽度合适，或者当前行为空，就添加这个单词
                current_line = test_line
            else:
                # 宽度超了，保存当前行，开始新行
                lines.append(current_line.strip())
                current_line = word + ' '

        # 添加最后一行
        if current_line:
            lines.append(current_line.strip())

        return lines

    def draw(self, surface):
        if not self.visible:
            return

        # 1. 绘制基本框架（背景、标题栏）
        # 复制父类的绘制逻辑，但不绘制消息文本
        pygame.draw.rect(surface, self.colors['background'], self.rect)
        pygame.draw.rect(surface, self.colors['border'], self.rect, 2)

        title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 30)
        pygame.draw.rect(surface, self.colors['title_bar'], title_rect)
        pygame.draw.rect(surface, self.colors['border'], title_rect, 1)

        title_surf = self.title_font.render(self.title, True, self.colors['title_text'])
        title_pos = (self.rect.x + 10, self.rect.y + 5)
        surface.blit(title_surf, title_pos)

        # 显示提示词 - 支持自动换行
        prompt_prefix = "使用的提示词: "
        full_prompt_text = f"{prompt_prefix}{self.prompt}"

        # 设置prompt的最大显示宽度（对话框宽度减去左右边距）
        max_prompt_width = self.rect.width - 40
        # 拆分文本为多行
        prompt_lines = self._wrap_text(full_prompt_text, self.message_font, max_prompt_width)

        # 计算prompt文本的总高度和起始Y坐标
        line_height = self.message_font.get_linesize()
        total_prompt_height = len(prompt_lines) * line_height
        prompt_start_y = self.rect.y + 50  # 标题栏下方开始

        # 逐行绘制prompt文本
        for i, line in enumerate(prompt_lines):
            prompt_surf = self.message_font.render(line, True, (0, 0, 0))
            # 每行都居中显示
            prompt_rect = prompt_surf.get_rect(center=(self.rect.centerx, prompt_start_y + i * line_height))
            surface.blit(prompt_surf, prompt_rect)

        # 2. 绘制图片和箭头
        # 计算位置 - 根据prompt的行数动态调整Y坐标
        content_y = prompt_start_y + total_prompt_height + 15  # prompt下方留出15像素间距
        center_x = self.rect.centerx

        # 原始图片在左
        orig_rect = self.original_image.get_rect(midright=(center_x - 30, content_y + 175))
        surface.blit(self.original_image, orig_rect)
        # 给原始图片加一个边框
        pygame.draw.rect(surface, (150, 150, 150), orig_rect, 2)

        # 箭头在中间
        arrow_rect = self.arrow_surf.get_rect(center=(center_x, content_y + 175))
        surface.blit(self.arrow_surf, arrow_rect)

        # 生成图片在右
        gen_rect = self.generated_image.get_rect(midleft=(center_x + 30, content_y + 175))
        surface.blit(self.generated_image, gen_rect)
        pygame.draw.rect(surface, (150, 150, 150), gen_rect, 2)

        # 绘制标签
        orig_label = self.button_font.render("原始涂鸦:", True, (100, 100, 100))
        surface.blit(orig_label, (orig_rect.centerx - orig_label.get_width() // 2, orig_rect.bottom + 5))

        gen_label = self.button_font.render("AI艺术:", True, (0, 120, 215))
        surface.blit(gen_label, (gen_rect.centerx - gen_label.get_width() // 2, gen_rect.bottom + 5))

        # 3. 绘制按钮
        ok_color = self.colors['button_hover'] if self.ok_hovered else self.colors['button_normal']
        pygame.draw.rect(surface, ok_color, self.ok_button_rect)
        pygame.draw.rect(surface, self.colors['border'], self.ok_button_rect, 2)
        ok_text = self.button_font.render('关闭', True, self.colors['button_text'])
        ok_text_pos = ok_text.get_rect(center=self.ok_button_rect.center)
        surface.blit(ok_text, ok_text_pos)

# ------------------- 测试代码（可直接运行） -------------------
if __name__ == "__main__":
    # 创建窗口
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("中文输入对话框测试")