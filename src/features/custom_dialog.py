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


class InputDialog(CustomDialog):
    def __init__(self, rect, title, message="", default_text="", font_path=None, font_size=14):
        """
        支持中文输入的自定义输入对话框

        参数:
            rect: 对话框位置和大小 (pygame.Rect)
            title: 对话框标题
            message: 提示信息
            default_text: 默认文本
            font_path: 字体文件路径
            font_size: 字体大小
        """
        # 计算合适的高度，留出输入框空间
        rect.height = max(rect.height, 150)
        super().__init__(rect, title, message, font_path, font_size)

        # 输入框相关属性
        self.input_text = default_text
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_interval = 500  # 光标闪烁间隔（毫秒）
        self.cursor_position = len(self.input_text)  # 光标位置

        # 输入框矩形
        self.input_rect = pygame.Rect(
            self.rect.x + 20,
            self.rect.y + 60,
            self.rect.width - 40,
            30
        )

        # 颜色定义（新增输入框颜色）
        self.colors.update({
            'input_bg': (240, 240, 240),
            'input_border': (100, 100, 100),
            'input_border_focus': (0, 120, 215),
            'cursor': (0, 0, 0)
        })

        # 输入状态
        self.input_active = True
        self.input_focus = True

        # 文本滚动相关
        self.text_offset = 0
        self.caret_offset = 0

        # 重新计算消息换行（考虑输入框位置）
        if message:
            self.message_lines = self.wrap_text(message, self.message_font, self.rect.width - 40)
            # 调整输入框位置
            message_height = len(self.message_lines) * 25
            self.input_rect.y = self.rect.y + 50 + message_height
            # 调整按钮位置
            self.ok_button_rect.y = self.input_rect.y + 50
            self.cancel_button_rect.y = self.input_rect.y + 50
        else:
            # 如果没有消息，向上移动输入框
            self.input_rect.y = self.rect.y + 50
            self.ok_button_rect.y = self.input_rect.y + 50
            self.cancel_button_rect.y = self.input_rect.y + 50

    def draw(self, surface):
        """绘制对话框"""
        if not self.visible:
            return

        # 调用父类的绘制方法
        super().draw(surface)

        # 绘制消息文本（如果有）
        for i, line in enumerate(self.message_lines):
            msg_surf = self.message_font.render(line, True, self.colors['message_text'])
            msg_pos = (self.rect.x + 20, self.rect.y + 35 + i * 25)
            surface.blit(msg_surf, msg_pos)

        # 绘制输入框
        border_color = self.colors['input_border_focus'] if self.input_focus else self.colors['input_border']
        pygame.draw.rect(surface, self.colors['input_bg'], self.input_rect)
        pygame.draw.rect(surface, border_color, self.input_rect, 2)

        # 创建用于文本渲染的表面
        text_surface = pygame.Surface((self.input_rect.width - 4, self.input_rect.height - 4), pygame.SRCALPHA)

        # 渲染文本
        font = self.message_font
        text_color = self.colors['message_text']

        # 计算可见文本部分
        visible_text = self.input_text

        temp_text = self.input_text

        # 渲染文本
        text_img = font.render(temp_text, True, text_color)

        # 计算文本位置（考虑滚动）
        text_x = 4 - self.text_offset
        text_y = (self.input_rect.height - text_img.get_height()) // 2

        # 绘制文本到文本表面
        text_surface.blit(text_img, (text_x, text_y))

        # 绘制光标
        if self.input_focus and self.cursor_visible:
            # 计算光标位置

            text_before_cursor = self.input_text[:self.cursor_position]

            cursor_x = font.size(text_before_cursor)[0] - self.text_offset

            # 确保光标在可见区域内
            if cursor_x < 0:
                self.text_offset += cursor_x
                cursor_x = 0
            elif cursor_x > self.input_rect.width - 10:
                self.text_offset += cursor_x - (self.input_rect.width - 10)
                cursor_x = self.input_rect.width + 10

            cursor_rect = pygame.Rect(cursor_x, 2, 2, self.input_rect.height - 8)
            pygame.draw.rect(text_surface, self.colors['cursor'], cursor_rect)



        # 将文本表面绘制到主表面
        surface.blit(text_surface, (self.input_rect.x + 2, self.input_rect.y + 2))

    def handle_event(self, event):
        """处理事件"""
        if not self.visible:
            return None

        # 更新按钮悬停状态
        mouse_pos = pygame.mouse.get_pos()
        self.ok_hovered = self.ok_button_rect.collidepoint(mouse_pos)
        self.cancel_hovered = self.cancel_button_rect.collidepoint(mouse_pos)

        # 处理鼠标点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.input_rect.collidepoint(event.pos):
                self.input_focus = True
                # 计算点击位置对应的光标位置
                self.update_cursor_position_from_mouse(event.pos)
                return "INPUT"
            elif self.ok_button_rect.collidepoint(event.pos):
                self.result = self.input_text
                self.hide()
                return "OK"
            elif self.cancel_button_rect.collidepoint(event.pos):
                self.result = None
                self.hide()
                return "CANCEL"
            else:
                self.input_focus = False

        # 处理键盘输入（仅在输入框获得焦点时）
        if self.input_focus:
            if event.type == pygame.KEYDOWN:
                # 处理特殊键
                if event.key == pygame.K_RETURN:
                    self.result = self.input_text
                    self.hide()
                    return "OK"
                elif event.key == pygame.K_ESCAPE:
                    self.result = None
                    self.hide()
                    return "CANCEL"
                elif event.key == pygame.K_BACKSPACE:
                    self.back_text()
                elif event.key == pygame.K_DELETE:
                    if self.cursor_position < len(self.input_text):
                        self.input_text = (self.input_text[:self.cursor_position] +
                                           self.input_text[self.cursor_position + 1:])
                else:
                    # 不处理其他按键，等待TEXTINPUT事件
                    pass

            # 处理文本输入事件
            elif event.type == pygame.TEXTINPUT:
                # 插入普通文本
                self.insert_text(event.text)

            # 处理按钮点击
            result = super().handle_event(event)
            if result == "OK":
                self.result = self.input_text
                # 如果没有选择选项，不关闭对话框
            return result



    def insert_text(self, text):
        """插入文本到当前光标位置"""
        self.input_text = (self.input_text[:self.cursor_position] +
                               text +
                               self.input_text[self.cursor_position:])
        self.cursor_position += len(text)

    def clear_text(self):
        self.input_text = ""
        self.cursor_position = 0

    def back_text(self):
        if self.cursor_position > 0:
            # 删除光标前的字符
            self.input_text = (self.input_text[:self.cursor_position - 1] +
                               self.input_text[self.cursor_position:])
            self.cursor_position -= 1

    def update_cursor_position_from_mouse(self, mouse_pos):
        """根据鼠标点击位置更新光标位置"""
        # 计算相对于输入框的位置
        rel_x = mouse_pos[0] - self.input_rect.x - 2 + self.text_offset

        # 找到最接近的字符位置
        font = self.message_font
        current_width = 0
        best_position = 0
        min_distance = float('inf')

        for i in range(len(self.input_text) + 1):
            # 计算到当前位置的距离
            distance = abs(rel_x - current_width)
            if distance < min_distance:
                min_distance = distance
                best_position = i

            if i < len(self.input_text):
                # 计算下一个字符的宽度
                char_width = font.size(self.input_text[i])[0]
                current_width += char_width

        self.cursor_position = best_position

    def update(self):
        """更新对话框状态"""
        # 更新光标闪烁
        current_time = pygame.time.get_ticks()
        if current_time - self.cursor_timer > self.cursor_blink_interval:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time

        # 确保文本滚动正确
        self.ensure_cursor_visible()

    def ensure_cursor_visible(self):
        """确保光标在可见区域内"""
        if not self.input_focus:
            return

        font = self.message_font
        text_before_cursor = self.input_text[:self.cursor_position]
        cursor_x = font.size(text_before_cursor)[0]

        # 检查光标是否在可见区域外
        if cursor_x < self.text_offset:
            self.text_offset = cursor_x
        elif cursor_x > self.text_offset + self.input_rect.width - 10:
            self.text_offset = cursor_x - self.input_rect.width + 10

    def show(self):
        """显示对话框"""
        super().show()
        self.input_focus = True
        self.cursor_visible = True
        self.cursor_timer = pygame.time.get_ticks()


# ------------------- 测试代码（可直接运行） -------------------
if __name__ == "__main__":
    # 创建窗口
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("中文输入对话框测试")