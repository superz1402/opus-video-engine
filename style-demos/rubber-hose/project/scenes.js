// scenes.js — every shot of the rubber-hose demo. Camera on ones (continuous t),
// characters on twos (tq = q(t)), everything breathing on the 120 BPM grid (beat = 0.5 s).
// FREEZE = the band-stop: breath amplitude 0 and poses held (style rule §5).
import * as T from './toon.js';
import { P, glove } from './chars.js';
import * as F from './figs.js';
import { drawBG, camBase, ROOM, LANE, DIN, FRONT } from './bg.js';
import { TL, K, SUBS, q, breath, beats } from './timeline.js';
import { clamp, lerp, seg, eio, eo, ei, back, TAU, hash } from '/core/lib.js';
import { subPlate, fatTitle } from './ui.js';
const { shape, stroke, ell, arc, spline, rr, rect, push, pop, translate, rotate, scale } = T;

let BGR, BGL, BGD, BGF, sg;
export function initScenes(bgr, bgl, bgd, bgf, sceneCtx) { BGR = bgr; BGL = bgl; BGD = bgd; BGF = bgf; sg = sceneCtx; }

const tw = (t, t0, t1, a, b, e = eio) => lerp(a, b, e(seg(t, t0, t1)));
const pulse = (t, t0, k = 6) => t < t0 ? 0 : Math.exp(-(t - t0) * k);
// walk cycle: p = phase in beats; returns leg poses + bob (one step per beat)
function walk(p, L = 46) {
  const a = Math.PI * p, c = Math.cos(a), s = Math.sin(a);
  return { legL: { x: c * L / 2, y: -Math.max(0, s) * 18, dir: 1, bend: 6 }, legR: { x: -c * L / 2, y: -Math.max(0, -s) * 18, dir: 1, bend: -6 }, bob: -Math.abs(Math.sin(a)) * 8, sw: c * 22 };
}
function setCam(t, bg, cam, squash = 0, pivotY = 1080) { drawBG(sg, bg, cam, squash, pivotY); T.BASE.splice(0, 6, ...camBase(cam)); T.frame(t); }
function lampPost(x, y, b, fl = 0) {
  push(); translate(x, y);
  shape(rr(-7, -330, 14, 330, 6), { fill: P.dark });
  shape(ell(0, -352, 30, 36, 18), { fill: P.pale, shade: () => shape(ell(0, -352, 17, 21, 14), { fill: P.white, stroke: false, boil: .2 }) });
  shape(arc(0, -388, 34, 20, Math.PI, TAU, 14), { fill: P.dark });
  if (fl) shape(ell(0, -352, 30 + fl * 26, 36 + fl * 30, 16), { fill: P.white, stroke: false, alpha: .16 * fl, boil: 0 });
  pop();
}
function iris(t, r0, r1, t0, t1, cx = 960, cy = 540) {
  const r = lerp(r0, r1, eo(seg(t, t0, t1)));
  if ((r1 > r0 && r >= 1240) || (r1 < r0 && r <= 0)) return;
  sg.save(); sg.setTransform(1, 0, 0, 1, 0, 0); sg.fillStyle = '#050505';
  sg.beginPath(); sg.rect(0, 0, 1920, 1080); sg.arc(cx, cy, Math.max(0.1, r), 0, TAU, true); sg.fill('evenodd'); sg.restore();
}
// ————— shared staging: the dinner table full of guests —————
function diner(x, y, k, o = {}) { F.figure(x, y, { k, seated: true, body: o.body || 'plain', col: o.col, eyes: o.eyes, mouth: o.mouth, b: o.b, bt: .5, armL: o.armL, armR: o.armR }); }
function tableSet(cx, ty, w, b) {
  // table: top + cloth front; plates, cups, a teapot — all breathing props
  shape(rr(cx - w / 2, ty, w, 26, 10), { fill: P.pale });
  shape(rr(cx - w / 2 + 14, ty + 24, w - 28, 120, 8), { fill: P.light, shade: () => { for (let x = cx - w / 2 + 60; x < cx + w / 2 - 40; x += 90) stroke([[x, ty + 34], [x, ty + 132]], T.S.lw * .4, { line: P.mid, boil: .3 }); } });
  for (let i = 0; i < 7; i++) {
    const px = cx - w / 2 + 70 + i * (w - 140) / 6;
    push(); translate(px, ty + 2); scale(1 - b * .015, 1 + b * .03);
    shape(ell(0, 0, 30, 9, 18), { fill: P.white }); shape(ell(24, -8, 10, 12, 12), { fill: P.white });
    pop();
  }
  push(); translate(cx + w * .18, ty - 6); scale(1 - b * .02, 1 + b * .04);
  shape(spline([[-26, 0], [-30, -26], [-12, -38], [14, -38], [28, -24], [24, 0]], true, 5), { fill: P.white });
  shape(arc(0, -40, 13, 9, Math.PI, TAU, 10), { fill: P.white }); pop();
}
// the principal trio + guests at the table; mode 'wide' | 'close' drives acting phases from K
function dinnerCast(t, tq, mode) {
  const b = breath(tq), DIN_Y = DIN.tableY + 128;   // seated baseline (table hides legs)
  // background guests (simpler, dimmer by smaller scale)
  diner(560, DIN_Y, .92, { b, mouth: { type: 'grin' }, armR: { x: 60, y: -60, hand: 'grab' } });
  diner(760, DIN_Y, .92, { b, mouth: { type: 'smile' }, eyes: { lx: .5 } });
  diner(1700, DIN_Y, .92, { b, mouth: { type: 'smile' }, eyes: { lx: -.5 } });
  diner(1920, DIN_Y, .92, { b, mouth: { type: 'grin' }, armL: { x: -58, y: -64, hand: 'grab' } });
  // THE DAUGHTER (small, bow, beside Miss Rose)
  F.figure(1560, DIN_Y, { k: .78, seated: true, body: 'plain', col: P.mid, bow: true, b, bt: .8,
    eyes: { lx: -.4 }, mouth: { type: 'smile' }, armL: { x: -52, y: -52, hand: 'open', bend: 10 } });
  // MISS ROSE — leans in progressively; hand lands on his shoulder at K.kandhe; kiss at K.kiss
  const leanIn = tw(t, K.kandhe - 1.2, K.kiss, 0, 1);
  const kissU = seg(t, K.kiss - .55, K.kiss + .1);
  const roseX = 1300 - leanIn * 66 - kissU * 48, roseLean = -leanIn * .1 - kissU * .17;
  const handOn = t >= K.kandhe - .45;
  F.figure(roseX, DIN_Y, { k: 1.02, seated: true, body: 'dress', hat: 'flop', b, lean: roseLean,
    eyes: t < K.kandhe ? { lx: -.55, ly: .1 } : { lx: -.7, ly: -.05 }, mouth: { type: t >= K.kiss - .6 ? 'pucker' : 'smile' },
    armL: handOn ? { x: -222, y: -106, hand: 'open', bend: -6, front: true } : { x: -64, y: -58, hand: 'open', bend: 12 },
    armR: { x: 62, y: -56, hand: 'grab', bend: -12 } });
  // MR. JACKET — glance chain before the whisper, wide eyes at the kiss, then delight
  let gaze = { lx: .3 };
  if (t > K.kandhe - 1.5 && t < K.kandhe - 1.0) gaze = { lx: -.8, ly: .5 };        // to her hand
  else if (t > K.kandhe - 1.0 && t < K.kandhe - .5) gaze = { lx: -.6, ly: -.2 };   // to her face
  else if (t > K.kandhe - .5) gaze = { lx: -.35 };
  const kissShock = pulse(t, K.kiss + .25, 3.2);
  F.figure(1035, DIN_Y, { k: 1.06, seated: true, body: 'jacket', b,
    eyes: kissShock > .25 ? { type: 'wide', lx: -.3 } : gaze, brows: kissShock > .25 ? 'up' : undefined,
    mouth: { type: t > K.kiss + .6 ? 'grin' : 'smile' },
    armL: { x: -66, y: -56, hand: 'grab', bend: 14 }, armR: { x: 68, y: -58, hand: 'open', bend: -14 } });
  tableSet(1240, DIN.tableY, 1240, b);
  // the kiss heart, floating up and popping
  if (t > K.kiss + .25 && t < K.kiss + 1.7) {
    const u = (t - K.kiss - .25) / 1.45, hx = 1152, hy = DIN_Y - 268 - u * 90;
    F.heart(hx, hy, .8 + u * .5, u > .85 ? (1 - u) / .15 : 1);
  }
}
// hanging lamps for the dining room (breathing props)
function diningLamps(tq) {
  const b = breath(tq);
  for (const lx of [760, 1280, 1800]) {
    push(); translate(lx, 0); scale(1 - b * .01, 1 + b * .02);
    stroke([[0, -40], [0, 120]], T.S.lw * .8, { line: P.dark });
    shape(arc(0, 176, 74, 56, Math.PI, TAU, 18), { fill: P.dmid });
    shape(ell(0, 182, 30, 16, 14), { fill: P.white, stroke: false, boil: .3 });
    pop();
  }
}

// ———————————————————— S0 · TITLE (0–4) ————————————————————
export function shotTitle(t) {
  const tq = q(t);
  setCam(t, BGR, { x: 1280, y: 500, z: 1.04 });
  F.clockChar(706, 415, { k: 1.0, b: breath(tq) * .5, pend: Math.sin(beats(tq) * Math.PI) * .4, mA: -Math.PI / 2, hA: Math.PI * .72, lx: .4 });
  lampPost(1980, ROOM.floorY, breath(tq));
  F.photo(ROOM.photoX, ROOM.photoY, 430, { b: breath(tq), alive: 1 });
  // museum plaque card with the title — falls away at 3.4 (drawn on the scene canvas, so it weaves with the film)
  const fall = seg(t, 3.4, 4.0), fy = fall * fall * 500, fr = fall * .3;
  titleCardScreen(t, tq, fy, fr);
  iris(t, 60, 1250, .1, 1.3, 960, 470);
}
function titleCardScreen(t, tq, fy, fr) {
  const cx = 960, cy = 891 + fy, g = sg;
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = P.paper; g.strokeStyle = P.ink; g.lineWidth = 7; g.beginPath(); g.roundRect(cx - 600, cy - 168, 1200, 336, 26); g.fill(); g.stroke();
  g.lineWidth = 2.4; g.beginPath(); g.roundRect(cx - 578, cy - 146, 1156, 292, 18); g.stroke();
  const hopL = i => -(Math.max(0, Math.cos((beats(tq) - i * .12) * Math.PI)) ** 6) * 20;
  fatTitle(g, 'WOH LADY JO', cx, cy - 92, 104, { bounce: hopL });
  fatTitle(g, 'NVIDIA KE ANDAR THI', cx, cy + 24, 93, { bounce: i => hopL(i + 5) });
  g.fillStyle = P.ink; g.font = '34px Limelight'; g.textAlign = 'center'; g.textBaseline = 'alphabetic';
  g.fillText('C A S E   F I L E :   H U A N G   /   H U A N G', cx, cy + 128);
  g.restore();
}

// ———————————————————— S1 · THE LANE → INSIDE (4–19) ————————————————————
export function shotLane(t) {
  const tq = q(t);
  if (t < K.table) {
    const pushU = t < K.glass ? tw(t, 4, K.glass, 0, 1) : tw(t, K.glass, K.table, 0, 1);
    const cam = t < K.glass ? { x: 1280, y: 515 - pushU * 25, z: 1.02 + pushU * .22 } : { x: LANE.winX, y: LANE.winY, z: 1.24 + pushU * 1.15 };
    setCam(t, BGL, cam, breath(tq) * .012, LANE.floorY);
    lampPost(430, LANE.floorY, breath(tq), .6); lampPost(1900, LANE.floorY, breath(tq), .6);
    // a reporter waits under the right lamp, bobbing on the beat
    F.figure(1848, LANE.floorY, { k: .92, body: 'coat', col: P.dmid, hat: 'bowler', b: breath(tq), eyes: { lx: -.6 }, mouth: { type: 'flat' }, armR: { x: 66, y: -120, hand: 'grab', bend: -20 } });
    F.boxCamera(1920, LANE.floorY - 128, .95, {});
    // silhouettes inside the lit window: three heads at a table
    const winGlow = .75 + Math.sin(t * 7) * .03;
    shape(rr(LANE.winX - 210, LANE.winY - 60, 420, 150, 8), { fill: `rgba(241,238,230,${.24 * winGlow})`, stroke: false, boil: 0 });
    for (const [sx, ss] of [[-110, 1], [0, 1.12], [115, .95]]) {
      shape(ell(LANE.winX + sx, LANE.winY + 26 - Math.abs(breath(tq)) * 3, 34 * ss, 40 * ss, 16), { fill: P.dark, stroke: false, boil: .3 });
      shape(rr(LANE.winX + sx - 52 * ss, LANE.winY + 58, 104 * ss, 40, 8), { fill: P.dark, stroke: false, boil: .3 });
    }
    // glass shine sweep as we push through
    if (t >= K.glass) { const u = seg(t, K.glass, K.table); shape([[LANE.winX - 340 + u * 300, LANE.winY - 230], [LANE.winX - 120 + u * 300, LANE.winY - 230], [LANE.winX - 320 + u * 300, LANE.winY + 230], [LANE.winX - 540 + u * 300, LANE.winY + 230]], { fill: 'rgba(252,251,247,.28)', stroke: false, boil: 0 }); }
    F.rain(300, -160, 2260, LANE.floorY, t, 110);
  } else {
    // inside, wide: the whole table for the last words of L1
    setCam(t, BGD, { x: 1280, y: 545, z: 1.0 }, breath(tq) * .012, DIN.floorY);
    diningLamps(tq);
    dinnerCast(t, tq, 'wide');
  }
}

// ———————————————————— S2 · THE DINNER (19–29.92) ————————————————————
export function shotDinner(t) {
  const tq = q(t);
  const cam = t < K.gulabi ? { x: 1240, y: 565, z: 1.28 } : { x: 1175, y: 585, z: 1.62 };
  setCam(t, BGD, cam, breath(tq) * .012, DIN.floorY);
  diningLamps(tq);
  dinnerCast(t, tq, 'close');
}

// ———————————————————— S3 · THE DOORWAY (29.92–43) ————————————————————
function reporter(x, o = {}) {
  F.figure(x, FRONT.floorY, { k: .9, body: 'coat', col: P.dmid, hat: 'bowler', b: o.b, eyes: { lx: .5 }, mouth: { type: o.munch ? 'o' : 'grin' },
    armL: { x: -58, y: -128, hand: 'grab', bend: 16 }, armR: o.packet ? { x: 56, y: -104, hand: 'grab', bend: -18, front: true } : { x: 62, y: -70, hand: 'open', bend: -14 } });
  F.boxCamera(x - 62, FRONT.floorY - 138, .9, { flash: o.flash || 0 });
  if (o.packet) F.ricePacket(x + 58, FRONT.floorY - 96, .95, {});
}
function doorwayCast(t, tq, frozen = false) {
  const b = frozen ? 0 : breath(tq);
  const evT = TL.ev.filter(e => e.type === 'shutter').map(e => e.t);
  const flashAt = x => frozen ? 0 : Math.max(0, ...evT.map(et => pulse(t, et, 14))) * (0.6 + 0.4 * Math.sin(x));
  // reporters: packets arrive one by one from K.client
  const got = i => t >= K.client + i * .5 + .3;
  reporter(520, { b, flash: flashAt(1), packet: got(0) || got(3), munch: t > 37 });
  reporter(650, { b, flash: flashAt(2), packet: got(1) || got(4), munch: t > 37.5 });
  reporter(780, { b, flash: flashAt(3), packet: got(2) || got(5), munch: t > 38 });
  // a packet arcs from the boss's hand to the reporters on each packet beat
  for (let i = 0; i < 6; i++) {
    const t0 = K.client + i * .5, u = seg(t, t0, t0 + .3);
    if (u > 0 && u < 1) {
      const tx_ = [520, 650, 780][i % 3] + 58, px = lerp(1560, tx_, u), py = lerp(806, FRONT.floorY - 96, u) - Math.sin(u * Math.PI) * 120;
      F.ricePacket(px, py, .95, { rot: u * 2 });
    }
  }
  // the client (right): shook the boss's hand, now steps back with his own packet
  F.figure(1830, FRONT.floorY, { k: .95, body: 'plain', col: P.mid, b, eyes: { lx: -.5 }, mouth: { type: 'grin' }, armL: { x: -64, y: -96, hand: 'grab', bend: 10, front: true } });
  if (t > K.client + .4) F.ricePacket(1762, FRONT.floorY - 92, .95, {});
  // MISS ROSE: waits in the doorway, then walks to the car and hops in
  const carX = t < 37.2 ? 2750 : tw(t, 37.2, 38.1, 2750, 1850, eo);
  if (t < 39.3) {
    const walkU = seg(t, 38.3, 39.3), wp = walk(beats(tq) * 1, 40);
    const rx = walkU > 0 ? lerp(1445, 1640, walkU) : 1445;
    F.figure(rx, FRONT.floorY + (walkU > 0 ? wp.bob : 0), { k: .98, body: 'dress', hat: 'flop', b, eyes: { lx: .6 }, mouth: { type: 'smile' },
      legL: walkU > 0 ? wp.legL : undefined, legR: walkU > 0 ? wp.legR : undefined,
      armL: { x: -56, y: -70, hand: 'open', bend: 12 }, armR: { x: 58, y: -66, hand: 'open', bend: -12 } });
  } else if (t < 39.95) {  // the hop into the car (drawn before the car, so the car swallows her)
    const u = seg(t, 39.3, 39.95), hx = lerp(1640, 1844, u), hy = FRONT.floorY - Math.sin(u * Math.PI) * 150;
    F.figure(hx, hy, { k: .98, body: 'dress', hat: 'flop', b: 0, eyes: { type: 'wide' }, mouth: { type: 'o' }, armL: { x: -70, y: -190, hand: 'open' }, armR: { x: 70, y: -190, hand: 'open' } });
  }
  // THE CAR (after Rose's hop, so she lands inside it)
  if (t >= 37.2) {
    const leaving = t > 40.4, cx = leaving ? tw(t, 40.4, 42.9, 1850, 3050, ei) : carX;
    F.car(cx, FRONT.floorY, { k: 1.02, dir: -1, b, spin: (leaving || t < 38.1) ? -t * 9 : 0, puff: leaving ? (t * 1.6) % 1 : null });
    if (t >= 39.95) {  // her head, visible in the car window
      shape(ell(cx + 8, FRONT.floorY - 168, 21, 24, 14), { fill: P.white });
      shape(arc(cx + 8, FRONT.floorY - 182, 27, 13, Math.PI, TAU, 12), { fill: P.pale });
    }
    if (t > 38.0 && t < 38.9) for (const s of [0, 1]) { const u = pulse(t, 38.13 + s * .5, 5); if (u > .05) stroke(arc(cx - 190, FRONT.floorY - 130, 20 + (1 - u) * 36, 20 + (1 - u) * 36, -.7, .7, 10), T.S.lw * .7, { line: P.dark }); }
  }
  // MR. JACKET: steps out, greets the client, waves the car away
  const outU = seg(t, 29.92, 31.4), wp2 = walk(beats(tq), 42);
  const bx = outU < 1 ? lerp(FRONT.doorX, 1560, outU) : 1560;
  const waving = t > 40.4;
  F.figure(bx, FRONT.floorY + (outU < 1 ? wp2.bob : 0), { k: 1.02, body: 'jacket', b, eyes: { lx: t < K.client ? .4 : -.2 }, mouth: { type: 'grin' },
    legL: outU < 1 ? wp2.legL : undefined, legR: outU < 1 ? wp2.legR : undefined,
    armL: { x: -60, y: -64, hand: 'open', bend: 14 },
    armR: waving ? { x: 96, y: -238 + Math.sin(t * 9) * 16, hand: 'wave', bend: -8, front: true } : { x: 74, y: -104, hand: 'grab', bend: -16, front: true } });
}
export function shotDoorway(t) {
  const tq = q(t);
  setCam(t, BGF, { x: 1230 + tw(t, 30, 40, 0, 60), y: 545, z: 1.12 }, breath(tq) * .012, FRONT.floorY);
  lampPost(215, FRONT.floorY, breath(tq), .5);
  doorwayCast(t, tq);
  F.rain(240, -160, 2320, FRONT.floorY, t, 100);
}

// ———————————————————— S4 · THE NEWSPAPER (43–50) ————————————————————
export function shotNews(t) {
  const tq = q(49.9);
  setCam(t, BGF, { x: 1290, y: 545, z: 1.12 }, 0, FRONT.floorY);
  doorwayCast(49.9, tq, true);                       // the world, already frozen under the paper
  sg.save(); sg.setTransform(1, 0, 0, 1, 0, 0); sg.fillStyle = 'rgba(10,10,10,.16)'; sg.fillRect(0, 0, 1920, 1080); sg.restore();
  T.frame(t);
  const down = seg(t, 43.0, 43.9), up = seg(t, 49.3, 50.0), frac = down * (1 - up);
  if (frac > 0.01) F.newspaper(1280, 66, 940, frac, {});
  if (frac > .9 && t > 45.2 && t < 47.2) {            // a glove on a hose arm taps the headline, twice
    const tap = Math.abs(Math.sin((t - 45.2) * Math.PI * 2)) * 14;
    T.shape(T.noodle([1660, -60], [1640, 190 + tap], 26, 15), { fill: P.ink, lw: T.S.lw * .8 });
    glove(1640, 196 + tap, Math.PI / 2 + .25, 'point', 1.5);
  }
}

// ———————————————————— S5 · FREEZE → THE EVIDENCE ROOM (50–73) ————————————————————
export function shotFreeze(t) {
  if (t < 52) {  // the band has stopped: the doorway world holds its breath, literally
    setCam(t, BGF, { x: 1290, y: 545, z: 1.12 }, 0, FRONT.floorY);
    doorwayCast(49.9, q(49.9), true);
    return;
  }
  const tq = q(t), b = breath(tq);
  // camera: settles on the wall, then pans with the carriers toward the board
  const carryX = tw(t, 62, 70.5, 0, 830);
  setCam(t, BGR, { x: 1280 + carryX * .52, y: 505, z: 1.0 }, b * .012, ROOM.floorY);
  // the clock: hands spin madly until the stamp, then it calms down
  const spin = t < K.stamp ? Math.pow(t - 52, 2) * 2.4 : 34;
  F.clockChar(700, 415, { k: 1.05, b: b * .5, pend: Math.sin(t * (t < K.stamp ? 9 : 2.2)) * .5,
    mA: -Math.PI / 2 + spin, hA: Math.PI * .72 + spin / 12, lx: .3, eyes: t < K.stamp ? 'wide' : 'open', mouth: t < K.stamp ? 'o' : 'smile' });
  lampPost(360, ROOM.floorY, b);
  // photo state: on the wall → stamped → lifted → carried → pinned on the board
  const stamped = t >= K.stamp ? Math.min(1, (t - K.stamp) / .16) : 0;
  const shake = pulse(t, K.stamp, 9) * .02;
  let px = ROOM.photoX, py = ROOM.photoY, pw = 430;
  if (t > 59.3) { const lift = seg(t, 59.3, 60.3); py = lerp(ROOM.photoY, 520, lift); }
  if (t > 62) { px += carryX; py = 520 + Math.abs(Math.sin(beats(tq) * Math.PI)) * -7; }
  if (t > 70.5) { const u = seg(t, 70.5, 71.8); px = lerp(1280 + 830, 2110, u); py = lerp(520, 375, u); pw = lerp(430, 380, u); }
  // carriers
  const cIn = seg(t, 58.3, 59.3), cOut = seg(t, 71.8, 72.6);
  const wp = walk(beats(tq), 40);
  const holdStill = (t > 59.8 && t < 62) || (t >= 59.3 && t <= 59.8);
  const cAct = (side) => {
    const home = side < 0 ? 1045 : 1515, startX = side < 0 ? 260 : 2300;
    let cx = t < 58.3 ? startX : lerp(startX, home, cIn);
    if (t > 62) cx = px + side * (pw / 2 + 42);
    if (t > 70.5) cx = lerp(px + side * (pw / 2 + 42), px + side * (pw / 2 + 130), cOut);
    const walking = (t >= 58.3 && t < 59.3) || (t > 62 && t < 70.5);
    F.figure(cx, ROOM.floorY + (walking ? wp.bob : 0), { k: .94, body: 'coat', col: P.dmid, hat: 'cap', b, eyes: { lx: -side * .5 }, mouth: { type: 'flat' },
      legL: walking ? wp.legL : undefined, legR: walking ? wp.legR : undefined,
      armL: { x: -side * 10 - 26, y: -300, hand: 'grab', bend: side * 8, front: true }, armR: { x: -side * 10 + 26, y: -300, hand: 'grab', bend: -side * 8, front: true } });
  };
  if (t >= 58.3) { cAct(-1); cAct(1); }
  F.photo(px, py, pw, { b: t < 52 ? 0 : b, alive: t > 62 ? 0 : 0, stamp: stamped, rot: shake * Math.sin(t * 60) });
  // the magnifier pass (K.intel): a big gloved hand sweeps a lens over the photo
  if (t > K.intel - .4 && t < K.intel + 2.4) {
    const u = seg(t, K.intel - .4, K.intel + 2.4), mx = px + lerp(-190, 200, u), my = py - 30 + Math.sin(u * Math.PI) * 26;
    push(); translate(mx, my); rotate(.5);
    shape(ell(0, 0, 118, 118, 40), { fill: 'rgba(252,251,247,.18)', lw: 13 });
    T.shape(T.noodle([86, 86], [210, 210], 8, 21), { fill: P.dark });
    pop();
  }
  if (t > 53.4 && t < 54.6) { const u = (t - 53.4) / 1.2; shape(ell(ROOM.photoX - 200, ROOM.photoY - 190 + u * 30, 16 + u * 26, 12 + u * 18, 14), { fill: P.light, stroke: false, alpha: .5 * (1 - u), boil: 0 }); }
}

// ———————————————————— S6 · THE DESK (73–88.5) ————————————————————
const CARD_SLOTS = [
  { x: 748, y: 622, rot: -.05, label: 'PHOTO' }, { x: 748, y: 838, rot: .04, label: 'KAAGAZ' },
  { x: 1472, y: 606, rot: .05, label: 'REPORT' }, { x: 1568, y: 822, rot: -.04, label: 'MEMO' },
  { x: 1085, y: 884, rot: .02, label: 'INKAAR' }, { x: 1258, y: 600, rot: -.03, label: null },
];
export function shotDesk(t) {
  const tq = q(t), b = breath(tq);
  setCam(t, BGR, { x: 1280, y: 645, z: 1.12 }, b * .01, ROOM.floorY);
  // the desk
  shape(rr(400, 792, 1760, 34, 10), { fill: P.dmid });
  shape(rr(430, 824, 1700, 260, 6), { fill: P.dark, shade: () => { for (const dx of [300, 850, 1400]) shape(rr(430 + dx, 866, 190, 120, 8), { fill: P.dmid, stroke: false, boil: .3 }); } });
  // desk lamp (breathing prop)
  push(); translate(1830, 792); scale(1 - b * .015, 1 + b * .03);
  shape(ell(0, 0, 52, 12, 18), { fill: P.ink });
  T.shape(T.noodle([0, -6], [-58, -128], 22, 13), { fill: P.ink });
  push(); translate(-66, -138); rotate(-.5); shape(arc(0, 0, 52, 40, Math.PI * .95, Math.PI * 2.05, 16), { fill: P.dmid }); shape(ell(0, 4, 24, 12, 12), { fill: P.white, stroke: false, boil: .3 }); pop();
  pop();
  // the photo, pushed in by a glove at 73, then propped on the desk
  const pushU = seg(t, 73.0, 74.2), phX = lerp(700, 1065, pushU), phW = 330;
  F.photo(phX, 668, phW, { b, alive: 0, rot: -.05, stamp: 1 });
  if (t < 74.6) { push(); translate(phX - phW / 2 - 66, 640 + Math.sin(t * 3) * 4); rotate(.2); scale(1.6); pop(); bigGlove(phX - phW / 2 - 40, 636, 1.6, .2, 'grab'); }
  // a pointing glove wags "faisla nahi" beside the photo
  if (t > 75.6 && t < 79.6) bigGlove(1330, 560, 1.5, -.35 + Math.sin(t * 6.5) * .16, 'point');
  // the stack of cards, then the dealing (one per beat from K.deal)
  const stackN = CARD_SLOTS.filter((s, i) => t < K.deal + i * .5).length;
  for (let i = 0; i < stackN; i++) F.evCard(1620 + i * 3, 724 - i * 7, 190, { rot: .03 * i });
  CARD_SLOTS.forEach((s, i) => {
    const t0 = K.deal + i * .5, u = seg(t, t0, t0 + .45);
    if (u <= 0) return;
    const px = lerp(1620, s.x, u), py = lerp(724, s.y, u) - Math.sin(u * Math.PI) * 150;
    F.evCard(px, py, 216, { rot: lerp(.1, s.rot, u), label: s.label });
    if (s.label === null) F.clockChar(px, py - 6, { k: .34, b: 0, pend: Math.sin(beats(tq) * Math.PI) * .4, mA: -Math.PI / 2 + beats(tq) * .2, hA: 2.2, lx: 0 });   // the "one clock" card
  });
}
function bigGlove(x, y, k, rot, type) {
  // a hose arm from above + the style's white glove at its end
  const ay = y - 130 * k;
  T.shape(T.noodle([x + 22 * k, ay], [x + 5 * k, y - 24 * k], 10 * k, 10.5 * k), { fill: P.ink, lw: T.S.lw * .7 });
  glove(x, y, rot, type, k);
}

// ———————————————————— S7 · THE FOUR DOORS (88.5–116) ————————————————————
const DOORS = [
  { x: 722, label: 'RECORD' }, { x: 1102, label: 'AAROP' }, { x: 1482, label: 'INKAAR' }, { x: 1862, label: 'AGYAAT' },
];
const DOOR_OPEN = [99.03, 100.53, 102.03, 103.53];
export function shotDoors(t) {
  const tq = q(t), b = breath(tq) * (t > 104 ? 1.7 : 1);
  const camZ = tw(t, 100, 106, 1.1, .88), camY = tw(t, 98, 100, 645, 545);
  setCam(t, BGR, { x: 1280, y: camY, z: camZ }, b * .012, ROOM.floorY);
  // the desk slides away as the doors rise
  const deskGone = seg(t, 98.0, 99.3);
  if (deskGone < 1) {
    push(); translate(0, deskGone * 320);
    shape(rr(400, 792, 1760, 34, 10), { fill: P.dmid });
    shape(rr(430, 824, 1700, 260, 6), { fill: P.dark });
    pop();
  }
  // doors rise one after another
  DOORS.forEach((d, i) => {
    const rise = seg(t, 98.03 + i * .15, 99.2 + i * .15), yOff = (1 - rise) * 580;
    if (rise <= 0) return;
    const open = seg(t, DOOR_OPEN[i], DOOR_OPEN[i] + .8);
    const fl = ROOM.floorY + yOff;
    F.doorUnit(d.x, fl, 302, 545, {
      open, label: d.label, labelSize: 37, behind: () => {
        if (open <= .25) return;
        if (i === 0) F.figure(d.x + 56, fl, { k: .92, body: 'jacket', b, eyes: { lx: .2 }, mouth: { type: 'grin' }, armR: { x: 84, y: -216 + Math.sin(t * 7) * 12, hand: 'wave', front: true } });
        if (i === 1) F.figure(d.x + 56, fl, { k: .92, body: 'dress', hat: 'flop', b, brows: 'sad', eyes: { lx: .45 }, mouth: { type: 'flat' }, armL: { x: -58, y: -70, hand: 'open' } });
        if (i === 2) F.figure(d.x + 56 + Math.sin(t * 11) * 4, fl, { k: .92, body: 'coat', col: P.dmid, hat: 'cap', b, eyes: { lx: -.3 }, mouth: { type: 'flat' } });
        if (i === 3) { const s = 1 + Math.abs(Math.sin(beats(tq) * Math.PI)) * .12; push(); translate(d.x, fl - 350); scale(s); T.text('?', 0, 0, { font: '170px Shrikhand', fill: P.white }); pop(); }
      }
    });
  });
  // the dealt cards ride the desk down and away
  if (deskGone < 1) CARD_SLOTS.forEach(s2 => F.evCard(s2.x, s2.y + deskGone * 320, 216, { rot: s2.rot, label: s2.label }));
  // the photo presides: on the desk until 98.2, then it floats up to the centre
  const phU = seg(t, 98.2, 100.6), phX = lerp(1065, 1280, phU), phY = lerp(668, 415, phU), phW = lerp(330, 405, phU);
  F.photo(phX, phY + Math.sin(beats(tq) * Math.PI * .5) * 5, phW, { b, alive: 0, stamp: 1, rot: -.02 });
  // iris out, grabbed by a glove at the end
  iris(t, 1250, 130, 112.5, 115.0, 960, 500);
  if (t > 113.6) {
    const u = seg(t, 113.6, 115.0), r = lerp(1250, 130, eo(seg(t, 112.5, 115.0))), a = -0.7;
    const gx = 960 + Math.cos(a) * r, gy = 500 + Math.sin(a) * r;
    glove(gx, gy, a + Math.PI / 2, 'grab', 2.6);
    iris(t, 130, 0, 115.0, 115.6, 960, 500);
  }
}

// ———————————————————— subtitles: period title cards ————————————————————
export function subtitles(t) {
  for (const s of SUBS) {
    if (t < s.t0 || t >= s.t1) continue;
    // smaller type when the line is long, so the plate stays inside the 4:3 gate
    const size = s.text.length > 46 ? 30 : s.text.length > 34 ? 33 : 36;
    subPlate(sg, s.text, 960, 984, { size });
  }
}
