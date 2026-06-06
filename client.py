# client.py
import pygame as pg #다운로드 파이썬은 3.12.XX추천
import random
from network import Network
from hero import Wizard, Knight, Archer, Priest
from enemy import Orc, Slime, OrcRider, ArmoredOrc, Skeleton, SkeletonArcher, SlimeBaby, GreatswordSkeleton, Zeppelin, Ship, BlueAngel, RedAngel, SkeletonTombstone
from bullet import Bullet
from battle import MagicEffect, InstaKillEffect, OrangeExplosion, FloatingText
import constant as c
from image import load_images
import math
from pytmx.util_pygame import load_pygame #다운로드


#리듬게임 미니게임
class RhythmMiniGame:
    def __init__(self, target_hero, role, notes_keys=None):
        self.target_hero = target_hero
        self.role = role
        self.active = True

        self.phase = 'RHYTHM'
        self.success_count = 0

        self.target_y = 500
        self.speed = 350
        self.keys = [pg.K_LEFT, pg.K_DOWN, pg.K_UP, pg.K_RIGHT]
        self.key_names = {pg.K_LEFT: "←", pg.K_DOWN: "↓", pg.K_UP: "↑", pg.K_RIGHT: "→"}
        self.notes = []

        start_y = 100
        if self.role == "ATTACKER":
            for i in range(3):
                self.notes.append(
                    {'key': random.choice(self.keys), 'y': start_y - (i * 180), 'hit': False, 'missed': False})
        else:
            if notes_keys:
                for i, k in enumerate(notes_keys):
                    self.notes.append({'key': k, 'y': start_y - (i * 180), 'hit': False, 'missed': False})

        self.current_note_idx = 0

        # --- 2단계: 발사 및 방어 데이터
        self.arrow_x = 100
        self.arrow_speed = 700
        self.is_faked = False
        self.shield_key = None
        self.shield_timer = 0
        self.result_timer = 2.0
        self.result_msg = ""
        self.damage_applied = False
        self.defense_used = False

    def update(self, dt, net_sender):
        if self.phase == 'RHYTHM':
            all_done = True
            for note in self.notes:
                if not note['hit'] and not note['missed']:
                    note['y'] += self.speed * dt
                    # 바닥에 떨어지면 양쪽 화면 모두에서 자동으로 '놓침' 처리
                    if note['y'] > self.target_y + 60:
                        note['missed'] = True
                        if self.role == "ATTACKER" and self.current_note_idx == self.notes.index(note):
                            self.current_note_idx += 1
                    all_done = False

            if all_done:
                # 노트가 다 떨어지면 '공격자만' 서버에 발사 명령을 내립니다!
                if self.role == "ATTACKER":
                    net_sender({"action": "fire_arrow", "stacks": self.success_count})
                    self.start_attack_phase(self.success_count)

        elif self.phase == 'ATTACK':
            hero_center_x = c.SCREEN_WIDTH // 2
            # 3스택 페이크 로직
            if self.success_count >= 3 and not self.is_faked and self.arrow_x > hero_center_x - 150:
                self.arrow_x = hero_center_x + 150
                self.arrow_speed = -700
                self.is_faked = True

            self.arrow_x += self.arrow_speed * dt

            if self.shield_timer > 0:
                self.shield_timer -= dt
            else:
                self.shield_key = None

            dist = abs(self.arrow_x - hero_center_x)
            if dist < 30 and not self.damage_applied:
                self.damage_applied = True
                self.resolve_hit()

        elif self.phase == 'RESULT':
            self.result_timer -= dt
            if self.result_timer <= 0:
                self.active = False

    def start_attack_phase(self, stacks):
        self.success_count = stacks
        self.phase = 'ATTACK'

    def resolve_hit(self):
        attack_from_left = (self.arrow_speed > 0)
        blocked = False
        if attack_from_left and self.shield_key == pg.K_LEFT:
            blocked = True
        elif not attack_from_left and self.shield_key == pg.K_RIGHT:
            blocked = True

        if blocked:
            self.result_msg = "방어성공! (데미지 0)"
        else:
            self.result_msg = f"명중! ({self.success_count}스택)"
            if self.success_count <= 1:
                self.target_hero.take_damage(130)
            elif self.success_count == 2:
                self.target_hero.take_damage(250)
            elif self.success_count >= 3:
                self.target_hero.take_damage(500)
        self.phase = 'RESULT'

    def handle_input(self, key):
        if key == pg.K_w:
            key = pg.K_UP
        elif key == pg.K_a:
            key = pg.K_LEFT
        elif key == pg.K_s:
            key = pg.K_DOWN
        elif key == pg.K_d:
            key = pg.K_RIGHT
        if self.phase == 'RHYTHM' and self.role == "ATTACKER":
            if self.current_note_idx < len(self.notes):
                note = self.notes[self.current_note_idx]
                status = "missed"
                if abs(note['y'] - self.target_y) < 50:
                    if key == note['key']:
                        note['hit'] = True
                        self.success_count += 1
                        status = "hit"
                    else:
                        note['missed'] = True
                else:
                    note['missed'] = True

                idx = self.current_note_idx
                self.current_note_idx += 1
                return {"action": "rhythm_hit", "idx": idx, "status": status}

        elif self.phase == 'ATTACK' and self.role == "DEFENDER":
            if not getattr(self, 'defense_used', False):
                if key in [pg.K_LEFT, pg.K_RIGHT]:
                    self.shield_key = key
                    self.shield_timer = 0.2
                    self.defense_used = True
                    return {"action": "deploy_shield", "key": key}

        return None

    def draw(self, screen):
        screen.fill((25, 25, 35))
        font = pg.font.SysFont("malgungothic", 30, bold=True)
        hx, hy = c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2
        screen.blit(self.target_hero.image, self.target_hero.image.get_rect(center=(hx, hy)))

        if self.phase == 'RHYTHM':
            pg.draw.rect(screen, (255, 255, 0), (hx - 100, self.target_y - 25, 200, 50), 3)
            for note in self.notes:
                if not note['hit'] and not note['missed']:
                    text = font.render(self.key_names[note['key']], True, (255, 255, 255))
                    screen.blit(text, text.get_rect(center=(hx, int(note['y']))))

            # 수비자에게는 관전 중임을 알려줍니다
            if self.role == "DEFENDER":
                msg = font.render("적군이 저격을 준비 중입니다!", True, (255, 100, 100))
                screen.blit(msg, msg.get_rect(center=(hx, 150)))

        elif self.phase == 'ATTACK' or self.phase == 'RESULT':
            if self.shield_key:
                shield_color = (0, 255, 255)
                if self.shield_key == pg.K_LEFT:
                    pg.draw.rect(screen, shield_color, (hx - 50, hy - 40, 10, 80))
                elif self.shield_key == pg.K_RIGHT:
                    pg.draw.rect(screen, shield_color, (hx + 40, hy - 40, 10, 80))

            if not self.damage_applied:
                arrow_text = "→" if self.arrow_speed > 0 else "←"
                arr_img = font.render(arrow_text, True, (255, 200, 0))
                screen.blit(arr_img, arr_img.get_rect(center=(int(self.arrow_x), hy)))

            if self.role == "DEFENDER" and self.phase == 'ATTACK':
                guide = font.render("타이밍에 맞춰 왼쪽(←/A) 또는 오른쪽(→/D) 키로 방어하세요!", True, (0, 255, 255))
                screen.blit(guide, guide.get_rect(center=(hx, 100)))

        if self.phase == 'RESULT':
            color = (0, 255, 0) if "성공" in self.result_msg else (255, 50, 50)
            res = pg.font.SysFont("malgungothic", 50, bold=True).render(self.result_msg, True, color)
            screen.blit(res, res.get_rect(center=(hx, hy - 100)))

class GameClient:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        pg.display.set_caption("1vs1 Tower Defense")
        self.clock = pg.time.Clock()

        # 1. 초기 로드
        self.net = Network()  # 서버와 연결
        self.player_id = self.net.initial_data["player_id"]
        self.images = load_images()#이미지 로드
        # 시계 이미지 로드 및 리스트화
        self.time_assets = {}
        parts = ["clock frame", "inner rune", "outer rune", "little hand", "big hand"]
        for p in parts:
            img = pg.image.load(f"effekseer clock/{p}.png").convert_alpha()
            self.time_assets[p] = pg.transform.scale(img, (600, 600))
        self.tik_tok_sound = pg.mixer.Sound("effekseer clock/tik tok.wav")

        #메인화면
        self.bg_start_img = pg.image.load("hasomm.png").convert()
        self.bg_start_img = pg.transform.scale(self.bg_start_img, (c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        artifact_raw = pg.image.load("hanso.png").convert_alpha()
        self.artifact_img = pg.transform.scale(artifact_raw, (140, 90))

        # 버튼 이미지 로드 및 적절한 크기로 조절
        self.btn_start_img = pg.image.load("btn.png").convert_alpha()
        self.btn_start_img = pg.transform.scale(self.btn_start_img, (250, 80))  # 가로 250, 세로 80
        self.btn_start_rect = self.btn_start_img.get_rect(center=(c.SCREEN_WIDTH // 2, 500))
        #버튼 이미지 동기화
        self.btn_start_img_base = pg.image.load("btn.png").convert_alpha()
        self.btn_start_img_base = pg.transform.scale(self.btn_start_img_base, (250, 80))
        self.btn_start_img_hover = pg.transform.scale(self.btn_start_img_base, (275, 88))
        self.btn_start_img = self.btn_start_img_base
        self.btn_start_rect = self.btn_start_img.get_rect(center=(c.SCREEN_WIDTH // 2, 500))
        #버튼 UI
        self.COLOR_BG_DARK = (15, 15, 25)  # 짙은 배경색
        self.COLOR_PANEL = (30, 30, 50)
        self.COLOR_TEXT_BASE = (220, 220, 220)  # 기본 글씨 색
        self.COLOR_HIGHLIGHT = (255, 220, 0)  # 강조색 (노랑)

        self.font_ui_title = pg.font.SysFont("malgungothic", 60, bold=True)
        self.font_ui_subtitle = pg.font.SysFont("malgungothic", 35, bold=True)
        self.font_ui_base = pg.font.SysFont("malgungothic", 20)
        self.font_ui_cost = pg.font.SysFont("malgungothic", 18, bold=True)

        # 편성 화면 전용 레이아웃 rect
        self.deck_list_rect = pg.Rect(50, 150, 420, 520)  # 좌측 목록 영역
        self.deck_my_rect = pg.Rect(530, 150, 440, 300)  # 우측 내 덱 영역

        self.btn_ready_rect = pg.Rect(c.SCREEN_WIDTH // 2 - 120, 700, 240, 60)


        # 2. 게임 상태
        self.state = 'START'
        self.minigame = None

        self.i_am_ready = False  # 나의 레디 상태
        self.opponent_is_ready = False  # 상대방의 레디 상태
        self.loading_dots = 0
        self.loading_timer = 0.0

        self.role = None  # 시작 시 역할 배정

        self.hero_deck = []  # 내가 짠 영웅 덱
        self.enemy_deck = []  # 내가 짠 몬스터 덱
        self.my_deck = []  # 역할 배정 후 확정될 내 진짜 덱
        self.opponent_deck = []
        self.opponent_hero_deck = []
        self.opponent_enemy_deck = []

        self.editing_mode = "HERO"
        self.hero_units = ["Wizard", "Knight", "Archer", "Priest"]
        self.enemy_units = ["Orc", "Slime", "OrcRider", "ArmoredOrc", "Skeleton", "SkeletonArcher",
                            "GreatswordSkeleton", "Zeppelin", "Ship", "BlueAngel", "RedAngel"]

        self.max_hero_deck = 4
        self.max_enemy_deck = 8
        self.available_units = self.hero_units + self.enemy_units  # 에러 방지용 임시 합침
        self.max_deck_size = 8

        self.selected_hero_to_place = None
        self.selected_placed_hero = None  # 맵에 배치된 영웅 중 마우스로 클릭(선택)한 영웅
        self.upgrade_btn_rect = pg.Rect(20, c.SCREEN_HEIGHT - 80, 150, 50)
        self.placement_nodes = [pg.Rect(x, y, w, h) for x, y, w, h in c.HERO_PLACEMENT_NODES]

        # 3. 객체 그룹
        self.heroes = pg.sprite.Group()
        self.enemies = pg.sprite.Group()
        self.bullets = pg.sprite.Group()
        self.effects = pg.sprite.Group()
        self.speed_zones = pg.sprite.Group()

        self.gold = c.INITIAL_GOLD
        if self.role == "DEFENDER":
            self.gold += 20 #수비자에게 추가 20골드
        self.running = True

        self.game_timer = 300.0  # 5분 (300초)
        self.artifact_max_hp = 500  # 타워(유물) 최대 체력
        self.artifact_hp = self.artifact_max_hp
        self.game_over = False
        self.winner = None

        self.gold_timer = 0.0

        self.network_timer = 0.0
        self.network_interval = 0.03

        self.auto_spawn_timer = 0.0
        self.auto_spawn_interval = 4.0
        self.current_bgm = None
        pg.mixer.music.set_volume(0.5)
        #몬스터 소환 타이머
        self.auto_spawn_timers = [0.0, 0.0, 0.0]
        self.auto_spawn_intervals = [3.5, 8.0, 4.0]
        #선택한 경로
        self.selected_path_pp = 0

        self.game_snapshots = []  # 과거 상태를 기록할 리스트
        self.snapshot_timer = 0.0  # 기록 주기 타이머
        self.last_reverse_time = -30000
        #적 덱 저장
        self.opponent_deck = []
        #카운트다운 변수
        self.intro_timer = 0.0
        self.font_large = pg.font.SysFont("malgun gothic", 100, bold=True)
        self.font_medium = pg.font.SysFont("malgun gothic", 50, bold=True)
        #미션 변수
        self.mission_schedule = [240, 210, 180, 150, 120, 90]
        self.active_mission = False
        self.current_mission_type = None
        self.my_mission_progress = 0
        self.opp_mission_progress = 0
        self.mission_max_me = 0
        self.mission_max_opp = 0
        self.mission_desc = ""

        self.available_elements = ["목", "화", "토", "금", "수"]
        self.my_coins = []  # 내가 획득한 오행 동전
        self.active_synergies = []  # 현재 발동 중인 시너지 이름 목록

        # 상생 버프 플래그 및 타이머
        self.buff_dmg_up = False  # 목생화 (딜 증가)
        self.buff_gold_up = False  # 토생금 (골드 증가)
        self.synergy_timer_15s = 0.0  # 수생목 (15초 힐)
        self.synergy_timer_30s = 0.0  # 화생토 (30초 즉사/폭발)

        self.deck_scroll_y = 0

        self.map_surface = pg.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        self.map_surface.fill(c.GRAY)  # 맵 로드 실패 시 기존 회색으로 대체
        self.load_tmx_map("untitled.tmx")

        self.selected_target_hero = None  # 공격자 화면에서 누른 영웅
        self.targeted_by_attacker_pos = None

        self.synergy_display_timer = 0.0
        self.synergy_display_elements = []
        self.synergy_display_name = ""
        self.synergy_display_desc = ""
        self.free_snipe_count = 0

        # 각 속성별 번개 색상 지정 (목=초록, 화=빨강, 토=노랑, 금=황금, 수=파랑)
        self.element_colors = {
            "목": (50, 255, 50),
            "화": (255, 50, 50),
            "토": (200, 150, 50),
            "금": (255, 255, 0),
            "수": (50, 150, 255)
        }

    def load_tmx_map(self, filename):
        try:
            tmx_data = load_pygame(filename)
            map_w = tmx_data.width * tmx_data.tilewidth
            map_h = tmx_data.height * tmx_data.tileheight
            temp_surface = pg.Surface((map_w, map_h))

            for layer in tmx_data.visible_layers:
                if hasattr(layer, 'data'):
                    for x, y, surf in layer.tiles():
                        temp_surface.blit(surf, (x * tmx_data.tilewidth, y * tmx_data.tileheight))

            self.map_surface = pg.transform.scale(temp_surface, (c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        except Exception as e:
            print(f" 맵 로드 실패 (파일 경로와 tsx, png 파일을 확인하세요): {e}")



    # [함수 1] 사용자 입력 처리
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

            if event.type == pg.MOUSEWHEEL:
                if self.state == 'EDIT_DECK':
                    self.deck_scroll_y += event.y * 30

                    max_scroll = 0
                    min_scroll = -max(0, (len(self.available_units) * 60) - 450)
                    self.deck_scroll_y = max(min_scroll, min(max_scroll, self.deck_scroll_y))

            if event.type == pg.KEYDOWN:
                #임시 테스트용(제거)
                if event.key == pg.K_t:
                    self.get_random_coin()
                #경로 선택
                if event.key == pg.K_1:
                    self.selected_path_pp = 0
                elif event.key == pg.K_2:
                    self.selected_path_pp = 1
                elif event.key == pg.K_3:
                    self.selected_path_pp = 2


                if self.state == 'MINIGAME' and self.minigame:
                    action_data = self.minigame.handle_input(event.key)
                    if action_data:
                        self.net.send(action_data)

            if event.type == pg.MOUSEBUTTONDOWN:
                mx, my = pg.mouse.get_pos()
                #print(f"마우스 클릭 좌표: X={mx}, Y={my}")#삭제할거

                if self.state == 'BATTLE' and self.game_over:
                    self.reset_game()
                    continue

                if self.state == 'START':
                    if self.btn_start_img:
                        if self.btn_start_rect.collidepoint(mx, my):
                            self.state = 'LOBBY'
                    else:
                        self.state = 'LOBBY'


                elif self.state == 'LOBBY':
                    cx, cy = c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2
                    start_btn = pg.Rect(cx - 100, cy - 100, 200, 80)
                    enemy_btn = pg.Rect(cx - 250, cy + 50, 200, 80)
                    hero_btn = pg.Rect(cx + 50, cy + 50, 200, 80)
                    if start_btn.collidepoint(mx, my):
                        # 두 덱을 모두 최소 1명 이상 짜야만 레디 가능!
                        if len(self.hero_deck) > 0 and len(self.enemy_deck) > 0:
                            self.i_am_ready = True

                            self.net.send(
                                {"action": "ready", "hero_deck": self.hero_deck, "enemy_deck": self.enemy_deck})
                            self.state = 'WAITING'
                            self.check_role_assignment()  # 역할 뽑기 시도


                    elif enemy_btn.collidepoint(mx, my):
                        self.editing_mode = "ENEMY"  # 적 편성 탭으로 진입
                        self.state = 'EDIT_DECK'
                    elif hero_btn.collidepoint(mx, my):
                        self.editing_mode = "HERO"  # 영웅 편성 탭으로 진입
                        self.state = 'EDIT_DECK'


                elif self.state == 'EDIT_DECK':
                    current_available = self.hero_units if self.editing_mode == "HERO" else self.enemy_units
                    current_deck = self.hero_deck if self.editing_mode == "HERO" else self.enemy_deck
                    max_size = self.max_hero_deck if self.editing_mode == "HERO" else self.max_enemy_deck
                    # 1. 우측 그리드 (전체 목록) 클릭 감지
                    grid_start_x, grid_start_y = 450, 150
                    icon_size = 90
                    spacing = 15
                    cols = 5

                    for i, unit in enumerate(current_available):
                        col, row = i % cols, i // cols
                        slot_rect = pg.Rect(grid_start_x + col * (icon_size + spacing),
                                            grid_start_y + row * (icon_size + spacing),
                                            icon_size, icon_size)

                        if slot_rect.collidepoint(mx, my):
                            if len(current_deck) < max_size and unit not in current_deck:
                                current_deck.append(unit)
                            break

                    # 2. 하단 내 덱 슬롯 클릭 감지 (편성취소)
                    deck_start_x, deck_start_y = 50, 600
                    for i, unit in enumerate(current_deck):
                        slot_rect = pg.Rect(deck_start_x + i * 100, deck_start_y, 80, 80)
                        if slot_rect.collidepoint(mx, my):
                            current_deck.pop(i)
                            break

                    back_btn = pg.Rect(c.SCREEN_WIDTH - 250, 600, 200, 80)
                    if back_btn.collidepoint(mx, my):
                        self.state = 'LOBBY'

                elif self.state == 'BATTLE':
                    self.handle_battle_click(mx, my)

    # [함수 2] 전투 중 클릭 처리
    def handle_battle_click(self, mx, my):
        ui_x = 800
        # 1. 우측 UI (덱 버튼) 영역을 클릭했을 때
        if mx > ui_x:
            for i, unit_name in enumerate(self.my_deck):
                col, row = i % 2, i // 2
                rect = pg.Rect(ui_x + 20 + (col * 90), 150 + (row * 90), 80, 80)

                if rect.collidepoint(mx, my):
                    # 클릭한 유닛의 비용 확인 (없으면 기본값 적용)
                    cost = c.UNIT_COSTS.get(unit_name, 30 if self.role == "ATTACKER" else 70)

                    if self.role == "ATTACKER":
                        if self.gold >= cost:
                            path_idx = self.selected_path_pp

                            self.net.send({"action": "spawn", "type": unit_name, "path_idx": path_idx})
                            self.spawn_enemy_local(unit_name, path_idx)
                            self.gold -= cost
                            self.add_mission_progress('SPEND_GOLD', cost)
                            self.add_mission_progress('SPAWN_BUILD', 1)

                    elif self.role == "DEFENDER":
                        # 방어자는 버튼 클릭 시 '장전'만 함
                        self.selected_hero_to_place = unit_name

        # 2. 좌측 맵 영역을 클릭했을 때
        else:
            if self.role == "ATTACKER":
                if getattr(self, 'selected_target_hero', None):
                    snipe_btn_rect = pg.Rect(20, c.SCREEN_HEIGHT - 60, 180, 40)
                    if snipe_btn_rect.collidepoint(mx, my):
                        free_count = getattr(self, 'free_snipe_count', 0)

                        if free_count > 0:
                            self.free_snipe_count -= 1  # 무료로 저격 통과!
                        elif self.gold >= 200:
                            self.gold -= 200
                            self.add_mission_progress('SPEND_GOLD', 200)
                        else:
                            return
                        clicked_hero = self.selected_target_hero
                        self.state = 'MINIGAME'
                        self.minigame = RhythmMiniGame(clicked_hero, self.role)
                        notes_keys = [n['key'] for n in self.minigame.notes]
                        self.net.send(
                            {"action": "start_snipe", "x": clicked_hero.rect.centerx, "y": clicked_hero.rect.centery,
                             "notes": notes_keys})

                        self.selected_target_hero = None
                        self.net.send({"action": "target_hero", "x": -1, "y": -1})
                        return  # 버튼을 눌렀다면 여기서 함수 종료

                clicked_hero = None
                for hero in self.heroes:
                    hitbox = pg.Rect(0, 0, 60, 70)
                    hitbox.center = hero.rect.center
                    if hitbox.collidepoint(mx, my):
                        clicked_hero = hero
                        break

                if clicked_hero:
                    self.selected_target_hero = clicked_hero
                    self.net.send(
                        {"action": "target_hero", "x": clicked_hero.rect.centerx, "y": clicked_hero.rect.centery})
                else:
                    # 빈 땅을 클릭하면 선택 취소
                    self.selected_target_hero = None
                    self.net.send({"action": "target_hero", "x": -1, "y": -1})

            elif self.role == "DEFENDER":
                #좌측 강화 확인
                if self.selected_placed_hero and hasattr(self.selected_placed_hero, 'level'):
                    if self.selected_placed_hero.level < self.selected_placed_hero.max_level:
                        if self.upgrade_btn_rect.collidepoint(mx, my):
                            current_lv = self.selected_placed_hero.level
                            hero_class_name = type(self.selected_placed_hero).__name__
                            upgrade_cost = 99999
                            if hero_class_name == "Knight":
                                upgrade_cost = c.KNIGHT_UPGRADE_COST.get(current_lv, 99999)
                            elif hero_class_name == "Archer":
                                upgrade_cost = getattr(c, 'ARCHER_UPGRADE_COST', c.KNIGHT_UPGRADE_COST).get(current_lv,150)
                            elif hero_class_name == "Priest":
                                upgrade_cost = c.PRIEST_UPGRADE_COST.get(current_lv, 99999)

                            if self.gold >= upgrade_cost:
                                self.gold -= upgrade_cost
                                self.add_mission_progress('SPEND_GOLD', upgrade_cost)
                                self.add_mission_progress('SPAWN_BUILD', 1)
                                self.selected_placed_hero.upgrade()
                                self.net.send({
                                    "action": "upgrade_hero",
                                    "x": self.selected_placed_hero.rect.centerx,
                                    "y": self.selected_placed_hero.rect.centery
                                })
                            else:
                                print(f"골드가 부족합니다! (필요: {upgrade_cost}G)")
                            return

                if self.selected_placed_hero and type(self.selected_placed_hero).__name__ == "Priest":
                    type_btn_rect = pg.Rect(self.selected_placed_hero.rect.centerx - 40,
                                            self.selected_placed_hero.rect.top - 70, 80, 25)
                    if type_btn_rect.collidepoint(mx, my):
                        self.selected_placed_hero.toggle_mode()
                        self.net.send({
                            "action": "set_priest_mode",
                            "x": self.selected_placed_hero.rect.centerx,
                            "y": self.selected_placed_hero.rect.centery,
                            "mode": self.selected_placed_hero.mode
                        })
                        return

                #강화 버튼이 아니라면, 맵에 배치된 영웅을 클릭했는지 확인합니다.
                clicked_hero = None
                for hero in self.heroes:
                    hitbox = pg.Rect(0, 0, 60, 70)
                    hitbox.center = hero.rect.center

                    if hitbox.collidepoint(mx, my):  # 이제 hitbox 안을 눌렀을 때만 작동!
                        clicked_hero = hero
                        break

                if clicked_hero:
                    # 영웅을 클릭했다면 '선택 상태'로 만들고 종료 (하단에 UI가 뜨게 됨)
                    self.selected_placed_hero = clicked_hero
                    return
                else:
                    # 영웅이 아닌 빈 땅을 클릭했다면 영웅 선택창 닫기(해제)
                    self.selected_placed_hero = None

                # 빈 땅을 클릭했고, 소환할 영웅을 장전했다면 지정 구역에만 생성
                if self.selected_hero_to_place:

                    # 1) 클릭한 마우스 좌표가 설치 구역(노드) 안인지 확인
                    target_node = None
                    for node in self.placement_nodes:
                        if node.collidepoint(mx, my):
                            target_node = node
                            break

                    if target_node:
                        #  (겹침 방지)
                        is_occupied = any(target_node.collidepoint(hero.rect.center) for hero in self.heroes)

                        if not is_occupied:
                            cost = c.UNIT_COSTS.get(self.selected_hero_to_place, 70)

                            if self.gold >= cost:
                                self.gold -= cost
                                combined_images = {**self.images['heroes'], **self.images['battle']}
                                spawn_x = target_node.centerx
                                spawn_y = target_node.centery

                                new_hero = None
                                if self.selected_hero_to_place == "Wizard":
                                    new_hero = Wizard(spawn_x, spawn_y, combined_images, self.screen)
                                elif self.selected_hero_to_place == "Knight":
                                    new_hero = Knight(spawn_x, spawn_y, combined_images, self.screen)
                                elif self.selected_hero_to_place == "Archer":
                                    new_hero = Archer(spawn_x, spawn_y, combined_images, self.images['battle']['arrows'],
                                                           self.screen)
                                elif self.selected_hero_to_place == "Priest":
                                    new_hero = Priest(spawn_x, spawn_y, combined_images, self.screen)

                                if new_hero:
                                    self.heroes.add(new_hero)
                                    self.net.send(
                                        {"action": "place_hero", "type": self.selected_hero_to_place, "x": spawn_x,
                                         "y": spawn_y})
                                    self.selected_hero_to_place = None  # 소환 후 장전 해제

                                    self.add_mission_progress('SPEND_GOLD', cost)
                                    self.add_mission_progress('SPAWN_BUILD', 1)
                            else:
                                self.selected_hero_to_place = None  # 돈 부족 시 장전 취소
                        else:
                            print("---배치 불가---")
                    else:
                        self.selected_hero_to_place = None  # 엉뚱한 곳 누르면 장전 취소

    # [함수 3] 로직 업데이트
    def update(self):
        dt = self.clock.tick(c.FPS) / 1000.0

        # 서버 통신은 게임 상태와 무관하게 '항상' 맨 먼저 실행합니다!
        reply = self.net.send({"action": None})
        if reply and "messages" in reply:
            for msg in reply["messages"]:
                self.process_network_message(msg)

        # 대기방 로직 (점 깜빡임 & 전투 시작 넘어가기)
        if self.state == 'WAITING':
            self.loading_timer += dt
            if self.loading_timer >= 0.5:
                self.loading_dots = (self.loading_dots + 1) % 4
                self.loading_timer = 0.0

        elif self.state == 'MINIGAME':
            if self.minigame:
                # 서버 통신 함수(self.net.send)를 미니게임에 전달해줍니다.
                self.minigame.update(dt, self.net.send)
                if not self.minigame.active:
                    self.state = 'BATTLE'
                    self.minigame = None

        if self.state == 'BATTLE' and self.intro_timer > 0:
            self.intro_timer -= dt
            return


        elif self.state == 'BATTLE' and not self.game_over:

            # 1. 게임 타이머 감소

            self.game_timer -= dt

            if getattr(self, 'coin_display_timer', 0) > 0:
                self.coin_display_timer -= dt
            if getattr(self, 'synergy_display_timer', 0) > 0:
                self.synergy_display_timer -= dt

            # 2. 과거 스냅샷 기록 (시간 역행용)
            self.snapshot_timer += dt
            if self.snapshot_timer >= 1.0:
                self.snapshot_timer -= 1.0
                heroes_data = []
                for h in self.heroes:
                    heroes_data.append({
                        'name': type(h).__name__,
                        'x': h.rect.centerx,
                        'y': h.rect.centery,
                        'level': getattr(h, 'level', 1),
                        'hp': getattr(h, 'hp', getattr(h, 'max_hp', 100))

                    })

                current_snapshot = {
                    'time': pg.time.get_ticks(),
                    'gold': self.gold,
                    'artifact_hp': self.artifact_hp,
                    'heroes': heroes_data
                }
                self.game_snapshots.append(current_snapshot)

                if len(self.game_snapshots) > 30:
                    self.game_snapshots.pop(0)

            # 3. 골드 자연 회복 (토생금 버프 적용!)

            self.gold_timer += dt
            if self.gold_timer >= 1.0:
                if self.role == "ATTACKER":
                    extra_gold = 5 if self.buff_gold_up else 0  # 토생금 발동 시 초당 2골드 추가
                    current_gain = 10

                    if self.game_timer <= 30:  # 최종 30초 남았을 때 (150초 지남)
                        current_gain = 40
                    elif self.game_timer <= 60:  # 최종 30초 남았을 때 (150초 지남)
                        current_gain = 30
                    elif self.game_timer <= 90:  # 60초 남았을 때 (120초 지남)
                        current_gain = 25
                    elif self.game_timer <= 150:  # 90초 남았을 때 (90초 지남)
                        current_gain = 20
                    elif self.game_timer <= 210:  # 120초 남았을 때 (60초 지남)
                        current_gain = 15
                    elif self.game_timer <= 240:  # 150초 남았을 때 (30초 지남)
                        current_gain = 12

                    self.gold += (current_gain + extra_gold)

                self.gold_timer -= 1.0

            # 4. 미션 발생 타이머 로직
            if hasattr(self, 'mission_schedule') and self.mission_schedule:
                if self.game_timer <= self.mission_schedule[0]:
                    self.mission_schedule.pop(0)
                    self.active_mission = True
                    self.my_mission_progress = 0
                    self.opp_mission_progress = 0

                    m_index = len(self.mission_schedule) % 3
                    types = ['SPAWN_BUILD', 'KILL', 'SPEND_GOLD']
                    self.current_mission_type = types[m_index]

                    if self.current_mission_type == 'SPAWN_BUILD':
                        self.mission_desc = "[미션] 적 8기 소환 VS 영웅 3회 배치/강화"
                        self.mission_max_me = 8 if self.role == "ATTACKER" else 3
                        self.mission_max_opp = 3 if self.role == "ATTACKER" else 8
                    elif self.current_mission_type == 'KILL':
                        self.mission_desc = "[미션] 영웅 1기 처치 VS 적 20기 처치"
                        self.mission_max_me = 1 if self.role == "ATTACKER" else 20
                        self.mission_max_opp = 20 if self.role == "ATTACKER" else 1
                    elif self.current_mission_type == 'SPEND_GOLD':
                        self.mission_desc = "[미션] 150골드 먼저 소모하기 대결!"
                        self.mission_max_me = 150
                        self.mission_max_opp = 150


            # 5. 오행 상생 쿨타임 스킬 (15초, 30초)
            if "수생목" in self.active_synergies:
                self.synergy_timer_15s += dt
                if self.synergy_timer_15s >= 15.0:
                    self.synergy_timer_15s = 0.0
                    if self.role == "DEFENDER":
                        for h in self.heroes:
                            if hasattr(h, 'hp'): h.hp = min(h.hp + 75, getattr(h, 'max_hp', 100))

                    else:  # ATTACKER
                        for e in self.enemies: e.hp = min(e.hp + 100, e.max_hp)
                    print(" [수생목] 15초 주기 회복 발동!")
            if "화생토" in self.active_synergies:
                self.synergy_timer_30s += dt
                if self.synergy_timer_30s >= 30.0:
                    self.synergy_timer_30s = 0.0
                    if self.role == "DEFENDER":
                        alive_enemies = [e for e in self.enemies if e.hp > 0 and e.state != 'dying']
                        if alive_enemies:
                            kill_count = max(1, len(alive_enemies) // 3)

                            targets = random.sample(alive_enemies, kill_count)

                            target_coords = []
                            for target in targets:
                                tx, ty = target.rect.centerx, target.rect.centery
                                target.take_damage(9999)  # 즉사!
                                target_coords.append((tx, ty))  # 동기화를 위해 좌표 저장

                                # 즉사 이펙트 띄우기
                                self.effects.add(InstaKillEffect(tx, ty, self.images['instakill']))

                            self.net.send({"action": "sync_kill_enemy_list", "targets": target_coords})


                    else:
                        alive_heroes = [h for h in self.heroes if getattr(h, 'hp', 0) > 0]
                        if alive_heroes:
                            target = random.choice(alive_heroes)
                            tx, ty = target.rect.centerx, target.rect.centery
                            target.kill()

                            self.effects.add(InstaKillEffect(tx, ty, self.images['instakill']))
                            self.net.send({"action": "sync_kill_hero", "x": tx, "y": ty})

            if self.role == "ATTACKER":
                for i in range(3):
                    self.auto_spawn_timers[i] += dt
                    if self.auto_spawn_timers[i] >= self.auto_spawn_intervals[i]:
                        self.auto_spawn_timers[i] -= self.auto_spawn_intervals[i]

                        auto_unit = random.choice(["Orc", "Slime"])
                        self.net.send({"action": "spawn", "type": auto_unit, "path_idx": i})
                        self.spawn_enemy_local(auto_unit, i)

            for enemy in list(self.enemies):
                #폭발 먼저
                if getattr(enemy, 'trigger_explosion', None):
                    radius, dmg = enemy.trigger_explosion
                    enemy.trigger_explosion = None
                    for h in self.heroes:
                        dist = pg.math.Vector2(enemy.rect.center).distance_to(pg.math.Vector2(h.rect.center))
                        if dist <= radius:
                            h.take_damage(dmg)
                    self.effects.add(OrangeExplosion(enemy.rect.centerx, enemy.rect.centery, radius))


                if getattr(enemy, 'spawn_tombstone', False):
                    enemy.spawn_tombstone = False

                    # 끝에 self.images['enemies'] 도 안전하게 추가되었습니다.
                    tomb = SkeletonTombstone(enemy.rect.centerx, enemy.rect.centery, enemy.waypoints,
                                             type(enemy).__name__, enemy.reward, enemy.target_waypoint_idx,
                                             self.images['enemies'])
                    self.apply_time_multiplier(tomb)
                    self.enemies.add(tomb)
                    enemy.kill()
                    continue
                if enemy.hp <= 0 and not enemy.reward_given:
                    if self.role == "DEFENDER":
                        self.gold += enemy.reward
                        self.add_mission_progress('KILL', 1)

                    enemy.reward_given = True

                    # 특수 능력 슬라임
                    if type(enemy).__name__ == "Slime":
                        baby1 = SlimeBaby(enemy.rect.centerx - 15, enemy.rect.centery, enemy.waypoints,
                                          self.images['enemies'], enemy.target_waypoint_idx)
                        baby2 = SlimeBaby(enemy.rect.centerx + 15, enemy.rect.centery, enemy.waypoints,
                                          self.images['enemies'], enemy.target_waypoint_idx)
                        self.apply_time_multiplier(baby1)
                        self.apply_time_multiplier(baby2)
                        self.enemies.add(baby1, baby2)

                    if type(enemy).__name__ == "Skeleton":
                        current_time = pg.time.get_ticks()

                        last_time = getattr(self, 'last_reverse_time', -30000)

                        # 마지막 발동 이후 30초(30000ms)가 지났는지 쿨타임 검사
                        if current_time - last_time >= 30000:
                            self.last_reverse_time = current_time  # 쿨타임 초기화

                            target_time = current_time - 15000

                            if hasattr(self, 'game_snapshots') and self.game_snapshots:
                                best_snapshot = self.game_snapshots[0]
                                for snap in self.game_snapshots:
                                    if snap['time'] >= target_time:
                                        best_snapshot = snap
                                        break

                                if best_snapshot:
                                    # --- 1. 시계 이펙트 재생 ---
                                    if hasattr(self, 'time_assets') and self.time_assets:
                                        try:
                                            self.tik_tok_sound.play()
                                        except:
                                            pass

                                        angle_inner, angle_outer, angle_big, angle_little = 0, 0, 0, 0
                                        for _ in range(40):
                                            overlay = pg.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pg.SRCALPHA)
                                            overlay.fill((0, 0, 0, 180))
                                            self.screen.blit(overlay, (0, 0))

                                            center_pos = (c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2)

                                            frame_rect = self.time_assets["clock frame"].get_rect(center=center_pos)
                                            self.screen.blit(self.time_assets["clock frame"], frame_rect)

                                            angle_outer -= 1
                                            outer_rot = pg.transform.rotate(self.time_assets["outer rune"], angle_outer)
                                            self.screen.blit(outer_rot, outer_rot.get_rect(center=center_pos))

                                            angle_inner += 2
                                            inner_rot = pg.transform.rotate(self.time_assets["inner rune"], angle_inner)
                                            self.screen.blit(inner_rot, inner_rot.get_rect(center=center_pos))

                                            angle_little += 3
                                            angle_big += 12
                                            little_rot = pg.transform.rotate(self.time_assets["little hand"],
                                                                             angle_little)
                                            self.screen.blit(little_rot, little_rot.get_rect(center=center_pos))

                                            big_rot = pg.transform.rotate(self.time_assets["big hand"], angle_big)
                                            self.screen.blit(big_rot, big_rot.get_rect(center=center_pos))

                                            pg.display.update()
                                            self.clock.tick(60)
                                    else:

                                        self.screen.fill((0, 200, 255))
                                        pg.display.update()
                                        pg.time.delay(500)
                                    #골드 초기화 및 체력 초기화
                                    #self.gold = best_snapshot['gold']
                                    #self.artifact_hp = best_snapshot['artifact_hp']

                                    # 영웅 초기화
                                    self.heroes.empty()
                                    combined_images = {**self.images['heroes'], **self.images['battle']}

                                    for h_data in best_snapshot['heroes']:
                                        name = h_data['name']
                                        hx, hy = h_data['x'], h_data['y']

                                        new_hero = None
                                        if name == "Knight":
                                            new_hero = Knight(hx, hy, combined_images, self.screen)

                                        elif name == "Wizard":
                                            new_hero = Wizard(hx, hy, combined_images, self.screen)

                                        elif name == "Archer":
                                            new_hero = Archer(hx, hy, combined_images, self.images['battle']['arrows'],
                                                              self.screen)

                                        elif name == "Priest":
                                            new_hero = Priest(hx, hy, combined_images, self.screen)

                                        if new_hero:
                                            # 레벨 시스템 있는 영웅만
                                            if hasattr(new_hero, 'level'):
                                                new_hero.level = h_data['level']
                                                if hasattr(new_hero, 'setup_stats'):
                                                    new_hero.setup_stats()

                                            if hasattr(new_hero, 'hp'):
                                                new_hero.hp = h_data['hp']
                                            self.heroes.add(new_hero)

                                    # self.enemies.empty()
                                    self.net.send({"action": "time_reversal", "snapshot_time": best_snapshot['time']})
                    enemy.kill()

            #스피드존 판정 특수 적
            self.speed_zones.update(dt)
            for enemy in self.enemies:
                # 1. 기본 속도 정의
                if not hasattr(enemy, 'base_speed'):
                    enemy.base_speed = enemy.speed
                # 2. 장판 체크
                in_zone = any(enemy.rect.colliderect(z.rect) for z in self.speed_zones)
                target_speed = enemy.base_speed * (1.5 if in_zone else 1.0)
                # 3. 감속 효과
                if hasattr(enemy, 'slow_timer') and enemy.slow_timer > 0:
                    target_speed *= 0.6
                enemy.speed = target_speed
            for enemy in self.enemies:
                backup_bw = {}
                if self.role == "DEFENDER":
                    for hero in self.heroes:
                        backup_bw[hero] = (getattr(hero, 'is_brainwashed', False),
                                           getattr(hero, 'brainwash_timer', 0.0))

                if type(enemy).__name__ in ["Zeppelin", "Ship", "RedAngel", "BlueAngel"]:
                    enemy.update(dt, self.heroes, self.bullets)
                else:
                    enemy.update(dt)

                if getattr(enemy, 'revive_triggered', False):
                    enemy.revive_triggered = False
                    new_skel = None
                    if enemy.original_type == "SkeletonArcher":
                        new_skel = SkeletonArcher(enemy.rect.centerx, enemy.rect.centery, enemy.waypoints,
                                                  self.images['enemies'])
                    elif enemy.original_type == "GreatswordSkeleton":
                        new_skel = GreatswordSkeleton(enemy.rect.centerx, enemy.rect.centery, enemy.waypoints,
                                                      self.images['enemies'])

                    if new_skel:
                        new_skel.revived = True
                        new_skel.reward_given = False
                        new_skel.target_waypoint_idx = enemy.target_waypoint_idx
                        self.apply_time_multiplier(new_skel)
                        self.enemies.add(new_skel)

                if getattr(enemy, 'grant_free_snipe', False):
                    enemy.grant_free_snipe = False
                    self.effects.add(FloatingText(enemy.rect.centerx, enemy.rect.top - 10, "+1 저격", (180, 100, 255), 16))
                    if self.role == "ATTACKER":
                        current_free_snipe = getattr(self, 'free_snipe_count', 0)
                        if self.free_snipe_count < 3:
                            self.free_snipe_count += 1

                if getattr(enemy, 'network_send_brainwash', None):
                    target_x, target_y = enemy.network_send_brainwash

                    if self.role == "ATTACKER":
                        self.net.send({"action": "BRAINWASH", "x": target_x, "y": target_y})
                    else:
                        for hero in self.heroes:
                            if hero in backup_bw:
                                hero.is_brainwashed, hero.brainwash_timer = backup_bw[hero]

                    # 변수 초기화
                    enemy.network_send_brainwash = None

            for hero in self.heroes:
                if getattr(hero, 'is_brainwashed', False):
                    hero.brainwash_timer -= dt
                    if hero.brainwash_timer <= 0:
                        hero.is_brainwashed = False

                if getattr(hero, 'level_down_timer', 0.0) > 0:
                    hero.level_down_timer -= dt

            heroes_count_before = len(self.heroes)
            self.heroes.update(pg.time.get_ticks(), dt, self.enemies, self.effects, self.bullets)
            if self.role == "ATTACKER" and len(self.heroes) < heroes_count_before:
                self.add_mission_progress('KILL', heroes_count_before - len(self.heroes))
            self.bullets.update(dt)
            self.effects.update()

            # 4. 적이 목표 지점에 도달했는지 확인 및 체력 감소
            for enemy in self.enemies:
                if enemy.state == 'moving' and enemy.target_waypoint_idx >= len(enemy.waypoints):
                    self.artifact_hp -= 50
                    if self.role == "DEFENDER" and not enemy.reward_given:
                        self.gold += (enemy.reward * 0.5)  # 절반(50%)만 획득!
                        enemy.reward_given = True
                    enemy.kill() # 데미지를 입히고 사라짐

            # 5. 승패 조건 판정
            if not self.game_over:
                if self.artifact_hp <= 0:
                    self.game_over = True
                    self.winner = "ATTACKER"
                    self.net.send({"action": "game_over", "winner": self.winner})

                elif self.game_timer <= 0:
                    self.game_over = True
                    self.winner = "DEFENDER"
                    self.net.send({"action": "game_over", "winner": self.winner})

            if self.gold > 1000:
                self.gold = 1000

    def check_role_assignment(self):
        if self.i_am_ready and self.opponent_is_ready:
            if self.player_id == 1:  # 1P가 대표로 동전 던지기
                p1_role = random.choice(["ATTACKER", "DEFENDER"])
                self.net.send({"action": "role_assign", "p1_role": p1_role})
                self.apply_role(p1_role)

    def apply_role(self, p1_role):
        if self.player_id == 1:
            self.role = p1_role
        else:
            self.role = "ATTACKER" if p1_role == "DEFENDER" else "DEFENDER"

        if self.role == "DEFENDER":
            self.my_deck = self.hero_deck
            self.opponent_deck = self.opponent_enemy_deck
        else:
            self.my_deck = self.enemy_deck
            self.opponent_deck = self.opponent_hero_deck

        self.state = 'BATTLE'
        self.intro_timer = 3.0


    # [함수 4] 네트워크 메시지 처리
    def process_network_message(self, msg):
        if not isinstance(msg, dict):
            return

        # 1. 상대방의 [레디] 신호를 받았을 때
        if msg.get("action") == "ready":
            self.opponent_is_ready = True
            self.opponent_hero_deck = msg.get("hero_deck", [])
            self.opponent_enemy_deck = msg.get("enemy_deck", [])
            self.check_role_assignment()

        # 2. 역할 배정 결과를 받았을 때
        elif msg.get("action") == "role_assign":
            self.apply_role(msg.get("p1_role"))

        # 2. 공격자의 [소환] 신호를 수비자가 받았을 때
        elif msg.get("action") == "spawn":
            unit_type = msg.get("type", "Orc")
            path_idx = msg.get("path_idx", 0)
            self.spawn_enemy_local(unit_type, path_idx)

        # 3. 수비자의 [영웅 배치] 신호를 공격자가 받았을 때
        elif msg.get("action") == "place_hero":
            unit_type = msg.get("type")
            sx, sy = msg.get("x"), msg.get("y")

            combined_images = {**self.images['heroes'], **self.images['battle']}
            new_hero = None
            if unit_type == "Wizard":
                new_hero = Wizard(sx, sy, combined_images, self.screen)
            elif unit_type == "Knight":
                new_hero = Knight(sx, sy, combined_images, self.screen)
            elif unit_type == "Archer":
                new_hero = Archer(sx, sy, combined_images, self.images['battle']['arrows'], self.screen)
            elif unit_type == "Priest":
                new_hero = Priest(sx, sy, combined_images, self.screen)

            if new_hero:
                self.heroes.add(new_hero)

        # 4. 수비자의 영웅 강화 신호를 공격자가 받았을 때
        elif msg.get("action") == "upgrade_hero":
            hx, hy = msg.get("x"), msg.get("y")
            for hero in self.heroes:
                if abs(hero.rect.centerx - hx) < 15 and abs(hero.rect.centery - hy) < 15:
                    hero.upgrade()
                    break

        elif msg.get("action") == "set_priest_mode":
            hx = msg.get("x")
            hy = msg.get("y")
            target_mode = msg.get("mode")

            for hero in self.heroes:
                if type(hero).__name__ == "Priest":
                    if abs(hero.rect.centerx - hx) < 10 and abs(hero.rect.centery - hy) < 10:
                        hero.mode = target_mode
                        hero.images = hero.images_attack if target_mode == 'attack' else hero.images_heal
                        hero.attack_count = 0
                        hero.state = 'idle'
                        hero.attack_range = 250 if target_mode == "attack" else 99999

                        if hero.images:
                            hero.image = hero.images[0]
                        break

        # 5. 미니게임 통신
        elif msg.get("action") == "start_snipe":
            tx, ty = msg.get("x"), msg.get("y")
            target = None
            for hero in self.heroes:
                if abs(hero.rect.centerx - tx) < 15 and abs(hero.rect.centery - ty) < 15:
                    target = hero
                    break
            if target:
                self.state = 'MINIGAME'
                self.minigame = RhythmMiniGame(target, self.role, msg.get("notes"))

        elif msg.get("action") == "fire_arrow":
            stacks = msg.get("stacks", 0)
            if self.state == 'MINIGAME' and self.minigame:
                self.minigame.start_attack_phase(stacks)

        elif msg.get("action") == "rhythm_hit":
            if self.state == 'MINIGAME' and self.minigame:
                idx = msg.get("idx")
                status = msg.get("status")
                if idx < len(self.minigame.notes):
                    if status == "hit":
                        self.minigame.notes[idx]['hit'] = True
                        self.minigame.success_count += 1
                    else:
                        self.minigame.notes[idx]['missed'] = True
                    self.minigame.current_note_idx += 1

        elif msg.get("action") == "deploy_shield":
            if self.state == 'MINIGAME' and self.minigame:
                self.minigame.shield_key = msg.get("key")
                self.minigame.shield_timer = 0.5
        #미션 통신
        elif msg.get("action") == "mission_update":
            self.opp_mission_progress = msg.get("progress", 0)
            self.check_mission_win()

        elif msg.get("action") == "mission_end":
            self.active_mission = False
            self.mission_timer = 30.0  # 미션 종료 후 다시 30초 대기

        elif msg.get("action") == "sync_kill_hero":
            hx, hy = msg.get("x"), msg.get("y")

            for h in self.heroes:
                if abs(h.rect.centerx - hx) < 15 and abs(h.rect.centery - hy) < 15:
                    h.kill()
                    self.effects.add(InstaKillEffect(hx, hy, self.images['instakill']))
                    break


        elif msg.get("action") == "sync_kill_enemy":
            ex, ey = msg.get("x"), msg.get("y")
            closest_enemy = None
            min_dist = 999999
            for e in self.enemies:
                dist = (e.rect.centerx - ex) ** 2 + (e.rect.centery - ey) ** 2
                if dist < min_dist:
                    min_dist = dist
                    closest_enemy = e

            if closest_enemy and min_dist < 2500:
                closest_enemy.take_damage(999)


        elif msg.get("action") == "sync_kill_enemy_list":

            targets = msg.get("targets", [])

            for tx, ty in targets:

                closest_enemy = None

                min_dist = 999999

                for e in self.enemies:
                    dist = (e.rect.centerx - tx) ** 2 + (e.rect.centery - ty) ** 2
                    if dist < min_dist:
                        min_dist = dist
                        closest_enemy = e
                if closest_enemy and min_dist < 2500:
                    closest_enemy.take_damage(999)
                    self.effects.add(InstaKillEffect(closest_enemy.rect.centerx, closest_enemy.rect.centery, self.images['instakill']))

        elif msg.get("action") == "BRAINWASH":
            target_x = msg.get("x")
            target_y = msg.get("y")

            for hero in self.heroes:
                if hero.rect.centerx == target_x and hero.rect.centery == target_y:
                    hero.is_brainwashed = True
                    hero.brainwash_timer = 10.0
                    break



        elif msg.get("action") == "game_over":
            self.game_over = True
            self.winner = msg.get("winner")

        elif msg.get("action") == "target_hero":
            tx, ty = msg.get("x"), msg.get("y")

            # x, y가 -1이면 선택 취소라는 뜻!
            if tx == -1 and ty == -1:
                self.targeted_by_attacker_pos = None
            else:
                self.targeted_by_attacker_pos = (tx, ty)

    # [함수 5] 화면 그리기
    def draw(self):
        # 1. 배경 화면 처리
        if self.state == 'BATTLE':
            self.screen.blit(self.map_surface, (0, 0))
        else:
            # 대기실/편성창
            self.screen.fill((150, 150, 150))

        if self.state == 'START':
            if self.bg_start_img:
                self.screen.blit(self.bg_start_img, (0, 0))
                self.draw_text("유물을 지켜라!", 80, c.SCREEN_WIDTH // 2 + 3, 153, c.BLACK)
                self.draw_text("유물을 지켜라!", 80, c.SCREEN_WIDTH // 2, 150, c.WHITE)

                mx, my = pg.mouse.get_pos()
                if self.btn_start_rect.collidepoint(mx, my):
                    current_btn = self.btn_start_img_hover
                else:
                    current_btn = self.btn_start_img_base

                rect = current_btn.get_rect(center=(c.SCREEN_WIDTH // 2, 500))
                self.screen.blit(current_btn, rect)


        elif self.state == 'LOBBY':

            cx, cy = c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2

            # 메인 대기실 판넬 (스케치의 커다란 박스)
            lobby_rect = pg.Rect(cx - 350, cy - 200, 700, 400)
            pg.draw.rect(self.screen, (245, 245, 240), lobby_rect, border_radius=15)
            pg.draw.rect(self.screen, c.BLACK, lobby_rect, 3, border_radius=15)
            self.draw_text("메인 대기실", 40, cx, cy - 150, c.BLACK)

            # [START] 버튼 (정중앙)

            start_btn = pg.Rect(cx - 100, cy - 80, 200, 80)
            can_start = len(self.hero_deck) > 0 and len(self.enemy_deck) > 0
            pg.draw.rect(self.screen, (0, 180, 0) if can_start else (150, 150, 150), start_btn, border_radius=10)
            pg.draw.rect(self.screen, c.BLACK, start_btn, 3, border_radius=10)
            self.draw_text("START", 40, start_btn.centerx, start_btn.centery, c.WHITE)
            if not can_start:
                self.draw_text("영웅/적 덱 편성 필수", 16, start_btn.centerx, start_btn.bottom + 15, (255, 50, 50))

            # [적 편성] 버튼 (좌측)
            enemy_btn = pg.Rect(cx - 250, cy + 50, 200, 80)
            pg.draw.rect(self.screen, (255, 100, 100), enemy_btn, border_radius=10)
            pg.draw.rect(self.screen, c.BLACK, enemy_btn, 3, border_radius=10)
            self.draw_text(f"적 편성 ({len(self.enemy_deck)}/{self.max_enemy_deck})", 24, enemy_btn.centerx,
                           enemy_btn.centery, c.WHITE)

            # [영웅 편성] 버튼 (우측)
            hero_btn = pg.Rect(cx + 50, cy + 50, 200, 80)
            pg.draw.rect(self.screen, (100, 100, 255), hero_btn, border_radius=10)
            pg.draw.rect(self.screen, c.BLACK, hero_btn, 3, border_radius=10)
            self.draw_text(f"영웅 편성 ({len(self.hero_deck)}/{self.max_hero_deck})", 24, hero_btn.centerx,
                           hero_btn.centery, c.WHITE)


        elif self.state == 'EDIT_DECK':
            current_available = self.hero_units if self.editing_mode == "HERO" else self.enemy_units
            current_deck = self.hero_deck if self.editing_mode == "HERO" else self.enemy_deck
            max_size = self.max_hero_deck if self.editing_mode == "HERO" else self.max_enemy_deck
            self.draw_text(f"{'영웅' if self.editing_mode == 'HERO' else '적'} 편성", 48, c.SCREEN_WIDTH // 2, 60, c.BLACK)
            mx, my = pg.mouse.get_pos()
            hovered_unit = None

            # [우측 영역] 전체 유닛 그리드
            grid_start_x, grid_start_y = 450, 150
            icon_size = 90
            spacing = 15
            cols = 5
            pg.draw.rect(self.screen, c.WHITE, (420, 100, 550, 450), 2)
            self.draw_text("배치 가능 유닛", 24, 695, 125, c.BLACK)
            for i, unit in enumerate(current_available):
                col, row = i % cols, i // cols
                slot_rect = pg.Rect(grid_start_x + col * (icon_size + spacing),
                                    grid_start_y + row * (icon_size + spacing),
                                    icon_size, icon_size)

                if slot_rect.collidepoint(mx, my): hovered_unit = unit
                bg_color = (150, 150, 150) if unit in current_deck else (200, 200, 255)
                pg.draw.rect(self.screen, bg_color, slot_rect, border_radius=5)
                pg.draw.rect(self.screen, c.BLACK, slot_rect, 2, border_radius=5)

                try:
                    img = self.get_unit_image(unit)
                    img_scaled = pg.transform.scale(img, (70, 70))
                    self.screen.blit(img_scaled, img_scaled.get_rect(center=slot_rect.center))

                except:

                    self.draw_text(unit, 14, slot_rect.centerx, slot_rect.centery, c.BLACK)

            # [하단 영역] 내 덱
            deck_start_x, deck_start_y = 50, 600
            pg.draw.rect(self.screen, c.WHITE, (30, 570, c.SCREEN_WIDTH - 300, 130), 2)
            self.draw_text(f"내 덱 ({len(current_deck)}/{max_size})", 20, 100, 585, c.BLACK)

            for i in range(max_size):
                slot_rect = pg.Rect(deck_start_x + i * 100, deck_start_y, 80, 80)
                pg.draw.rect(self.screen, (220, 220, 220), slot_rect, border_radius=5)
                pg.draw.rect(self.screen, c.BLACK, slot_rect, 2, border_radius=5)

                if i < len(current_deck):
                    unit = current_deck[i]
                    if slot_rect.collidepoint(mx, my): hovered_unit = unit

                    try:
                        img = self.get_unit_image(unit)
                        img_scaled = pg.transform.scale(img, (70, 70))
                        self.screen.blit(img_scaled, img_scaled.get_rect(center=slot_rect.center))

                    except:
                        self.draw_text(unit, 14, slot_rect.centerx, slot_rect.centery, c.BLACK)

            # [좌측 영역] 상세 정보
            info_box = pg.Rect(50, 100, 350, 450)
            pg.draw.rect(self.screen, c.WHITE, info_box, 2)
            self.draw_text("상세 정보", 24, info_box.centerx, 125, c.BLACK)
            unit_descriptions = {
                "Knight": "단일 dps최강, 비행유닛 공격불가",
                "Archer": "원거리 공격, 3레벨 폭탄화살.",
                "Wizard": "원거리 단일 스턴 공격",
                "Priest": "클릭형, 서포터 특화",
                "Orc": "기본 몬스터",
                "Slime": "죽으면 두마리로 분열",
                "OrcRider": "이동속도가 빠름",
                "ArmoredOrc": "체력이 높음",
                "Skeleton": "죽을시 배치된 영웅이 15초전 상황으로 역행",
                "SkeletonArcher": "부활 유닛, 10초마다 무료저격 1회 획득",
                "GreatswordSkeleton": "부활 유닛, 죽으면 범위피해",
                "Zeppelin": "비행 유닛, 체력절반이하시 영웅 공격",
                "Ship": "15초마다 10초간 도발및 범위 피해 탱커형",
                "BlueAngel": "비행유닛, 유혹 특화",
                "RedAngel": "비행유닛, 레벨 다운시킴"
            }

            if hovered_unit:
                try:
                    img = self.get_unit_image(hovered_unit)
                    img_big = pg.transform.scale(img, (200, 200))
                    self.screen.blit(img_big, img_big.get_rect(center=(info_box.centerx, 260)))
                except:
                    pass

                pg.draw.rect(self.screen, (240, 240, 240), (70, 400, 310, 140), border_radius=5)
                pg.draw.rect(self.screen, c.BLACK, (70, 400, 310, 140), 2, border_radius=5)

                cost = 70
                if hasattr(c, 'UNIT_COSTS'):
                    cost = c.UNIT_COSTS.get(hovered_unit, 70)

                self.draw_text(f"이름: {hovered_unit}", 24, info_box.centerx, 425, c.BLACK)
                self.draw_text(f"비용: {cost} 골드", 22, info_box.centerx, 460, (200, 50, 50))

                desc_text = unit_descriptions.get(hovered_unit, "특징이 없는 일반 유닛입니다.")
                self.draw_text(desc_text, 14, info_box.centerx, 495, (50, 100, 255))
                self.draw_text("클릭하여 덱에 추가/제거", 12, info_box.centerx, 525, c.GRAY)
            else:
                self.draw_text("유닛에 마우스를 올려보세요", 20, info_box.centerx, info_box.centery, c.GRAY)
            back_btn = pg.Rect(c.SCREEN_WIDTH - 250, 600, 200, 80)
            pg.draw.rect(self.screen, (100, 100, 255), back_btn, border_radius=10)
            pg.draw.rect(self.screen, c.BLACK, back_btn, 3, border_radius=10)
            self.draw_text("완료", 24, back_btn.centerx, back_btn.centery, c.WHITE)


        elif self.state == 'WAITING':
            dots = "." * self.loading_dots
            self.draw_text(f"상대방을 기다리는 중{dots}", 30, c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2 + 20, c.GRAY)

        elif self.state == 'BATTLE':
            # 미션
            if self.active_mission:
                pg.draw.rect(self.screen, (50, 50, 80), (c.SCREEN_WIDTH // 2 - 200, 60, 400, 70), border_radius=10)
                pg.draw.rect(self.screen, (255, 200, 0), (c.SCREEN_WIDTH // 2 - 200, 60, 400, 70), 3, border_radius=10)
                self.draw_text(self.mission_desc, 18, c.SCREEN_WIDTH // 2, 75, c.WHITE)
                self.draw_text(
                    f"나: {self.my_mission_progress}/{self.mission_max_me}  VS  적: {self.opp_mission_progress}/{self.mission_max_opp}",
                    24,
                    c.SCREEN_WIDTH // 2, 105, (255, 255, 0))

            # 2. 내 오행 동전 슬롯
            coin_x = c.SCREEN_WIDTH - 280
            coin_y = c.SCREEN_HEIGHT - 60
            self.draw_text("보유 코인", 16, coin_x, coin_y - 30, c.WHITE)

            for i in range(5):
                rect = pg.Rect(coin_x - 30 + (i * 45), coin_y - 20, 40, 40)
                pg.draw.rect(self.screen, (100, 100, 100), rect, border_radius=20)

                if i < len(self.my_coins):
                    coin_name = self.my_coins[i]
                    coin_img = self.images['OHANG'].get(coin_name)
                    coin_img_scaled = pg.transform.scale(coin_img, (40, 40))
                    self.screen.blit(coin_img_scaled, rect.topleft)

            # 3. 활성화된 버프(시너지) 표시
            if self.active_synergies:
                self.draw_text("발동된 오행 효과", 16, coin_x - 120, coin_y - 30, c.WHITE)
                for i, syn in enumerate(self.active_synergies):
                    self.draw_text(f"{syn}", 16, coin_x - 120, coin_y + (i * 20) - 5, (0, 255, 255))
            for node in self.placement_nodes:
                is_occupied = any(node.collidepoint(hero.rect.center) for hero in self.heroes)
                if not is_occupied:
                    pg.draw.rect(self.screen, (180, 180, 180), node, 2)

            # 1. 맵, 유닛들 그리기
            self.speed_zones.draw(self.screen)
            self.enemies.draw(self.screen)
            for enemy in self.enemies:
                if enemy.hp > 0 and enemy.state != 'dying':
                    hp_ratio = max(0, enemy.hp / enemy.max_hp)
                    bar_width = 40
                    bar_height = 6
                    bar_x = enemy.rect.centerx - (bar_width // 2)
                    bar_y = enemy.rect.centery - 40

                    pg.draw.rect(self.screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
                    pg.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, bar_width * hp_ratio, bar_height))

                    # 배의 타이머
                    if type(enemy).__name__ == "Ship":
                        gauge_ratio = 0.0
                        if getattr(enemy, 'is_taunting', False):
                            gauge_ratio = getattr(enemy, 'taunt_duration', 5.0) / 5.0
                            gauge_color = (255, 50, 50)
                        else:
                            current_cycle = getattr(enemy, 'taunt_cycle', 10.0)
                            gauge_ratio = (10.0 - current_cycle) / 10.0
                            gauge_color = (255, 150, 0)

                        gauge_ratio = max(0.0, min(1.0, gauge_ratio))
                        gauge_y = bar_y + bar_height + 2
                        pg.draw.rect(self.screen, (50, 50, 50), (bar_x, gauge_y, bar_width, 4))
                        pg.draw.rect(self.screen, gauge_color, (bar_x, gauge_y, bar_width * gauge_ratio, 4))

                    elif type(enemy).__name__ in ["RedAngel", "BlueAngel"]:
                        current_timer = getattr(enemy, 'skill_timer', 0.0)
                        cooldown = getattr(enemy, 'skill_cooldown', 15.0)
                        gauge_ratio = (cooldown - current_timer) / cooldown
                        gauge_ratio = max(0.0, min(1.0, gauge_ratio))

                        if type(enemy).__name__ == "BlueAngel":
                            gauge_color = (180, 130, 255)
                        else:
                            gauge_color = (255, 50, 50)
                        gauge_y = bar_y + bar_height + 2

                        pg.draw.rect(self.screen, (50, 50, 50), (bar_x, gauge_y, bar_width, 4))
                        pg.draw.rect(self.screen, gauge_color, (bar_x, gauge_y, bar_width * gauge_ratio, 4))

                    elif type(enemy).__name__ == "SkeletonTombstone":
                        current_timer = getattr(enemy, 'alive_timer', 3.0)
                        gauge_ratio = max(0.0, min(1.0, current_timer / 3.0))
                        gauge_y = bar_y + bar_height + 2

                        pg.draw.rect(self.screen, (50, 50, 50), (bar_x, gauge_y, bar_width, 4))
                        pg.draw.rect(self.screen, (255, 255, 255), (bar_x, gauge_y, bar_width * gauge_ratio, 4))

                    elif type(enemy).__name__ == "SkeletonArcher":
                        current_timer = getattr(enemy, 'alive_timer', 0.0)
                        gauge_ratio = current_timer / 10.0
                        gauge_ratio = max(0.0, min(1.0, gauge_ratio))
                        gauge_y = bar_y + bar_height + 2

                        pg.draw.rect(self.screen, (50, 50, 50), (bar_x, gauge_y, bar_width, 4))
                        pg.draw.rect(self.screen, (180, 100, 255), (bar_x, gauge_y, bar_width * gauge_ratio, 4))
            base_x, base_y = c.WAYPOINTS_LIST[0][-1]

            if hasattr(self, 'artifact_img'):
                img_rect = self.artifact_img.get_rect(center=(base_x, base_y - 40))
                self.screen.blit(self.artifact_img, img_rect)

            hp_ratio = max(0, self.artifact_hp / self.artifact_max_hp)

            bar_y = base_y - 105
            pg.draw.rect(self.screen, c.BLACK, (base_x - 40, bar_y, 80, 10))
            pg.draw.rect(self.screen, (255, 0, 0), (base_x - 40, bar_y, 80 * hp_ratio, 10))

            if self.role == "DEFENDER" and self.selected_placed_hero:
                hero = self.selected_placed_hero
                hitbox = pg.Rect(0, 0, 60, 70)
                hitbox.center = hero.rect.center
                pg.draw.rect(self.screen, (0, 255, 255), hitbox, 3)

                if hasattr(hero, 'attack_range'):
                    pg.draw.circle(self.screen, (0, 0, 255), hero.rect.center, hero.attack_range, 2)

                panel_rect = pg.Rect(10, c.SCREEN_HEIGHT - 120, 200, 110)
                pg.draw.rect(self.screen, (40, 40, 40), panel_rect)
                pg.draw.rect(self.screen, c.WHITE, panel_rect, 2)

                hero_name_kr = "영웅"
                hero_class_name = type(hero).__name__

                if hero_class_name == "Knight":
                    hero_name_kr = "기사"
                elif hero_class_name == "Archer":
                    hero_name_kr = "아처"
                elif hero_class_name == "Wizard":
                    hero_name_kr = "마법사"
                elif hero_class_name == "Priest":
                    hero_name_kr = "사제"

                if hasattr(hero, 'level'):
                    self.draw_text(f"{hero_name_kr} (Lv.{hero.level})", 20, panel_rect.centerx, c.SCREEN_HEIGHT - 100,
                                   c.WHITE)

                    if hero.level < hero.max_level:
                        upgrade_cost = 999
                        if hero_class_name == "Knight":
                            upgrade_cost = c.KNIGHT_UPGRADE_COST.get(hero.level, 999)
                        elif hero_class_name == "Archer":
                            upgrade_cost = getattr(c, 'ARCHER_UPGRADE_COST', c.KNIGHT_UPGRADE_COST).get(hero.level, 150)
                        elif hero_class_name == "Priest":
                            upgrade_cost = c.PRIEST_UPGRADE_COST.get(hero.level, 999)

                        btn_color = (0, 180, 0) if self.gold >= upgrade_cost else (180, 50, 50)
                        pg.draw.rect(self.screen, btn_color, self.upgrade_btn_rect)
                        pg.draw.rect(self.screen, c.WHITE, self.upgrade_btn_rect, 2)
                        self.draw_text(f"강화 ({upgrade_cost}G)", 20, self.upgrade_btn_rect.centerx,
                                       self.upgrade_btn_rect.centery, c.WHITE)
                    else:
                        self.draw_text("최고 레벨 (MAX)", 20, panel_rect.centerx, c.SCREEN_HEIGHT - 60, (255, 255, 0))
                else:
                    self.draw_text(f"{hero_name_kr}", 20, panel_rect.centerx, c.SCREEN_HEIGHT - 80, c.WHITE)
                    self.draw_text("강화 불가", 20, panel_rect.centerx, c.SCREEN_HEIGHT - 50, c.GRAY)

                if type(self.selected_placed_hero).__name__ == "Priest":
                    btn_x = self.selected_placed_hero.rect.centerx - 40
                    btn_y = self.selected_placed_hero.rect.top - 70
                    btn_color = (255, 100, 100) if self.selected_placed_hero.mode == 'attack' else (100, 255, 100)
                    btn_text = "공격 모드" if self.selected_placed_hero.mode == 'attack' else "힐러 모드"
                    pg.draw.rect(self.screen, btn_color, (btn_x, btn_y, 80, 25), border_radius=5)
                    self.draw_text(btn_text, 14, btn_x + 40, btn_y + 12, c.WHITE)

            if self.role == "ATTACKER" and getattr(self, 'selected_target_hero', None):
                hero = self.selected_target_hero
                hitbox = pg.Rect(0, 0, 60, 70)
                hitbox.center = hero.rect.center
                pg.draw.rect(self.screen, (255, 0, 0), hitbox, 3)

                if hasattr(hero, 'attack_range'):
                    pg.draw.circle(self.screen, (0, 0, 255), hero.rect.center, hero.attack_range, 2)

                panel_rect = pg.Rect(10, c.SCREEN_HEIGHT - 120, 200, 110)
                pg.draw.rect(self.screen, (40, 40, 40), panel_rect)
                pg.draw.rect(self.screen, c.WHITE, panel_rect, 2)

                hero_name_kr = type(hero).__name__
                if hero_name_kr == "Knight":
                    hero_name_kr = "기사"
                elif hero_name_kr == "Archer":
                    hero_name_kr = "아처"
                elif hero_name_kr == "Wizard":
                    hero_name_kr = "마법사"
                elif hero_name_kr == "Priest":
                    hero_name_kr = "사제"

                level_text = f" (Lv.{hero.level})" if hasattr(hero, 'level') else ""
                self.draw_text(f"{hero_name_kr}{level_text}", 20, panel_rect.centerx, c.SCREEN_HEIGHT - 100,
                                   c.WHITE)
                hp_text = f"HP: {int(getattr(hero, 'hp', 0))}/{int(getattr(hero, 'max_hp', 100))}"
                self.draw_text(hp_text, 16, panel_rect.centerx, c.SCREEN_HEIGHT - 78, (255, 100, 100))

                snipe_btn_rect = pg.Rect(20, c.SCREEN_HEIGHT - 60, 180, 40)
                free_count = getattr(self, 'free_snipe_count', 0)
                if free_count > 0:
                    btn_color = (150, 50, 255)  # 무료: 보라색
                    btn_text = f"저격 시작 (무료: {free_count}/3)"
                else:
                    btn_color = (255, 50, 50) if self.gold >= 200 else (100, 50, 50)
                    btn_text = "저격 시작 (200G)"
                pg.draw.rect(self.screen, btn_color, snipe_btn_rect)
                pg.draw.rect(self.screen, c.WHITE, snipe_btn_rect, 2)
                self.draw_text(btn_text, 20, snipe_btn_rect.centerx, snipe_btn_rect.centery, c.WHITE)

            if self.role == "DEFENDER" and getattr(self, 'targeted_by_attacker_pos', None):
                tx, ty = self.targeted_by_attacker_pos
                for hero in self.heroes:
                    if abs(hero.rect.centerx - tx) < 15 and abs(hero.rect.centery - ty) < 15:
                        self.draw_text("조준됨!", 22, hero.rect.centerx, hero.rect.top - 40, (255, 0, 0))
                        break
            self.heroes.draw(self.screen)
            for hero in self.heroes:
                if hasattr(hero, 'hp') and hasattr(hero, 'max_hp') and hero.hp > 0:
                    hp_ratio = max(0, hero.hp / hero.max_hp)
                    bar_width = 40
                    bar_height = 6
                    bar_x = hero.rect.centerx - (bar_width // 2)
                    bar_y = hero.rect.top - 2

                    pg.draw.rect(self.screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
                    pg.draw.rect(self.screen, (0, 150, 255), (bar_x, bar_y, bar_width * hp_ratio, bar_height))

                    if getattr(hero, 'is_brainwashed', False):
                        bw_timer = getattr(hero, 'brainwash_timer', 0.0)
                        bw_ratio = max(0.0, min(1.0, bw_timer / 10.0))
                        bw_y = bar_y - 6
                        pg.draw.rect(self.screen, (50, 50, 50), (bar_x, bw_y, bar_width, 4))
                        pg.draw.rect(self.screen, (180, 130, 255), (bar_x, bw_y, bar_width * bw_ratio, 4))
                        self.draw_text("♥", 25, hero.rect.centerx, bar_y - 22, (255, 50, 50))

                    if type(hero).__name__ == "Priest" and hasattr(hero, 'attack_count') and hasattr(hero,
                                                                                                     'max_attack_count'):
                        gauge_ratio = max(0.0, min(1.0, hero.attack_count / hero.max_attack_count))
                        gauge_y = bar_y + bar_height + 2
                        pg.draw.rect(self.screen, (50, 50, 50), (bar_x, gauge_y, bar_width, 4))
                        pg.draw.rect(self.screen, (255, 255, 0), (bar_x, gauge_y, bar_width * gauge_ratio, 4))

                    if getattr(hero, 'level_down_timer', 0.0) > 0:
                        self.draw_text("DOWN", 18, hero.rect.centerx, bar_y - 35, (255, 50, 50))

                if hasattr(hero, 'level'):
                    if hero.level == 1:
                        lv_color = (255, 255, 0)
                    elif hero.level == 2:
                        lv_color = (255, 150, 0)
                    elif hero.level >= 3:
                        lv_color = (255, 50, 50)
                    self.draw_text(f"Lv.{hero.level}", 16, hero.rect.centerx, hero.rect.centery + 35, lv_color)

            self.bullets.draw(self.screen)
            self.effects.draw(self.screen)

            # 우측 UI 패널 배경 정보 그리기
            ui_x = 800
            if self.gold >= 1000:
                gold_text = "GOLD: 1000(MAX)"
                gold_color = (255, 150, 0)  # 주황색
            else:
                gold_text = f"GOLD: {int(self.gold)}"
                gold_color = c.BLACK

            self.draw_text(gold_text, 20, ui_x + 112, 50, gold_color)

            if self.role == "ATTACKER":
                path_text = f"현재 경로: {self.selected_path_pp + 1}번 길"
                self.draw_text(path_text, 18, ui_x + 112, 100, (255, 255, 0))

            # 3. 상점에서 캐릭터 버튼화시킨 덱 그려주기
            for i, unit_name in enumerate(self.my_deck):
                col, row = i % 2, i // 2
                rect = pg.Rect(ui_x + 20 + (col * 90), 150 + (row * 90), 80, 80)

                cost = 30 if self.role == "ATTACKER" else 70
                if hasattr(c, 'UNIT_COSTS'): cost = c.UNIT_COSTS.get(unit_name, cost)

                bg_color = (100, 220, 100) if self.gold >= cost else (150, 150, 150)
                pg.draw.rect(self.screen, bg_color, rect, border_radius=5)

                if self.selected_hero_to_place == unit_name:
                    pg.draw.rect(self.screen, (255, 255, 0), rect, 4, border_radius=5)
                else:
                    pg.draw.rect(self.screen, c.BLACK, rect, 2, border_radius=5)

                try:
                    unit_img = self.get_unit_image(unit_name)
                    unit_img_scaled = pg.transform.scale(unit_img, (68, 68))
                    self.screen.blit(unit_img_scaled, unit_img_scaled.get_rect(center=(rect.centerx, rect.top + 34)))
                except:
                    self.draw_text(unit_name, 12, rect.centerx, rect.top + 30, c.BLACK)

                text_color = c.BLACK if self.gold >= cost else (200, 0, 0)
                self.draw_text(f"{cost}G", 16, rect.centerx, rect.bottom - 13, text_color)

            # 상단 중앙: 남은 시간 표시
            time_text = f"{int(self.game_timer // 60):02d}:{int(self.game_timer % 60):02d}"

            hp_mult = 1.0
            gold_mult = 1.0
            if self.game_timer <= 60:
                hp_mult, gold_mult = 1.7, 1.6
            elif self.game_timer <= 120:
                hp_mult, gold_mult = 1.5, 1.4
            elif self.game_timer <= 180:
                hp_mult, gold_mult = 1.2, 1.2

            pg.draw.rect(self.screen, (20, 20, 30), (c.SCREEN_WIDTH // 2 - 210, 10, 420, 40), border_radius=5)
            pg.draw.rect(self.screen, (100, 100, 150), (c.SCREEN_WIDTH // 2 - 210, 10, 420, 40), 2, border_radius=5)

            if self.role == "DEFENDER":
                info_text = f"{time_text}  |  보상 골드: x{gold_mult:.1f}  |  적 체력: x{hp_mult:.1f}"
                self.draw_text(info_text, 16, c.SCREEN_WIDTH // 2, 30, (100, 200, 255))  # 하늘색 글씨

            elif self.role == "ATTACKER":
                extra_gold = 5 if getattr(self, 'buff_gold_up', False) else 0
                current_gain = 10
                if self.game_timer <= 30:
                    current_gain = 40
                elif self.game_timer <= 60:
                    current_gain = 30
                elif self.game_timer <= 90:
                    current_gain = 25
                elif self.game_timer <= 150:
                    current_gain = 20
                elif self.game_timer <= 210:
                    current_gain = 15
                elif self.game_timer <= 240:
                    current_gain = 12
                attacker_gold_per_sec = current_gain + extra_gold

                info_text = f"{time_text}  |  초당 골드: +{attacker_gold_per_sec}G  |  적 체력: x{hp_mult:.1f}"
                self.draw_text(info_text, 16, c.SCREEN_WIDTH // 2, 30, (255, 120, 120))  # 살짝 빨간색 글씨


            # 게임 오버 화면
            if self.game_over:
                overlay = pg.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
                overlay.set_alpha(180)
                overlay.fill(c.BLACK)
                self.screen.blit(overlay, (0, 0))

                result_text = "승리했습니다!" if self.winner == self.role else "당신이 패배했습니다..."
                color = (0, 255, 0) if self.winner == self.role else (255, 0, 0)
                self.draw_text("GAME OVER", 80, c.SCREEN_WIDTH // 2, 300, color)
                self.draw_text(result_text, 40, c.SCREEN_WIDTH // 2, 400, c.WHITE)

                win_role = "방어자 승리!" if self.winner == "DEFENDER" else "공격자 승리"
                self.draw_text(win_role, 30, c.SCREEN_WIDTH // 2, 480, c.GRAY)
                self.draw_text("화면을 클릭하면 로비로 돌아갑니다", 20, c.SCREEN_WIDTH // 2, 600, (200, 200, 200))

        elif self.state == 'MINIGAME':
            if self.minigame:
                self.minigame.draw(self.screen)

        if self.state == 'BATTLE' and self.intro_timer > 0:
            self.draw_intro_screen()

        if self.state == 'BATTLE':
            if getattr(self, 'coin_display_timer', 0) > 0 and getattr(self, 'synergy_display_timer', 0) <= 0:
                overlay = pg.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pg.SRCALPHA)
                overlay.fill((0, 0, 0, 130))  # 반투명 배경
                self.screen.blit(overlay, (0, 0))

                coin_name = self.coin_display_name
                coin_img = self.images['OHANG'].get(coin_name)
                if coin_img:
                    scale_val = 150 + int(math.sin(self.coin_display_timer * 8) * 10)
                    coin_scaled = pg.transform.scale(coin_img, (scale_val, scale_val))
                    rect = coin_scaled.get_rect(center=(c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2 - 50))
                    self.screen.blit(coin_scaled, rect)

                    self.draw_text(f"[{coin_name}] 코인 획득!", 45, c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2 + 70,
                                   (255, 255, 0))

            # 2. 오행 시너지(조합) 발동 번개 애니메이션
            if getattr(self, 'synergy_display_timer', 0) > 0:
                t = self.synergy_display_timer
                max_t = 2.5
                cx, cy = c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2

                overlay = pg.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pg.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))

                e1, e2 = self.synergy_display_elements
                color1 = self.element_colors.get(e1, (255, 255, 255))
                color2 = self.element_colors.get(e2, (255, 255, 255))

                try:
                    img1 = pg.transform.scale(self.images['OHANG'].get(e1), (120, 120))
                    img2 = pg.transform.scale(self.images['OHANG'].get(e2), (120, 120))

                    if t > 1.5:
                        progress = (max_t - t) / 1.0  # 0.0 에서 1.0으로 증가
                        dist = 400 * (1.0 - progress)  # 400px 거리에서 중앙(0)으로 좁혀짐

                        x1, x2 = cx - dist, cx + dist
                        self.screen.blit(img1, img1.get_rect(center=(int(x1), cy)))
                        self.screen.blit(img2, img2.get_rect(center=(int(x2), cy)))
                        for color in [color1, color2, (255, 255, 255)]:  # 각 속성 색상 + 흰색 섞기
                            points = []
                            curr_x = x1
                            while curr_x < x2:
                                points.append((curr_x, cy + random.randint(-60, 60)))  # 상하로 마구 튐
                                curr_x += 40
                            points.append((x2, cy))
                            if len(points) > 2:
                                pg.draw.lines(self.screen, color, False, points, random.randint(3, 6))
                    else:
                        radius = int((1.5 - t) * 600)
                        if radius < c.SCREEN_WIDTH:
                            thickness = max(1, 20 - int(radius / 30))
                            pg.draw.circle(self.screen, (255, 255, 200), (cx, cy), radius, thickness)

                        self.draw_text("SYNERGY", 30, cx, cy - 80, (255, 200, 0))
                        self.draw_text(f"【 {self.synergy_display_name} 】", 70, cx, cy - 20, (255, 255, 255))
                        self.draw_text(self.synergy_display_desc, 35, cx, cy + 60, (0, 255, 255))
                except:
                    pass

        pg.display.flip()

    # [함수 6] 글자 그리기 도구
    def draw_text(self, text, size, x, y, color):
        font = pg.font.SysFont("malgungothic", size)
        img = font.render(text, True, color)
        rect = img.get_rect(center=(x, y))
        self.screen.blit(img, rect)

    # [함수7] 게임을 초기 상태로 되돌립니다.
    def reset_game(self):
        self.state = 'LOBBY'
        self.my_deck = []

        self.heroes.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.effects.empty()
        self.speed_zones.empty()
        self.i_am_ready = False
        self.opponent_is_ready = False

        # 기본 게임 스탯 초기화
        self.gold = c.INITIAL_GOLD
        if self.role == "DEFENDER":
            self.gold += 20
        self.game_timer = 300.0
        self.artifact_hp = self.artifact_max_hp
        self.game_over = False
        self.winner = None
        self.selected_hero_to_place = None
        self.selected_placed_hero = None

        self.my_coins = []
        self.active_synergies = []
        self.available_elements = ["목", "화", "토", "금", "수"]

        self.buff_dmg_up = False
        self.buff_gold_up = False
        self.synergy_timer_15s = 0.0
        self.synergy_timer_30s = 0.0

        self.game_snapshots = []
        self.snapshot_timer = 0.0
        self.last_reverse_time = -30000

        # 미션 진행도 초기화
        self.mission_schedule = [240, 210, 180, 150, 120, 90]
        self.active_mission = False
        self.current_mission_type = None
        self.my_mission_progress = 0
        self.opp_mission_progress = 0
        self.mission_max_me = 0
        self.mission_max_opp = 0
        self.mission_desc = ""
        self.free_snipe_count = 0

    def spawn_enemy_local(self, unit_type, path_idx=0):
        new_enemy = None
        #웨이포인트 값 불러오기
        target_waypoints = c.WAYPOINTS_LIST[path_idx]
        start_x, start_y = target_waypoints[0]

        if unit_type == "Orc":
            new_enemy = Orc(start_x, start_y, target_waypoints, self.images['enemies'])
        elif unit_type == "Slime":
            new_enemy = Slime(start_x, start_y, target_waypoints, self.images['enemies'])
        elif unit_type == "OrcRider":
            new_enemy = OrcRider(start_x, start_y, target_waypoints, self.images['enemies'])
        elif unit_type == "ArmoredOrc":
            new_enemy = ArmoredOrc(start_x, start_y, target_waypoints, self.images['enemies'])
        elif unit_type == "Skeleton":
            new_enemy = Skeleton(start_x, start_y, target_waypoints, self.images['enemies'])
        elif unit_type == "SkeletonArcher":
            new_enemy = SkeletonArcher(start_x, start_y, target_waypoints, self.images['enemies'])
        elif unit_type == "GreatswordSkeleton":
            new_enemy = GreatswordSkeleton(start_x, start_y, target_waypoints, self.images['enemies'])
        elif unit_type == "Zeppelin":
            new_enemy = Zeppelin(start_x, start_y, target_waypoints, self.images['enemies'])
        elif unit_type == "Ship":
            new_enemy = Ship(start_x, start_y, target_waypoints, self.images['enemies'], self.speed_zones)
        elif unit_type == "RedAngel":
            new_enemy = RedAngel(start_x, start_y, target_waypoints, self.images['enemies'])
        elif unit_type == "BlueAngel":
            new_enemy = BlueAngel(start_x, start_y, target_waypoints, self.images['enemies'])

        if new_enemy:
            self.apply_time_multiplier(new_enemy)
            self.enemies.add(new_enemy)

    #음악 생성
    def update_bgm(self):
        main_states = ['START', 'LOBBY', 'EDIT_DECK', 'WAITING']
        battle_states = ['BATTLE', 'MINIGAME']

        if self.state in main_states:
            if self.current_bgm != "MAIN":
                try:
                    # 음악적기
                    pg.mixer.music.load("bgm.mp3")
                    pg.mixer.music.play(-1)
                    self.current_bgm = "MAIN"
                except Exception as e:
                    print("메인 BGM 로드 실패 (파일 이름을 확인하세요):", e)
                    self.current_bgm = "MAIN"

        # 2. 전투 화면일 때
        elif self.state in battle_states and not self.game_over:
            if self.current_bgm != "BATTLE":
                try:
                    battle_bgm_list = ["bgm_7.mp3", "bgm_8.mp3", "bgm_9.mp3"]
                    chosen_bgm = random.choice(battle_bgm_list)
                    pg.mixer.music.load(chosen_bgm)
                    pg.mixer.music.play(-1)
                    self.current_bgm = "BATTLE"
                except Exception as e:
                    print("전투 BGM 로드 실패 (파일 이름을 확인하세요):", e)
                    self.current_bgm = "BATTLE"

        # 3. 게임 오버 시 음악 끄기
        elif self.game_over and self.current_bgm != "STOP":
            pg.mixer.music.stop()
            self.current_bgm = "STOP"
    #유닛 이미지 가져오기
    def get_unit_image(self, unit_name):

        if unit_name in ["Knight", "Archer"]:
            return self.images['heroes'][f"{unit_name.lower()}_attack_lvl1"][0]
        elif unit_name == "Wizard":
            return self.images['heroes']["wizard_attack"][0]
        elif unit_name == "Priest":
            return self.images['heroes']["priest_attack"][0]
        else:  # 몬스터일 경우
            return self.images['enemies'][f"{unit_name.lower()}_move"][0]

    #[함수8]인트로 그리기
    def draw_intro_screen(self):
        # 1. 반투명한 검은색 배경 깔기
        overlay = pg.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # 2. 중앙에 'VS' 글자 그리기
        vs_text = self.font_medium.render("V S", True, (255, 50, 50))
        vs_rect = vs_text.get_rect(center=(c.SCREEN_WIDTH // 2, 150))
        self.screen.blit(vs_text, vs_rect)

        # 3. 텍스트 그리기
        player_text = self.font_medium.render("영웅", True, (100, 200, 255))
        enemy_text = self.font_medium.render("몬스터", True, (255, 100, 100))

        hero_x = c.SCREEN_WIDTH // 4
        enemy_x = c.SCREEN_WIDTH * 3 // 4

        self.screen.blit(player_text, player_text.get_rect(center=(hero_x, 80)))
        self.screen.blit(enemy_text, enemy_text.get_rect(center=(enemy_x, 80)))

        # 덱위치
        if self.role == "DEFENDER":
            hero_deck = self.hero_deck
            enemy_deck = getattr(self, 'opponent_enemy_deck', [])
        else:
            hero_deck = getattr(self, 'opponent_hero_deck', [])
            enemy_deck = self.enemy_deck

        # 크기조정
        def draw_grid(deck, center_x, start_y, cols, img_size):
            spacing_x = img_size + 30  # 유닛 간의 좌우 간격
            spacing_y = img_size + 40  # 유닛 간의 상하 간격

            for i, unit in enumerate(deck):
                img = self.get_unit_image(unit)
                img = pg.transform.scale(img, (img_size, img_size))  # 크기 큼직하게 키우기!

                row = i // cols
                col = i % cols

                total_in_row = min(len(deck) - row * cols, cols)
                start_x = center_x - (total_in_row * spacing_x) // 2 + (spacing_x // 2)

                x = start_x + col * spacing_x
                y = start_y + row * spacing_y

                rect = img.get_rect(center=(x, y))
                self.screen.blit(img, rect)
                # 유닛 이름 텍스트 크기
                self.draw_text(unit, 18, x, y + (img_size // 2) + 15, (255, 255, 255))

        draw_grid(hero_deck, hero_x, 220, cols=2, img_size=130)
        draw_grid(enemy_deck, enemy_x, 220, cols=3, img_size=130)

        # 4. 카운트다운 숫자 그리기
        current_count = math.ceil(self.intro_timer)
        if current_count > 0:
            count_text = self.font_large.render(str(current_count), True, (255, 255, 0))
            count_rect = count_text.get_rect(center=(c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2 + 100))

            # 숫자 테두리 효과(나중에 제거)
            #pg.draw.rect(self.screen, (255, 255, 255), count_rect.inflate(40, 40), 5, border_radius=10)
            self.screen.blit(count_text, count_rect)

    def add_mission_progress(self, action_type, amount):
        if not self.active_mission: return
        if self.current_mission_type != action_type: return
        self.my_mission_progress += amount
        self.net.send({"action": "mission_update", "progress": self.my_mission_progress})
        self.check_mission_win()

    def check_mission_win(self):
        if not self.active_mission: return

        if self.my_mission_progress >= self.mission_max_me:
            self.active_mission = False
            self.net.send({"action": "mission_end"})
            self.get_random_coin()

        elif self.opp_mission_progress >= self.mission_max_opp:
            self.active_mission = False

    def get_random_coin(self):
        if not self.available_elements:
            return

        new_element = random.choice(self.available_elements)
        self.available_elements.remove(new_element)
        self.coin_display_timer = 1.0
        self.coin_display_name = new_element

        for old_element in self.my_coins:
            self.check_sangsaeng(old_element, new_element)

        self.my_coins.append(new_element)

    def check_sangsaeng(self, e1, e2):
        pair = {e1, e2}
        name = ""
        desc = ""

        if pair == {"수", "목"} and "수생목" not in self.active_synergies:
            self.active_synergies.append("수생목")
            name, desc = "수생목", "15초마다 아군 전체 체력 회복!"
        elif pair == {"목", "화"} and "목생화" not in self.active_synergies:
            self.active_synergies.append("목생화")
            self.buff_dmg_up = True
            name, desc = "목생화", "아군 전체 공격력 30% 증가!"
        elif pair == {"화", "토"} and "화생토" not in self.active_synergies:
            self.active_synergies.append("화생토")
            name, desc = "화생토", "30초마다 적 즉사!"
        elif pair == {"토", "금"} and "토생금" not in self.active_synergies:
            self.active_synergies.append("토생금")
            self.buff_gold_up = True
            name, desc = "토생금", "추가 골드 획득!"
        elif pair == {"금", "수"} and "금생수" not in self.active_synergies:
            self.active_synergies.append("금생수")
            self.gold += 500
            name, desc = "금생수", "즉시 500 골드 획득!"

        if name:
            self.coin_display_timer = 0.0
            self.synergy_display_timer = 2.5
            self.synergy_display_elements = [e1, e2]
            self.synergy_display_name = name
            self.synergy_display_desc = desc
    #배율 먹이기
    def apply_time_multiplier(self, enemy):
        hp_mult = 1.0
        gold_mult = 1.0

        if self.game_timer <= 60:
            hp_mult = 1.7
            gold_mult = 1.6
        elif self.game_timer <= 120:
            hp_mult = 1.5
            gold_mult = 1.4
        elif self.game_timer <= 180:
            hp_mult = 1.2
            gold_mult = 1.2

        enemy.max_hp = enemy.max_hp * hp_mult
        enemy.hp = enemy.max_hp

        if type(enemy).__name__ != "SkeletonTombstone":
            if hasattr(enemy, 'reward'):
                enemy.reward = int(enemy.reward * gold_mult)


# 최종 실행 부분
if __name__ == "__main__":
    game = GameClient()
    while game.running:
        game.handle_events()
        game.update()
        game.update_bgm()
        game.draw()
    pg.quit()