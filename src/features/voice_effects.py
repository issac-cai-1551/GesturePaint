import pygame
import random
import math


class VoiceEffects:
    """语音特效系统"""

    def __init__(self):
        self.particles = []
        self.sounds = {}
        self.load_sounds()

    def load_sounds(self):
        """加载音效"""
        try:
            # 使用系统默认音效或加载文件
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

            # 生成简单音效
            self.sounds['success'] = self.generate_beep(800, 200)
            self.sounds['error'] = self.generate_beep(400, 300)
            self.sounds['recording'] = self.generate_beep(600, 100)

        except Exception as e:
            print(f"⚠️ 音效加载失败: {e}")

    def generate_beep(self, frequency, duration):
        """生成简单的蜂鸣声"""
        try:
            sample_rate = 22050
            n_samples = int(sample_rate * duration / 1000.0)

            buf = bytearray()
            for i in range(n_samples):
                sample = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
                buf.extend([sample & 0xFF, (sample >> 8) & 0xFF])

            sound = pygame.mixer.Sound(buffer=bytes(buf))
            sound.set_volume(0.3)
            return sound
        except:
            return None

    def play_sound(self, sound_type):
        """播放音效"""
        if sound_type in self.sounds and self.sounds[sound_type]:
            try:
                self.sounds[sound_type].play()
            except:
                pass

    def create_command_effect(self, command, position):
        """创建命令特效"""
        if '保存' in command:
            self._create_save_effect(position)
        elif '清空' in command:
            self._create_clear_effect(position)
        elif '切换' in command or '颜色' in command:
            self._create_color_effect(position)
        elif '画' in command or '创作' in command:
            self._create_paint_effect(position)

    def _create_save_effect(self, position):
        """保存特效"""
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            self.particles.append({
                'x': position[0],
                'y': position[1],
                'vx': speed * math.cos(angle),
                'vy': speed * math.sin(angle),
                'color': (255, 255, 0),  # 黄色
                'life': 30,
                'size': 4
            })
        self.play_sound('success')

    def _create_color_effect(self, position):
        """颜色切换特效"""
        colors = [
            (255, 0, 0),  # 红
            (0, 255, 0),  # 绿
            (0, 0, 255),  # 蓝
            (255, 255, 0),  # 黄
            (255, 0, 255),  # 紫
            (0, 255, 255)  # 青
        ]

        for _ in range(30):
            color = random.choice(colors)
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            self.particles.append({
                'x': position[0],
                'y': position[1],
                'vx': speed * math.cos(angle),
                'vy': speed * math.sin(angle),
                'color': color,
                'life': 40,
                'size': 3
            })

    def _create_paint_effect(self, position):
        """绘画特效"""
        for _ in range(50):
            color = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.5, 2)
            self.particles.append({
                'x': position[0],
                'y': position[1],
                'vx': speed * math.cos(angle),
                'vy': speed * math.sin(angle),
                'color': color,
                'life': 60,
                'size': random.randint(2, 6)
            })

    def update(self):
        """更新粒子特效"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['vy'] += 0.1  # 重力

            if particle['life'] <= 0:
                self.particles.remove(particle)

    def draw(self, screen):
        """绘制粒子特效"""
        for particle in self.particles:
            alpha = min(255, particle['life'] * 6)
            color_with_alpha = (*particle['color'], alpha)

            # 绘制圆形粒子
            surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, color_with_alpha,
                               (particle['size'], particle['size']), particle['size'])
            screen.blit(surface, (particle['x'] - particle['size'], particle['y'] - particle['size']))