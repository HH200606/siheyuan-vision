# -*- coding: utf-8 -*-
"""全局配置：尺寸、配色、字体、关卡表。

配色走「宣纸 + 墨 + 朱砂 + 青瓦」的路子，和四合院的材料一致。
"""

WIDTH, HEIGHT = 1180, 760
FPS = 60
TITLE = "四合檐影 · 构件识别"

# 中文优先用系统字体，找不到再退回 pygame 默认（会显示方块，但不会崩）
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]

# ---------------- 配色 ----------------
PAPER = (243, 234, 216)        # 宣纸底色
PAPER_DEEP = (232, 220, 198)   # 纸的阴影面
INK = (38, 34, 32)             # 墨
INK_SOFT = (92, 84, 76)        # 淡墨
INK_MUTE = (140, 130, 118)     # 更淡
CINNABAR = (158, 58, 46)       # 朱砂
GOLD = (186, 146, 78)          # 描金
TILE_BLUE = (74, 96, 126)      # 青瓦
TILE_DARK = (52, 68, 92)
WOOD = (146, 104, 68)          # 木构
WOOD_DARK = (104, 72, 46)
BRICK = (150, 142, 132)        # 灰砖
BRICK_DARK = (120, 112, 103)
STONE = (176, 170, 160)        # 石作
STONE_DARK = (140, 134, 124)
LEAF = (104, 132, 96)          # 点景绿

# ---------------- 规则 ----------------
COMBO_CAP = 5          # 连击倍率上限
BASE_POINTS = 10       # 每题基础分
COMBO_STEP = 2         # 每级连击的额外分

LEVELS = [
    {"id": 1, "name": "入门 · 窗棂", "category": "window", "questions": 6, "lives": 3, "seconds": None},
    {"id": 2, "name": "门饰 · 门墩", "category": "doorstone", "questions": 6, "lives": 3, "seconds": None},
    {"id": 3, "name": "檐下 · 砖雕", "category": "brick", "questions": 6, "lives": 3, "seconds": None},
    {"id": 4, "name": "院门 · 大门形制", "category": "gate", "questions": 6, "lives": 3, "seconds": None},
    {"id": 5, "name": "综合试炼", "category": "mixed", "questions": 8, "lives": 3, "seconds": 75},
]

# 评级：按「实得分 / 理论最高分」的比例划线
RANKS = [
    (0.85, "大师", "看得懂瓦当，也读得懂礼制。"),
    (0.60, "匠人", "构件认得全，眼力已经到家了。"),
    (0.00, "学徒", "刚进门，先去院里转两圈。"),
]
