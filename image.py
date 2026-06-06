# image.py

import pygame as pg
import os


def get_images_from_sheet(sheet_path, frame_count, frame_width, frame_height, scale_factor=2):
    try:
        sheet = pg.image.load(sheet_path).convert_alpha()
    except Exception as e:
        print(f"이미지 로드 실패: {sheet_path}")
        return [pg.Surface((frame_width, frame_height)) for _ in range(frame_count)]

    images = []
    for i in range(frame_count):
        rect = pg.Rect(i * frame_width, 0, frame_width, frame_height)
        image = pg.Surface(rect.size, pg.SRCALPHA)
        image.blit(sheet, (0, 0), rect)

        scaled_image = pg.transform.scale(image, (int(frame_width * scale_factor), int(frame_height * scale_factor)))
        images.append(scaled_image)

    return images


def load_images():
    #파일 불러오기 기존 하나하나 읽어서 가져오는데 공통인 부분은 하나로 묶음
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CHAR_DIR = os.path.join(BASE_DIR, "tiny", "Characters(100x100)")
    TINY_DIR = os.path.join(BASE_DIR, "tiny", "Arrow(Projectile)")
    PIXEL_DIR = os.path.join(BASE_DIR, "Pixel effect") #사용
    FIVE_DIR = os.path.join(BASE_DIR, "오행")
    SHIP_DIR = os.path.join(BASE_DIR, "Ship", "Ship", "Assets")


    def load_arrow(filename):
        path = os.path.join(BASE_DIR, filename)
        if os.path.exists(path):
            return pg.image.load(path).convert_alpha()
        return pg.Surface((32, 32), pg.SRCALPHA)

    def load_zep_img(folder_name, filename):
        path = os.path.join(SHIP_DIR, folder_name, filename)
        return pg.transform.scale(pg.image.load(path).convert_alpha(), (120, 80))

    try:
        beasuk_img = pg.transform.scale(pg.image.load(os.path.join(BASE_DIR, "beasuk.png")).convert_alpha(), (55, 70))
    except:
        beasuk_img = pg.Surface((55, 70), pg.SRCALPHA)
        pg.draw.rect(beasuk_img, (120, 120, 120), (0, 0, 55, 70), border_radius=5)

    return {
        'enemies': {
            'orc_move': get_images_from_sheet(os.path.join(CHAR_DIR, "Orc", "Orc", "Orc-Walk.png"), 8, 100, 100),
            'orc_death': get_images_from_sheet(os.path.join(CHAR_DIR, "Orc", "Orc", "Orc-Death.png"), 4, 100, 100),
            'orcrider_move': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Orc rider", "Orc rider", "Orc rider-Walk.png"), 8, 100, 100),
            'orcrider_death': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Orc rider", "Orc rider", "Orc rider-Death.png"), 4, 100, 100),
            'slime_move': get_images_from_sheet(os.path.join(CHAR_DIR, "Slime", "Slime", "Slime-Walk.png"), 6, 100,
                                                100),
            'slime_death': get_images_from_sheet(os.path.join(CHAR_DIR, "Slime", "Slime", "Slime-Death.png"), 4, 100,
                                                 100),
            'armoredorc_move': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Armored Orc", "Armored Orc", "Armored Orc-Walk.png"), 8, 100, 100),
            'armoredorc_death': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Armored Orc", "Armored Orc", "Armored Orc-Death.png"), 4, 100, 100),
            'skeleton_move': get_images_from_sheet(os.path.join(CHAR_DIR, "Skeleton", "Skeleton", "Skeleton-Walk.png"),
                                                   8, 100, 100),
            'skeleton_death': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Skeleton", "Skeleton", "Skeleton-Death.png"), 4, 100, 100),
            'skeletonarcher_move': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Skeleton Archer", "Skeleton Archer", "Skeleton Archer-Walk.png"), 8, 100, 100),
            'skeletonarcher_death': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Skeleton Archer", "Skeleton Archer", "Skeleton Archer-Death.png"), 4, 100, 100),
            'greatswordskeleton_move': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Greatsword Skeleton", "Greatsword Skeleton", "Greatsword Skeleton-Walk.png"), 9, 100, 100),
            'greatswordskeleton_death': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Greatsword Skeleton", "Greatsword Skeleton", "Greatsword Skeleton-Death.png"), 4, 100, 100),
            'zeppelin_move': [
                load_zep_img("Zeppelin2", f"Zeppelin{i}.png") for i in range(1, 4)
            ],
            'zeppelin_gun': [
                load_zep_img("Zeppelin1", f"Zep{i}.png") for i in range(1, 4)
            ],
            'ship_move': get_images_from_sheet(
                os.path.join(SHIP_DIR, "Ship", "Ship_Idle.png"), 12, 33, 87, 2),
            'ship_taunt': get_images_from_sheet(
                os.path.join(SHIP_DIR, "Ship", "Ship_Damage.png"), 1, 32, 32, 2),
            'redangel_move': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Angels.png"), 8,64, 64)[0:3],
            'blueangel_move': get_images_from_sheet(os.path.join(CHAR_DIR, "Angels.png"), 8, 64, 64)[4:7],
            'tombstone': beasuk_img

        },


        'heroes': {
            'wizard_attack': get_images_from_sheet(os.path.join(CHAR_DIR, "Wizard", "Wizard", "Wizard-Attack01.png"), 6,
                                                   100, 100),
            'knight_attack_lvl1': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Knight", "Knight", "Knight-Attack01.png"), 7, 100, 100),
            'knight_attack_lvl2': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Knight", "Knight", "Knight-Attack02.png"), 6, 100, 100),
            'knight_attack_lvl3': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Knight", "Knight", "Knight-Attack03.png"), 11, 100, 100),
            'archer_attack_lvl1': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Archer", "Archer", "Archer-Attack01.png"), 9, 100, 100),
            'archer_attack_lvl2': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Archer", "Archer", "Archer-Attack01.png"), 9, 100, 100),
            'archer_attack_lvl3': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Archer", "Archer", "Archer-Attack01.png"), 9, 100, 100),
            'priest_attack': get_images_from_sheet(os.path.join(CHAR_DIR, "Priest", "Priest", "Priest-Attack.png"), 9, 100, 100),
            'priest_heal': get_images_from_sheet(os.path.join(CHAR_DIR, "Priest", "Priest", "Priest-Heal.png"), 6, 100, 100)
        },

        'battle': {
            'magic_effect': get_images_from_sheet(
                os.path.join(CHAR_DIR, "Wizard", "Magic(projectile)", "Wizard-Attack01_Effect.png"), 12, 100, 100),
            'arrows': {
                'lvl1': pg.image.load(os.path.join(TINY_DIR, "Arrow01(32x32).png")).convert_alpha(),
                'lvl2': pg.image.load(os.path.join(TINY_DIR, "Arrow02(32x32).png")).convert_alpha(),
                'lvl3': pg.image.load(os.path.join(TINY_DIR, "Arrow03(32x32).png")).convert_alpha()
            },
            'priest_attack_effect': get_images_from_sheet(os.path.join(CHAR_DIR, "Priest", "Priest(Split Effects)", "Priest-Attack_Effect.png"),5, 100, 100),
            'priest_heal_effect': get_images_from_sheet(os.path.join(CHAR_DIR, "Priest", "Priest(Split Effects)", "Priest-Heal_Effect.png"), 4,100, 100)
        },

        'OHANG': {
            '수': pg.image.load(os.path.join(FIVE_DIR, "강수.png")).convert_alpha(),
            '목': pg.image.load(os.path.join(FIVE_DIR, "나무목.png")).convert_alpha(),
            '화': pg.image.load(os.path.join(FIVE_DIR, "불화.png")).convert_alpha(),
            '금': pg.image.load(os.path.join(FIVE_DIR, "쇠금.png")).convert_alpha(),
            '토': pg.image.load(os.path.join(FIVE_DIR, "흙토.png")).convert_alpha()
        },

        'instakill': get_images_from_sheet(os.path.join(PIXEL_DIR, "766.png"), 8, 64, 64, 2)
    }