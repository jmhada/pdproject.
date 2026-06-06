import pygame as pg
import constant as c
import random

# 모든 적들의 공통 기능을 담은 부모 클래스
class Enemy(pg.sprite.Sprite):
    def __init__(self, x, y, waypoints):
        super().__init__()

        self.state = 'moving'
        self.move_images = []
        self.death_images = []
        self.current_frame = 0
        self.animation_speed = 0.15

        self.max_hp = 100
        self.hp = self.max_hp
        self.speed = 2

        self.image = None
        self.rect = None

        self.waypoints = waypoints
        self.target_waypoint_idx = 0
        self.pos = pg.math.Vector2(x, y)

        self.stun_timer = 0
        self.is_stunned = False

        self.reward = 10  # 기본 보상
        self.reward_given = False

    def setup_initial_image(self):
        if self.move_images:
            self.image = self.move_images[0]
            self.rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

    def update(self, dt=0):
        # 1. 스턴 로직 수정
        if self.is_stunned:
            self.stun_timer -= dt
            if self.stun_timer <= 0:
                self.is_stunned = False
                if self.state != 'dying':
                    self.state = 'moving'

        # 2. 상태별 행동 제어
        if self.state == 'moving':
            self.move()
            self.animate(self.move_images, loop=True)
            if self.target_waypoint_idx < len(self.waypoints):
                # 목표 지점의 X 좌표
                target_x = self.waypoints[self.target_waypoint_idx][0]

                # 목표 지점이 내 위치보다 작으면(왼쪽이면)
                moving_left = target_x < self.rect.centerx

                if moving_left:
                    self.image = pg.transform.flip(self.image, True, False)

        elif self.state == 'dying':
            self.animate(self.death_images, loop=False)

        elif self.state == 'stunned':
            pass

    def move(self):
        if self.state == 'dying':
            return

        if self.target_waypoint_idx < len(self.waypoints):
            target = pg.math.Vector2(self.waypoints[self.target_waypoint_idx])
            move_vec = target - self.pos

            if move_vec.length() < self.speed:
                self.target_waypoint_idx += 1
            else:
                move_vec.scale_to_length(self.speed)
                self.pos += move_vec
                self.rect.center = self.pos

    def animate(self, image_list, loop=True):
        if not image_list:
            if not loop:
                self.kill()
            return

        self.current_frame += self.animation_speed

        if self.current_frame >= len(image_list):
            if loop:
                self.current_frame = 0
            else:
                self.kill()  # 애니메이션 종료 시 확실히 삭제
                return

        # 인덱스 범위 초과 방지
        idx = int(self.current_frame)
        if idx < len(image_list):
            self.image = image_list[idx]

    def take_damage(self, amount):
        if self.state == 'dying':
            return

        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.state = 'dying'
            self.current_frame = 0
            if not self.death_images:
                self.kill()

    def set_stun(self, duration):
        self.is_stunned = True
        self.stun_timer = duration
        if self.state != 'dying':
            self.state = 'stunned'


# --- 개별 몬스터 클래스 ---
class Orc(Enemy):
    def __init__(self, x, y, waypoints, image_data):
        super().__init__(x, y, waypoints)
        self.max_hp = 100
        self.hp = self.max_hp
        self.speed = 1.5
        self.move_images = image_data['orc_move']
        self.death_images = image_data['orc_death']
        self.setup_initial_image()
        self.reward = c.ENEMY_REWARDS["Orc"]


class OrcRider(Enemy):
    def __init__(self, x, y, waypoints, image_data):
        super().__init__(x, y, waypoints)
        self.max_hp = 120
        self.hp = self.max_hp
        self.speed = 3
        self.move_images = image_data['orcrider_move']
        self.death_images = image_data['orcrider_death']
        self.setup_initial_image()
        self.reward = c.ENEMY_REWARDS["OrcRider"]


class Slime(Enemy):
    def __init__(self, x, y, waypoints, image_data):
        super().__init__(x, y, waypoints)
        self.max_hp = 80
        self.hp = self.max_hp
        self.speed = 1.2
        self.move_images = image_data['slime_move']
        self.death_images = image_data['slime_death']
        self.setup_initial_image()
        self.reward = c.ENEMY_REWARDS["Slime"]


class SlimeBaby(Enemy):
    def __init__(self, x, y, waypoints, image_data, target_idx):
        super().__init__(x, y, waypoints)
        self.max_hp = 20
        self.hp = self.max_hp
        self.speed = 2.5
        self.reward = c.ENEMY_REWARDS["SlimeBaby"]
        self.move_images = [pg.transform.scale(img, (img.get_width() // 2, img.get_height() // 2)) for img in
                            image_data['slime_move']]
        self.death_images = [pg.transform.scale(img, (img.get_width() // 2, img.get_height() // 2)) for img in
                             image_data['slime_death']]

        self.setup_initial_image()
        self.target_waypoint_idx = target_idx

class ArmoredOrc(Enemy):
    def __init__(self, x, y, waypoints, image_data):
        super().__init__(x, y, waypoints)
        self.max_hp = 300
        self.hp = self.max_hp
        self.speed = 1.3
        self.move_images = image_data['armoredorc_move']
        self.death_images = image_data['armoredorc_death']
        self.setup_initial_image()
        self.reward = c.ENEMY_REWARDS["ArmoredOrc"]

class Skeleton(Enemy):
    def __init__(self, x, y, waypoints, image_data):
        super().__init__(x, y, waypoints)
        self.max_hp = 50
        self.hp = self.max_hp
        self.speed = 1.8
        self.move_images = image_data['skeleton_move']
        self.death_images = image_data['skeleton_death']
        self.setup_initial_image()
        self.reward = c.ENEMY_REWARDS["Skeleton"]


class SkeletonArcher(Enemy):
    def __init__(self, x, y, waypoints, image_data):
        super().__init__(x, y, waypoints)
        self.max_hp = 200
        self.hp = self.max_hp
        self.speed = 1.7
        self.move_images = image_data['skeletonarcher_move']
        self.death_images = image_data['skeletonarcher_death']
        self.setup_initial_image()
        self.reward = c.ENEMY_REWARDS["SkeletonArcher"]
        self.alive_timer = 0.0

        self.revived = False
        self.grant_free_snipe = False
        self.spawn_tombstone = False  # 비석 스폰 신호 플래그

    def take_damage(self, amount):
        if self.state == 'dying': return
        self.hp -= amount
        if self.hp <= 0:
            if not self.revived:
                self.hp = 0
                self.state = 'dying'
                self.spawn_tombstone = True
                self.reward_given = True
            else:
                self.hp = 0
                self.state = 'dying'
                self.current_frame = 0
                if not self.death_images: self.kill()

    def update(self, dt=0, heroes=None, bullets=None):
        super().update(dt)
        if self.state in ['moving', 'idle']:
            self.alive_timer += dt
            if self.alive_timer >= 10.0:
                self.alive_timer -= 10.0
                self.grant_free_snipe = True


class GreatswordSkeleton(Enemy):
    def __init__(self, x, y, waypoints, image_data):
        super().__init__(x, y, waypoints)
        self.max_hp = 180
        self.hp = self.max_hp
        self.speed = 1.5
        self.move_images = image_data['greatswordskeleton_move']
        self.death_images = image_data['greatswordskeleton_death']
        self.setup_initial_image()
        self.reward = c.ENEMY_REWARDS["GreatswordSkeleton"]

        self.revived = False
        self.trigger_explosion = None
        self.spawn_tombstone = False  # 비석 스폰 신호 플래그

    def take_damage(self, amount):
        if self.state == 'dying': return
        self.hp -= amount
        if self.hp <= 0:
            if not self.revived:
                self.hp = 0
                self.state = 'dying'
                self.spawn_tombstone = True
                self.reward_given = True  # client.py의 보상 루프를 가로막음
                self.trigger_explosion = (120, 50)
            else:
                # 부활 후 두 번째 죽음: 2차 더 넓은 범위 피해 후 완전히 사망
                self.hp = 0
                self.state = 'dying'
                self.current_frame = 0
                self.trigger_explosion = (200, 100)
                if not self.death_images: self.kill()


class SkeletonTombstone(Enemy):
    def __init__(self, x, y, waypoints, original_type, original_reward, current_waypoint_idx, image_data):
        super().__init__(x, y, waypoints)
        self.max_hp = 150
        self.hp = self.max_hp
        self.speed = 0.0
        self.state = 'moving'
        self.original_type = original_type
        self.reward = original_reward
        self.reward_given = False
        self.target_waypoint_idx = current_waypoint_idx
        self.alive_timer = 3.0  # 3초 대기 타이머
        self.revive_triggered = False
        self.image = image_data.get('tombstone')

        if not self.image:
            self.image = pg.Surface((55, 70), pg.SRCALPHA)
            pg.draw.rect(self.image, (120, 120, 120), (0, 0, 55, 70), border_radius=5)

        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt=0):
        if self.state != 'dying':
            self.alive_timer -= dt
            if self.alive_timer <= 0:
                self.revive_triggered = True
                self.hp = 0
                self.state = 'dying'
                self.reward_given = True
                self.kill()


class Zeppelin(Enemy):
    def __init__(self, x, y, waypoints, image_dict):
        self.images_normal = image_dict.get('zeppelin_move', [pg.Surface((120, 80))])
        self.images_gun = image_dict.get('zeppelin_gun', [pg.Surface((120, 80))])

        super().__init__(x, y, waypoints)

        self.zep_frame = 0.0
        self.animation_speed = 8.0

        self.image = self.images_normal[0]
        self.rect = self.image.get_rect(center=(x, y))

        self.max_hp = 500
        self.hp = self.max_hp
        self.speed = 1.5
        self.reward = c.ENEMY_REWARDS["Zeppelin"]
        self.is_flying = True

        self.is_gun_mode = False
        self.attack_cooldown = 0
        self.attack_speed = 1.0
        self.attack_range = 300
        self.attack_power = 60

        self.facing_left = False

    def update(self, dt, heroes=None, bullets=None):
        super().update(dt)

        if self.state == 'moving' and self.target_waypoint_idx < len(self.waypoints):
            target_x = self.waypoints[self.target_waypoint_idx][0]
            if self.rect.centerx - target_x > 2:
                self.facing_left = True
            elif target_x - self.rect.centerx > 2:
                self.facing_left = False

        self.zep_frame += self.animation_speed * dt
        if self.zep_frame >= len(self.images_normal):
            self.zep_frame = 0.0
        frame_idx = int(self.zep_frame)

        if self.hp <= self.max_hp * 0.5:
            base_img = self.images_gun[frame_idx]
            self.is_gun_mode = True
        else:
            base_img = self.images_normal[frame_idx]

        if self.facing_left:
            self.image = pg.transform.flip(base_img, True, False)
        else:
            self.image = base_img

        if self.state in ['moving', 'idle']:
            if self.is_gun_mode:
                if self.attack_cooldown > 0:
                    self.attack_cooldown -= dt

                if self.attack_cooldown <= 0 and heroes and bullets:
                    target = self.find_hero_target(heroes)
                    if target:
                        from bullet import EnemyBullet
                        new_bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, target, self.attack_power)
                        bullets.add(new_bullet)
                        self.attack_cooldown = 1.0 / self.attack_speed

    def find_hero_target(self, heroes):
        closest_hero = None
        min_dist = self.attack_range
        for hero in heroes:
            dist = pg.math.Vector2(self.rect.center).distance_to(pg.math.Vector2(hero.rect.center))
            if dist < min_dist:
                min_dist = dist
                closest_hero = hero
        return closest_hero


class SpeedZone(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 파란색 반투명 장판 생성
        width, height = 120, 120
        self.image = pg.Surface((width, height), pg.SRCALPHA)
        pg.draw.rect(self.image, (0, 100, 255, 100), (0, 0, width, height), border_radius=10)

        self.rect = self.image.get_rect(center=(x, y))
        self.timer = 4.0  # 장판 지속 시간 (4초)

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.kill()


class Ship(Enemy):
    def __init__(self, x, y, waypoints, image_data, zones_group):
        super().__init__(x, y, waypoints)
        self.max_hp = 700
        self.hp = self.max_hp
        self.base_speed = 0.8
        self.speed = self.base_speed
        self.reward = c.ENEMY_REWARDS["Ship"]

        self.move_images = image_data.get('ship_move', [pg.Surface((100, 100))])
        self.image_taunt = image_data.get('ship_taunt', [pg.Surface((100, 100))])[0]
        self.setup_initial_image()

        self.zones_group = zones_group
        self.drop_timer = 0.0

        self.is_taunting = False
        self.taunt_cycle = 10.0
        self.taunt_duration = 5.0
        self.dot_timer = 0.0
        self.slow_timer = 0.0

        self.dot_range = 250

    def set_stun(self, duration):
        self.slow_timer = duration

    def update(self, dt=0, heroes=None, bullets=None):
        slow_factor = 1.0
        if self.slow_timer > 0:
            self.slow_timer -= dt
            slow_factor = 0.6

        self.speed = self.base_speed * slow_factor

        if self.state in ['moving', 'idle']:
            if not self.is_taunting:
                self.taunt_cycle -= dt
                if self.taunt_cycle <= 0:
                    self.is_taunting = True
                    self.taunt_duration = 5.0
                    self.taunt_cycle = 10.0
                    self.image = self.image_taunt
                else:
                    super().update(dt)
                    self.drop_timer -= dt
                    if self.drop_timer <= 0:
                        new_zone = SpeedZone(self.rect.centerx, self.rect.centery)
                        self.zones_group.add(new_zone)
                        self.drop_timer = 1.5
            else:
                self.taunt_duration -= dt
                if self.taunt_duration <= 0:
                    self.is_taunting = False
                else:
                    if heroes:
                        self.dot_timer -= dt
                        if self.dot_timer <= 0:
                            for h in heroes:
                                if hasattr(h, 'hp') and h.hp > 0:
                                    dist = pg.math.Vector2(self.rect.center).distance_to(pg.math.Vector2(h.rect.center))
                                    if dist <= self.dot_range:
                                        h.hp -= 35
                                        if h.hp <= 0: h.kill()
                            self.dot_timer = 1.0

        if self.image:
            self.rect = self.image.get_rect(center=self.pos)

    def take_damage(self, amount):
        if getattr(self, 'is_taunting', False):
            amount *= 0.5
        super().take_damage(amount)

#감소되는효과  게이지 형식 필요
class RedAngel(Enemy):
    def __init__(self, x, y, waypoints, image_data):
        super().__init__(x, y, waypoints)
        self.max_hp = 300
        self.hp = self.max_hp
        self.base_speed = 1.5
        self.speed = self.base_speed
        self.reward = c.ENEMY_REWARDS["RedAngel"]

        self.move_images = image_data.get('redangel_move', [pg.Surface((85, 64))])
        self.death_images = image_data.get('redangel_death', [pg.Surface((85, 64))])
        self.setup_initial_image()

        self.skill_timer = 5.0  # 최초 5초
        self.skill_cooldown = 15.0  # 이후 15초마다
        self.stop_timer = 0.0  # 멈춤 지속 시간

        self.is_flying = True

    def update(self, dt=0, heroes=None, bullets=None):
        # 1. 멈춤 로직
        if self.stop_timer > 0:
            self.stop_timer -= dt
            self.speed = 0.0  # 멈춤!
        else:
            self.speed = self.base_speed  # 다시 이동

        super().update(dt)

        # 2. 광역 레벨 다운 스킬
        if self.state in ['moving', 'idle']:
            self.skill_timer -= dt
            if self.skill_timer <= 0:
                self.skill_timer = self.skill_cooldown
                self.stop_timer = 3.0  # 스킬 발동 시 3초간 정지

                if heroes:
                    for h in heroes:
                        if hasattr(h, 'level') and h.level > 1:
                            h.level -= 1
                            h.level_down_timer = 1.5
                            if hasattr(h, 'setup_stats'):
                                h.setup_stats()

class BlueAngel(Enemy):
    def __init__(self, x, y, waypoints, image_data):
        super().__init__(x, y, waypoints)
        self.max_hp = 450
        self.hp = self.max_hp
        self.base_speed = 1.5
        self.speed = self.base_speed
        self.reward = c.ENEMY_REWARDS["BlueAngel"]

        self.move_images = image_data.get('blueangel_move', [pg.Surface((85, 64))])
        self.death_images = image_data.get('blueangel_death', [pg.Surface((85, 64))])
        self.setup_initial_image()


        self.skill_timer = 7.0
        self.skill_cooldown = 15.0

        self.is_flying = True

        self.is_casting = False

    def update(self, dt=0, heroes=None, bullets=None):
        if self.state in ['moving', 'idle']:
            if self.skill_timer <= 5.0:
                self.speed = 0.0  # 이동 멈춤
                self.is_casting = True  # 1.5배 피해를 받는 취약 상태 돌입
            else:
                self.speed = self.base_speed
                self.is_casting = False

        super().update(dt)


        if self.state in ['moving', 'idle']:
            self.skill_timer -= dt

            if self.skill_timer <= 0:
                self.skill_timer = self.skill_cooldown
                self.is_casting = False

                if heroes and len(heroes) > 0:
                    alive_heroes = [h for h in heroes if
                                    getattr(h, 'hp', 0) > 0 and not getattr(h, 'is_brainwashed', False)]

                    if alive_heroes:
                        target_hero = random.choice(alive_heroes)
                        target_hero.is_brainwashed = True
                        target_hero.brainwash_timer = 10.0
                        self.network_send_brainwash = (target_hero.rect.centerx, target_hero.rect.centery)

    def take_damage(self, amount):
        if getattr(self, 'is_casting', False):
            amount *= 1.5
        super().take_damage(amount)