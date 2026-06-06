# bullet.py

import pygame as pg
import math
from battle import MagicEffect, PriestSkillEffect, PriestHealEffect
from image import load_images


class Bullet(pg.sprite.Sprite):
    def __init__(self, x, y, image_data, target, damage, battle_group, bullet_type="arrow"):
        super().__init__()
        self.bullet_type = bullet_type

        if self.bullet_type in ["magic", "priest_magic", "priest_heal"]:
            self.image = pg.Surface((10, 10), pg.SRCALPHA)
            self.image.fill((0, 0, 0, 0))
            self.original_image = self.image
        else:
            self.image = image_data
            self.original_image = image_data

        self.rect = self.image.get_rect(center=(x, y))
        self.target = target
        self.damage = damage
        self.battle_group = battle_group

        self.speed = 12
        if self.bullet_type in ["priest_magic", "priest_heal"]:
            self.speed = 3000

        self.pos = pg.math.Vector2(x, y)
        self.priest_effect = None

    def update(self, dt):
        if not self.target or not self.target.alive() or self.target.state == 'dying':
            self.kill()
            return

        target_pos = pg.math.Vector2(self.target.rect.center)
        distance = self.pos.distance_to(target_pos)

        if distance < self.speed + 15:

            if self.bullet_type == "priest_heal":
                self.target.hp = min(self.target.hp + self.damage, getattr(self.target, 'max_hp', self.target.hp))

                if getattr(self, 'priest_effect', None):
                    effect = PriestHealEffect(self.target.rect.centerx, self.target.rect.centery + 10,
                                              self.priest_effect)
                    self.battle_group.add(effect)

            else:
                self.target.take_damage(self.damage)

                if self.bullet_type == "magic":
                    magic_images = load_images()['battle']['magic_effect']
                    effect = MagicEffect(target_pos.x, target_pos.y, magic_images, self.target)
                    self.battle_group.add(effect)

                if self.bullet_type == "priest_magic" and getattr(self, 'priest_effect', None):
                    effect = PriestSkillEffect(self.target.rect.centerx, self.target.rect.centery, self.priest_effect)
                    self.battle_group.add(effect)

            self.kill()  # 볼일이 끝난 총알은 삭제
            return

        # 이동 로직
        direction = (target_pos - self.pos).normalize()
        self.pos += direction * self.speed
        self.rect.center = self.pos

        # 화살 회전 로직
        if self.bullet_type == "arrow":
            angle = direction.angle_to(pg.math.Vector2(1, 0))
            self.image = pg.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.rect.center)


#2. 폭발하는 광역 투사체
class AoEBullet(pg.sprite.Sprite):
    def __init__(self, x, y, arrow_img, explosion_images_ignored, target, damage, enemy_group):
        super().__init__()
        self.original_image = arrow_img
        self.image = arrow_img
        self.rect = self.image.get_rect(center=(x, y))

        self.target = target
        self.damage = damage
        self.enemy_group = enemy_group

        self.speed = 15
        self.pos = pg.math.Vector2(x, y)
        self.state = 'flying'

        self.max_radius = 90
        self.current_radius = 0
        self.alpha = 255
        self.expansion_speed = 350
        self.fade_speed = 500
        self.damage_applied = False

    def update(self, dt):
        if self.state == 'flying':
            if not self.target or not self.target.alive() or self.target.state == 'dying':
                self.explode()
                return

            target_pos = pg.math.Vector2(self.target.rect.center)
            distance = self.pos.distance_to(target_pos)

            if distance < self.speed + 15:
                self.explode()
                return

            direction = (target_pos - self.pos).normalize()
            self.pos += direction * self.speed
            self.rect.center = self.pos

            angle = direction.angle_to(pg.math.Vector2(1, 0))
            self.image = pg.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.rect.center)

        elif self.state == 'exploding':
            # 1. 데미지 적용
            if not self.damage_applied:
                for enemy in self.enemy_group:
                    if enemy.alive():
                        dist = self.pos.distance_to(pg.math.Vector2(enemy.rect.center))
                        if dist <= self.max_radius:
                            enemy.take_damage(self.damage)
                self.damage_applied = True

            self.current_radius += self.expansion_speed * dt  # 불꽃이 퍼짐
            self.alpha -= self.fade_speed * dt  # 불꽃이 사라짐

            if self.current_radius > self.max_radius:
                self.current_radius = self.max_radius

            if self.alpha <= 0:
                self.kill()
                return
            surf = pg.Surface((int(self.max_radius * 2), int(self.max_radius * 2)), pg.SRCALPHA)
            surf.fill((0, 0, 0, 0))
            center = (int(self.max_radius), int(self.max_radius))
            pg.draw.circle(surf, (255, 69, 0, max(0, int(self.alpha))), center, int(self.current_radius))
            if self.current_radius > 10:
                pg.draw.circle(surf, (255, 255, 0, max(0, int(self.alpha))), center, int(self.current_radius * 0.6))
            self.image = surf
            self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
    def explode(self):
        self.state = 'exploding'


class EnemyBullet(pg.sprite.Sprite):
    def __init__(self, x, y, target, damage):
        super().__init__()
        self.image = pg.Surface((10, 10), pg.SRCALPHA)
        pg.draw.circle(self.image, (255, 50, 0), (5, 5), 5)
        self.rect = self.image.get_rect(center=(x, y))

        self.target = target
        self.damage = damage
        self.speed = 350
        self.pos = pg.math.Vector2(x, y)

    def update(self, dt):
        if not self.target or getattr(self.target, 'hp', 0) <= 0:
            self.kill()
            return

        target_pos = pg.math.Vector2(self.target.rect.center)
        distance = self.pos.distance_to(target_pos)

        if distance < self.speed * dt + 15:
            self.target.hp -= self.damage
            if self.target.hp <= 0:
                self.target.kill()
            self.kill()
            return


        direction = (target_pos - self.pos).normalize()
        self.pos += direction * self.speed * dt
        self.rect.center = self.pos
