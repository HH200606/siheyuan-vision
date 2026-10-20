/* Web 版逻辑层单测：node --test tests/web-engine.test.js */

const test = require('node:test');
const assert = require('node:assert/strict');

const { Engine, buildQuestions, makeRng } = require('../docs/js/engine.js');
const { CATEGORIES, LEVELS } = require('../docs/js/content.js');

function playThrough(g, perfect = true) {
  let guard = 0;
  while (g.phase !== 'finished' && guard++ < 500) {
    if (g.phase === 'playing') {
      const q = g.question;
      g.answer(perfect ? q.options.indexOf(q.answer) : (q.options.indexOf(q.answer) + 1) % 4);
    } else {
      g.advance();
    }
  }
}

test('出题：四个选项互不相同且包含答案', () => {
  for (const cat of Object.keys(CATEGORIES)) {
    const qs = buildQuestions(cat, 30, makeRng(1));
    for (const q of qs) {
      assert.equal(q.options.length, 4);
      assert.equal(new Set(q.options).size, 4);
      assert.ok(q.options.includes(q.answer));
      assert.equal(q.category, cat);
    }
  }
});

test('出题：不会连续出同一个形制', () => {
  const qs = buildQuestions('window', 60, makeRng(2));
  for (let i = 1; i < qs.length; i++) assert.notEqual(qs[i].answer, qs[i - 1].answer);
});

test('混合关：五类轮转出现', () => {
  const qs = buildQuestions('mixed', 10, makeRng(3));
  assert.equal(new Set(qs.map((q) => q.category)).size, Object.keys(CATEGORIES).length);
});

test('开始游戏：进入第一关并重置状态', () => {
  const g = new Engine({ rng: makeRng(0) });
  g.start();
  assert.equal(g.phase, 'playing');
  assert.equal(g.questions.length, LEVELS[0].questions);
  assert.equal(g.lives, LEVELS[0].lives);
  assert.equal(g.qIdx, 0);
});

test('答对：加分、连击 +1', () => {
  const g = new Engine({ rng: makeRng(0) });
  g.start();
  const fb = g.answer(g.question.options.indexOf(g.question.answer));
  assert.equal(fb.correct, true);
  assert.equal(g.score, 10);
  assert.equal(g.combo, 1);
  assert.ok(fb.note.length > 10);
});

test('连击加分并封顶 ×5', () => {
  const g = new Engine({ rng: makeRng(0) });
  g.start();
  let expected = 0;
  for (let i = 0; i < 6; i++) {
    if (g.phase !== 'playing') break;
    const combo = Math.min(5, i + 1);
    expected += 10 + (combo - 1) * 2;
    g.answer(g.question.options.indexOf(g.question.answer));
    g.advance();
  }
  assert.equal(g.score, expected);
  assert.ok(g.combo <= 5);
});

test('答错：不扣分，扣一条命，连击清零', () => {
  const g = new Engine({ rng: makeRng(0) });
  g.start();
  const q = g.question;
  const wrong = (q.options.indexOf(q.answer) + 1) % 4;
  const before = g.score;
  const fb = g.answer(wrong);
  assert.equal(fb.correct, false);
  assert.equal(g.score, before);
  assert.equal(g.lives, LEVELS[0].lives - 1);
  assert.equal(g.combo, 0);
});

test('生命耗尽：本关失败，重玩后复位', () => {
  const g = new Engine({ rng: makeRng(0) });
  g.start();
  for (let i = 0; i < LEVELS[0].lives; i++) {
    if (g.phase !== 'playing') break;
    const q = g.question;
    g.answer((q.options.indexOf(q.answer) + 1) % 4);
    g.advance();
  }
  assert.equal(g.phase, 'levelFailed');
  assert.equal(g.failReason, '生命耗尽');
  g.advance();
  assert.equal(g.phase, 'playing');
  assert.equal(g.lives, LEVELS[0].lives);
  assert.equal(g.qIdx, 0);
});

test('全对通关：满分且评级为大师', () => {
  const g = new Engine({ rng: makeRng(7) });
  g.start();
  playThrough(g, true);
  assert.equal(g.phase, 'finished');
  assert.equal(g.results.length, LEVELS.length);
  assert.equal(g.score, g.maxScore());
  assert.equal(g.rating().title, '大师');
});

test('超时：限时关失败', () => {
  const g = new Engine({ rng: makeRng(9) });
  g.start(4);
  assert.equal(g.level.id, 5);
  assert.notEqual(g.timeLeft, null);
  g.update(999);
  assert.equal(g.phase, 'levelFailed');
  assert.equal(g.failReason, '时间到');
});

test('满分是 476，评级分档正确', () => {
  const g = new Engine({ rng: makeRng(0) });
  assert.equal(g.maxScore(), 476);
  g.score = 476;
  assert.equal(g.rating().title, '大师');
  g.score = 300;
  assert.equal(g.rating().title, '匠人');
  g.score = 100;
  assert.equal(g.rating().title, '学徒');
});
