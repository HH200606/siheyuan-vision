/* =============================================================================
   四合檐影 · 逻辑层（纯函数式状态机，不碰 DOM 与 Canvas，可在 node 里直接测）

   状态机：
     title → playing ──答对/答错──→ feedback ──继续──→ playing
                        └── 本关题目答完 → levelClear → 下一关
                        └── 生命耗尽 / 超时 → levelFailed → 重玩本关
                        最后一关通关 → finished（评级 + 证书）
   ========================================================================== */

(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./content.js'));
  else {
    const mod = factory(root.SYY);
    root.SYY = Object.assign(root.SYY || {}, {
      Engine: mod.Engine,
      buildQuestions: mod.buildQuestions,
      makeRng: mod.makeRng,
    });
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function (C) {
  'use strict';

  const { CATEGORIES, LEVELS, RULES, RANKS } = C;

  /** 可复现的伪随机（mulberry32），保证同一 seed 的题序一致 */
  function makeRng(seed) {
    let a = seed >>> 0;
    return function () {
      a += 0x6d2b79f5;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function shuffle(list, rng) {
    const out = list.slice();
    for (let i = out.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [out[i], out[j]] = [out[j], out[i]];
    }
    return out;
  }

  const categoryKeys = Object.keys(CATEGORIES);

  function buildQuestions(category, count, rng) {
    const pool = category === 'mixed' ? categoryKeys : [category];
    const out = [];
    let last = null;

    for (let i = 0; i < count; i++) {
      const cat = category === 'mixed' ? pool[i % pool.length] : category;
      const variants = Object.keys(CATEGORIES[cat].variants);
      const choices = variants.filter((v) => v !== last);
      const key = (choices.length ? choices : variants)[Math.floor(rng() * (choices.length || variants.length))];
      last = key;
      out.push({ category: cat, answer: key, options: shuffle(variants, rng) });
    }
    return out;
  }

  class Engine {
    constructor(opts) {
      const o = opts || {};
      this.levels = o.levels || LEVELS;
      this.rng = o.rng || makeRng(20261020);
      this.phase = 'title';
      this.levelIdx = 0;
      this.questions = [];
      this.qIdx = 0;
      this.score = 0;
      this.combo = 0;
      this.bestCombo = 0;
      this.lives = 0;
      this.correctCount = 0;
      this.answeredCount = 0;
      this.timeLeft = null;
      this.results = [];
      this.failReason = '';
    }

    get level() { return this.levels[this.levelIdx]; }

    get question() {
      if (this.phase === 'playing' || this.phase === 'feedback') {
        return this.questions[this.qIdx] || null;
      }
      return null;
    }

    start(atLevel = 0) {
      this.score = 0;
      this.bestCombo = 0;
      this.results = [];
      this.levelIdx = Math.max(0, Math.min(this.levels.length - 1, atLevel | 0));
      this._beginLevel();
    }

    _beginLevel() {
      const lv = this.level;
      this.questions = buildQuestions(lv.category, lv.questions, this.rng);
      this.qIdx = 0;
      this.lives = lv.lives;
      this.combo = 0;
      this.correctCount = 0;
      this.answeredCount = 0;
      this.timeLeft = lv.seconds ? Number(lv.seconds) : null;
      this.failReason = '';
      this.phase = 'playing';
    }

    answer(index) {
      if (this.phase !== 'playing') throw new Error('不在答题状态');
      const q = this.question;
      const correct = index === q.options.indexOf(q.answer);

      this.answeredCount += 1;
      let points = 0;

      if (correct) {
        this.combo = Math.min(RULES.comboCap, this.combo + 1);
        this.bestCombo = Math.max(this.bestCombo, this.combo);
        points = RULES.basePoints + (this.combo - 1) * RULES.comboStep;
        this.score += points;
        this.correctCount += 1;
      } else {
        this.combo = 0;
        this.lives = Math.max(0, this.lives - 1);
      }

      if (this.lives <= 0) this.failReason = '生命耗尽';
      this.phase = 'feedback';

      return {
        correct,
        points,
        answerIndex: q.options.indexOf(q.answer),
        answerName: CATEGORIES[q.category].variants[q.answer].name,
        note: CATEGORIES[q.category].variants[q.answer].note,
        combo: this.combo,
        lives: this.lives,
      };
    }

    advance() {
      if (this.phase === 'feedback') {
        if (this.lives <= 0) {
          this.phase = 'levelFailed';
          this.failReason = this.failReason || '生命耗尽';
          return;
        }
        this.qIdx += 1;
        if (this.qIdx >= this.questions.length) this._finishLevel();
        else this.phase = 'playing';
        return;
      }

      if (this.phase === 'levelClear') {
        if (this.levelIdx + 1 >= this.levels.length) this.phase = 'finished';
        else {
          this.levelIdx += 1;
          this._beginLevel();
        }
        return;
      }

      if (this.phase === 'levelFailed') this._beginLevel();
    }

    _finishLevel() {
      this.results.push({
        name: this.level.name,
        correct: this.correctCount,
        total: this.questions.length,
      });
      this.phase = this.correctCount > 0 ? 'levelClear' : 'levelFailed';
    }

    update(dt) {
      if (this.phase !== 'playing' || this.timeLeft === null) return;
      this.timeLeft = Math.max(0, this.timeLeft - dt);
      if (this.timeLeft <= 0) {
        this.phase = 'levelFailed';
        this.failReason = '时间到';
      }
    }

    maxScore() {
      let total = 0;
      for (const lv of this.levels) {
        for (let i = 0; i < lv.questions; i++) {
          const combo = Math.min(RULES.comboCap, i + 1);
          total += RULES.basePoints + (combo - 1) * RULES.comboStep;
        }
      }
      return total;
    }

    rating() {
      const ratio = this.score / Math.max(1, this.maxScore());
      return RANKS.find((r) => ratio >= r.min) || RANKS[RANKS.length - 1];
    }
  }

  return { Engine, buildQuestions, makeRng };
});
