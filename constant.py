# constant.py
SCREEN_WIDTH = 1024#34
SCREEN_HEIGHT = 768#38
FPS = 60

# 색상(이건 삭제 가능성 있음 아직 미정)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

# 이동 경로(수정 최종테스트전 필이 필요)
WAYPOINTS_LIST = [
    [(-50, 90), (670, 90), (660, 660), (60, 660)],

    [(780, 90), (110, 90), (110, 360), (420, 360), (420, 660), (60, 660)],

    [(420, 0), (420, 250), (660, 250), (660, 660), (60, 660)]
    # 3번 경로 (아래쪽)
]

INITIAL_GOLD = 100
#초반 무조건 지는 구조 너무 불리함 그러나 후반가면 무조건 적이이기는 구조임 수정해야함
ORC_COST = 30
GOLD_GAIN_PER_SEC = 10

# 유닛 비용

UNIT_COSTS = {
    "Orc": 15,
    "Slime": 20,
    "OrcRider": 35,
    "ArmoredOrc": 40,
    "Wizard": 80,
    "Knight": 40,
    "Skeleton": 150,
    "SkeletonArcher": 50,
    "Archer": 60,
    "GreatswordSkeleton": 50,
    "Zeppelin": 140,
    "Ship": 220,
    "Priest": 50,
    "RedAngel": 110,
    "BlueAngel": 180
}

# 업그레이드
KNIGHT_UPGRADE_COST = {
    1: 40,
    2: 90
}
ARCHER_UPGRADE_COST = {
    1: 60,
    2: 130
}

PRIEST_UPGRADE_COST = {
    1: 80,
    2: 150
}

#히어로 웨이포인트
HERO_PLACEMENT_NODES = [
    [150, 140, 80, 80], [250, 140, 80, 80],
    [150, 240, 80, 80], [250, 240, 80, 80],

    # 2. 중앙 상단 (가로 2칸)
    [460, 140, 80, 80], [560, 140, 80, 80],

    # 3. 중앙 우측
    [520, 310, 80, 80],
    [520, 410, 80, 80],
    [520, 510, 80, 80],

    # 4. 좌측 하단 (2x2 구역)
    [220, 400, 80, 80], [320, 400, 80, 80],
    [220, 500, 80, 80], [320, 500, 80, 80],

    # 5. 우측 가장자리 라인 (세로 5칸)
    [700, 150, 80, 80],
    [700, 270, 80, 80],
    [700, 390, 80, 80],
    [700, 510, 80, 80],
    [700, 630, 80, 80]
]
#적 보상
ENEMY_REWARDS = {
    "Orc": 10,
    "Slime": 5,
    "OrcRider": 15,
    "ArmoredOrc": 15,
    "Skeleton": 100,
    "SkeletonArcher": 30,
    "SlimeBaby": 2,
    "GreatswordSkeleton": 30,
    "Zeppelin": 50,
    "Ship": 80,
    "BlueAngel": 45,
    "RedAngel": 45
}