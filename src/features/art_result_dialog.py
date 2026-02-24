import pygame
from .custom_dialog import CustomDialog


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