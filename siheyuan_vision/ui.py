# -*- coding: utf-8 -*-
"""界面与交互：宣纸底、墨线框、朱砂印章，全部用 pygame 绘制。"""

from __future__ import annotations

import datetime
import os
import random

import pygame

from . import art
from .config import (
    CINNABAR, COMBO_CAP, FONT_CANDIDATES, FPS, GOLD, HEIGHT, INK, INK_MUTE,
    INK_SOFT, PAPER, PAPER_DEEP, TILE_BLUE, TITLE, WIDTH,
)
from .game import Game
from .questions import CATEGORIES

# --------------------------------------------------------------------------
# 字体
# --------------------------------------------------------------------------

_FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
_font_cache: dict = {}


def font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _font_cache:
        if _FONT_PATH:
            f = pygame.font.Font(_FONT_PATH, size)
            f.set_bold(bold)
        else:
            f = pygame.font.Font(None, size)
            f.set_bold(bold)
        _font_cache[key] = f
    return _font_cache[key]


def text(surf, s, pos, size=22, color=INK, center=False, bold=False, shadow=False):
    img = font(size, bold).render(s, True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    if shadow:
        sh = font(size, bold).render(s, True, (0, 0, 0, 40))
        surf.blit(sh, rect.move(1, 2))
    surf.blit(img, rect)
    return rect


def wrap(s, f, max_w):
    lines, cur = [], ""
    for ch in s:
        if f.size(cur + ch)[0] > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def paragraph(surf, s, pos, max_w, size=20, color=INK_SOFT, gap=8, bold=False):
    f = font(size, bold)
    x, y = pos
    for line in wrap(s, f, max_w):
        surf.blit(f.render(line, True, color), (x, y))
        y += f.get_height() + gap
    return y


# --------------------------------------------------------------------------
# 纸与框
# --------------------------------------------------------------------------

def paper_background(surf):
    surf.fill(PAPER)
    rng = random.Random(3)
    for _ in range(1400):
        x, y = rng.randrange(WIDTH), rng.randrange(HEIGHT)
        surf.set_at((x, y), (236, 226, 206))
    # 四角淡淡的墨晕
    haze = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(6):
        pygame.draw.rect(haze, (120, 100, 70, 6), (0, 0, WIDTH, HEIGHT), 40 + i * 26)
    surf.blit(haze, (0, 0))


def ink_frame(surf, rect, width=2, inset=10):
    pygame.draw.rect(surf, INK, rect, width)
    pygame.draw.rect(surf, INK_SOFT, rect.inflate(-inset * 2, -inset * 2), 1)


def seal(surf, center, size=34, label="印"):
    """朱砂小印，用作生命与装饰。"""
    r = pygame.Rect(0, 0, size, size)
    r.center = center
    pygame.draw.rect(surf, CINNABAR, r, border_radius=4)
    pygame.draw.rect(surf, (120, 40, 32), r, 2, border_radius=4)
    text(surf, label, center, int(size * 0.5), (250, 240, 225), center=True, bold=True)


# --------------------------------------------------------------------------
# 应用
# --------------------------------------------------------------------------

class App:
    def __init__(self, capture_dir: str | None = None):
        pygame.init()
        pygame.display.set_caption(TITLE)
        flags = 0
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        self.clock = pygame.time.Clock()
        self.game = Game()
        self.running = True
        self.hover = -1
        self.capture_dir = capture_dir
        self.cert_saved = None

    # ------------------------------------------------------------- 主循环
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.game.update(dt)
            self.render()
            pygame.display.flip()
        pygame.quit()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                self.on_key(e.key)
            elif e.type == pygame.MOUSEMOTION:
                self.hover = self.hit_option(e.pos)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.on_click(e.pos)

    def on_key(self, key):
        g = self.game
        if key == pygame.K_ESCAPE:
            self.running = False
            return
        if g.phase == "title":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                g.start()
            return
        if g.phase == "playing" and key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            self.submit(key - pygame.K_1)
            return
        if g.phase == "feedback" and key in (pygame.K_RETURN, pygame.K_SPACE):
            g.advance()
            return
        if g.phase in ("level_clear", "level_failed") and key in (pygame.K_RETURN, pygame.K_SPACE):
            g.advance()
            return
        if g.phase == "finished":
            if key == pygame.K_r:
                g.start()
            elif key == pygame.K_s:
                self.save_certificate()

    def submit(self, idx: int):
        """答题并记住这次结果，供反馈层绘制。"""
        fb = self.game.answer(idx)
        self._last_choice = idx
        self._last_correct = fb.correct
        self._last_points = fb.points

    def on_click(self, pos):
        g = self.game
        if g.phase == "title":
            g.start()
        elif g.phase == "playing":
            idx = self.hit_option(pos)
            if idx >= 0:
                self.submit(idx)
        elif g.phase == "feedback":
            g.advance()
        elif g.phase in ("level_clear", "level_failed"):
            g.advance()
        elif g.phase == "finished":
            if self.cert_rect().collidepoint(pos):
                self.save_certificate()
            elif self.btn_rect("again").collidepoint(pos):
                g.start()

    # ------------------------------------------------------------- 布局
    def option_rects(self):
        w, h = 470, 58
        gap_x, gap_y = 40, 16
        left = (WIDTH - (w * 2 + gap_x)) / 2
        top = 572
        return [
            pygame.Rect(left, top, w, h),
            pygame.Rect(left + w + gap_x, top, w, h),
            pygame.Rect(left, top + h + gap_y, w, h),
            pygame.Rect(left + w + gap_x, top + h + gap_y, w, h),
        ]

    def hit_option(self, pos):
        if self.game.phase != "playing":
            return -1
        for i, r in enumerate(self.option_rects()):
            if r.collidepoint(pos):
                return i
        return -1

    def cert_rect(self):
        return pygame.Rect(WIDTH // 2 - 310, 136, 620, 424)

    def btn_rect(self, name):
        if name == "again":
            return pygame.Rect(WIDTH // 2 - 230, 604, 210, 52)
        if name == "save":
            return pygame.Rect(WIDTH // 2 + 20, 604, 210, 52)
        return pygame.Rect(0, 0, 0, 0)

    # ------------------------------------------------------------- 绘制入口
    def render(self):
        paper_background(self.screen)
        phase = self.game.phase
        if phase == "title":
            self.draw_title()
        elif phase in ("playing", "feedback"):
            self.draw_play()
            if phase == "feedback":
                self.draw_feedback()
        elif phase == "level_clear":
            self.draw_level_clear()
        elif phase == "level_failed":
            self.draw_level_failed()
        elif phase == "finished":
            self.draw_finished()

    # ------------------------------------------------------------- 标题
    def draw_title(self):
        s = self.screen
        # 顶部檐口装饰
        pygame.draw.polygon(s, TILE_BLUE, [(60, 120), (WIDTH - 60, 120), (WIDTH - 110, 78), (110, 78)])
        pygame.draw.line(s, (40, 52, 70), (110, 78), (WIDTH - 110, 78), 4)
        for i in range(1, 24):
            x = 110 + (WIDTH - 220) * i / 24
            pygame.draw.line(s, (52, 68, 92), (x, 78), (x, 120), 1)

        text(s, "四合檐影", (WIDTH // 2, 220), 76, INK, center=True, bold=True)
        text(s, "BEIJING SIHEYUAN · COMPONENT QUIZ", (WIDTH // 2, 272), 18, INK_MUTE, center=True)
        paragraph(s, "化身古建筑观察员：看一张构件特写，从四个名字里挑出它。答对连击，答错不扣分但要听一段讲究。",
                  (WIDTH // 2 - 330, 320), 660, 22, INK_SOFT, 10)

        # 三个小图示
        icons = [("window", "bubujin", "窗棂"), ("doorstone", "baogu", "门墩"), ("eave", "wadang", "檐部")]
        for i, (cat, var, label) in enumerate(icons):
            r = pygame.Rect(WIDTH // 2 - 330 + i * 230, 400, 190, 150)
            art.draw_component(s, r, cat, var)
            ink_frame(s, r, 2, 6)
            text(s, label, (r.centerx, r.bottom + 18), 18, INK_MUTE, center=True)

        btn = pygame.Rect(WIDTH // 2 - 130, 620, 260, 58)
        pygame.draw.rect(s, CINNABAR, btn, border_radius=6)
        pygame.draw.rect(s, (110, 36, 28), btn, 2, border_radius=6)
        text(s, "开 始 闯 关", btn.center, 24, (252, 244, 230), center=True, bold=True)
        text(s, "回车 / 空格 也可以", (WIDTH // 2, 700), 16, INK_MUTE, center=True)

    # ------------------------------------------------------------- 答题
    def draw_play(self):
        s, g = self.screen, self.game
        level = g.level

        # 顶栏
        bar = pygame.Rect(40, 28, WIDTH - 80, 64)
        pygame.draw.rect(s, PAPER_DEEP, bar, border_radius=8)
        ink_frame(s, bar, 2, 8)
        text(s, f"第 {level['id']} 关 · {level['name']}", (bar.left + 24, bar.top + 20), 24, INK, bold=True)

        q = g.question
        if q:
            text(s, f"{g.q_idx + 1} / {len(g.questions)}", (bar.centerx - 70, bar.top + 22), 20, INK_MUTE)

        # 分数、连击、生命（标签在上，数值在下，互不压字）
        text(s, "分数", (bar.right - 316, bar.top + 8), 13, INK_MUTE)
        text(s, f"{g.score}", (bar.right - 316, bar.top + 24), 26, INK, bold=True)
        text(s, "连击", (bar.right - 226, bar.top + 8), 13, INK_MUTE)
        text(s, f"×{g.combo}" if g.combo else "×0", (bar.right - 226, bar.top + 24), 26,
             CINNABAR if g.combo else INK_MUTE, bold=True)
        for i in range(level["lives"]):
            cx = bar.right - 120 + i * 40
            if i < g.lives:
                seal(s, (cx, bar.top + 32), 30, "生")
            else:
                lost = pygame.Rect(0, 0, 30, 30)
                lost.center = (cx, bar.top + 32)
                pygame.draw.rect(s, INK_MUTE, lost, 2, border_radius=4)

        # 计时（第 5 关）
        if g.time_left is not None:
            text(s, f"剩余 {int(g.time_left)}s", (bar.centerx + 90, bar.top + 22), 20,
                 CINNABAR if g.time_left < 15 else INK_SOFT, bold=True)

        # 构件图
        card = pygame.Rect(WIDTH // 2 - 300, 118, 600, 400)
        pygame.draw.rect(s, PAPER_DEEP, card.move(0, 6), border_radius=6)
        art.draw_component(s, card, q.category, q.answer)
        ink_frame(s, card, 3, 12)

        # 题面
        text(s, "这是什么构件？", (WIDTH // 2, 538), 26, INK, center=True, bold=True)

        # 选项
        reveal = g.phase == "feedback"
        for i, r in enumerate(self.option_rects()):
            chosen_correct = reveal and i == q.answer_index
            is_wrong_pick = reveal and i == getattr(self, "_last_choice", -1) and i != q.answer_index
            bg = (252, 246, 234)
            border = INK_SOFT
            if chosen_correct:
                bg, border = (226, 240, 222), (74, 120, 76)
            elif is_wrong_pick:
                bg, border = (246, 226, 222), CINNABAR
            elif self.hover == i and not reveal:
                bg, border = (247, 238, 220), CINNABAR
            pygame.draw.rect(s, bg, r, border_radius=6)
            pygame.draw.rect(s, border, r, 2, border_radius=6)
            text(s, f"{i + 1}", (r.left + 22, r.centery - 12), 20, INK_MUTE, bold=True)
            text(s, q.option_name(i), (r.left + 54, r.centery - 14), 23, INK, bold=chosen_correct)

        text(s, "点选项，或按 1 / 2 / 3 / 4", (WIDTH // 2, 716), 15, INK_MUTE, center=True)

    # ------------------------------------------------------------- 反馈
    def draw_feedback(self):
        s = self.screen
        g = self.game
        q = g.question
        panel = pygame.Rect(WIDTH // 2 - 340, 200, 680, 300)
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((20, 16, 12, 120))
        s.blit(veil, (0, 0))
        pygame.draw.rect(s, (250, 244, 231), panel, border_radius=10)
        pygame.draw.rect(s, INK, panel, 3, border_radius=10)
        pygame.draw.rect(s, INK_SOFT, panel.inflate(-18, -18), 1, border_radius=8)

        ok = getattr(self, "_last_correct", False)
        text(s, "答对了" if ok else "答错了", (panel.centerx, panel.top + 44), 30,
             (58, 104, 62) if ok else CINNABAR, center=True, bold=True)
        text(s, f"正确答案：{q.answer_name}", (panel.centerx, panel.top + 84), 22, INK, center=True)

        y = paragraph(s, q.note(), (panel.left + 40, panel.top + 118), panel.w - 80, 19, INK_SOFT, 9)

        if getattr(self, "_last_points", 0) > 0:
            text(s, f"+{self._last_points} 分" + (f"    连击 ×{g.combo}" if g.combo > 1 else ""),
                 (panel.centerx, panel.bottom - 40), 22, GOLD, center=True, bold=True)
        else:
            text(s, f"生命 -1（剩 {g.lives}）", (panel.centerx, panel.bottom - 40), 20, INK_MUTE, center=True)

        text(s, "点任意处 / 回车 继续", (panel.centerx, panel.bottom + 28), 16, INK_MUTE, center=True)

    # ------------------------------------------------------------- 关卡结算
    def draw_level_clear(self):
        s, g = self.screen, self.game
        text(s, "本关通过", (WIDTH // 2, 220), 54, INK, center=True, bold=True)
        text(s, g.level["name"], (WIDTH // 2, 272), 22, INK_MUTE, center=True)
        text(s, f"{g.correct_count} / {len(g.questions)} 题", (WIDTH // 2, 330), 30, CINNABAR, center=True, bold=True)
        text(s, f"总分 {g.score}    最高连击 ×{g.best_combo}", (WIDTH // 2, 384), 22, INK_SOFT, center=True)
        text(s, "点击 / 回车 继续", (WIDTH // 2, 470), 20, INK, center=True, bold=True)

    def draw_level_failed(self):
        s, g = self.screen, self.game
        text(s, "本关未过", (WIDTH // 2, 220), 54, CINNABAR, center=True, bold=True)
        text(s, g.fail_reason or "生命耗尽", (WIDTH // 2, 276), 24, INK_SOFT, center=True)
        text(s, "这一关的题目会重新出，再来一次", (WIDTH // 2, 330), 20, INK_MUTE, center=True)
        text(s, "点击 / 回车 重玩本关", (WIDTH // 2, 420), 22, INK, center=True, bold=True)

    # ------------------------------------------------------------- 终局 + 证书
    def draw_finished(self):
        s, g = self.screen, self.game
        rank, desc = g.rating()

        head = pygame.Rect(40, 28, WIDTH - 80, 92)
        pygame.draw.rect(s, PAPER_DEEP, head, border_radius=8)
        ink_frame(s, head, 2, 8)
        text(s, "五 关 全 通", (head.centerx, head.top + 28), 28, INK, center=True, bold=True)
        text(s, f"总分 {g.score} / {g.max_score()}　·　评级 {rank}", (head.centerx, head.top + 64), 20,
             CINNABAR, center=True, bold=True)

        # 证书
        cert = self.cert_rect()
        pygame.draw.rect(s, (250, 245, 233), cert, border_radius=8)
        pygame.draw.rect(s, CINNABAR, cert, 4, border_radius=8)
        pygame.draw.rect(s, (196, 170, 130), cert.inflate(-24, -24), 3, border_radius=6)

        text(s, "电 子 纪 念 证 书", (cert.centerx, cert.top + 52), 28, INK, center=True, bold=True)
        text(s, "四合檐影 · 古建筑构件识别", (cert.centerx, cert.top + 88), 15, INK_MUTE, center=True)
        text(s, "兹证明", (cert.centerx, cert.top + 122), 15, INK_MUTE, center=True)
        text(s, "古 建 筑 观 察 员", (cert.centerx, cert.top + 162), 30, INK, center=True, bold=True)
        text(s, f"以 {g.score} 分的成绩通关五关，识得窗棂、门墩、砖雕、院门与檐部构件。",
             (cert.centerx, cert.top + 204), 17, INK_SOFT, center=True)
        text(s, f"等级：{rank}　·　{desc}", (cert.centerx, cert.top + 240), 17, CINNABAR, center=True, bold=True)

        text(s, datetime.date.today().strftime("%Y 年 %m 月 %d 日"), (cert.left + 56, cert.bottom - 54), 15, INK_MUTE)
        seal(s, (cert.right - 62, cert.bottom - 52), 44, "檐")

        # 各关成绩一行带过
        summary = " · ".join(f"{r.correct}/{r.total}" for r in g.results)
        text(s, f"各关成绩：{summary}", (WIDTH // 2, 580), 16, INK_MUTE, center=True)

        # 按钮
        again = self.btn_rect("again")
        pygame.draw.rect(s, INK, again, border_radius=6)
        text(s, "再 玩 一 次", again.center, 20, (250, 244, 231), center=True, bold=True)

        save = self.btn_rect("save")
        pygame.draw.rect(s, (252, 246, 234), save, border_radius=6)
        pygame.draw.rect(s, INK_SOFT, save, 2, border_radius=6)
        text(s, "保存证书（S）", save.center, 19, INK, center=True, bold=True)

        if self.cert_saved:
            text(s, f"已保存：{os.path.basename(self.cert_saved)}", (WIDTH // 2, 676), 15, INK_MUTE, center=True)

    # ------------------------------------------------------------- 存证书
    def save_certificate(self):
        rect = self.cert_rect().inflate(30, 30)
        rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        sub = self.screen.subsurface(rect).copy()
        path = os.path.join(os.getcwd(), "certificate.png")
        pygame.image.save(sub, path)
        self.cert_saved = path
        return path
