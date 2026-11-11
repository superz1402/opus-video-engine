// figs.js — original characters for "Woh Lady Jo Nvidia Ke Andar Thi" (rubber-hose demo)
// Built on the style's anatomy kit (chars.js parts): pie eyes, white gloves, hose limbs, big shoes.
// NO likenesses, NO existing cartoon designs: a round boss, a lady in a pale dress, a little
// daughter, reporters, carriers, a car and a clock — all generic 1930s figures.
import * as T from './toon.js';
import { P, pieEye, brow, mouth, glove, shoe, hose, ribbon } from './chars.js';
import { clamp, lerp, TAU, hash } from '/core/lib.js';
const { shape, stroke, ell, arc, spline, quad, rr, rect, push, pop, translate, rotate, scale } = T;

// squash & stretch around the ground point (breathing): b in -1..1
export const breathe = (b, a = .055) => { scale(1 - b * a * .6, 1 + b * a); };

// ———————————————————— A person ————————————————————
// local origin = ground between the feet; ~300 tall at k=1.
// o: { body:'jacket'|'dress'|'plain'|'coat', col, hat:'flop'|'cap'|'bowler'|null, bow, seated,
//      eyes, mouth, brows, armL/armR {x,y,hand,bend,front,rot}, legL/legR {x,y,bend,dir,ang},
//      lean, sx, sy, b (breath), bt (breath amp) }
export function figure(x, y, o = {}) {
  const k = o.k || 1, b = (o.b ?? 0) * (o.bt ?? 1);
  push(); translate(x, y); scale(k); if (o.lean) rotate(o.lean);
  scale((o.sx || 1) * (1 - b * .033), (o.sy || 1) * (1 + b * .055));
  const bodyTop = o.seated ? -150 : -208, hipY = -64;
  const bodyW = o.body === 'dress' ? 86 : 74;
  // legs (skipped when seated — the table hides them)
  if (!o.seated) {
    for (const [key, s] of [['legL', -1], ['legR', 1]]) {
      const L = o[key] || { x: s * 30, y: 0 };
      hose([s * 22, hipY], [L.x, L.y - 8], L.bend ?? s * 4, 15, P.ink);
    }
    for (const [key, s] of [['legL', -1], ['legR', 1]]) {
      const L = o[key] || { x: s * 30, y: 0 };
      shoe(L.x - (L.dir ?? s) * 6, L.y, L.dir ?? s, 1.05, L.ang || 0);
    }
  }
  const arm = (key, s, front) => {
    const A = o[key]; if (!A || !!A.front !== front) return;
    const sh = [s * bodyW * .82, bodyTop + 38];
    hose(sh, [A.x, A.y], A.bend ?? s * -16, 14, P.ink);
    glove(A.x, A.y, A.rot ?? Math.atan2(A.y - sh[1], A.x - sh[0]), A.hand || 'open', A.hk || 1, { flip: A.flip ?? s < 0 });
  };
  arm('armL', -1, false); arm('armR', 1, false);
  // body
  let bodyPts;
  if (o.body === 'dress') {        // bell dress (pale — reads white in B&W)
    bodyPts = spline([[-bodyW * .45, bodyTop + 6], [bodyW * .45, bodyTop + 6], [bodyW * .95, -6], [bodyW * .7, 4], [0, 10], [-bodyW * .7, 4], [-bodyW * .95, -6]], true, 7);
  } else {                          // round potato body
    bodyPts = spline([[-bodyW, bodyTop + 46], [-bodyW * 1.02, -60], [-bodyW * .6, -2], [0, 8], [bodyW * .6, -2], [bodyW * 1.02, -60], [bodyW, bodyTop + 46], [bodyW * .55, bodyTop + 4], [-bodyW * .55, bodyTop + 4]], true, 7);
  }
  const col = o.col || (o.body === 'dress' ? P.pale : o.body === 'plain' ? P.mid : P.dark);
  shape(bodyPts, {
    fill: col, shade: () => {
      if (o.body === 'jacket') {    // white shirt wedge + bow tie
        shape([[-17, bodyTop + 30], [17, bodyTop + 30], [0, bodyTop + 118]], { fill: P.white, stroke: false, boil: .4 });
        shape(ell(-13, bodyTop + 26, 10, 6, 10), { fill: P.ink, stroke: false }); shape(ell(13, bodyTop + 26, 10, 6, 10), { fill: P.ink, stroke: false });
      }
      if (o.body === 'dress') {     // dark sash band
        shape([[-bodyW * .62, bodyTop + 74], [bodyW * .62, bodyTop + 74], [bodyW * .78, bodyTop + 96], [-bodyW * .78, bodyTop + 96]], { fill: P.dmid, stroke: false, boil: .4 });
      }
    }
  });
  // head
  const hy = bodyTop - 36, hr = 41;
  shape(ell(0, hy, hr, hr * .96, 36), { fill: P.white });
  const E = o.eyes || {};
  pieEye(-14, hy - 4, 12.5, 17, { ...E, side: 1, lwk: .7 });
  pieEye(14, hy - 4, 12.5, 17, { ...E, side: -1, lwk: .7 });
  if (o.brows) { brow(-14, hy - 30, 21, o.brows, -1); brow(14, hy - 30, 21, o.brows, 1); }
  shape(ell(3, hy + 12, 5.5, 4, 12), { fill: P.ink, stroke: false, boil: .3 });   // little nose
  const M = o.mouth || { type: 'smile' };
  mouth(1, hy + 24, M.w || 34, M.type, M);
  // hair / hats
  if (o.hat === 'flop') {          // lady's floppy hat: wide drooping brim + soft crown (pale, dark band)
    shape(arc(0, hy - 16, 31, 27, Math.PI, TAU, 18), { fill: P.pale });
    stroke(arc(0, hy - 16, 31, 27, Math.PI * 1.12, Math.PI * 1.88, 10), T.S.lw * 1.7, { line: P.dark });
    shape(spline([[-64, hy - 14], [-30, hy - 22], [0, hy - 24], [30, hy - 22], [64, hy - 14], [58, hy - 2], [24, hy - 9], [0, hy - 10], [-24, hy - 9], [-58, hy - 2]], true, 6), { fill: P.pale });
  } else if (o.hat === 'cap') {
    shape(arc(0, hy - 12, 36, 22, Math.PI, TAU, 18), { fill: P.dmid });
    shape(rr(-38, hy - 16, 76, 9, 4), { fill: P.dmid });
  } else if (o.hat === 'bowler') {
    shape(ell(0, hy - 26, 52, 10, 24), { fill: P.dark });
    shape(arc(0, hy - 24, 30, 24, Math.PI, TAU, 18), { fill: P.dark });
  } else {                          // hair swoop
    shape(arc(0, hy - 6, hr * .98, hr * .8, Math.PI * 1.08, Math.PI * 1.95, 20), { fill: P.ink, stroke: false, boil: .5 });
  }
  if (o.bow) {                      // daughter's bow
    push(); translate(24, hy - 34); rotate(.3);
    shape(spline([[-16, 0], [-4, -9], [0, 0], [-4, 9]], true, 4), { fill: P.white });
    shape(spline([[16, 0], [4, -9], [0, 0], [4, 9]], true, 4), { fill: P.white });
    shape(ell(0, 0, 5, 5, 10), { fill: P.ink, stroke: false }); pop();
  }
  arm('armL', -1, true); arm('armR', 1, true);
  pop();
}

// ———————————————————— The Car (object character) ————————————————————
// local origin = ground centre; headlights are its eyes, the grille its grin. faces +x when dir=1.
export function car(x, y, o = {}) {
  const k = o.k || 1, b = o.b ?? 0, dir = o.dir || 1;
  push(); translate(x, y); scale(dir * k, k); scale(1 - b * .02, 1 + b * .045);
  // wheels (spin spokes by o.spin)
  for (const wx of [-118, 118]) {
    shape(ell(wx, -34, 36, 36, 26), { fill: P.ink });
    shape(ell(wx, -34, 15, 15, 18), { fill: P.light });
    const a0 = o.spin || 0;
    for (let i = 0; i < 3; i++) { const a = a0 + i / 3 * TAU; stroke([[wx, -34], [wx + Math.cos(a) * 13, -34 + Math.sin(a) * 13]], T.S.lw * .5); }
  }
  // body: one round 1930s saloon blob
  const body = spline([[-168, -38], [-172, -96], [-128, -128], [-96, -196], [-30, -216], [52, -212], [104, -176], [150, -130], [172, -92], [166, -40], [90, -30], [-90, -30]], true, 7);
  shape(body, { fill: P.dark, shade: () => { shape(rr(-58, -196, 116, 74, 16), { fill: P.mid, stroke: false, boil: .3 }); shape(rr(-46, -186, 40, 56, 8), { fill: P.pale, stroke: false, boil: .3 }); shape(rr(8, -186, 40, 56, 8), { fill: P.pale, stroke: false, boil: .3 }); } });
  // headlight = one round lamp at the nose (side view), with a pie-cut glint
  shape(ell(163, -104, 19, 19, 20), { fill: P.white });
  shape(ell(168, -110, 6, 6, 10), { fill: P.ink, stroke: false, boil: .3 });
  shape(rr(150, -52, 22, 10, 5), { fill: P.light });   // bumper
  // grille grin
  shape(rr(150, -66, 16, 30, 7), { fill: P.light, shade: () => { for (const dx of [-4, 2]) stroke([[152 + dx + 4, -62], [152 + dx + 4, -40]], T.S.lw * .45, { line: P.dark }); } });
  // exhaust puffs (o.puff = 0..1 phase) — scattered, growing (never a neat row)
  if (o.puff != null) for (let i = 0; i < 3; i++) {
    const u = (o.puff + i / 3) % 1, px = -186 - u * 90, py = -26 - u * 42 + Math.sin(i * 7.3) * 8;
    shape(ell(px, py, 8 + u * 20, (8 + u * 20) * .75, 14), { fill: P.light, stroke: false, boil: .4, alpha: .75 * (1 - u) });
  }
  pop();
}

// ———————————————————— The Clock (object character) ————————————————————
// Wall clock: dial face, pie eyes above the centre, hands set by o.hA / o.mA (radians), pendulum = one kicking leg.
export function clockChar(x, y, o = {}) {
  const k = o.k || 1, b = o.b ?? 0;
  push(); translate(x, y); scale(k); scale(1 - b * .025, 1 + b * .04);
  shape(ell(0, 0, 86, 86, 48), { fill: P.dmid });
  shape(ell(0, 0, 70, 70, 44), {
    fill: P.white, shade: () => {
      for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; stroke([[Math.cos(a) * 57, Math.sin(a) * 57], [Math.cos(a) * 64, Math.sin(a) * 64]], T.S.lw * (i % 3 ? .45 : .8), { boil: .3 }); }
    }
  });
  pieEye(-19, -26, 12, 16, { lx: o.lx || 0, type: o.eyes, lwk: .65, side: 1 });
  pieEye(19, -26, 12, 16, { lx: o.lx || 0, type: o.eyes, lwk: .65, side: -1 });
  stroke([[0, 4], [Math.cos(o.hA || 0) * 34, 4 + Math.sin(o.hA || 0) * 34]], T.S.lw * 1.05);
  stroke([[0, 4], [Math.cos(o.mA || 0) * 50, 4 + Math.sin(o.mA || 0) * 50]], T.S.lw * .7);
  shape(ell(0, 4, 6, 6, 12), { fill: P.ink, stroke: false });
  mouth(0, 34, 26, o.mouth || 'smile', {});
  // pendulum leg with a shoe, swinging by o.pend
  const pa = o.pend || 0;
  push(); translate(0, 84); rotate(pa);
  hose([0, 0], [0, 56], 0, 11, P.ink); shoe(2, 62, 1, .8); pop();
  pop();
}

// ———————————————————— The Photo (hero object) ————————————————————
// A framed photograph: inside it, a miniature painted dinner (two figures at a table, window rain).
// o.alive = 0..1 — how much the picture's tiny world breathes; o.stamp = draw the SABOOT stamp.
export function photo(x, y, w, o = {}) {
  const h = w * .72, b = (o.b ?? 0) * (o.alive ?? 1);
  push(); translate(x, y); if (o.rot) rotate(o.rot); scale(1 - b * .02, 1 + b * .03);
  shape(rr(-w / 2 - 14, -h / 2 - 14, w + 28, h + 28, 10), { fill: P.dark });                    // frame
  shape(rr(-w / 2, -h / 2, w, h, 4), {
    fill: '#55534E', shade: () => {
      // window mullions + rain streaks inside the picture
      for (const fx of [-.25, 0, .25]) stroke([[w * fx, -h / 2], [w * fx, h / 2]], T.S.lw * .5, { line: P.dmid, boil: .2 });
      stroke([[-w / 2, 0], [w / 2, 0]], T.S.lw * .5, { line: P.dmid, boil: .2 });
      for (let i = 0; i < 14; i++) { const rx = (hash(i * 3.7) - .5) * w * .92, ry = (hash(i * 9.1) - .5) * h * .8; stroke([[rx, ry], [rx - 3, ry + 12]], T.S.lw * .35, { line: P.light, boil: 0 }); }
      // the table + two tiny figures (schematic miniatures of the dinner)
      shape(rr(-w * .3, h * .08, w * .6, h * .1, 5), { fill: P.ink, stroke: false, boil: .2 });
      shape(ell(-w * .13, -h * .02, w * .075, w * .105, 18), { fill: P.ink, stroke: false, boil: .2 });          // boss silhouette
      shape(ell(w * .13, -h * .03, w * .07, w * .1, 18), { fill: P.pale, stroke: false, boil: .2 });           // lady silhouette
      shape(ell(-w * .13, -h * .19, w * .045, w * .045, 14), { fill: P.white, stroke: false, boil: .2 });
      shape(ell(w * .1, -h * .2, w * .042, w * .042, 14), { fill: P.white, stroke: false, boil: .2 });
    }
  });
  // brass plate
  shape(rr(-44, h / 2 + 1, 88, 15, 4), { fill: P.mid, stroke: false, boil: .3 });
  if (o.stamp) {  // SABOOT No. 1 stamp, slammed at an angle
    push(); translate(w * .18, -h * .1); rotate(-.18); scale(o.stamp);
    T.g.setTransform(...T.getM()); const g = T.g;
    g.font = '700 30px Limelight'; g.textAlign = 'center'; g.textBaseline = 'middle';
    shape(rr(-108, -26, 216, 52, 6), { fill: 'rgba(241,238,230,.88)', lw: 3.4 });
    T.text('SABOOT No. 1', 0, 2, { font: '30px Limelight', fill: P.ink });
    pop();
  }
  pop();
}

// ———————————————————— An evidence card ————————————————————
export function evCard(x, y, w, o = {}) {
  const h = w * .68;
  push(); translate(x, y); if (o.rot) rotate(o.rot);
  shape(rr(-w / 2, -h / 2, w, h, 8), {
    fill: P.paper, shade: () => {
      stroke([[-w / 2 + 16, -h * .08], [w / 2 - 16, -h * .08]], T.S.lw * .5, { line: P.mid, boil: .3 });
      stroke([[-w / 2 + 16, h * .14], [w / 2 - 30, h * .14]], T.S.lw * .5, { line: P.mid, boil: .3 });
      stroke([[-w / 2 + 16, h * .32], [w / 2 - 52, h * .32]], T.S.lw * .5, { line: P.mid, boil: .3 });
    }
  });
  if (o.label) T.text(o.label, 0, -h * .26, { font: `${Math.round(w * .115)}px Limelight`, fill: P.ink });
  pop();
}

// ———————————————————— A door (one of the four khane) ————————————————————
// o.open = 0..1 swing; label in Limelight on the lintel.
export function doorUnit(x, yFloor, w, hgt, o = {}) {
  const open = o.open || 0;
  // dark opening
  shape(rr(x - w / 2, yFloor - hgt, w, hgt, 10), { fill: P.ink, stroke: false, boil: 0 });
  shape(arc(x, yFloor - hgt + 10, w / 2, w / 2, Math.PI, TAU, 20), { fill: P.ink, stroke: false, boil: 0 });
  if (o.behind) o.behind();   // whoever stands in the opening (drawn over the dark, under the leaf)
  // the door leaf, swung by scaling around its left hinge
  push(); translate(x - w / 2, yFloor); scale(Math.max(.08, 1 - open * .82), 1); translate(-(x - w / 2), -yFloor);
  shape(rr(x - w / 2, yFloor - hgt, w, hgt, 10), {
    fill: P.light, shade: () => {
      shape(rr(x - w / 2 + 16, yFloor - hgt + 90, w - 32, hgt * .34, 8), { fill: P.mid, stroke: false, boil: .3 });
      shape(rr(x - w / 2 + 16, yFloor - hgt * .5, w - 32, hgt * .3, 8), { fill: P.mid, stroke: false, boil: .3 });
    }
  });
  shape(ell(x + w / 2 - 20, yFloor - hgt * .46, 8, 8, 14), { fill: P.dark, stroke: false });
  pop();
  // frame + lintel label
  stroke(arc(x, yFloor - hgt + 8, w / 2 + 8, w / 2 + 8, Math.PI, TAU, 20), T.S.lw * 1.1);
  stroke([[x - w / 2 - 8, yFloor - hgt + 8], [x - w / 2 - 8, yFloor]], T.S.lw * 1.1);
  stroke([[x + w / 2 + 8, yFloor - hgt + 8], [x + w / 2 + 8, yFloor]], T.S.lw * 1.1);
  if (o.label) T.text(o.label, x, yFloor - hgt - 34, { font: `${o.labelSize || 40}px Limelight`, fill: P.paper });
}

// ———————————————————— A reporter's box camera ————————————————————
export function boxCamera(x, y, k = 1, o = {}) {
  push(); translate(x, y); scale(k); if (o.rot) rotate(o.rot);
  shape(rr(-34, -30, 68, 56, 7), { fill: P.dmid });
  shape(ell(0, -2, 17, 17, 20), { fill: P.ink });
  shape(ell(0, -2, 8, 8, 14), { fill: P.pale, stroke: false });
  shape(rr(-8, -52, 16, 22, 4), { fill: P.light });           // flash pan on a stem
  shape(ell(0, -56, 13, 7, 14), { fill: P.white });
  if (o.flash) { const r = 46 * o.flash; shape(ell(0, -56, r, r * .6, 18), { fill: P.white, stroke: false, alpha: .5 * o.flash, boil: 0 }); }
  pop();
}

// ———————————————————— A fried-rice packet ————————————————————
export function ricePacket(x, y, k = 1, o = {}) {
  push(); translate(x, y); scale(k); if (o.rot) rotate(o.rot);
  shape(spline([[-26, 10], [-30, -12], [-12, -20], [12, -20], [30, -12], [26, 10], [10, 16], [-10, 16]], true, 5), { fill: P.paper });
  shape(arc(0, -18, 20, 9, Math.PI, TAU, 14), { fill: P.white });   // rice dome
  pop();
}

// ———————————————————— A newspaper (rolls down like a window shade) ————————————————————
export function newspaper(x, y, w, frac, o = {}) {
  const fullH = w * .78, h = Math.max(2, fullH * frac);
  push(); translate(x, y);
  shape(rect(-w / 2, 0, w, h), {
    fill: P.paper, shade: () => {
      if (frac > .25) {
        T.text('SUBAH KI KHABAR', 0, 44, { font: `${Math.round(w * .062)}px Limelight`, fill: P.ink });
        stroke([[-w / 2 + 18, 66], [w / 2 - 18, 66]], T.S.lw * .6, { line: P.ink, boil: .2 });
      }
      if (frac > .55) {
        T.text('FRIED RICE!', 0, 128, { font: `${Math.round(w * .105)}px Shrikhand`, fill: P.ink });
        for (let i = 0; i < 5; i++) stroke([[-w / 2 + 22, 168 + i * 26], [w * .06, 168 + i * 26]], T.S.lw * .45, { line: P.mid, boil: .2 });
        // little rice-bowl drawing on the right
        shape(arc(w * .27, 190, 52, 30, 0, Math.PI, 16), { fill: P.white });
        shape(arc(w * .27, 178, 44, 20, Math.PI, TAU, 14), { fill: P.white });
      }
    }
  });
  // the roll at the bottom edge
  shape(rr(-w / 2 - 8, h - 12, w + 16, 26, 13), { fill: P.dmid });
  pop();
}

// rain: deterministic streaks in a rect, phase from t
export function rain(x0, y0, x1, y1, t, n = 90, col = P.light) {
  for (let i = 0; i < n; i++) {
    const cyc = .55 + hash(i * 1.31) * .5;
    const u = (t / cyc + hash(i * 7.7)) % 1;
    const x = x0 + hash(i * 3.13) * (x1 - x0) + u * 26, y = y0 + u * (y1 - y0);
    stroke([[x, y], [x - 5, y + 17]], T.S.lw * .32, { line: col, boil: 0 });
  }
}
// heart puff for the kiss
export function heart(x, y, s, alpha = 1) {
  const pts = spline([[0, 10], [-16, -6], [-10, -18], [0, -8], [10, -18], [16, -6]], true, 6).map(p => [x + p[0] * s, y + p[1] * s]);
  shape(pts, { fill: P.white, alpha, lw: T.S.lw * .5 });
}
