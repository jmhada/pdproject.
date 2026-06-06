import pygame as pg
import math
from bullet import Bullet, AoEBullet
from battle import PriestHealEffect

# --- 모든 영웅의 부모 클래스 ---
class Hero(pg.sprite.Sprite):
    def __init__(self, x, y, image_data, screen=None):
        super().__init__()
        self.image_data = image_data

        self.state = 'idle'
        self.current_frame = 0
        self.animation_speed = 0.15

        # 기본 스탯 (하위 클래스에서 덮어씀)
        self.max_hp = 100
        self.hp = self.max_hp
        self.attack_power = 10
        self.attack_range = 100
        self.attack_speed = 1.0
        self.attack_cooldown = 0

        self.images = []
        self.image = None
        self.rect = None
        self.target = None

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.kill()

    def update(self, current_time, dt, enemies, battle_group, bullet_group):
        self.enemy_group = enemies

        self.find_target(enemies)

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        if self.state == 'idle':
            if self.target and self.attack_cooldown <= 0:
                self.state = 'attacking'
                self.current_frame = 0
                self.attack_cooldown = 1.0 / self.attack_speed
                self.attack(battle_group, bullet_group)

        elif self.state == 'attacking':
            self.animate(loop=False)

    def find_target(self, enemies):
        if getattr(self, 'is_brainwashed', False):
            enemies = [h for h in self.groups()[0].sprites() if h != self and getattr(h, 'hp', 0) > 0]

        taunting_enemies = []
        for e in enemies:
            if getattr(e, 'is_taunting', False) and getattr(e, 'hp', 0) > 0 and getattr(e, 'state', '') != 'dying':
                dist = pg.math.Vector2(self.rect.center).distance_to(pg.math.Vector2(e.rect.center))
                if dist <= self.attack_range:
                    taunting_enemies.append(e)
        target_list = taunting_enemies if taunting_enemies else enemies

        valid_targets = []
        for enemy in target_list:
            if getattr(enemy, 'hp', 0) > 0 and getattr(enemy, 'state', '') != 'dying':
                if getattr(enemy, 'is_flying', False) and type(self).__name__ not in ["Archer", "Wizard"]:
                    continue

                dist = pg.math.Vector2(self.rect.center).distance_to(pg.math.Vector2(enemy.rect.center))
                if dist <= self.attack_range:
                    valid_targets.append((dist, enemy.rect.x, enemy.rect.y, enemy))

        if valid_targets:
            valid_targets.sort(key=lambda t: (t[0], t[1], t[2]))
            self.target = valid_targets[0][3]
        else:
            self.target = None
    def animate(self, loop=True):
        if not self.images: return
        self.current_frame += self.animation_speed

        if self.current_frame >= len(self.images):
            if loop:
                self.current_frame = 0
            else:
                self.state = 'idle'  # 공격이 끝나면 다시 대기 상태로
                self.current_frame = 0
                return

        self.image = self.images[int(self.current_frame)]

    def attack(self, battle_group, bullet_group):
        pass
    def upgrade(self):
        pass


# 원거리 마법사 클래스
class Wizard(Hero):
    def __init__(self, x, y, image_data, screen=None):
        super().__init__(x, y, image_data, screen)
        # 마법사 고유 스탯
        self.attack_power = 60
        self.attack_range = 250
        self.attack_speed = 1.0
        self.max_hp = 150
        self.hp = self.max_hp

        # 마법사 이미지 로드
        self.images = self.image_data['wizard_attack']
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=(x, y))

    def attack(self, battle_group, bullet_group):
        if self.target and self.target.alive():
            # 원거리 공격: 투명 투사체(Bullet) 발사
            bullet_img = [self.image_data.get('magic_effect', [self.image])[0]]
            new_bullet = Bullet(self.rect.centerx, self.rect.centery, bullet_img, self.target, self.attack_power,
                                battle_group, bullet_type="magic" )
            bullet_group.add(new_bullet)


# ---근접 기사 클래스 ---
class Knight(Hero):
    def __init__(self, x, y, image_data, screen=None):
        super().__init__(x, y, image_data, screen)
        self.level = 1
        self.max_level = 3
        self.setup_stats()  # 레벨에 맞는 스탯/이미지 적용
        self.max_hp = 400
        self.hp = self.max_hp

        self.image = self.images[0]
        self.rect = self.image.get_rect(center=(x, y))

    def setup_stats(self):
        if self.level == 1:
            self.attack_power = 50
            self.attack_range = 150
            self.attack_speed = 1.0
            self.images = self.image_data['knight_attack_lvl1']
        elif self.level == 2:
            self.attack_power = 90
            self.attack_range = 160
            self.attack_speed = 1.2
            self.images = self.image_data['knight_attack_lvl2']
        elif self.level == 3:
            self.attack_power = 150
            self.attack_range = 170
            self.attack_speed = 1.5
            self.images = self.image_data['knight_attack_lvl3']

    def attack(self, battle_group, bullet_group):
        if self.target and self.target.alive():
            self.target.take_damage(self.attack_power)

    def upgrade(self):
        if self.level < self.max_level:
            self.level += 1
            self.setup_stats()  # 스탯 및 이미지 갱신
            self.current_frame = 0  # 모션 초기화
            return True
        return False

# ---원거리 아처 클래스---
class Archer(Hero):
    def __init__(self, x, y, image_data, arrow_image_data, screen=None):
        super().__init__(x, y, image_data, screen)
        # 엘리트 궁수 고유 변수
        self.projectile_img = None
        self.level = 1
        self.max_level = 3
        self.attack_counter = 0  # 공격 횟수 카운터
        self.arrow_image_data = arrow_image_data  # 레벨별 화살 이미지 딕셔너리
        self.max_hp = 150
        self.hp = self.max_hp

        self.setup_stats()  # 초기 스탯/이미지 적용

        # 초기 rect 설정
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=(x, y))

    def setup_stats(self):
        if self.level == 1:
            self.attack_power = 35
            self.attack_range = 300
            self.attack_speed = 1.3
            self.images = self.image_data['archer_attack_lvl1']
            # 레벨 1 화살 이미지 설정
            self.projectile_img = self.arrow_image_data['lvl1']
        elif self.level == 2:
            self.attack_power = 55
            self.attack_range = 300
            self.attack_speed = 1.6
            self.images = self.image_data['archer_attack_lvl2']
            # 레벨 2 화살 이미지 설정
            self.projectile_img = self.arrow_image_data['lvl2']
        elif self.level == 3:
            self.attack_power = 60
            self.attack_range = 300
            self.attack_speed = 2.0
            self.images = self.image_data['archer_attack_lvl3']
            # 레벨 3 화살 이미지 설정
            self.projectile_img = self.arrow_image_data['lvl3']

    def attack(self, battle_group, bullet_group):
        if self.target and self.target.alive():
            self.attack_counter += 1

            if self.level == 3 and self.attack_counter % 3 == 0:
                explosion_anim = self.image_data.get('magic_effect', [self.image])

                new_bullet = AoEBullet(
                    self.rect.centerx,
                    self.rect.centery,
                    self.projectile_img,
                    explosion_anim,
                    self.target,
                    self.attack_power * 2.0,
                    self.enemy_group
                )
                bullet_group.add(new_bullet)

            else:
                new_bullet = Bullet(self.rect.centerx, self.rect.centery, self.projectile_img, self.target,
                                    self.attack_power, battle_group, bullet_type="arrow")
                bullet_group.add(new_bullet)

    def upgrade(self):
        if self.level < self.max_level:
            self.level += 1
            self.setup_stats()
            self.current_frame = 0  # 모션 초기화
            #3레벨 부터 카운터 시작
            if self.level == 3:
                self.attack_counter = 0
            return True
        return False


class Priest(Hero):
    def __init__(self, x, y, image_data, screen=None):
        super().__init__(x, y, image_data, screen)

        fallback_img = [pg.Surface((100, 100), pg.SRCALPHA)]
        self.images_attack = image_data.get('priest_attack', fallback_img)
        self.images_heal = image_data.get('priest_heal', fallback_img)
        self.effect_attack = image_data.get('priest_attack_effect', fallback_img)
        self.effect_heal = image_data.get('priest_heal_effect', fallback_img)

        self.mode = 'attack'
        self.images = self.images_attack
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=(x, y))

        self.level = 1
        self.max_level = 3
        self.attack_count = 0
        self.hero_list_cache = []
        self.max_hp = 250
        self.hp = self.max_hp

        self.invisible_bullet = pg.Surface((1, 1), pg.SRCALPHA)
        self.invisible_bullet.fill((0, 0, 0, 0))

        self.action_triggered = False

        self.setup_stats()

    def setup_stats(self):
        if self.level == 1:
            self.base_attack_power = 30
            self.heal_power = 40
            self.max_attack_count = 25
        elif self.level == 2:
            self.base_attack_power = 55
            self.heal_power = 100
            self.max_attack_count = 20
        elif self.level == 3:
            self.base_attack_power = 80
            self.heal_power = 120
            self.max_attack_count = 10

        self.attack_power = self.base_attack_power
        self.attack_speed = 0.5
        self.attack_range = 300 if self.mode == 'attack' else 99999

    def upgrade(self):
        if self.level < self.max_level:
            self.level += 1
            self.setup_stats()
            self.current_frame = 0
            return True
        return False

    def toggle_mode(self):
        if self.mode == 'attack':
            self.mode = 'heal'
            self.images = self.images_heal
        else:
            self.mode = 'attack'
            self.images = self.images_attack

        self.attack_range = 250 if self.mode == 'attack' else 99999
        self.attack_count = 0
        self.current_frame = 0
        self.state = 'idle'
        self.image = self.images[0]
        self.action_triggered = False  # 모드 변경 시 초기화

    def update(self, current_time, dt, enemies, battle_group, bullet_group):
        heroes = self.groups()[0].sprites() if self.groups() else []
        self.hero_list_cache = heroes

        if hasattr(self, 'atk_buff_timer') and self.atk_buff_timer > 0:
            self.atk_buff_timer -= dt
            self.attack_power = self.base_attack_power * 1.5
        else:
            self.attack_power = self.base_attack_power

        if self.mode == 'attack':
            self.find_enemy_target(enemies)
        else:
            self.find_heal_target(heroes)

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        if self.state == 'idle':
            if self.images:
                self.image = self.images[0]

            if self.target and self.attack_cooldown <= 0:
                self.state = 'attacking'
                self.current_frame = 0
                self.attack_cooldown = 1.0 / self.attack_speed

                self.action_triggered = False

        elif self.state == 'attacking':
            self.animate(loop=False)


            if not getattr(self, 'action_triggered', False):
                if self.mode == 'attack' and int(self.current_frame) >= 3:
                    self.attack(battle_group, bullet_group)
                    self.action_triggered = True  # 발사 완료 처리

                # 힐러 모드: 2번째 프레임 (인덱스 1) 이상일 때 발사
                elif self.mode == 'heal' and int(self.current_frame) >= 1:
                    self.attack(battle_group, bullet_group)
                    self.action_triggered = True  # 발사 완료 처리

    def find_enemy_target(self, enemies):
        if getattr(self, 'is_brainwashed', False):
            enemies = [h for h in self.groups()[0].sprites() if h != self and getattr(h, 'hp', 0) > 0]

        valid_targets = []
        for enemy in enemies:
            if getattr(enemy, 'hp', 0) > 0 and getattr(enemy, 'state', '') != 'dying':
                dist = pg.math.Vector2(self.rect.center).distance_to(pg.math.Vector2(enemy.rect.center))
                if dist <= self.attack_range:
                    valid_targets.append((dist, enemy.rect.x, enemy.rect.y, enemy))

        if valid_targets:
            valid_targets.sort(key=lambda t: (t[0], t[1], t[2]))
            self.target = valid_targets[0][3]
        else:
            self.target = None
    def find_heal_target(self, heroes):
        if getattr(self, 'is_brainwashed', False):
            heroes = [e for e in getattr(self, 'enemy_group', []) if getattr(e, 'hp', 0) > 0]

        valid_targets = []
        for hero in heroes:
            if hasattr(hero, 'hp') and hasattr(hero, 'max_hp'):
                if 0 < hero.hp < hero.max_hp:
                    dist = pg.math.Vector2(self.rect.center).distance_to(pg.math.Vector2(hero.rect.center))
                    if dist <= self.attack_range:
                        ratio = hero.hp / hero.max_hp
                        valid_targets.append((ratio, hero.rect.x, hero.rect.y, hero))

        if valid_targets:
            valid_targets.sort(key=lambda t: (t[0], t[1], t[2]))
            self.target = valid_targets[0][3]
        else:
            self.target = None

    def attack(self, battle_group, bullet_group):
        if not self.target:
            return

        self.attack_count += 1

        if self.attack_count >= self.max_attack_count:
            self.attack_count = 0
            if self.mode == 'attack':
                enemy_list = self.target.groups()[0].sprites() if self.target.groups() else []
                for enemy in enemy_list:
                    if enemy.hp > 0 and enemy.state != 'dying':
                        enemy.hp = min(enemy.hp, enemy.max_hp * 0.5)
            else:
                for hero in self.hero_list_cache:
                    if hasattr(hero, 'hp') and hero.hp > 0:
                        hero.hp = getattr(hero, 'max_hp', hero.hp)
                        hero.atk_buff_timer = 20.0

        if self.mode == 'attack':
            if self.target.alive():
                new_bullet = Bullet(self.rect.centerx, self.rect.centery, self.invisible_bullet, self.target,
                                    self.attack_power, battle_group, bullet_type="priest_magic")
                new_bullet.priest_effect = self.effect_attack
                bullet_group.add(new_bullet)
        else:
            if self.target.alive():
                new_bullet = Bullet(self.rect.centerx, self.rect.centery, self.invisible_bullet, self.target,
                                    self.heal_power, battle_group, bullet_type="priest_heal")
                new_bullet.priest_effect = self.effect_heal
                bullet_group.add(new_bullet)