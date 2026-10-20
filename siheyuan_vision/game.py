# -*- coding: utf-8 -*-
"""游戏状态机（纯逻辑，不依赖 pygame，方便无头测试）。

流程：
    title → playing --答对/答错--> feedback --继续--> playing …
                     └── 本关题目答完 → level_clear → 下一关
                     └── 生命耗尽 / 超时 → level_failed → 重玩本关
                     最后一关通关 → finished（出评级与证书）
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .config import BASE_POINTS, COMBO_CAP, COMBO_STEP, LEVELS, RANKS
from .questions import CATEGORIES, Question, build_questions


@dataclass
class Feedback:
    correct: bool
    answer_name: str
    note: str
    points: int = 0
    combo: int = 1
    lives: int = 0
    level_clear: bool = False
    level_failed: bool = False
    timed_out: bool = False


@dataclass
class LevelResult:
    name: str
    correct: int
    total: int
    time_used: float = 0.0


class Game:
    def __init__(self, levels=None, rng: random.Random | None = None):
        self.levels = list(levels or LEVELS)
        self.rng = rng or random.Random()
        self.phase = "title"
        self.level_idx = 0
        self.questions: list[Question] = []
        self.q_idx = 0
        self.score = 0
        self.combo = 0
        self.best_combo = 0
        self.lives = 0
        self.correct_count = 0
        self.answered_count = 0
        self.time_left = None
        self.results: list[LevelResult] = []
        self.fail_reason = ""
        self._level_started_at = 0.0

    # ------------------------------------------------------------ 关卡控制
    @property
    def level(self) -> dict:
        return self.levels[self.level_idx]

    @property
    def question(self) -> Question | None:
        if self.phase in ("playing", "feedback") and self.q_idx < len(self.questions):
            return self.questions[self.q_idx]
        return None

    def start(self):
        """从标题页进入第一关。"""
        self.score = 0
        self.best_combo = 0
        self.results = []
        self.level_idx = 0
        self._begin_level()

    def _begin_level(self):
        level = self.level
        self.questions = build_questions(level["category"], level["questions"], self.rng)
        self.q_idx = 0
        self.lives = level["lives"]
        self.combo = 0
        self.correct_count = 0
        self.answered_count = 0
        self.time_left = float(level["seconds"]) if level["seconds"] else None
        self.fail_reason = ""
        self.phase = "playing"

    def retry_level(self):
        self._begin_level()

    def advance(self):
        """feedback / level_clear 之后调用：进下一题或下一关。"""
        if self.phase == "feedback":
            if self.lives <= 0:
                self.phase = "level_failed"
                self.fail_reason = self.fail_reason or "生命耗尽"
                return
            self.q_idx += 1
            if self.q_idx >= len(self.questions):
                self._finish_level()
            else:
                self.phase = "playing"
            return

        if self.phase == "level_clear":
            if self.level_idx + 1 >= len(self.levels):
                self.phase = "finished"
            else:
                self.level_idx += 1
                self._begin_level()
            return

        if self.phase == "level_failed":
            self._begin_level()

    def _finish_level(self):
        level = self.level
        self.results.append(
            LevelResult(name=level["name"], correct=self.correct_count, total=len(self.questions))
        )
        self.phase = "level_clear" if self.correct_count > 0 else "level_failed"

    # ------------------------------------------------------------ 答题
    def answer(self, index: int) -> Feedback:
        """选择第 index 个选项（0-3）。"""
        q = self.question
        if q is None or self.phase != "playing":
            raise RuntimeError("当前不在答题状态")

        self.answered_count += 1
        correct = index == q.answer_index

        if correct:
            self.combo = min(COMBO_CAP, self.combo + 1)
            self.best_combo = max(self.best_combo, self.combo)
            points = BASE_POINTS + (self.combo - 1) * COMBO_STEP
            self.score += points
            self.correct_count += 1
        else:
            points = 0
            self.combo = 0
            self.lives = max(0, self.lives - 1)

        self.phase = "feedback"
        failed = self.lives <= 0
        if failed:
            self.fail_reason = "生命耗尽"

        return Feedback(
            correct=correct,
            answer_name=q.answer_name,
            note=q.note(),
            points=points,
            combo=CONFIG_COMBO(self.combo),
            lives=self.lives,
            level_clear=False,
            level_failed=failed,
        )

    # ------------------------------------------------------------ 时间
    def update(self, dt: float):
        if self.phase != "playing" or self.time_left is None:
            return
        self.time_left = max(0.0, self.time_left - dt)
        if self.time_left <= 0.0:
            self.phase = "level_failed"
            self.fail_reason = "时间到"

    # ------------------------------------------------------------ 结算
    def max_score(self) -> int:
        total = 0
        for level in self.levels:
            for i in range(level["questions"]):
                combo = min(COMBO_CAP, i + 1)
                total += BASE_POINTS + (combo - 1) * COMBO_STEP
        return total

    def accuracy(self) -> float:
        return self.correct_count / max(1, self.answered_count)

    def rating(self) -> tuple[str, str]:
        ratio = self.score / max(1, self.max_score())
        for threshold, title, desc in RANKS:
            if ratio >= threshold:
                return title, desc
        return RANKS[-1][1], RANKS[-1][2]

    def totals(self) -> dict:
        total_q = sum(len(c) for c in [self.questions]) if self.questions else 0
        return {
            "score": self.score,
            "max_score": self.max_score(),
            "best_combo": self.best_combo,
            "correct": sum(r.correct for r in self.results),
            "answered": sum(r.total for r in self.results),
            "level": self.level_idx + 1,
            "level_total": len(self.levels),
            "total_q": total_q,
        }


def CONFIG_COMBO(value: int) -> int:
    """连击对外展示的倍率：0 表示断了。"""
    return min(COMBO_CAP, value)


def category_meta(category: str) -> dict:
    return CATEGORIES[category]
