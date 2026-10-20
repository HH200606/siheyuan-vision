/* =============================================================================
   四合檐影 · 美术层（Canvas 2D）

   和 Pygame 版共用一套画法与比例：所有绘制都在 600×400 的逻辑坐标里完成，
   由 app.js 用 setTransform 映射到真实像素，因此两端观感一致、也不会因为
   窗口尺寸变化而变形。
   ========================================================================== */

(function (root) {
  'use strict';

  const W = 600;
  const H = 400;

  const C = {
    paper: '#f3ead8',
    paperDeep: '#e8dcc6',
    ink: '#262220',
    inkSoft: '#5c544c',
    inkMute: '#8c8276',
    cinnabar: '#9e3a2e',
    gold: '#ba924e',
    tile: '#4a607e',
    tileDark: '#34445c',
    wood: '#926846',
    woodDark: '#68482e',
    brick: '#968e84',
    brickDark: '#78706a',
    stone: '#b0aaa0',
    stoneDark: '#8c867c',
    leaf: '#688460',
  };

  function hexToRgb(hex) {
    const n = parseInt(hex.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function shade(hex, f) {
    const [r, g, b] = hexToRgb(hex);
    const c = (v) => Math.max(0, Math.min(255, Math.round(v * f)));
    return `rgb(${c(r)},${c(g)},${c(b)})`;
  }

  function alpha(hex, a) {
    const [r, g, b] = hexToRgb(hex);
    return `rgba(${r},${g},${b},${a})`;
  }

  // ---------------------------------------------------------------- 基础图元

  function rect(ctx, color, x, y, w, h, r) {
    ctx.beginPath();
    if (r) ctx.roundRect(x, y, w, h, r);
    else ctx.rect(x, y, w, h);
    ctx.fillStyle = color;
    ctx.fill();
  }

  function strokeRect(ctx, color, x, y, w, h, lw, r) {
    ctx.beginPath();
    if (r) ctx.roundRect(x, y, w, h, r);
    else ctx.rect(x, y, w, h);
    ctx.lineWidth = lw || 2;
    ctx.strokeStyle = color;
    ctx.stroke();
  }

  function line(ctx, color, x1, y1, x2, y2, lw) {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.lineWidth = lw || 1;
    ctx.strokeStyle = color;
    ctx.stroke();
  }

  function circle(ctx, color, cx, cy, r, lw) {
    ctx.beginPath();
    ctx.arc(cx, cy, Math.max(0.5, r), 0, Math.PI * 2);
    if (lw) {
      ctx.lineWidth = lw;
      ctx.strokeStyle = color;
      ctx.stroke();
    } else {
      ctx.fillStyle = color;
      ctx.fill();
    }
  }

  function poly(ctx, color, pts, lw) {
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
    ctx.closePath();
    if (lw) {
      ctx.lineWidth = lw;
      ctx.strokeStyle = color;
      ctx.stroke();
    } else {
      ctx.fillStyle = color;
      ctx.fill();
    }
  }

  // ---------------------------------------------------------------- 背景

  function paper(ctx) {
    rect(ctx, C.paper, 0, 0, W, H);
    // 纸纹：稀疏小点
    let seed = 7;
    const rnd = () => {
      seed = (seed * 1103515245 + 12345) & 0x7fffffff;
      return seed / 0x7fffffff;
    };
    ctx.fillStyle = shade(C.paper, 0.965);
    for (let i = 0; i < 260; i++) {
      const x = rnd() * W;
      const y = rnd() * H;
      ctx.beginPath();
      ctx.arc(x, y, 0.8 + rnd() * 0.8, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function brickGround(ctx, topRatio) {
    const split = H * topRatio;
    rect(ctx, C.paper, 0, 0, W, split);
    rect(ctx, shade(C.brick, 1.06), 0, split, W, H - split);

    const bw = W / 9;
    const bh = H * 0.055;
    const rows = Math.floor(split / bh);
    for (let row = 0; row <= rows; row++) {
      const y = row * bh;
      line(ctx, shade(C.brick, 0.92), 0, y, W, y, 1);
      const offset = row % 2 ? bw / 2 : 0;
      for (let x = offset; x < W; x += bw) line(ctx, shade(C.brick, 0.92), x, y, x, y + bh, 1);
    }
    for (let i = 1; i <= 5; i++) {
      const y = split + (H - split) * Math.pow(i / 6, 1.6);
      line(ctx, shade(C.brick, 0.9), 0, y, W, y, 1);
    }
  }

  // ---------------------------------------------------------------- 窗棂

  function windowFrame(ctx) {
    const fw = W * 0.8;
    const fh = H * 0.7;
    const x = (W - fw) / 2;
    const y = H * 0.4 - fh / 2;

    rect(ctx, shade(C.wood, 0.82), x, y + 6, fw, fh, 6);
    rect(ctx, C.wood, x, y, fw, fh, 4);
    strokeRect(ctx, shade(C.wood, 1.12), x, y, fw, fh, 3, 4);

    const iw = fw * 0.9;
    const ih = fh * 0.9;
    const ix = x + (fw - iw) / 2;
    const iy = y + (fh - ih) / 2;
    rect(ctx, shade(C.paper, 1.02), ix, iy, iw, ih, 2);
    strokeRect(ctx, shade(C.paper, 0.97), ix, iy, iw, ih, 8);
    return { x: ix, y: iy, w: iw, h: ih };
  }

  function latticeBubujin(ctx, r) {
    const cols = 4;
    const rows = 3;
    const cw = r.w / cols;
    const ch = r.h / rows;
    const gap = 13;
    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        const x = r.x + i * cw + gap / 2;
        const y = r.y + j * ch + gap / 2;
        strokeRect(ctx, C.woodDark, x, y, cw - gap, ch - gap, 5);
        if ((i + j) % 2 === 0) line(ctx, C.woodDark, x + cw - gap, y + (ch - gap) / 2, x + cw - gap + gap, y + (ch - gap) / 2, 5);
        else line(ctx, C.woodDark, x + (cw - gap) / 2, y, x + (cw - gap) / 2, y - gap, 5);
      }
    }
  }

  function latticeBinglie(ctx, r) {
    let seed = 11;
    const rnd = () => {
      seed = (seed * 1103515245 + 12345) & 0x7fffffff;
      return seed / 0x7fffffff;
    };
    const pts = [];
    for (let i = 0; i < 52; i++) pts.push([r.x + rnd() * r.w, r.y + rnd() * r.h]);
    pts.push([r.x, r.y], [r.x + r.w, r.y], [r.x, r.y + r.h], [r.x + r.w, r.y + r.h]);

    for (const p of pts) {
      const near = pts
        .map((q) => [q, (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2])
        .sort((a, b) => a[1] - b[1])
        .slice(1, 4);
      for (const [q] of near) line(ctx, C.woodDark, p[0], p[1], q[0], q[1], 4);
    }
  }

  function latticeGuibei(ctx, r) {
    const rad = Math.min(r.w, r.h) / 8.5;
    const dx = rad * 1.5;
    const dy = rad * Math.sqrt(3);
    let col = 0;
    for (let x = r.x; x < r.x + r.w + rad; x += dx) {
      const y0 = r.y + (col % 2 ? dy / 2 : 0);
      for (let y = y0; y < r.y + r.h + rad; y += dy) {
        const pts = [];
        for (let k = 0; k < 6; k++) {
          const a = (Math.PI / 3) * k;
          pts.push([x + rad * Math.cos(a), y + rad * Math.sin(a)]);
        }
        poly(ctx, C.woodDark, pts, 4);
      }
      col += 1;
    }
  }

  function latticeDenglong(ctx, r) {
    const rad = Math.min(r.w, r.h) * 0.36;
    const cx = r.x + r.w / 2;
    const cy = r.y + r.h / 2;

    rect(ctx, C.woodDark, cx - rad * 0.78, cy - rad - 16, rad * 1.56, 11);
    rect(ctx, C.woodDark, cx - rad * 0.78, cy + rad + 5, rad * 1.56, 11);
    circle(ctx, C.woodDark, cx, cy, rad, 5);
    circle(ctx, C.woodDark, cx, cy, rad * 0.56, 3);
    for (const d of [-0.5, 0, 0.5]) {
      line(ctx, C.woodDark, cx + d * rad, cy - rad * 0.92, cx + d * rad, cy + rad * 0.92, 4);
    }
    line(ctx, C.woodDark, cx - rad * 0.92, cy, cx + rad * 0.92, cy, 3);
  }

  const LATTICES = {
    bubujin: latticeBubujin,
    binglie: latticeBinglie,
    guibei: latticeGuibei,
    denglong: latticeDenglong,
  };

  function paintWindow(ctx, variant) {
    brickGround(ctx, 0.78);
    const inner = windowFrame(ctx);
    ctx.save();
    ctx.beginPath();
    ctx.rect(inner.x, inner.y, inner.w, inner.h);
    ctx.clip();
    LATTICES[variant](ctx, inner);
    ctx.restore();
    // 窗台
    const sillW = inner.w * 1.18;
    const sillH = H * 0.035;
    const sillX = inner.x + inner.w / 2 - sillW / 2;
    const sillY = inner.y + inner.h + inner.h * 0.07;
    rect(ctx, shade(C.stone, 1.0), sillX, sillY, sillW, sillH, 3);
    strokeRect(ctx, C.stoneDark, sillX, sillY, sillW, sillH, 2, 3);
  }

  // ---------------------------------------------------------------- 门墩

  function stoneBase(ctx, widthRatio) {
    const w = W * (widthRatio || 0.66);
    const h = H * 0.18;
    const x = (W - w) / 2;
    const y = H * 0.7;
    rect(ctx, C.stoneDark, x, y + 6, w, h, 4);
    rect(ctx, C.stone, x, y, w, h, 4);
    strokeRect(ctx, shade(C.stone, 0.86), x, y, w, h, 2, 4);
    return { x, y, w, h };
  }

  function paintDoorstone(ctx, variant) {
    brickGround(ctx, 0.68);
    const base = stoneBase(ctx, 0.66);
    const cx = base.x + base.w / 2;
    const top = base.y;
    const h = base.h;

    if (variant === 'shizi') {
      const bw = base.w * 0.4;
      const bh = h * 1.7;
      const bx = cx - bw / 2;
      const by = top + 4 - bh;
      rect(ctx, shade(C.stone, 0.96), bx, by, bw, bh, bw * 0.28);
      strokeRect(ctx, shade(C.stone, 0.86), bx, by, bw, bh, 3, bw * 0.28);

      const hr = bw * 0.44;
      const hx = cx;
      const hy = by - hr * 0.35;
      for (let a = 0; a < 360; a += 45) {
        const rad = (a * Math.PI) / 180;
        circle(ctx, shade(C.stone, 0.9), hx + Math.cos(rad) * hr * 0.95, hy + Math.sin(rad) * hr * 0.95, hr * 0.38);
      }
      circle(ctx, shade(C.stone, 1.04), hx, hy, hr);
      circle(ctx, shade(C.stone, 0.82), hx, hy, hr, 3);
      for (const d of [-0.34, 0.34]) circle(ctx, C.inkSoft, hx + d * hr, hy - hr * 0.18, hr * 0.12);
      circle(ctx, C.inkSoft, hx, hy + hr * 0.22, hr * 0.1);
      for (const d of [-0.3, 0.3]) {
        const pw = bw * 0.24;
        const ph = h * 0.34;
        rect(ctx, shade(C.stone, 1.0), cx + d * bw - pw / 2, top + 6 - ph, pw, ph, 6);
      }
    } else if (variant === 'baogu') {
      const rad = h * 0.86;
      const cy = top - rad * 0.62;
      rect(ctx, shade(C.stone, 0.92), cx - rad * 0.5, cy, rad, top - cy + 4);
      circle(ctx, C.stone, cx, cy, rad);
      circle(ctx, shade(C.stone, 0.86), cx, cy, rad, 4);
      circle(ctx, shade(C.stone, 0.9), cx, cy, rad * 0.66, 3);
      circle(ctx, shade(C.stone, 0.86), cx, cy, rad * 0.16);
      for (const d of [-1, 1]) {
        const ccx = cx + d * rad * 1.02;
        const ccy = cy + rad * 0.12;
        circle(ctx, shade(C.stone, 0.94), ccx, ccy, rad * 0.3, 3);
        circle(ctx, shade(C.stone, 0.84), ccx, ccy, rad * 0.16, 2);
      }
    } else if (variant === 'xiangxing') {
      const bw = base.w * 0.82;
      const bh = h * 2.0;
      const bx = cx - bw / 2;
      const by = top + 4 - bh;
      rect(ctx, C.stone, bx, by, bw, bh, 3);
      strokeRect(ctx, shade(C.stone, 0.84), bx, by, bw, bh, 4, 3);

      const pw = bw * 0.76;
      const ph = bh * 0.74;
      const px = cx - pw / 2;
      const py = by + bh * 0.13;
      strokeRect(ctx, shade(C.stone, 0.92), px, py, pw, ph, 3);

      const hy = py + ph * 0.28;
      for (const d of [-0.9, 0, 0.9]) {
        circle(ctx, shade(C.stone, 0.86), px + pw / 2 + d * pw * 0.16, hy, pw * 0.09, 3);
      }
      line(ctx, shade(C.stone, 0.86), px + pw / 2, hy, px + pw / 2, py + ph - 10, 3);
    } else {
      const widths = [0.98, 0.84, 0.92, 0.76, 0.86];
      const heights = [0.22, 0.14, 0.3, 0.14, 0.2];
      let y = top + 4;
      widths.forEach((wr, i) => {
        const bw = base.w * wr;
        const bh = h * heights[i] * 2;
        const bx = cx - bw / 2;
        y -= bh;
        rect(ctx, shade(C.stone, i % 2 ? 0.94 : 1.0), bx, y, bw, bh);
        strokeRect(ctx, shade(C.stone, 0.82), bx, y, bw, bh, 2);
      });
      for (let i = 0; i < 3; i++) {
        circle(ctx, shade(C.stone, 0.86), cx - base.w * 0.22 + i * base.w * 0.22, top - h * 0.9, h * 0.1, 2);
      }
    }
  }

  // ---------------------------------------------------------------- 砖雕

  function carvePanel(ctx) {
    const pw = W * 0.72;
    const ph = H * 0.72;
    const x = (W - pw) / 2;
    const y = H * 0.46 - ph / 2;
    rect(ctx, shade(C.brick, 1.16), x, y, pw, ph);
    strokeRect(ctx, shade(C.brick, 0.7), x, y, pw, ph, 7);

    const iw = pw * 0.86;
    const ih = ph * 0.86;
    const ix = x + (pw - iw) / 2;
    const iy = y + (ph - ih) / 2;
    strokeRect(ctx, shade(C.brick, 0.74), ix, iy, iw, ih, 2);
    return { x: ix, y: iy, w: iw, h: ih };
  }

  function paintBrick(ctx, variant) {
    brickGround(ctx, 0.86);
    const r = carvePanel(ctx);
    const cx = r.x + r.w / 2;
    const cy = r.y + r.h / 2;
    const carve = shade(C.brick, 0.62);
    const carveSoft = shade(C.brick, 0.8);

    if (variant === 'huacao') {
      [0.26, 0.19, 0.12].forEach((k, i) => {
        circle(ctx, i === 0 ? carve : carveSoft, cx, cy, r.w * k, 5);
      });
      for (let a = 0; a < 360; a += 45) {
        const rad = (a * Math.PI) / 180;
        circle(ctx, carveSoft, cx + Math.cos(rad) * r.w * 0.32, cy + Math.sin(rad) * r.w * 0.32, r.w * 0.075, 4);
      }
      for (const d of [-1, 1]) line(ctx, carveSoft, cx, cy, cx + d * r.w * 0.42, cy + r.h * 0.18, 5);
    } else if (variant === 'bogu') {
      poly(ctx, carveSoft, [
        [cx - r.w * 0.12, cy - r.h * 0.1],
        [cx - r.w * 0.05, cy - r.h * 0.34],
        [cx + r.w * 0.05, cy - r.h * 0.34],
        [cx + r.w * 0.12, cy - r.h * 0.1],
        [cx + r.w * 0.07, cy + r.h * 0.26],
        [cx - r.w * 0.07, cy + r.h * 0.26],
      ], 4);
      strokeRect(ctx, carveSoft, cx + r.w * 0.16, cy + r.h * 0.12, r.w * 0.24, r.h * 0.12, 4);
      strokeRect(ctx, carveSoft, cx + r.w * 0.14, cy + r.h * 0.26, r.w * 0.28, r.h * 0.09, 4);
      circle(ctx, carveSoft, cx - r.w * 0.3, cy + r.h * 0.2, r.w * 0.08, 4);
    } else if (variant === 'ruishou') {
      const bw = r.w * 0.52;
      const bh = r.h * 0.22;
      const bx = cx - bw / 2;
      const by = cy - r.h * 0.02;
      strokeRect(ctx, carveSoft, bx, by, bw, bh, 5, bh / 2);
      circle(ctx, carveSoft, bx + bw * 0.94, by - r.h * 0.04, r.w * 0.1, 4);
      line(ctx, carve, bx + bw * 0.98, by - r.h * 0.1, bx + bw * 1.06, by - r.h * 0.28, 5);
      line(ctx, carveSoft, bx, by + bh * 0.2, bx - r.w * 0.12, by - r.h * 0.14, 5);
      for (const d of [0.22, 0.44]) line(ctx, carveSoft, bx + bw * d, by + bh, bx + bw * d, by + bh + r.h * 0.13, 5);
    } else {
      const size = Math.min(r.w, r.h) * 0.13;
      const step = size * 1.55;
      for (let x = r.x + size; x + size < r.x + r.w; x += step) {
        for (const y of [r.y + 6, r.y + r.h - size - 6]) {
          strokeRect(ctx, carveSoft, x, y, size, size, 4);
          strokeRect(ctx, carve, x + 6, y + 6, size - 12, size - 12, 3);
        }
      }
      for (let y = r.y + size + step; y + size < r.y + r.h - size; y += step) {
        for (const x of [r.x + 6, r.x + r.w - size - 6]) {
          strokeRect(ctx, carveSoft, x, y, size, size, 4);
          strokeRect(ctx, carve, x + 6, y + 6, size - 12, size - 12, 3);
        }
      }
    }
  }

  // ---------------------------------------------------------------- 院门

  function roof(ctx, x, y, w, h, overhang) {
    const top = y - h;
    poly(ctx, C.tile, [
      [x - overhang, y], [x + w + overhang, y], [x + w - 10, top], [x + 10, top],
    ]);
    poly(ctx, shade(C.tile, 0.82), [
      [x - overhang, y], [x + w + overhang, y], [x + w + overhang, y + 8], [x - overhang, y + 8],
    ]);
    const n = Math.max(3, Math.round(w / 14));
    for (let i = 0; i <= n; i++) {
      const px = x - overhang + ((w + overhang * 2) * i) / n;
      line(ctx, C.tileDark, px, y, x + 10 + ((w - 20) * i) / n, top, 2);
    }
    rect(ctx, shade(C.tileDark, 0.9), x + 6, top - 6, w - 12, 7);
  }

  function paintGate(ctx, variant) {
    brickGround(ctx, 0.8);
    const wallY = H * 0.3;
    const wallH = H * 0.52;

    if (variant === 'guangliang') {
      rect(ctx, shade(C.brick, 1.0), 0, wallY, W, wallH);
      const bayW = W * 0.6;
      const bayX = (W - bayW) / 2;
      roof(ctx, bayX, wallY, bayW, H * 0.17, 22);
      rect(ctx, alpha('#000000', 0.55), bayX, wallY, bayW, wallH);
      strokeRect(ctx, shade(C.brick, 0.9), bayX, wallY, bayW, wallH, 4);
      const dw = bayW * 0.44;
      const dh = wallH * 0.62;
      const dx = bayX + (bayW - dw) / 2;
      const dy = wallY + wallH * 0.24;
      rect(ctx, C.cinnabar, dx, dy, dw, dh);
      strokeRect(ctx, shade(C.cinnabar, 0.7), dx, dy, dw, dh, 4);
      line(ctx, shade(C.cinnabar, 0.6), dx + dw / 2, dy, dx + dw / 2, dy + dh, 3);
      for (let i = 0; i < 4; i++) rect(ctx, C.gold, bayX + bayW / 2 - 30 + i * 18, wallY + 6, 8, 10);
    } else if (variant === 'jinzhu') {
      rect(ctx, shade(C.brick, 1.0), 0, wallY, W, wallH);
      const bayW = W * 0.52;
      const bayX = (W - bayW) / 2;
      roof(ctx, bayX, wallY, bayW, H * 0.15, 18);
      strokeRect(ctx, shade(C.brick, 0.86), bayX, wallY, bayW, wallH, 4);
      const dw = bayW * 0.52;
      const dh = wallH * 0.58;
      const dx = bayX + (bayW - dw) / 2;
      const dy = wallY + wallH * 0.28;
      rect(ctx, C.cinnabar, dx, dy, dw, dh);
      strokeRect(ctx, shade(C.cinnabar, 0.72), dx, dy, dw, dh, 4);
      line(ctx, shade(C.cinnabar, 0.62), dx + dw / 2, dy, dx + dw / 2, dy + dh, 3);
      for (const d of [-1, 1]) {
        rect(ctx, shade(C.wood, 0.9), bayX + bayW / 2 + (d * bayW) / 2.94 - 6, wallY, 12, wallH);
      }
    } else if (variant === 'ruyi') {
      rect(ctx, shade(C.brick, 1.0), 0, wallY, W, wallH);
      const bayW = W * 0.36;
      const bayX = (W - bayW) / 2;
      roof(ctx, bayX, wallY, bayW, H * 0.12, 16);
      strokeRect(ctx, shade(C.brick, 0.88), bayX, wallY, bayW, wallH, 4);

      const lh = wallH * 0.16;
      const lx = bayX + 8;
      const ly = wallY + 10;
      const lw = bayW - 16;
      rect(ctx, shade(C.brick, 0.94), lx, ly, lw, lh);
      strokeRect(ctx, shade(C.brick, 0.78), lx, ly, lw, lh, 2);
      for (let i = 0; i < 5; i++) {
        circle(ctx, shade(C.brick, 0.84), lx + 18 + (i * (lw - 36)) / 4, ly + lh / 2, 5, 2);
      }

      const dw = bayW * 0.48;
      const dh = wallH * 0.5;
      const dx = bayX + (bayW - dw) / 2;
      const dy = ly + lh + 8;
      rect(ctx, C.cinnabar, dx, dy, dw, dh);
      strokeRect(ctx, shade(C.cinnabar, 0.7), dx, dy, dw, dh, 4);
    } else {
      rect(ctx, shade(C.brick, 1.0), 0, wallY, W, wallH);
      const dw = W * 0.26;
      const dh = wallH * 0.72;
      const dx = (W - dw) / 2;
      const dy = wallY + wallH * 0.28;
      rect(ctx, alpha('#000000', 0.5), dx - 5, dy - 3, dw + 10, dh + 6);
      rect(ctx, C.cinnabar, dx, dy, dw, dh);
      strokeRect(ctx, shade(C.cinnabar, 0.7), dx, dy, dw, dh, 4);
      line(ctx, shade(C.cinnabar, 0.6), dx + dw / 2, dy, dx + dw / 2, dy + dh, 3);
    }

    const sw = W * 0.32;
    const sh = H * 0.09;
    const sx = (W - sw) / 2;
    const sy = wallY + wallH;
    rect(ctx, shade(C.stone, 0.95), sx, sy, sw, sh);
    line(ctx, C.stoneDark, sx, sy + sh / 2, sx + sw, sy + sh / 2, 2);
  }

  // ---------------------------------------------------------------- 檐部

  function paintEave(ctx, variant) {
    rect(ctx, C.paper, 0, 0, W, H);

    if (variant === 'feiyan') {
      const pts = [];
      for (let i = 0; i <= 40; i++) {
        const t = i / 40;
        pts.push([W * (0.08 + 0.82 * t), H * (0.68 - 0.32 * Math.pow(t, 2.2))]);
      }
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (const p of pts) ctx.lineTo(p[0], p[1]);
      ctx.lineWidth = 34;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.strokeStyle = C.tile;
      ctx.stroke();
      ctx.lineWidth = 5;
      ctx.strokeStyle = C.tileDark;
      ctx.stroke();

      const tip = pts[pts.length - 1];
      line(ctx, C.tile, tip[0], tip[1], tip[0] + 30, tip[1] - 40, 16);
      line(ctx, C.tileDark, tip[0], tip[1], tip[0] + 30, tip[1] - 40, 4);
      for (let i = 1; i <= 10; i++) {
        const t = i / 11;
        const x = W * (0.08 + 0.82 * t);
        const y = H * (0.68 - 0.32 * Math.pow(t, 2.2));
        line(ctx, C.tileDark, x, y - 10, x, y - 40, 2);
      }
    } else if (variant === 'qiangji') {
      const a = [W * 0.08, H * 0.24];
      const b = [W * 0.9, H * 0.84];
      line(ctx, C.tileDark, a[0], a[1], b[0], b[1], 28);
      line(ctx, shade(C.tileDark, 0.82), a[0], a[1], b[0], b[1], 10);
      for (let i = 0; i < 6; i++) {
        const t = 0.14 + i * 0.14;
        const x = a[0] + (b[0] - a[0]) * t;
        const y = a[1] + (b[1] - a[1]) * t - 15;
        circle(ctx, shade(C.tileDark, 1.12), x, y, 11);
        circle(ctx, shade(C.tileDark, 0.9), x, y, 11, 2);
      }
    } else if (variant === 'wadang') {
      const cx = W / 2;
      const cy = H / 2;
      const rad = Math.min(W, H) * 0.36;
      circle(ctx, shade(C.tile, 1.06), cx, cy, rad * 1.16);
      circle(ctx, C.tile, cx, cy, rad);
      circle(ctx, C.tileDark, cx, cy, rad, 6);
      circle(ctx, C.tileDark, cx, cy, rad * 0.6, 4);
      for (let a = 0; a < 360; a += 90) {
        const rad2 = ((a + 45) * Math.PI) / 180;
        circle(ctx, C.tileDark, cx + Math.cos(rad2) * rad * 0.4, cy + Math.sin(rad2) * rad * 0.4, rad * 0.13, 4);
      }
      circle(ctx, C.tileDark, cx, cy, rad * 0.15);
    } else {
      const cx = W / 2;
      const top = H * 0.24;
      const shape = [
        [cx - W * 0.26, top], [cx + W * 0.26, top],
        [cx + W * 0.12, top + H * 0.4], [cx, top + H * 0.54],
        [cx - W * 0.12, top + H * 0.4],
      ];
      poly(ctx, C.tile, shape);
      poly(ctx, C.tileDark, shape, 6);
      for (let i = -2; i <= 2; i++) {
        circle(ctx, shade(C.tile, 1.12), cx + i * W * 0.1, top - 6, W * 0.05, 4);
      }
    }
  }

  const PAINTERS = {
    window: paintWindow,
    doorstone: paintDoorstone,
    brick: paintBrick,
    gate: paintGate,
    eave: paintEave,
  };

  /** 在 ctx 当前的 600×400 变换下画一张构件卡 */
  function draw(ctx, category, variant) {
    ctx.save();
    paper(ctx);
    const painter = PAINTERS[category];
    if (painter) painter(ctx, variant);
    ctx.restore();
  }

  root.SYY = Object.assign(root.SYY || {}, { Art: { draw, W, H, colors: C } });
})(typeof window !== 'undefined' ? window : globalThis);
