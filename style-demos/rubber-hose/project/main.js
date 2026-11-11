// main.js — entry: film mode (default) + ?mode=sheet model sheet for the look check
import * as T from './toon.js';
import { P } from './chars.js';
import { TL, DUR, shotAt } from './timeline.js';
const Q = new URLSearchParams(location.search), MODE = Q.get('mode') || 'film';
const cv = document.getElementById('c');
const CW = +(Q.get('w') || 1920), CH = +(Q.get('h') || 1080);
cv.width = CW; cv.height = CH; cv.style.width = CW + 'px'; cv.style.height = CH + 'px';
T.init(cv);

let draw = null;
if (MODE === 'sheet') {
  const F = await import('./figs.js');
  draw = t => {
    const g = T.g; g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#8C8981'; g.fillRect(0, 0, CW, CH);
    T.frame(t);
    const tq = Math.floor(t * 12) / 12, b = Math.cos(Math.floor(t * 12) / 12 * Math.PI * 4);
    const label = (x, y, s) => { g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#0E0D0C'; g.font = '30px Limelight'; g.textAlign = 'center'; g.fillText(s, x, y); g.restore(); };
    F.figure(300, 460, { k: 1.15, body: 'jacket', b, eyes: { lx: .3 }, mouth: { type: 'grin' }, armL: { x: -80, y: -60, hand: 'open' }, armR: { x: 90, y: -190, hand: 'wave', front: true } });
    label(300, 520, 'MR. JACKET');
    F.figure(760, 460, { k: 1.15, body: 'dress', hat: 'flop', b, eyes: { lx: -.5 }, mouth: { type: 'smile' }, armL: { x: -110, y: -120, hand: 'open', front: true }, armR: { x: 70, y: -60, hand: 'grab' } });
    label(760, 520, 'MISS ROSE');
    F.figure(1130, 460, { k: .95, body: 'plain', col: '#6B6963', bow: true, b, mouth: { type: 'smile' } });
    label(1130, 520, 'THE DAUGHTER');
    F.figure(1420, 460, { k: 1.05, body: 'coat', col: '#6B6963', hat: 'bowler', b, mouth: { type: 'grin' }, armL: { x: -60, y: -130, hand: 'grab' } });
    F.boxCamera(1358, 322, 1, {});
    label(1420, 520, 'A REPORTER');
    F.car(420, 900, { k: 1.25, b, spin: 0, puff: (t * .8) % 1 });
    label(420, 960, 'THE CAR');
    F.clockChar(880, 760, { k: 1.5, b, pend: Math.sin(t * 4) * .4, mA: -.6, hA: 2.4, lx: .3 });
    label(880, 960, 'THE CLOCK');
    F.photo(1330, 730, 380, { b, alive: 1, stamp: 1 });
    label(1330, 960, 'THE PHOTO');
    F.doorUnit(1730, 950, 240, 430, { open: .75, label: 'RECORD', labelSize: 30, behind: () => F.figure(1730, 950, { k: .75, body: 'jacket', b, mouth: { type: 'grin' } }) });
    label(1730, 1010, 'A DOOR');
  };
}
await document.fonts.ready;
for (const f of ['46px Limelight', '36px "IM Fell English SC"', '40px Shrikhand', '30px Limelight']) await document.fonts.load(f);
if (MODE === 'film') {
  const { makeFilm, post } = await import('./film.js');
  const BG = await import('./bg.js');
  const S = await import('./scenes.js');
  const F = makeFilm(cv); T.init(F.scene);
  const bgr = BG.paintRoom(), bgl = BG.paintLane(), bgd = BG.paintDining(), bgf = BG.paintFront();
  T.init(F.scene); S.initScenes(bgr, bgl, bgd, bgf, F.sg);
  const FN = { title: S.shotTitle, lane: S.shotLane, dinner: S.shotDinner, doorway: S.shotDoorway, news: S.shotNews, freeze: S.shotFreeze, desk: S.shotDesk, doors: S.shotDoors };
  const cutAt = TL.shots.map(s => s[0]);
  const nosub = Q.get('nosub') === '1';
  draw = t => {
    t = Math.min(t, DUR - 1e-4);
    const sg = F.sg; sg.setTransform(1, 0, 0, 1, 0, 0); sg.fillStyle = '#000'; sg.fillRect(0, 0, 1920, 1080);
    const sh = shotAt(t);
    FN[sh[2]](t);
    if (!nosub) S.subtitles(t);
    const f = Math.round(t * 24), jump = cutAt.some(c => c > 0 && Math.abs(Math.round(c * 24) - f) === 0) ? 3 : 0;
    post(F, t, { jump });
  };
  window.DUR = DUR;
  window.EV = [...TL.ev, ...TL.vo.map(v => ({ t: v.start, type: 'vo', id: v.id, srcStart: v.srcStart, dur: v.dur }))];
}
window.DUR = window.DUR || DUR;
window.render = t => draw(t);
window.READY = true;
