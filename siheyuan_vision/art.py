# -*- coding: utf-8 -*-
"""构件美术：全部用 pygame 图元绘制，不依赖任何外部图片。

设计上刻意做成「局部特写」：一张宣纸卡片里只放一个构件的最有辨识度的部分，
玩家看形状而不是看场景，这也是原版四合院项目「用代码画图」的延续。

渲染流程：先在 SS 倍尺寸的透明画布上绘制，再平滑缩小 —— 这样曲线和斜线不会锯齿。
"""

from __future__ import annotations

import math
import random

import pygame

from .config import (
    BRICK, BRICK_DARK, CINNABAR, GOLD, INK, INK_MUTE, INK_SOFT, LEAF,
    PAPER, PAPER_DEEP, STONE, STONE_DARK, TILE_BLUE, TILE_DARK, WOOD, WOOD_DARK,
)

SS = 2  # 超采样倍数


# --------------------------------------------------------------------------
# 基础图元
# --------------------------------------------------------------------------

def _rect(surf, color, rect, width=0, radius=0):
    if radius:
        pygame.draw.rect(surf, color, rect, width, border_radius=radius)
    else:
        pygame.draw.rect(surf, color, rect, width)


def _line(surf, color, a, b, w=1):
    pygame.draw.line(surf, color, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), w)


def _lines(surf, color, pts, w=1):
    pygame.draw.lines(surf, color, False, [(int(x), int(y)) for x, y in pts], w)


def _poly(surf, color, points, width=0):
    pygame.draw.polygon(surf, color, [(int(x), int(y)) for x, y in points], width)


def _circle(surf, color, center, r, width=0):
    pygame.draw.circle(surf, color, (int(center[0]), int(center[1])), int(r), width)


def _shade(color, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in color[:3])


# --------------------------------------------------------------------------
# 背景：宣纸 + 淡淡的墙面/地面
# --------------------------------------------------------------------------

def _paper(surf, r):
    _rect(surf, PAPER, r)
    # 纸纹：稀疏的小点
    rng = random.Random(7)
    for _ in range(int(r.w * r.h / 900)):
        x = int(rng.uniform(r.left, r.right))
        y = int(rng.uniform(r.top, r.bottom))
        _circle(surf, _shade(PAPER, 0.965), (x, y), int(rng.uniform(1, 2)))


def _brick_ground(surf, r, top_ratio=0.62):
    """下方砖地、上方墙面，做出「蹲下来看构件」的视角。"""
    split = r.top + r.h * top_ratio
    _rect(surf, PAPER, (r.left, r.top, r.w, r.h * top_ratio))
    _rect(surf, _shade(BRICK, 1.06), (r.left, split, r.w, r.h - r.h * top_ratio))

    # 墙面砖缝
    bw, bh = r.w / 9.0, r.h * 0.055
    for row in range(int(top_ratio * 18)):
        y = r.top + row * bh
        if y > split:
            break
        _line(surf, _shade(BRICK, 0.92), (r.left, y), (r.right, y), 1)
        offset = (bw / 2) if row % 2 else 0
        x = r.left + offset
        while x < r.right:
            _line(surf, _shade(BRICK, 0.92), (x, y), (x, y + bh), 1)
            x += bw

    # 地面砖缝（透视一点）
    for i in range(1, 6):
        y = split + (r.h - (split - r.top)) * (i / 6.0) ** 1.6
        _line(surf, _shade(BRICK, 0.9), (r.left, y), (r.right, y), 1)


# --------------------------------------------------------------------------
# 1. 窗棂
# --------------------------------------------------------------------------

def _wood_frame(surf, r):
    """木窗框，返回内部玻璃/纸的矩形。"""
    frame = pygame.Rect(0, 0, int(r.w * 0.80), int(r.h * 0.70))
    frame.center = (r.centerx, int(r.top + r.h * 0.40))

    _rect(surf, _shade(WOOD, 0.82), frame.move(0, 6), radius=6)     # 投影
    _rect(surf, WOOD, frame, radius=4)
    _rect(surf, _shade(WOOD, 1.12), frame, width=3, radius=4)
    inner = frame.inflate(-int(frame.w * 0.10), -int(frame.h * 0.10))
    _rect(surf, _shade(PAPER, 1.02), inner, radius=2)
    # 窗纸的暗角，让窗心有一点厚度
    _rect(surf, _shade(PAPER, 0.97), inner, width=8)
    return inner


def _lat_bubujin(surf, inner):
    """步步锦：错位的小格 + 连接短棂。"""
    cols, rows = 4, 3
    cw, ch = inner.w / cols, inner.h / rows
    gap = 13
    for i in range(cols):
        for j in range(rows):
            box = pygame.Rect(int(inner.left + i * cw), int(inner.top + j * ch),
                              int(cw), int(ch)).inflate(-gap, -gap)
            _rect(surf, WOOD_DARK, box, width=5)
            if (i + j) % 2 == 0:
                _line(surf, WOOD_DARK, (box.right, box.centery), (box.right + gap, box.centery), 5)
            else:
                _line(surf, WOOD_DARK, (box.centerx, box.top), (box.centerx, box.top - gap), 5)


def _lat_binglie(surf, inner):
    """冰裂纹：随机点连最近的几个邻点，像冰面裂开。"""
    rng = random.Random(11)
    pts = [(rng.uniform(inner.left, inner.right), rng.uniform(inner.top, inner.bottom)) for _ in range(52)]
    pts += [(inner.left, inner.top), (inner.right, inner.top),
            (inner.left, inner.bottom), (inner.right, inner.bottom)]
    for p in pts:
        near = sorted(pts, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2)[1:4]
        for q in near:
            _line(surf, WOOD_DARK, p, q, 4)


def _lat_guibei(surf, inner):
    """龟背锦：六边形连缀。"""
    rad = min(inner.w, inner.h) / 8.5
    dx = rad * 1.5
    dy = rad * math.sqrt(3)
    col = 0
    x = inner.left
    while x < inner.right + rad:
        y = inner.top + (dy / 2 if col % 2 else 0)
        while y < inner.bottom + rad:
            pts = [
                (x + rad * math.cos(math.radians(60 * k)), y + rad * math.sin(math.radians(60 * k)))
                for k in range(6)
            ]
            _poly(surf, WOOD_DARK, pts, 4)
            y += dy
        x += dx
        col += 1


def _lat_denglong(surf, inner):
    """灯笼框：上下横梁 + 圆形灯笼身 + 竖棂。"""
    rad = min(inner.w, inner.h) * 0.36
    cy = inner.centery
    cx = inner.centerx
    _rect(surf, WOOD_DARK, (cx - rad * 0.78, cy - rad - 16, rad * 1.56, 11))
    _rect(surf, WOOD_DARK, (cx - rad * 0.78, cy + rad + 5, rad * 1.56, 11))
    _circle(surf, WOOD_DARK, (cx, cy), rad, 5)
    _circle(surf, WOOD_DARK, (cx, cy), rad * 0.56, 3)
    for dx in (-0.5, 0.0, 0.5):
        x = cx + dx * rad
        _line(surf, WOOD_DARK, (x, cy - rad * 0.92), (x, cy + rad * 0.92), 4)
    _line(surf, WOOD_DARK, (cx - rad * 0.92, cy), (cx + rad * 0.92, cy), 3)


WINDS = {
    "bubujin": _lat_bubujin,
    "binglie": _lat_binglie,
    "guibei": _lat_guibei,
    "denglong": _lat_denglong,
}


def _paint_window(surf, r, variant):
    _brick_ground(surf, r, 0.78)
    inner = _wood_frame(surf, r)
    surf.set_clip(inner)          # 棂条不许画到窗框外
    WINDS[variant](surf, inner)
    surf.set_clip(None)
    # 窗台
    sill = pygame.Rect(0, 0, int(inner.w * 1.18), int(r.h * 0.035))
    sill.midtop = (inner.centerx, inner.bottom + int(inner.h * 0.07))
    _rect(surf, _shade(STONE, 1.0), sill, radius=3)
    _rect(surf, STONE_DARK, sill, width=2, radius=3)


# --------------------------------------------------------------------------
# 2. 门墩
# --------------------------------------------------------------------------

def _stone_base(surf, r, width_ratio=0.62):
    w = r.w * width_ratio
    h = r.h * 0.18
    base = pygame.Rect(int(r.centerx - w / 2), int(r.top + r.h * 0.70), int(w), int(h))
    _rect(surf, STONE_DARK, base.move(0, 6), radius=4)
    _rect(surf, STONE, base, radius=4)
    _rect(surf, _shade(STONE, 0.86), base, width=2, radius=4)
    return base


def _paint_doorstone(surf, r, variant):
    _brick_ground(surf, r, 0.68)
    base = _stone_base(surf, r, 0.66)
    cx = base.centerx
    top = base.top
    h = base.h

    if variant == "shizi":
        # 蹲狮：方座 + 狮身 + 狮头 + 鬃毛 + 前爪
        body = pygame.Rect(0, 0, int(base.w * 0.40), int(h * 1.7))
        body.midbottom = (cx, top + 4)
        _rect(surf, _shade(STONE, 0.96), body, radius=int(body.w * 0.28))
        _rect(surf, _shade(STONE, 0.86), body, width=3, radius=int(body.w * 0.28))

        head_r = body.w * 0.44
        head_c = (cx, body.top - head_r * 0.35)
        # 鬃毛：一圈花瓣
        for ang in range(0, 360, 45):
            x = head_c[0] + math.cos(math.radians(ang)) * head_r * 0.95
            y = head_c[1] + math.sin(math.radians(ang)) * head_r * 0.95
            _circle(surf, _shade(STONE, 0.90), (x, y), head_r * 0.38)
        _circle(surf, _shade(STONE, 1.04), head_c, head_r)
        _circle(surf, _shade(STONE, 0.82), head_c, head_r, 3)
        # 眼、鼻
        for dx in (-0.34, 0.34):
            _circle(surf, INK_SOFT, (head_c[0] + dx * head_r, head_c[1] - head_r * 0.18), head_r * 0.12)
        _circle(surf, INK_SOFT, (head_c[0], head_c[1] + head_r * 0.22), head_r * 0.10)
        # 前爪
        for dx in (-0.30, 0.30):
            paw = pygame.Rect(0, 0, int(body.w * 0.24), int(h * 0.34))
            paw.midbottom = (cx + dx * body.w, top + 6)
            _rect(surf, _shade(STONE, 1.0), paw, radius=6)

    elif variant == "baogu":
        # 抱鼓石：鼓 + 鼓架 + 两侧卷草
        rad = h * 0.86
        drum_c = (cx, top - rad * 0.62)
        _rect(surf, _shade(STONE, 0.92), (cx - rad * 0.5, drum_c[1], rad, top - drum_c[1] + 4))
        _circle(surf, STONE, drum_c, rad)
        _circle(surf, _shade(STONE, 0.86), drum_c, rad, 4)
        _circle(surf, _shade(STONE, 0.90), drum_c, rad * 0.66, 3)
        _circle(surf, _shade(STONE, 0.86), drum_c, rad * 0.16)
        # 两侧卷草（螺旋）
        for dx in (-1, 1):
            cc = (drum_c[0] + dx * rad * 1.02, drum_c[1] + rad * 0.12)
            _circle(surf, _shade(STONE, 0.94), cc, rad * 0.30, 3)
            _circle(surf, _shade(STONE, 0.84), cc, rad * 0.16, 2)

    elif variant == "xiangxing":
        # 箱形：方墩 + 面板 + 如意头
        box = pygame.Rect(0, 0, int(base.w * 0.82), int(h * 2.0))
        box.midbottom = (cx, top + 4)
        _rect(surf, STONE, box, radius=3)
        _rect(surf, _shade(STONE, 0.84), box, width=4, radius=3)
        panel = box.inflate(-box.w * 0.24, -box.h * 0.26)
        _rect(surf, _shade(STONE, 0.92), panel, width=3)
        # 如意头：三个圆 + 一根柄
        cy = panel.top + panel.h * 0.28
        for dx in (-0.9, 0, 0.9):
            _circle(surf, _shade(STONE, 0.86), (panel.centerx + dx * panel.w * 0.16, cy), panel.w * 0.09, 3)
        _line(surf, _shade(STONE, 0.86), (panel.centerx, cy), (panel.centerx, panel.bottom - 10), 3)

    else:  # xumizuo
        # 须弥座：层叠线脚，一层比一层收
        y = top + 4
        widths = [0.98, 0.84, 0.92, 0.76, 0.86]
        heights = [0.22, 0.14, 0.30, 0.14, 0.20]
        for w_r, h_r in zip(widths, heights):
            bw, bh = base.w * w_r, h * h_r * 2.0
            band = pygame.Rect(int(cx - bw / 2), int(y - bh), int(bw), int(bh))
            _rect(surf, _shade(STONE, 1.0 if int(w_r * 100) % 2 else 0.94), band)
            _rect(surf, _shade(STONE, 0.82), band, 2)
            y -= bh
        # 束腰上的小雕饰
        for i in range(3):
            _circle(surf, _shade(STONE, 0.86), (cx - base.w * 0.22 + i * base.w * 0.22, top - h * 0.9), h * 0.10, 2)


# --------------------------------------------------------------------------
# 3. 砖雕
# --------------------------------------------------------------------------

def _carve_panel(surf, r):
    panel = pygame.Rect(0, 0, int(r.w * 0.72), int(r.h * 0.72))
    panel.center = (r.centerx, int(r.top + r.h * 0.46))
    _rect(surf, _shade(BRICK, 1.16), panel)                       # 砖面提亮
    _rect(surf, _shade(BRICK, 0.70), panel, width=7)              # 边框压深
    inner = panel.inflate(-int(panel.w * 0.14), -int(panel.h * 0.14))
    _rect(surf, _shade(BRICK, 0.74), inner, width=2)
    return inner


def _paint_brick(surf, r, variant):
    _brick_ground(surf, r, 0.86)
    inner = _carve_panel(surf, r)
    cx, cy = inner.center
    carve = _shade(BRICK, 0.62)          # 雕纹的暗面
    carve_soft = _shade(BRICK, 0.80)

    if variant == "huacao":
        # 牡丹：多层花瓣 + 卷草
        for k, rr in enumerate((0.26, 0.19, 0.12)):
            _circle(surf, carve if k == 0 else carve_soft, (cx, cy), inner.w * rr, 5)
        for ang in range(0, 360, 45):
            x = cx + math.cos(math.radians(ang)) * inner.w * 0.32
            y = cy + math.sin(math.radians(ang)) * inner.w * 0.32
            _circle(surf, carve_soft, (x, y), inner.w * 0.075, 4)
        for dx in (-1, 1):
            _line(surf, carve_soft, (cx, cy), (cx + dx * inner.w * 0.42, cy + inner.h * 0.18), 5)

    elif variant == "bogu":
        # 博古：花瓶 + 书 + 果盘
        vase = [(cx - inner.w * 0.12, cy - inner.h * 0.10), (cx - inner.w * 0.05, cy - inner.h * 0.34),
                (cx + inner.w * 0.05, cy - inner.h * 0.34), (cx + inner.w * 0.12, cy - inner.h * 0.10),
                (cx + inner.w * 0.07, cy + inner.h * 0.26), (cx - inner.w * 0.07, cy + inner.h * 0.26)]
        _poly(surf, carve_soft, vase, 4)
        _rect(surf, carve_soft, (cx + inner.w * 0.16, cy + inner.h * 0.12, inner.w * 0.24, inner.h * 0.12), 4)
        _rect(surf, carve_soft, (cx + inner.w * 0.14, cy + inner.h * 0.26, inner.w * 0.28, inner.h * 0.09), 4)
        _circle(surf, carve_soft, (cx - inner.w * 0.30, cy + inner.h * 0.20), inner.w * 0.08, 4)

    elif variant == "ruishou":
        # 瑞兽（简化麒麟）：身 + 头 + 独角 + 尾
        body = pygame.Rect(int(cx - inner.w * 0.26), int(cy - inner.h * 0.02), int(inner.w * 0.52), int(inner.h * 0.22))
        _rect(surf, carve_soft, body, radius=int(body.h * 0.5), width=5)
        _circle(surf, carve_soft, (body.right - body.w * 0.06, body.top - inner.h * 0.04), inner.w * 0.10, 4)
        _line(surf, carve, (body.right - body.w * 0.02, body.top - inner.h * 0.10),
              (body.right + body.w * 0.06, body.top - inner.h * 0.28), 5)
        _line(surf, carve_soft, (body.left, body.top + body.h * 0.2),
              (body.left - inner.w * 0.12, body.top - inner.h * 0.14), 5)
        for dx in (0.22, 0.44):
            _line(surf, carve_soft, (body.left + body.w * dx, body.bottom),
                  (body.left + body.w * dx, body.bottom + inner.h * 0.13), 5)

    else:  # huiwen
        # 回纹：沿四边连续的回字纹，中间留白
        size = int(min(inner.w, inner.h) * 0.13)
        step = int(size * 1.55)
        x = inner.left + size
        while x + size < inner.right:
            for y in (inner.top + 6, inner.bottom - size - 6):
                _rect(surf, carve_soft, (x, y, size, size), 4)
                _rect(surf, carve, (x + 6, y + 6, size - 12, size - 12), 3)
            x += step
        y = inner.top + size + step
        while y + size < inner.bottom - size:
            for x in (inner.left + 6, inner.right - size - 6):
                _rect(surf, carve_soft, (x, y, size, size), 4)
                _rect(surf, carve, (x + 6, y + 6, size - 12, size - 12), 3)
            y += step


# --------------------------------------------------------------------------
# 4. 院门（立面）
# --------------------------------------------------------------------------

def _roof(surf, x, y, w, h, overhang=18):
    """简化的硬山/歇山屋面：一条弧线 + 瓦垄。"""
    top = y - h
    _poly(surf, TILE_BLUE, [(x - overhang, y), (x + w + overhang, y), (x + w - 10, top), (x + 10, top)])
    _poly(surf, _shade(TILE_BLUE, 0.82), [(x - overhang, y), (x + w + overhang, y), (x + w + overhang, y + 8), (x - overhang, y + 8)])
    # 瓦垄
    n = max(3, int(w / 14))
    for i in range(n + 1):
        px = x - overhang + (w + overhang * 2) * i / n
        _line(surf, TILE_DARK, (px, y), (x + 10 + (w - 20) * i / n, top), 2)
    # 正脊
    _rect(surf, _shade(TILE_DARK, 0.9), (x + 6, top - 6, w - 12, 7))


def _paint_gate(surf, r, variant):
    _brick_ground(surf, r, 0.80)
    wall_y = int(r.top + r.h * 0.30)
    wall_h = int(r.h * 0.52)

    if variant == "guangliang":
        # 广亮大门：门道深，门扇退进
        _rect(surf, _shade(BRICK, 1.0), (r.left, wall_y, r.w, wall_h))
        bay = pygame.Rect(int(r.centerx - r.w * 0.30), wall_y, int(r.w * 0.60), wall_h)
        _roof(surf, bay.left, bay.top, bay.w, int(r.h * 0.17), 22)
        _rect(surf, _shade(INK, 0.25), bay)                              # 门道阴影
        _rect(surf, _shade(BRICK, 0.9), (bay.left, bay.top, bay.w, bay.h), width=4)
        door = pygame.Rect(int(bay.centerx - bay.w * 0.22), bay.top + bay.h * 0.24, int(bay.w * 0.44), int(bay.h * 0.62))
        _rect(surf, CINNABAR, door)
        _rect(surf, _shade(CINNABAR, 0.7), door, width=4)
        _line(surf, _shade(CINNABAR, 0.6), (door.centerx, door.top), (door.centerx, door.bottom), 3)
        for i in range(4):  # 门簪
            _rect(surf, GOLD, (bay.centerx - 30 + i * 18, bay.top + 6, 8, 10))

    elif variant == "jinzhu":
        # 金柱大门：门扇贴在前檐，门道浅
        _rect(surf, _shade(BRICK, 1.0), (r.left, wall_y, r.w, wall_h))
        bay = pygame.Rect(int(r.centerx - r.w * 0.26), wall_y, int(r.w * 0.52), wall_h)
        _roof(surf, bay.left, bay.top, bay.w, int(r.h * 0.15), 18)
        _rect(surf, _shade(BRICK, 0.86), bay, width=4)
        door = pygame.Rect(int(bay.centerx - bay.w * 0.26), int(bay.top + bay.h * 0.28), int(bay.w * 0.52), int(bay.h * 0.58))
        _rect(surf, CINNABAR, door)
        _rect(surf, _shade(CINNABAR, 0.72), door, width=4)
        _line(surf, _shade(CINNABAR, 0.62), (door.centerx, door.top), (door.centerx, door.bottom), 3)
        # 前檐柱
        for dx in (-1, 1):
            _rect(surf, _shade(WOOD, 0.9), (bay.centerx + dx * bay.w * 0.34 - 6, bay.top, 12, bay.h))

    elif variant == "ruyi":
        # 如意门：单间、砖雕门楣
        _rect(surf, _shade(BRICK, 1.0), (r.left, wall_y, r.w, wall_h))
        bay = pygame.Rect(int(r.centerx - r.w * 0.18), wall_y, int(r.w * 0.36), wall_h)
        _roof(surf, bay.left, bay.top, bay.w, int(r.h * 0.12), 16)
        _rect(surf, _shade(BRICK, 0.88), bay, width=4)
        # 门楣砖雕
        lintel = pygame.Rect(bay.left + 8, bay.top + 10, bay.w - 16, int(bay.h * 0.16))
        _rect(surf, _shade(BRICK, 0.94), lintel)
        _rect(surf, _shade(BRICK, 0.78), lintel, width=2)
        for i in range(5):
            _circle(surf, _shade(BRICK, 0.84), (lintel.left + 18 + i * (lintel.w - 36) / 4, lintel.centery), 5, 2)
        door = pygame.Rect(int(bay.centerx - bay.w * 0.24), lintel.bottom + 8, int(bay.w * 0.48), int(bay.h * 0.5))
        _rect(surf, CINNABAR, door)
        _rect(surf, _shade(CINNABAR, 0.7), door, width=4)

    else:  # suqiang
        # 随墙门：墙上直接开门洞，没有门楼
        _rect(surf, _shade(BRICK, 1.0), (r.left, wall_y, r.w, wall_h))
        door = pygame.Rect(int(r.centerx - r.w * 0.13), int(wall_y + wall_h * 0.28), int(r.w * 0.26), int(wall_h * 0.72))
        _rect(surf, _shade(INK, 0.35), door.inflate(10, 6))
        _rect(surf, CINNABAR, door)
        _rect(surf, _shade(CINNABAR, 0.7), door, width=4)
        _line(surf, _shade(CINNABAR, 0.6), (door.centerx, door.top), (door.centerx, door.bottom), 3)

    # 台阶
    steps = pygame.Rect(int(r.centerx - r.w * 0.16), int(wall_y + wall_h), int(r.w * 0.32), int(r.h * 0.09))
    _rect(surf, _shade(STONE, 0.95), steps)
    _line(surf, STONE_DARK, (steps.left, steps.centery), (steps.right, steps.centery), 2)


# --------------------------------------------------------------------------
# 5. 檐部
# --------------------------------------------------------------------------

def _paint_eave(surf, r, variant):
    _rect(surf, PAPER, r)

    if variant == "feiyan":
        # 飞檐翘角：一条上翘的曲线 + 瓦垄
        pts = []
        for i in range(41):
            t = i / 40
            x = r.left + r.w * (0.08 + 0.82 * t)
            y = r.top + r.h * (0.68 - 0.32 * t ** 2.2)
            pts.append((x, y))
        pygame.draw.lines(surf, TILE_BLUE, False, [(int(x), int(y)) for x, y in pts], 34)
        _lines(surf, TILE_DARK, pts, 5)
        # 翘角
        tip = pts[-1]
        _line(surf, TILE_BLUE, tip, (tip[0] + 30, tip[1] - 40), 16)
        _line(surf, TILE_DARK, tip, (tip[0] + 30, tip[1] - 40), 4)
        # 瓦垄短线
        for i in range(1, 11):
            t = i / 11
            x = r.left + r.w * (0.08 + 0.82 * t)
            y = r.top + r.h * (0.68 - 0.32 * t ** 2.2)
            _line(surf, TILE_DARK, (x, y - 10), (x, y - 40), 2)

    elif variant == "qiangji":
        # 戗脊：一条斜脊 + 脊上小兽
        a = (r.left + r.w * 0.08, r.top + r.h * 0.24)
        b = (r.left + r.w * 0.90, r.top + r.h * 0.84)
        _line(surf, TILE_DARK, a, b, 28)
        _line(surf, _shade(TILE_DARK, 0.82), a, b, 10)
        for i in range(6):
            t = 0.14 + i * 0.14
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t - 15
            _circle(surf, _shade(TILE_DARK, 1.12), (x, y), 11)
            _circle(surf, _shade(TILE_DARK, 0.9), (x, y), 11, 2)

    elif variant == "wadang":
        # 瓦当：正圆的瓦头 + 当面纹样
        cx, cy = r.center
        rad = min(r.w, r.h) * 0.36
        _circle(surf, _shade(TILE_BLUE, 1.06), (cx, cy), rad * 1.16)
        _circle(surf, TILE_BLUE, (cx, cy), rad)
        _circle(surf, TILE_DARK, (cx, cy), rad, 6)
        _circle(surf, TILE_DARK, (cx, cy), rad * 0.60, 4)
        for ang in range(0, 360, 90):
            x = cx + math.cos(math.radians(ang + 45)) * rad * 0.40
            y = cy + math.sin(math.radians(ang + 45)) * rad * 0.40
            _circle(surf, TILE_DARK, (x, y), rad * 0.13, 4)
        _circle(surf, TILE_DARK, (cx, cy), rad * 0.15)

    else:  # dishui
        # 滴水：下垂的尖角瓦，顶部一排弧
        cx = r.centerx
        top = r.top + r.h * 0.24
        shape = [
            (cx - r.w * 0.26, top), (cx + r.w * 0.26, top),
            (cx + r.w * 0.12, top + r.h * 0.40), (cx, top + r.h * 0.54),
            (cx - r.w * 0.12, top + r.h * 0.40),
        ]
        _poly(surf, TILE_BLUE, shape)
        _poly(surf, TILE_DARK, shape, 6)
        for i in range(-2, 3):  # 顶部的筒瓦弧
            _circle(surf, _shade(TILE_BLUE, 1.12), (cx + i * r.w * 0.10, top - 6), r.w * 0.05, 4)


# --------------------------------------------------------------------------
# 对外接口
# --------------------------------------------------------------------------

PAINTERS = {
    "window": _paint_window,
    "doorstone": _paint_doorstone,
    "brick": _paint_brick,
    "gate": _paint_gate,
    "eave": _paint_eave,
}


def draw_component(target: pygame.Surface, rect: pygame.Rect, category: str, variant: str):
    """把构件画进 rect（超采样后平滑缩小）。"""
    w, h = max(8, rect.w), max(8, rect.h)
    big = pygame.Surface((w * SS, h * SS), pygame.SRCALPHA)
    r = pygame.Rect(0, 0, w * SS, h * SS)
    big.set_clip(r)               # 整幅卡片裁切，屋檐出挑也不会溢出
    _paper(big, r)
    PAINTERS[category](big, r, variant)
    big.set_clip(None)
    small = pygame.transform.smoothscale(big, (w, h))
    target.blit(small, rect.topleft)
