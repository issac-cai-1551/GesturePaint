# voice_ui.py
import time

import pygame


class VoiceUI:
    """语音控制UI组件"""

    def __init__(self):
        self.is_visible = True
        self.last_update = time.time()
        self.volume = 0
        self.waveform_data = []
        self.command_history = []
        self.max_history = 5

    def update_volume(self, volume):
        """更新音量数据"""
        self.volume = volume
        self.waveform_data.append(volume)
        if len(self.waveform_data) > 50:
            self.waveform_data.pop(0)

    def add_command(self, command):
        """添加命令到历史"""
        self.command_history.append({
            'text': command,
            'time': time.time()
        })
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)

    def draw(self, screen, is_listening, last_command=None):
        """绘制语音UI"""
        if not self.is_visible:
            return

        screen_width, screen_height = screen.get_size()

        # 1. 语音状态面板
        self._draw_status_panel(screen, is_listening, screen_width)

        # 2. 波形可视化
        self._draw_waveform(screen, screen_width)

        # 3. 最近命令
        if last_command:
            self._draw_last_command(screen, last_command, screen_width)

        # 4. 命令历史
        self._draw_command_history(screen, screen_width)

    def _draw_status_panel(self, screen, is_listening, screen_width):
        """绘制状态面板"""
        panel_rect = pygame.Rect(screen_width - 300, 10, 280, 80)

        # 背景
        pygame.draw.rect(screen, (30, 30, 40, 220), panel_rect, border_radius=10)
        pygame.draw.rect(screen, (60, 60, 80), panel_rect, 2, border_radius=10)

        # 麦克风图标
        mic_color = (0, 255, 0) if is_listening else (100, 100, 100)
        pygame.draw.circle(screen, mic_color, (screen_width - 280, 40), 15)
        pygame.draw.circle(screen, (255, 255, 255), (screen_width - 280, 40), 15, 2)

        # 状态文本
        font = pygame.font.SysFont('simhei', 18)
        status = "监听中..." if is_listening else "语音关闭"
        status_text = font.render(f"🎤 {status}", True, (255, 255, 255))
        screen.blit(status_text, (screen_width - 250, 25))

        # 提示文本
        hint = "说出命令，如'画一个红色的猫'"
        hint_text = font.render(hint, True, (180, 180, 200))
        screen.blit(hint_text, (screen_width - 250, 50))

    def _draw_waveform(self, screen, screen_width):
        """绘制声波波形"""
        if not self.waveform_data:
            return

        base_x = screen_width - 300
        base_y = 100
        width = 280
        height = 60

        # 背景
        pygame.draw.rect(screen, (20, 20, 30, 180),
                         (base_x, base_y, width, height), border_radius=5)

        # 绘制波形
        for i in range(len(self.waveform_data) - 1):
            x1 = base_x + i * (width / len(self.waveform_data))
            x2 = base_x + (i + 1) * (width / len(self.waveform_data))
            y1 = base_y + height / 2 - self.waveform_data[i] * 20
            y2 = base_y + height / 2 - self.waveform_data[i + 1] * 20

            # 根据音量改变颜色
            vol = (self.waveform_data[i] + self.waveform_data[i + 1]) / 2
            color = (
                int(100 + vol * 155),
                int(100 + vol * 155),
                255
            )

            pygame.draw.line(screen, color, (x1, y1), (x2, y2), 2)

    def _draw_last_command(self, screen, command, screen_width):
        """绘制最近命令"""
        font = pygame.font.SysFont('simhei', 16)

        # 命令背景
        cmd_bg = pygame.Rect(screen_width - 300, 170, 280, 40)
        pygame.draw.rect(screen, (40, 40, 60, 200), cmd_bg, border_radius=5)
        pygame.draw.rect(screen, (80, 80, 100), cmd_bg, 1, border_radius=5)

        # 命令文本
        cmd_text = font.render(f"📝 {command[:30]}", True, (255, 255, 200))
        screen.blit(cmd_text, (screen_width - 290, 180))

    def _draw_command_history(self, screen, screen_width):
        """绘制命令历史"""
        if not self.command_history:
            return

        font = pygame.font.SysFont('simhei', 14)

        # 历史背景
        hist_bg = pygame.Rect(screen_width - 300, 220, 280, 150)
        pygame.draw.rect(screen, (30, 30, 40, 180), hist_bg, border_radius=5)
        pygame.draw.rect(screen, (60, 60, 80), hist_bg, 1, border_radius=5)

        # 标题
        title = font.render("📜 命令历史", True, (220, 220, 255))
        screen.blit(title, (screen_width - 290, 225))

        # 历史记录
        for i, cmd in enumerate(reversed(self.command_history[-5:])):
            text = f"• {cmd['text'][:25]}"
            if len(text) > 25:
                text = text[:22] + "..."

            cmd_text = font.render(text, True, (200, 200, 220))
            screen.blit(cmd_text, (screen_width - 290, 250 + i * 25))