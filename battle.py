import pygame as pg


class BattleEffect(pg.sprite.Sprite):
    def __init__(self, x, y, images):
        super().__init__()
        self.images = images
        self.current_frame = 0
        self.animation_speed = 0.3  # 효과 애니메이션 속도
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.animate(self.images, loop=False)

    def animate(self, image_list, loop=True):
        self.current_frame += self.animation_speed
        if self.current_frame >= len(image_list):
            if loop:
                self.current_frame = 0
            else:
                self.kill()  # 애니메이션이 끝나면 효과 삭제
                return
        self.image = image_list[int(self.current_frame)]


class MagicEffect(BattleEffect):
    def __init__(self, x, y, images, target_enemy):
        super().__init__(x, y, images)
        self.target_enemy = target_enemy
        self.stun_duration = 1.3   # 스턴 지속 시간 (초)
        self.applied_stun = False  # 스턴 부여 여부

    def update(self):
        super().update()

        # 효과 애니메이션이 진행될 때 적에게 스턴 부여
        if self.current_frame >= 2 and not self.applied_stun:  # 2프레임쯤에서 스턴 부여
            self.apply_stun()
            self.applied_stun = True

    def apply_stun(self):
        if self.target_enemy and self.target_enemy.alive() and getattr(self.target_enemy, 'hp', 0) > 0:
            if hasattr(self.target_enemy, 'set_stun'):
                self.target_enemy.set_stun(self.stun_duration)

class PriestHealEffect(BattleEffect):
    def __init__(self, x, y, images):
        super().__init__(x, y, images)
        self.animation_speed = 0.2  # 힐 이펙트는 조금 더 부드럽게 재생
        self.rect = self.image.get_rect(center=(x, y))
class PriestSkillEffect(BattleEffect):
    def __init__(self, x, y, images):
        super().__init__(x, y, images)
        self.animation_speed = 0.4  # 타격감 있게 빠른 속도
        self.rect = self.image.get_rect(center=(x, y))

#오행
class InstaKillEffect(pg.sprite.Sprite):
    def __init__(self, x, y, images):
        super().__init__()
        self.images = images
        self.current_frame = 0
        self.image = self.images[0] if self.images else pg.Surface((0, 0), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.animation_speed = 0.4  # 재생 속도

    def update(self):
        if not self.images:
            self.kill()
            return
        self.current_frame += self.animation_speed
        if self.current_frame >= len(self.images):
            self.kill()  # 애니메이션이 끝나면 삭제
        else:
            self.image = self.images[int(self.current_frame)]
            self.rect = self.image.get_rect(center=self.rect.center)


class OrangeExplosion(pg.sprite.Sprite):
    def __init__(self, x, y, radius):
        super().__init__()
        self.image = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
        pg.draw.circle(self.image, (255, 150, 0, 100), (radius, radius), radius)
        pg.draw.circle(self.image, (255, 100, 0, 200), (radius, radius), radius, 3)
        self.rect = self.image.get_rect(center=(x, y))
        self.frames = 30  # 0.5초 지속

    def update(self):
        self.frames -= 1
        if self.frames <= 0:
            self.kill()


class FloatingText(pg.sprite.Sprite):
    def __init__(self, x, y, text, color=(255, 255, 255), size=20):
        super().__init__()
        font = pg.font.SysFont("malgungothic", size, bold=True)
        self.original_image = font.render(text, True, color)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.frames = 45  # 약 0.75초 동안 화면에 표시됨
        self.alpha = 255

    def update(self):
        self.rect.y -= 1
        self.frames -= 1

        if self.frames < 15:
            self.alpha = max(0, self.alpha - 17)
            self.image = self.original_image.copy()
            self.image.set_alpha(self.alpha)

        if self.frames <= 0:
            self.kill()