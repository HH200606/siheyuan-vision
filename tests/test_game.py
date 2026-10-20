# -*- coding: utf-8 -*-
"""逻辑单测：不依赖 pygame，可直接 python -m unittest 跑。"""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from siheyuan_vision.config import BASE_POINTS, COMBO_CAP, COMBO_STEP, LEVELS  # noqa: E402
from siheyuan_vision.game import Game  # noqa: E402
from siheyuan_vision.questions import CATEGORIES, build_questions  # noqa: E402


def new_game(seed: int = 0) -> Game:
    return Game(rng=random.Random(seed))


def play_through(g: Game, perfect: bool = True):
    """把整局打完（perfect=True 全对）。"""
    guard = 0
    while g.phase != "finished" and guard < 500:
        guard += 1
        if g.phase == "playing":
            q = g.question
            idx = q.answer_index if perfect else (q.answer_index + 1) % 4
            g.answer(idx)
        else:
            g.advance()


class QuestionTests(unittest.TestCase):
    def test_options_are_four_distinct_and_include_answer(self):
        rng = random.Random(1)
        for cat in CATEGORIES:
            for q in build_questions(cat, 20, rng):
                self.assertEqual(len(q.options), 4)
                self.assertEqual(len(set(q.options)), 4)
                self.assertIn(q.answer, q.options)
                self.assertEqual(q.category, cat)

    def test_no_immediate_repeat(self):
        rng = random.Random(2)
        qs = build_questions("window", 40, rng)
        for a, b in zip(qs, qs[1:]):
            self.assertNotEqual(a.answer, b.answer)

    def test_mixed_level_rotates_all_categories(self):
        rng = random.Random(3)
        qs = build_questions("mixed", 10, rng)
        self.assertEqual(len({q.category for q in qs}), len(CATEGORIES))

    def test_every_variant_has_note(self):
        for cat, meta in CATEGORIES.items():
            for key, variant in meta["variants"].items():
                self.assertTrue(variant["name"])
                self.assertGreaterEqual(len(variant["note"]), 15, f"{cat}/{key} 的科普太短")


class FlowTests(unittest.TestCase):
    def test_start_enters_first_level(self):
        g = new_game()
        g.start()
        self.assertEqual(g.phase, "playing")
        self.assertEqual(len(g.questions), LEVELS[0]["questions"])
        self.assertEqual(g.lives, LEVELS[0]["lives"])
        self.assertEqual(g.q_idx, 0)

    def test_correct_answer_scores_and_combo(self):
        g = new_game()
        g.start()
        fb = g.answer(g.question.answer_index)
        self.assertTrue(fb.correct)
        self.assertEqual(g.score, BASE_POINTS)
        self.assertEqual(g.combo, 1)
        self.assertTrue(fb.note)

    def test_combo_points_and_cap(self):
        g = new_game()
        g.start()
        expected = 0
        for i in range(6):
            if g.phase != "playing":
                break
            combo = min(COMBO_CAP, i + 1)
            expected += BASE_POINTS + (combo - 1) * COMBO_STEP
            g.answer(g.question.answer_index)
            g.advance()
        self.assertEqual(g.score, expected)
        self.assertLessEqual(g.combo, COMBO_CAP)

    def test_wrong_answer_no_penalty_but_lose_life(self):
        g = new_game()
        g.start()
        q = g.question
        before_score, before_lives = g.score, g.lives
        fb = g.answer((q.answer_index + 1) % 4)
        self.assertFalse(fb.correct)
        self.assertEqual(g.score, before_score)
        self.assertEqual(g.lives, before_lives - 1)
        self.assertEqual(g.combo, 0)

    def test_lives_exhausted_fails_level(self):
        g = new_game()
        g.start()
        for _ in range(LEVELS[0]["lives"]):
            if g.phase != "playing":
                break
            g.answer((g.question.answer_index + 1) % 4)
            g.advance()
        self.assertEqual(g.phase, "level_failed")
        self.assertEqual(g.fail_reason, "生命耗尽")

    def test_retry_level_resets_lives_and_questions(self):
        g = new_game()
        g.start()
        for _ in range(LEVELS[0]["lives"]):
            if g.phase != "playing":
                break
            g.answer((g.question.answer_index + 1) % 4)
            g.advance()
        g.advance()  # level_failed -> 重玩
        self.assertEqual(g.phase, "playing")
        self.assertEqual(g.lives, LEVELS[0]["lives"])
        self.assertEqual(g.q_idx, 0)

    def test_perfect_run_finishes_with_max_score(self):
        g = new_game(7)
        g.start()
        play_through(g, perfect=True)
        self.assertEqual(g.phase, "finished")
        self.assertEqual(len(g.results), len(LEVELS))
        self.assertEqual(g.score, g.max_score())
        self.assertEqual(g.rating()[0], "大师")

    def test_timeout_fails_timed_level(self):
        g = new_game(11)
        g.start()
        play_through(g, perfect=True)
        # 重新开始，直接推进到第 5 关
        g.start()
        guard = 0
        while g.level_idx < 4 and guard < 200:
            guard += 1
            if g.phase == "playing":
                g.answer(g.question.answer_index)
            else:
                g.advance()
        self.assertEqual(g.level_idx, 4)
        self.assertIsNotNone(g.time_left)
        g.update(10_000)
        self.assertEqual(g.phase, "level_failed")
        self.assertEqual(g.fail_reason, "时间到")

    def test_all_wrong_gives_lowest_rank(self):
        g = new_game(5)
        g.start()
        play_through(g, perfect=False)
        self.assertIn(g.rating()[0], ("学徒", "匠人"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
