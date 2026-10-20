/* =============================================================================
   四合檐影 · 网页版交互层
   负责：画布缩放与绘制、HUD、选项、弹窗、结算与证书。
   游戏规则全部在 engine.js 里，这里只做「把状态画出来 + 把输入喂回去」。
   ========================================================================== */

(function () {
  'use strict';

  const { Engine, makeRng } = window.SYY;
  const Art = window.SYY.Art;
  const CATEGORIES = window.SYY.CATEGORIES;

  const el = (id) => document.getElementById(id);

  const canvas = el('card');
  const ctx = canvas.getContext('2d');
  const certCanvas = el('cert');
  const cctx = certCanvas.getContext('2d');

  const engine = new Engine({ rng: makeRng(20261020) });
  let lastChoice = -1;
  let lastFeedback = null;
  let optionKey = '';
  let lastTs = 0;
  let rafId = 0;

  const screens = {
    title: el('screenStart'),
    levelClear: el('screenClear'),
    levelFailed: el('screenFailed'),
    finished: el('screenFinished'),
  };

  /* ------------------------------- 画布 ---------------------------------- */

  function resizeCanvas() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    const cssW = canvas.clientWidth || 600;
    const cssH = (cssW * 2) / 3;
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    const s = (cssW * dpr) / Art.W;
    ctx.setTransform(s, 0, 0, s, 0, 0);
  }

  function drawCard() {
    const q = engine.question;
    ctx.save();
    ctx.clearRect(0, 0, Art.W, Art.H);
    if (q) Art.draw(ctx, q.category, q.answer);
    else Art.draw(ctx, 'window', 'bubujin');
    ctx.restore();
  }

  /* -------------------------------- HUD ---------------------------------- */

  function renderHud() {
    const lv = engine.level;
    el('hudLevel').textContent = `第 ${lv.id} 关 · ${lv.name}`;
    el('hudScore').textContent = String(engine.score);

    const combo = el('hudCombo');
    combo.textContent = `×${engine.combo}`;
    combo.parentElement.classList.toggle('is-zero', engine.combo === 0);

    const total = engine.questions.length || lv.questions;
    el('hudProgress').textContent = `${Math.min(engine.qIdx + 1, total)}/${total}`;

    const lives = el('hudLives');
    lives.innerHTML = '';
    for (let i = 0; i < lv.lives; i++) {
      const s = document.createElement('span');
      s.className = i < engine.lives ? 'seal' : 'seal seal--lost';
      s.textContent = i < engine.lives ? '生' : '';
      lives.appendChild(s);
    }

    const timer = el('hudTimer');
    if (engine.timeLeft === null) {
      timer.hidden = true;
    } else {
      timer.hidden = false;
      timer.textContent = `剩余 ${Math.ceil(engine.timeLeft)}s`;
    }
  }

  /* ------------------------------- 选项 ---------------------------------- */

  function rebuildOptions() {
    const q = engine.question;
    const box = el('options');
    box.innerHTML = '';
    if (!q) return;

    q.options.forEach((key, i) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'opt';
      btn.dataset.index = String(i);
      btn.innerHTML = `<span class="opt__num">${i + 1}</span><span>${CATEGORIES[q.category].variants[key].name}</span>`;
      btn.addEventListener('click', () => submit(i));
      box.appendChild(btn);
    });
  }

  function markOptions() {
    const q = engine.question;
    if (!q) return;
    const answerIdx = q.options.indexOf(q.answer);
    [...el('options').children].forEach((btn, i) => {
      btn.disabled = true;
      if (i === answerIdx) btn.classList.add('is-correct');
      if (i === lastChoice && i !== answerIdx) btn.classList.add('is-wrong');
    });
  }

  /* ------------------------------- 交互 ---------------------------------- */

  function submit(index) {
    if (engine.phase !== 'playing') return;
    lastChoice = index;
    lastFeedback = engine.answer(index);
    markOptions();
    showModal(lastFeedback);
  }

  function advance() {
    if (engine.phase === 'feedback') {
      engine.advance();
      hideModal();
    } else if (engine.phase === 'levelClear' || engine.phase === 'levelFailed') {
      engine.advance();
    }
    render();
    if (engine.phase === 'playing') drawCard();
  }

  function showModal(fb) {
    const modal = el('modal');
    const title = el('modalTitle');
    title.textContent = fb.correct ? '答对了' : '答错了';
    title.className = fb.correct ? 'good' : 'bad';
    el('modalAnswer').textContent = `正确答案：${fb.answerName}`;
    el('modalNote').textContent = fb.note;
    el('modalPoints').textContent = fb.correct
      ? `+${fb.points} 分${fb.combo > 1 ? `　连击 ×${fb.combo}` : ''}`
      : `生命 -1（剩 ${fb.lives}）`;
    modal.classList.add('is-open');
  }

  function hideModal() {
    el('modal').classList.remove('is-open');
  }

  /* ------------------------------- 屏幕 ---------------------------------- */

  function showScreen(name) {
    for (const [key, node] of Object.entries(screens)) {
      node.classList.toggle('is-open', key === name);
    }
  }

  function render() {
    renderHud();

    const phase = engine.phase;
    const q = engine.question;

    if (phase === 'title') {
      showScreen('title');
      return;
    }

    if (phase === 'playing' || phase === 'feedback') {
      showScreen(null);
      const key = `${engine.levelIdx}-${engine.qIdx}-${q ? q.answer : ''}`;
      if (key !== optionKey) {
        optionKey = key;
        rebuildOptions();
        drawCard();
      }
      el('ask').textContent = '这是什么构件？';
      if (phase === 'feedback') markOptions();
      return;
    }

    if (phase === 'levelClear') {
      el('clearScore').textContent = `${engine.correctCount} / ${engine.questions.length} 题`;
      el('clearDetail').textContent = `总分 ${engine.score}　最高连击 ×${engine.bestCombo}`;
      showScreen('levelClear');
      return;
    }

    if (phase === 'levelFailed') {
      el('failReason').textContent = engine.failReason || '生命耗尽';
      showScreen('levelFailed');
      return;
    }

    if (phase === 'finished') {
      renderFinish();
      showScreen('finished');
    }
  }

  /* ------------------------------- 证书 ---------------------------------- */

  function renderFinish() {
    const rank = engine.rating();
    el('finalLine').textContent = `总分 ${engine.score} / ${engine.maxScore()}　·　评级 ${rank.title}`;
    drawCertificate(rank);
  }

  function fitCanvasToBox(c, cssW) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    const ratio = c.height / c.width;
    const w = cssW;
    const h = w * ratio;
    c.style.width = '100%';
    c.style.height = 'auto';
    c.width = Math.round(w * dpr);
    c.height = Math.round(h * dpr);
    const s = (w * dpr) / 720;
    c.getContext('2d').setTransform(s, 0, 0, s, 0, 0);
  }

  function drawCertificate(rank) {
    fitCanvasToBox(certCanvas, certCanvas.parentElement.clientWidth || 720);
    const c = cctx;
    const W = 720;
    const H = 480;

    c.clearRect(0, 0, W, H);
    c.fillStyle = '#faf4e6';
    c.fillRect(0, 0, W, H);

    c.strokeStyle = '#9e3a2e';
    c.lineWidth = 6;
    c.strokeRect(10, 10, W - 20, H - 20);
    c.strokeStyle = '#c4aa82';
    c.lineWidth = 2;
    c.strokeRect(24, 24, W - 48, H - 48);

    c.textAlign = 'center';
    c.fillStyle = '#262220';
    c.font = '600 30px "Songti SC","Microsoft YaHei",serif';
    c.fillText('电 子 纪 念 证 书', W / 2, 86);

    c.font = '400 14px "Microsoft YaHei",sans-serif';
    c.fillStyle = '#8c8276';
    c.fillText('四合檐影 · 古建筑构件识别', W / 2, 116);
    c.fillText('兹证明', W / 2, 148);

    c.font = '700 34px "Songti SC","Microsoft YaHei",serif';
    c.fillStyle = '#262220';
    c.fillText('古 建 筑 观 察 员', W / 2, 200);

    c.font = '400 16px "Microsoft YaHei",sans-serif';
    c.fillStyle = '#5c544c';
    c.fillText(`以 ${engine.score} 分的成绩通关五关，识得窗棂、门墩、砖雕、院门与檐部构件。`, W / 2, 240);

    c.font = '700 17px "Microsoft YaHei",sans-serif';
    c.fillStyle = '#9e3a2e';
    c.fillText(`等级：${rank.title}　·　${rank.desc}`, W / 2, 274);

    c.textAlign = 'left';
    c.font = '400 14px "Microsoft YaHei",sans-serif';
    c.fillStyle = '#8c8276';
    const d = new Date();
    const stamp = `${d.getFullYear()} 年 ${String(d.getMonth() + 1).padStart(2, '0')} 月 ${String(d.getDate()).padStart(2, '0')} 日`;
    c.fillText(stamp, 70, H - 66);

    // 朱砂印
    c.fillStyle = '#9e3a2e';
    c.beginPath();
    c.roundRect(W - 118, H - 104, 52, 52, 6);
    c.fill();
    c.strokeStyle = '#7c2b22';
    c.lineWidth = 2;
    c.stroke();
    c.fillStyle = '#faf3e4';
    c.textAlign = 'center';
    c.font = '600 26px "Songti SC","Microsoft YaHei",serif';
    c.fillText('檐', W - 92, H - 66);
  }

  function saveCertificate() {
    const a = document.createElement('a');
    a.download = 'four-eaves-certificate.png';
    a.href = certCanvas.toDataURL('image/png');
    a.click();
  }

  /* ------------------------------- 主循环 -------------------------------- */

  function loop(ts) {
    const dt = lastTs ? Math.min((ts - lastTs) / 1000, 0.25) : 0;
    lastTs = ts;

    if (engine.phase === 'playing') {
      engine.update(dt);
      if (engine.phase === 'levelFailed') {
        render();
      } else if (engine.timeLeft !== null) {
        renderHud();
      }
    }
    rafId = requestAnimationFrame(loop);
  }

  /* ------------------------------- 事件 ---------------------------------- */

  function bindEvents() {
    el('btnStart').addEventListener('click', () => {
      engine.start();
      render();
      drawCard();
    });

    el('btnNext').addEventListener('click', advance);
    el('btnRetry').addEventListener('click', advance);
    el('btnContinue').addEventListener('click', advance);
    el('btnAgain').addEventListener('click', () => {
      engine.start();
      render();
      drawCard();
    });
    el('btnSave').addEventListener('click', saveCertificate);

    el('modal').addEventListener('click', (e) => {
      if (e.target === el('modal')) advance();
    });

    document.addEventListener('keydown', (e) => {
      const phase = engine.phase;

      if (phase === 'title' && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        engine.start();
        render();
        drawCard();
        return;
      }
      if (phase === 'playing' && ['1', '2', '3', '4'].includes(e.key)) {
        e.preventDefault();
        submit(Number(e.key) - 1);
        return;
      }
      if (phase === 'feedback' && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        advance();
        return;
      }
      if ((phase === 'levelClear' || phase === 'levelFailed') && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        advance();
        return;
      }
      if (phase === 'finished') {
        if (e.key === 'r' || e.key === 'R') {
          engine.start();
          render();
          drawCard();
        }
        if (e.key === 's' || e.key === 'S') saveCertificate();
      }
    });

    window.addEventListener('resize', () => {
      resizeCanvas();
      drawCard();
      if (engine.phase === 'finished') renderFinish();
    });

    if ('ResizeObserver' in window) {
      new ResizeObserver(() => {
        resizeCanvas();
        drawCard();
      }).observe(canvas.parentElement);
    }
  }

  /* ------------------------------- 启动 ---------------------------------- */

  function applyUrlState() {
    const params = new URLSearchParams(location.search);

    // ?end=1：直接看结算页（截图 / 分享用）
    if (params.get('end') === '1') {
      engine.start();
      let guard = 0;
      while (engine.phase !== 'finished' && guard++ < 400) {
        if (engine.phase === 'playing') {
          const q = engine.question;
          engine.answer(q.options.indexOf(q.answer));
        } else {
          engine.advance();
        }
      }
      return;
    }

    // ?lv=3：从第 3 关开始（试玩 / 截图用）
    const lv = Number(params.get('lv'));
    if (Number.isFinite(lv) && lv >= 1 && lv <= engine.levels.length) {
      engine.start(lv - 1);
    }
  }

  function init() {
    resizeCanvas();
    bindEvents();
    applyUrlState();
    render();
    drawCard();
    rafId = requestAnimationFrame(loop);

    // 调试 / 自动化测试用
    window.__syy = { engine, render, drawCard, submit, advance };
  }

  init();
})();
