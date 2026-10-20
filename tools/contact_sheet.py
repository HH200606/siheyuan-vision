# -*- coding: utf-8 -*-
"""构件对照表：把每类的四个形制并排画出来，用于自查辨识度。"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from siheyuan_vision import art  # noqa: E402
from siheyuan_vision.config import HEIGHT, INK, INK_MUTE, PAPER, WIDTH  # noqa: E402
from siheyuan_vision.questions import CATEGORIES  # noqa: E402
from siheyuan_vision.ui import font  # noqa: E402


def main():
    outdir = os.path.join(ROOT, "docs", "screenshots")
    os.makedirs(outdir, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    for category, meta in CATEGORIES.items():
        screen.fill(PAPER)
        f = font(26, True)
        screen.blit(f.render(f"{meta['title']} · 四形制对照", True, INK), (40, 24))

        variants = list(meta["variants"].items())
        card_w, card_h = 250, 300
        gap = 28
        total = card_w * 4 + gap * 3
        left = (WIDTH - total) // 2
        for i, (key, v) in enumerate(variants):
            r = pygame.Rect(left + i * (card_w + gap), 90, card_w, card_h)
            art.draw_component(screen, r, category, key)
            pygame.draw.rect(screen, INK, r, 2)
            label = font(20, True).render(v["name"], True, INK)
            screen.blit(label, (r.centerx - label.get_width() // 2, r.bottom + 10))
            note_f = font(15)
            ys = r.bottom + 40
            line = ""
            for ch in v["note"]:
                if note_f.size(line + ch)[0] > card_w - 6 and line:
                    img = note_f.render(line, True, INK_MUTE)
                    screen.blit(img, (r.centerx - img.get_width() // 2, ys))
                    ys += 19
                    line = ch
                else:
                    line += ch
            if line:
                img = note_f.render(line, True, INK_MUTE)
                screen.blit(img, (r.centerx - img.get_width() // 2, ys))

        path = os.path.join(outdir, f"art-{category}.png")
        pygame.image.save(screen, path)
        print("saved", path)

    pygame.quit()


if __name__ == "__main__":
    main()
