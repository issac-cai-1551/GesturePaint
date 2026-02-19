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
        self.cancel_button_rect.x = -100 # 移出屏幕
        
        # 居中确认按钮
        self.ok_button_rect.centerx = self.rect.centerx

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

        # 显示提示词
        prompt_text = f"使用的提示词: {self.prompt}"
        prompt_surf = self.message_font.render(prompt_text, True, (0, 0, 0))
        # 居中显示在标题栏下方
        prompt_rect = prompt_surf.get_rect(center=(self.rect.centerx, self.rect.y + 100))
        surface.blit(prompt_surf, prompt_rect)

        # 2. 绘制图片和箭头
        # 计算位置 - 整体下移以容纳提示词
        content_y = self.rect.y + 135
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
        surface.blit(orig_label, (orig_rect.centerx - orig_label.get_width()//2, orig_rect.bottom + 5))
        
        gen_label = self.button_font.render("AI艺术:", True, (0, 120, 215))
        surface.blit(gen_label, (gen_rect.centerx - gen_label.get_width()//2, gen_rect.bottom + 5))

        # 3. 绘制按钮
        ok_color = self.colors['button_hover'] if self.ok_hovered else self.colors['button_normal']
        pygame.draw.rect(surface, ok_color, self.ok_button_rect)
        pygame.draw.rect(surface, self.colors['border'], self.ok_button_rect, 2)
        ok_text = self.button_font.render('关闭', True, self.colors['button_text'])
        ok_text_pos = ok_text.get_rect(center=self.ok_button_rect.center)
        surface.blit(ok_text, ok_text_pos)
