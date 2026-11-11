// bg.js — painted backgrounds for the rubber-hose demo (cached watercolour canvases; never boil).
// Technique per the style's demo bg.js; all sets are new paintings for this film.
// World space: x 0..2560, y -220..1240. Characters own the extremes; sets live in the middle greys.
import * as T from './toon.js';
import { P } from './chars.js';
import { mulberry } from '/core/lib.js';
const { shape, stroke, ell, arc, rr, rect, spline } = T;

export function wash(pts, col, o = {}) {
  const g = T.g, Pth = shape(pts, { fill: col, stroke: false, boil: 0 });
  const rnd = mulberry(o.seed ?? 7);
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.clip(Pth);
  const bb = pts.map(p => T.tx(p[0], p[1])), xs = bb.map(p => p[0]), ys = bb.map(p => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const n = Math.min(40, Math.max(6, ((x1 - x0) * (y1 - y0)) / 26000 | 0));
  g.filter = 'blur(6px)';
  for (let i = 0; i < n; i++) { const r = 26 + rnd() * 110; g.fillStyle = rnd() > .5 ? `rgba(30,28,25,${.03 + rnd() * .05})` : `rgba(255,253,245,${.03 + rnd() * .05})`; g.beginPath(); g.ellipse(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0), r, r * (.5 + rnd() * .6), rnd() * 3, 0, 7); g.fill(); }
  if ((o.edge ?? .16) > 0) { g.filter = 'blur(5px)'; g.strokeStyle = `rgba(20,18,16,${o.edge ?? .16})`; g.lineWidth = 26; g.stroke(Pth); }
  g.filter = 'none'; g.restore();
  if (o.line !== false) T.outline(Pth, o.lw ?? 3.2, o.lineCol ?? '#2A2927');
  return Pth;
}
function paperGrain(g, w, h, seed = 3) {
  const rnd = mulberry(seed); g.setTransform(1, 0, 0, 1, 0, 0);
  for (let i = 0; i < w * h / 900; i++) { g.fillStyle = rnd() > .5 ? 'rgba(20,18,15,.06)' : 'rgba(255,255,250,.05)'; g.fillRect(rnd() * w, rnd() * h, 1 + rnd() * 2, 1 + rnd() * 2); }
}
function withCanvas(bg, fn) {
  const prev = T.g, oldB = T.BASE.slice(), oldL = T.S.lwScale, { PS, ox, oy } = bg;
  T.init(bg.cv); T.BASE.splice(0, 6, PS, 0, 0, PS, -ox * PS, -oy * PS); T.S.lwScale = PS; T.frame(0, { amp: 0 });
  const raw = () => T.g.setTransform(PS, 0, 0, PS, -ox * PS, -oy * PS);
  fn(T.g, raw); T.g.setTransform(1, 0, 0, 1, 0, 0);
  paperGrain(T.g, bg.cv.width, bg.cv.height, ox + 3);
  T.BASE.splice(0, 6, ...oldB); T.S.lwScale = oldL; T.init(prev.canvas);
}
function makeBG(x0, y0, x1, y1, PS) { const cv = document.createElement('canvas'); cv.width = Math.round((x1 - x0) * PS); cv.height = Math.round((y1 - y0) * PS); return { cv, ox: x0, oy: y0, PS, w: x1 - x0, h: y1 - y0 }; }
export function drawBG(sg, bg, cam, squash = 0, pivotY = 1080) {
  const z = cam.z, ox = 960 - cam.x * z, oy = 540 - cam.y * z;
  sg.save(); sg.setTransform(z, 0, 0, z, ox, oy);
  if (squash) { sg.translate(0, pivotY); sg.scale(1 - squash * .4, 1 + squash); sg.translate(0, -pivotY); }
  sg.drawImage(bg.cv, bg.ox, bg.oy, bg.w, bg.h); sg.restore();
}
export const camBase = cam => [cam.z, 0, 0, cam.z, 960 - cam.x * cam.z, 540 - cam.y * cam.z];

function wallpaper(g, raw, x0, x1, y0, y1, seed) {
  wash(rect(x0, y0, x1 - x0, y1 - y0), '#8C8981', { line: false, seed, edge: 0 });
  raw();
  for (let x = x0; x < x1; x += 64) { g.fillStyle = 'rgba(255,253,245,.07)'; g.fillRect(x, y0, 22, y1 - y0); }
  for (let x = x0 + 32; x < x1; x += 128) for (let y = y0 + 40; y < y1; y += 96) { g.fillStyle = 'rgba(30,28,24,.2)'; g.beginPath(); g.moveTo(x, y - 8); g.lineTo(x + 6, y); g.lineTo(x, y + 8); g.lineTo(x - 6, y); g.fill(); }
}
function floorBoards(g, raw, x0, x1, yF) {
  wash(rect(x0, yF, x1 - x0, 1260 - yF), '#6E6B64', { line: false, seed: 61, edge: 0 });
  raw(); g.strokeStyle = 'rgba(30,28,25,.35)'; g.lineWidth = 2.5;
  for (let y = yF + 44; y < 1260; y += 52) { g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke(); }
  wash(rect(x0, yF - 10, x1 - x0, 14), '#3F3E3A', { seed: 62, edge: 0 });
}

// ————— The evidence room (title / freeze / desk / doors) —————
export const ROOM = { floorY: 990, photoX: 1280, photoY: 430 };
export function paintRoom() {
  const bg = makeBG(-40, -220, 2600, 1260, 1.0);
  withCanvas(bg, (g, raw) => {
    wallpaper(g, raw, -60, 2620, -240, ROOM.floorY, 41);
    wash(rect(-60, 700, 2680, 290), '#7C7972', { line: false, seed: 42, edge: 0 });               // wainscot
    raw(); g.strokeStyle = 'rgba(30,28,25,.3)'; g.lineWidth = 2.5;
    for (let x = 20; x < 2600; x += 180) { g.beginPath(); g.moveTo(x, 716); g.lineTo(x, 974); g.stroke(); }
    wash(rect(-60, 690, 2680, 16), '#4A4844', { seed: 43, edge: 0 });
    // a cork evidence board, right of where the photo hangs (strings + pins painted; cards come in the scene layer)
    wash(rr(1760, 130, 700, 470, 10), '#5E5C57', { seed: 44 });
    wash(rr(1784, 154, 652, 422, 6), '#77746D', { seed: 45, edge: .22 });
    raw(); g.strokeStyle = 'rgba(35,33,30,.4)'; g.lineWidth = 2;
    g.beginPath(); g.moveTo(1830, 220); g.lineTo(2100, 380); g.lineTo(2330, 250); g.stroke();
    g.beginPath(); g.moveTo(2100, 380); g.lineTo(2260, 500); g.stroke();
    for (const [px, py] of [[1830, 220], [2100, 380], [2330, 250], [2260, 500]]) { g.fillStyle = '#2E2D2A'; g.beginPath(); g.arc(px, py, 7, 0, 7); g.fill(); }
    floorBoards(g, raw, -60, 2620, ROOM.floorY);
  });
  return bg;
}

// ————— The rainy lane + restaurant front (wide) —————
export const LANE = { floorY: 950, winX: 1280, winY: 470, winW: 620, winH: 430 };
export function paintLane() {
  const bg = makeBG(-40, -220, 2600, 1260, 1.0);
  withCanvas(bg, (g, raw) => {
    wash(rect(-60, -240, 2680, 700), '#4A4844', { line: false, seed: 51, edge: 0 });              // night sky band
    // neighbouring buildings (dark silhouettes, lit windows as pale slots)
    for (const [bx, bw, bh] of [[-40, 480, 800], [470, 330, 660], [1850, 360, 720], [2240, 380, 840]]) {
      wash(rect(bx, LANE.floorY - bh, bw, bh), '#3B3A37', { seed: bx, edge: .1 });
      raw(); g.fillStyle = 'rgba(241,238,230,.5)';
      for (let wy = LANE.floorY - bh + 50; wy < LANE.floorY - 90; wy += 92) for (let wx = bx + 36; wx < bx + bw - 50; wx += 84)
        if ((wx * 7 + wy * 13) % 3) g.fillRect(wx, wy, 34, 44);
    }
    // the restaurant block
    wash(rect(880, 130, 800, LANE.floorY - 130), '#6B6963', { seed: 52 });
    wash(rect(860, 104, 840, 34), '#3F3E3A', { seed: 53, edge: 0 });
    // awning over the window
    wash([[940, 268], [1620, 268], [1668, 330], [892, 330]], '#4A4844', { seed: 54 });
    raw(); g.fillStyle = 'rgba(241,238,230,.35)';
    for (let x = 950; x < 1640; x += 86) g.fillRect(x, 272, 40, 56);
    // the big window: warm pale glass (lit from inside), mullions dark
    wash(rect(LANE.winX - LANE.winW / 2, LANE.winY - LANE.winH / 2, LANE.winW, LANE.winH), '#C8C5BC', { seed: 55, edge: .2 });
    raw(); g.strokeStyle = '#2A2927'; g.lineWidth = 7;
    for (const fx of [-LANE.winW / 6, LANE.winW / 6]) { g.beginPath(); g.moveTo(LANE.winX + fx, LANE.winY - LANE.winH / 2); g.lineTo(LANE.winX + fx, LANE.winY + LANE.winH / 2); g.stroke(); }
    g.beginPath(); g.moveTo(LANE.winX - LANE.winW / 2, LANE.winY); g.lineTo(LANE.winX + LANE.winW / 2, LANE.winY); g.stroke();
    g.lineWidth = 10; g.strokeRect(LANE.winX - LANE.winW / 2, LANE.winY - LANE.winH / 2, LANE.winW, LANE.winH);
    // door at the right of the block + hanging sign (blank oval)
    wash(rr(1470, 560, 150, 390, 10), '#3F3E3A', { seed: 56 });
    wash(rr(1496, 592, 98, 130, 6), '#9A978F', { seed: 57, edge: .1 });
    raw(); g.strokeStyle = '#2A2927'; g.lineWidth = 5; g.beginPath(); g.moveTo(1010, 150); g.lineTo(1010, 196); g.stroke();
    wash(ell(1010, 236, 62, 40), '#77746D', { seed: 58 });
    // street: wet, with long pale reflection streaks under the window and lamps
    wash(rect(-60, LANE.floorY, 2680, 310), '#55534E', { line: false, seed: 59, edge: 0 });
    raw(); g.fillStyle = 'rgba(241,238,230,.16)';
    for (let x = LANE.winX - 280; x < LANE.winX + 280; x += 34) g.fillRect(x, LANE.floorY + 16, 15, 150 + (x * 37 % 60));
    for (const lx of [300, 2300]) { g.fillRect(lx - 6, LANE.floorY + 10, 12, 110); }
    wash(rect(-60, LANE.floorY - 8, 2680, 12), '#2E2D2A', { seed: 60, edge: 0 });
  });
  return bg;
}

// ————— The dining room (interior) —————
export const DIN = { floorY: 1020, tableY: 800 };
export function paintDining() {
  const bg = makeBG(-40, -220, 2600, 1260, 1.0);
  withCanvas(bg, (g, raw) => {
    wallpaper(g, raw, -60, 2620, -240, DIN.floorY, 71);
    wash(rect(-60, 760, 2680, 260), '#7C7972', { line: false, seed: 72, edge: 0 });
    wash(rect(-60, 750, 2680, 15), '#4A4844', { seed: 73, edge: 0 });
    // round window with rain on it, left
    wash(ell(430, 330, 128, 128), '#5E5C57', { seed: 74 });
    wash(ell(430, 330, 104, 104), '#9A978F', { seed: 75, edge: .2 });
    raw(); g.strokeStyle = 'rgba(35,33,30,.5)'; g.lineWidth = 3;
    for (let i = 0; i < 12; i++) { const rx = 352 + (i * 67) % 150, ry = 258 + (i * 41) % 130; g.beginPath(); g.moveTo(rx, ry); g.lineTo(rx - 3, ry + 14); g.stroke(); }
    // sideboard + jars, right
    wash(rect(1960, 620, 520, 26), '#4A4844', { seed: 76 });
    wash(rect(1990, 646, 34, 130), '#4A4844', { seed: 77 }); wash(rect(2390, 646, 34, 130), '#4A4844', { seed: 78 });
    for (const [jx, jh] of [[2050, 92], [2170, 118], [2300, 84]]) wash(rr(jx, 620 - jh, 76, jh, 14), '#B3B0A8', { seed: jx, edge: .1 });
    // framed picture (a boat), right wall
    wash(rr(1560, 190, 210, 160, 8), '#5E5C57', { seed: 79 }); wash(rr(1578, 208, 174, 124, 4), '#A9A69E', { seed: 80, edge: .1 });
    wash(spline([[1620, 300], [1665, 262], [1710, 300]], true, 4), '#6E6B64', { seed: 81, edge: 0 });
    floorBoards(g, raw, -60, 2620, DIN.floorY);
  });
  return bg;
}

// ————— The restaurant front, closer (doorway scene) —————
export const FRONT = { floorY: 950, doorX: 1330 };
export function paintFront() {
  const bg = makeBG(-40, -220, 2600, 1260, 1.0);
  withCanvas(bg, (g, raw) => {
    wash(rect(-60, -240, 2680, 700), '#4A4844', { line: false, seed: 91, edge: 0 });
    wash(rect(240, 60, 2080, FRONT.floorY - 60), '#6B6963', { seed: 92 });
    wash(rect(210, 30, 2140, 38), '#3F3E3A', { seed: 93, edge: 0 });
    // awning, bigger
    wash([[330, 210], [2230, 210], [2290, 292], [270, 292]], '#4A4844', { seed: 94 });
    raw(); g.fillStyle = 'rgba(241,238,230,.35)';
    for (let x = 350; x < 2240; x += 108) g.fillRect(x, 216, 52, 70);
    // window left (lit), door right
    wash(rect(400, 350, 620, 470), '#C8C5BC', { seed: 95, edge: .2 });
    raw(); g.strokeStyle = '#2A2927'; g.lineWidth = 8;
    g.beginPath(); g.moveTo(710, 350); g.lineTo(710, 820); g.stroke();
    g.beginPath(); g.moveTo(400, 585); g.lineTo(1020, 585); g.stroke();
    g.lineWidth = 11; g.strokeRect(400, 350, 620, 470);
    wash(rr(FRONT.doorX - 105, 330, 210, 620, 12), '#3F3E3A', { seed: 96 });
    wash(rr(FRONT.doorX - 74, 366, 148, 220, 8), '#9A978F', { seed: 97, edge: .1 });
    raw(); g.fillStyle = '#C8C5BC'; g.beginPath(); g.arc(FRONT.doorX + 66, 660, 11, 0, 7); g.fill();
    // building continuing right, dark
    wash(rect(1900, 200, 640, FRONT.floorY - 200), '#3B3A37', { seed: 98, edge: .1 });
    // street
    wash(rect(-60, FRONT.floorY, 2680, 310), '#55534E', { line: false, seed: 99, edge: 0 });
    raw(); g.fillStyle = 'rgba(241,238,230,.15)';
    for (let x = 460; x < 980; x += 36) g.fillRect(x, FRONT.floorY + 14, 15, 130 + (x * 29 % 50));
    wash(rect(-60, FRONT.floorY - 8, 2680, 12), '#2E2D2A', { seed: 100, edge: 0 });
  });
  return bg;
}
