# -*- coding: utf-8 -*-
"""冒烟测试：无头跑一遍交互（点击选项、存证书），确保事件与渲染不崩。"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from siheyuan_vision.ui import App  # noqa: E402


def run():
    app = App()
    g = app.game

    # 标题 → 点开始
    app.render()
    app.on_click((590, 649))
    assert g.phase == "playing", g.phase

    # 点第一个选项
    rect = app.option_rects()[0]
    app.on_click(rect.center)
    assert g.phase == "feedback", g.phase

    # 键盘继续
    app.on_key(pygame.K_RETURN)
    assert g.phase == "playing", g.phase

    # 数字键答题
    app.on_key(pygame.K_2)
    assert g.phase == "feedback", g.phase
    app.on_key(pygame.K_SPACE)

    # 打完整局（全对），进入结算
    guard = 0
    while g.phase != "finished" and guard < 400:
        guard += 1
        if g.phase == "playing":
            app.submit(g.question.answer_index)
        else:
            app.on_key(pygame.K_RETURN)

    assert g.phase == "finished", g.phase
    app.render()

    # 存证书
    path = app.save_certificate()
    assert os.path.exists(path), path
    app.render()
    print("smoke ok:", path, os.path.getsize(path), "bytes")
    pygame.quit()


if __name__ == "__main__":
    run()
