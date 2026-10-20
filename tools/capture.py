# -*- coding: utf-8 -*-
"""无头截图：把每一屏都渲染成 PNG，用于 README 与自查。

用法：
    python tools/capture.py [输出目录]
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from siheyuan_vision.ui import App  # noqa: E402


def snapshot(app, name, outdir):
    app.render()
    path = os.path.join(outdir, f"{name}.png")
    pygame.image.save(app.screen, path)
    print("saved", path)
    return path


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "screenshots")
    os.makedirs(outdir, exist_ok=True)

    app = App()
    snapshot(app, "01-title", outdir)

    # 第 1 关：答对一题，停在反馈层
    app.game.start()
    snapshot(app, "02-level1", outdir)
    app.submit(app.game.question.answer_index)
    snapshot(app, "03-feedback", outdir)
    app.game.advance()

    # 打到第 5 关，展示限时界面
    while app.game.phase != "finished":
        g = app.game
        if g.phase == "playing":
            app.submit(g.question.answer_index)
        elif g.phase == "feedback":
            g.advance()
        elif g.phase == "level_clear":
            g.advance()
        elif g.phase == "level_failed":
            g.advance()
        if g.level_idx == 4 and g.phase == "playing":
            snapshot(app, "04-level5", outdir)
            # 把这一关答完，走向终局
            while g.phase != "finished":
                if g.phase == "playing":
                    app.submit(g.question.answer_index)
                elif g.phase == "feedback":
                    g.advance()
                elif g.phase == "level_clear":
                    g.advance()
                elif g.phase == "level_failed":
                    g.advance()
            break

    snapshot(app, "05-finished", outdir)
    pygame.quit()


if __name__ == "__main__":
    main()
