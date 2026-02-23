# voice_visualizer.py
import pygame

class VoiceVisualizer:
    def __init__(self, width=800, height=600):  # 添加默认参数
        """
        初始化语音可视化器

        参数:
            width: 波形图宽度（默认800）
            height: 波形图高度（默认600）
        """
        self.width = width
        self.height = height
        self.audio_data = []
        self.max_samples = 100

    def add_audio_sample(self, volume):
        """添加音频样本用于可视化"""
        self.audio_data.append(volume)
        if len(self.audio_data) > self.max_samples:
            self.audio_data.pop(0)

    def draw_waveform(self, screen, position):
        """绘制声波图"""
        x, y = position

        if not self.audio_data:
            return

        # 绘制声波背景
        pygame.draw.rect(screen, (20, 20, 30),
                         (x, y, self.width, self.height))

        # 绘制声波
        for i in range(len(self.audio_data) - 1):
            value1 = self.audio_data[i] * self.height
            value2 = self.audio_data[i + 1] * self.height

            # 根据音量改变颜色
            volume = (self.audio_data[i] + self.audio_data[i + 1]) / 2
            color = (
                int(100 + volume * 155),
                int(100 + volume * 155),
                255
            )

            pygame.draw.line(
                screen,
                color,
                (x + i * (self.width / self.max_samples), y + self.height / 2 - value1 / 2),
                (x + (i + 1) * (self.width / self.max_samples), y + self.height / 2 - value2 / 2),
                2
            )