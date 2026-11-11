#!/usr/bin/env python3
"""mix.py — foley (synthesised by material) + radio-chain narration + score + ducking
+ 1930s optical-soundtrack ageing → out/mix.wav. Events come from events.json
(node core/render/events.mjs). The band-stop (50–52 s) contains only the projector
bed: no score (music.py wrote silence), no foley events exist there by design."""
import os, sys, json, numpy as np, soundfile as sf
from scipy.signal import resample_poly
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB', os.path.expanduser('~/workspace/research/nvidia-spy-doc/lemo-opuscar-upstream'))
sys.path.insert(0, os.path.join(LIB, 'core/audio'))
import sfx as X
from sfx import SR, t_, env_exp, bp, lp, hp, norm, add

R = np.random.default_rng(1932)
def nz(d): return R.standard_normal(len(t_(d)))
ev = json.load(open(os.path.join(HERE, 'events.json'))); DUR = ev['dur']; E = ev['ev']
N = int(round(DUR * SR))
FX = np.zeros((N, 2)); VOX = np.zeros((N, 2)); BED = np.zeros((N, 2))

# ———————————————————— Foley recipes ————————————————————
def sine_sweep(f0, f1, d, curve=1.0):
    t = t_(d); f = f0 + (f1 - f0) * (t / d) ** curve; return np.sin(2 * np.pi * np.cumsum(f) / SR)
def partials(fs, d, taus, amps=None):
    t = t_(d); amps = amps or [1] * len(fs)
    return sum(a * np.sin(2 * np.pi * f * t + R.random() * 6) * np.exp(-t / tau) for f, tau, a in zip(fs, taus, amps))
def porcelain(p=1.0, d=.25):
    x = partials([2750 * p, 4180 * p, 6320 * p, 1650 * p], d, [.07, .05, .03, .09], [1, .7, .4, .5])
    return norm(x + hp(nz(d), 3000) * env_exp(d, .002) * .6)
def woodblock(f=2400, d=.09):
    t = t_(d); x = np.sin(2 * np.pi * f * t) * np.exp(-t / .018) + .5 * np.sin(2 * np.pi * f * 1.52 * t) * np.exp(-t / .01)
    return norm(x + hp(nz(d), 2000) * env_exp(d, .0015) * .4)
def boing(f=210, d=.6, depth=.35):
    t = t_(d); f_ = f * (1 + depth * np.sin(2 * np.pi * 13 * t) * np.exp(-t * 4)); ph = 2 * np.pi * np.cumsum(f_) / SR
    return norm((np.sin(ph) + .4 * np.sin(2 * ph) + .2 * np.sin(3 * ph)) * np.exp(-t * 4.5))
def ratchet(d):
    out = np.zeros(int(d * SR) + 2000)
    for k in range(14):
        s = int((1 - (1 - k / 14) ** 1.6) * d * SR); c = woodblock(3200, .03) * .6; out[s:s + len(c)] += c
    return norm(out)
def rubber_creak(d, f0=90, f1=260):
    t = t_(d); f = f0 * (f1 / f0) ** (t / d); saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    return norm(bp(saw, 300, 2500) * (.6 + .4 * np.abs(np.sin(2 * np.pi * 17 * t))) * np.sin(np.pi * t / d) ** .5)
def seq(clips, total):
    out = np.zeros(int(total * SR))
    for t0, c in clips:
        s0 = int(t0 * SR); n = max(0, min(len(c), len(out) - s0)); out[s0:s0 + n] += c[:n]
    return norm(out)
def clock_ticks(d):
    # ticks that accelerate as the clock's hands spin up (52 → K.stamp)
    out = np.zeros(int(d * SR) + 2000); tcur, gap = 0.0, .34
    while tcur < d - .05:
        s = int(tcur * SR); c = woodblock(2900 + (tcur / d) * 500, .03) * .5; out[s:s + len(c)] += c
        tcur += gap; gap = max(.07, gap * .86)
    return norm(out)
def card_snap(i=0):
    t = t_(.22)
    x = bp(nz(.22), 1400, 5200) * np.exp(-t / .05) * (0.7 + 0.3 * np.sin(2 * np.pi * 30 * t))
    return seq([(0, x), (0, woodblock(1900 + i * 90, .09) * .35)], .22)

RECIPES = {
    'glassTap': lambda e: (porcelain(1.15, .18), .3),
    'tick': lambda e: (woodblock(3300, .05), .26),
    'kissPop': lambda e: (seq([(0, norm(bp(nz(.05), 900, 3200) * env_exp(.05, .006))), (.02, sine_sweep(500, 1150, .09) * env_exp(.09, .03))], .14), .5),
    'chair': lambda e: (rubber_creak(.28, 160, 110), .3),
    'shutter': lambda e: (seq([(0, hp(nz(.02), 3000) * env_exp(.02, .002)), (0, partials([1800, 3100], .06, [.01, .006]))], .07), .4),
    'packet': lambda e: (norm(bp(nz(.16), 1600, 6000) * np.sin(np.pi * t_(.16) / .16)), .3),
    'hopIn': lambda e: (boing(300, .4, .3), .45),
    'shadeRoll': lambda e: (ratchet(e.get('d', .8)) * .55, .5),
    'clockSpin': lambda e: (clock_ticks(e.get('d', 5.0)), .5),
    'stamp': lambda e: (seq([(0, X.thump(1, 85)), (0, bp(nz(.12), 700, 2600) * env_exp(.12, .03) * .7)], .25), .7),
    'stepSoft': lambda e: (woodblock(660, .1) * .6, .17),
    'magnifier': lambda e: (norm(sine_sweep(1400, 2100, e.get('d', 2.0)) * np.sin(np.pi * t_(e.get('d', 2.0)) / e.get('d', 2.0)) * .4 + bp(nz(e.get('d', 2.0)), 3000, 6000) * .05), .14),
    'cardDeal': lambda e: (card_snap(e.get('i', 0)), .5),
    'clockCard': lambda e: (partials([1568, 3136], .8, [.4, .15], [1, .4]), .4),
    'doorCreak': lambda e: (rubber_creak(.7, 120 + e.get('i', 0) * 22, 70), .34),
    'irisGrab': lambda e: (seq([(0, X.whoosh(.3)), (.55, X.thump(1, 80))], .8), .5),
    'freezeMark': lambda e: (np.zeros(8), 0.0),
    'honk': lambda e: (np.zeros(8), 0.0),   # the car's honks are written into the score (trumpet blasts)
}
for e in E:
    ty = e['type']
    if ty in ('vo',): continue
    if ty not in RECIPES: print('no recipe for', ty); continue
    x, g = RECIPES[ty](e)
    add(FX, np.asarray(x, dtype=np.float64), e['t'], g, e.get('pan', 0))

# ———————————————————— rain bed (4–50 s; hushed indoors 13.5–30) ————————————————————
rain_t = np.arange(N) / SR
rain = lp(nz(DUR), 2600) * .5 + hp(nz(DUR), 5200) * .12
rg = np.clip((rain_t - 4) / 1.5, 0, 1) * np.clip((50.2 - rain_t) / .8, 0, 1)
rg *= .5 + .5 * (0.7 + 0.3 * np.sin(2 * np.pi * .11 * rain_t))          # slow wander
indoor = (rain_t > 13.5) & (rain_t < 30.0); rg[indoor] *= .4
FX[:, 0] += rain * rg * .16; FX[:, 1] += rain * rg * .15

# ———————————————————— Narration: radio microphone chain ————————————————————
src, sr0 = sf.read(os.path.join(HERE, 'voice', 'voice.wav'))
assert sr0 == 24000, sr0
src = resample_poly(src.astype(np.float64), 2, 1)
def room_ir(d=.28):
    t = t_(d); ir = R.standard_normal(len(t)) * np.exp(-t / .06); ir[0] = 1; return ir / np.abs(ir).sum() * 6
IR = room_ir()
vo_mask = np.zeros(N)
for e in E:
    if e['type'] != 'vo': continue
    a = int(e['srcStart'] * SR); b = int((e['srcStart'] + e['dur']) * SR)
    y = src[a:b].copy()
    peak = np.max(np.abs(y)) or 1.0; y = y / peak * .82
    y = hp(y, 260, 3); y = lp(y, 4600, 3)
    y = np.tanh(y / (np.abs(y).max() + 1e-9) * 2.2) / np.tanh(2.2)
    y = y + np.convolve(y, IR)[:len(y)] * .12
    y = X.compress(norm(y), .3, 3.0)
    add(VOX, norm(y), e['t'], 1.05)
    s = int(e['t'] * SR); vo_mask[max(0, s - 2400): s + len(y) + 4800] = 1

# ———————————————————— Score + ducking ————————————————————
mus, msr = sf.read(os.path.join(HERE, 'out', 'score.wav'))
assert msr == SR
if mus.ndim == 1: mus = np.stack([mus, mus], 1)
mus = mus[:N]; mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
from scipy.ndimage import uniform_filter1d
duck = uniform_filter1d(vo_mask, int(.12 * SR))
mus = mus * (1 - .62 * duck)[:, None]

# ———————————————————— Optical soundtrack ageing (music + foley bus) ————————————————————
def optical(x):
    y = np.stack([hp(lp(x[:, c], 6200, 2), 110, 2) for c in range(2)], 1)
    t = np.arange(N) / SR; dl = (.00035 * np.sin(2 * np.pi * .6 * t) + .00008 * np.sin(2 * np.pi * 7 * t)) * SR
    idx = np.clip(np.arange(N) - 40 + dl, 0, N - 1); i0 = idx.astype(int); fr = idx - i0; i1 = np.minimum(i0 + 1, N - 1)
    y = y[i0] * (1 - fr)[:, None] + y[i1] * fr[:, None]
    return np.tanh(y * 1.4) / np.tanh(1.4)
bus = optical(mus * 1.0 + FX * .9)
# noise floor + crackle + projector gate clatter — the only sound inside the band-stop
hiss = bp(R.standard_normal(N), 800, 6000) * .0035
crk = np.zeros(N); pos = R.random(int(DUR * 9)) * (N - 200)
for p in pos.astype(int): L_ = R.integers(8, 60); crk[p:p + L_] += R.standard_normal(L_) * np.exp(-np.arange(L_) / 10) * (.02 + R.random() * .05)
crk = hp(crk, 900)
proj = np.zeros(N); per = SR / 24
for k_ in range(int(DUR * 24)):
    s = int(k_ * per); c = hp(R.standard_normal(200), 1500) * np.exp(-np.arange(200) / 30); proj[s:s + 200] += c[:max(0, min(200, N - s))] * .012
proj += np.sin(2 * np.pi * 50 * np.arange(N) / SR) * .002 + lp(R.standard_normal(N), 180) * .006
BED[:, 0] = hiss + crk + proj; BED[:, 1] = hiss * .9 + crk + proj * .95
mix = bus + VOX + BED
for c in range(2): mix[:, c] = X.limit(mix[:, c], .95)
mix = mix / np.abs(mix).max() * .89
sf.write(os.path.join(HERE, 'out', 'mix.wav'), mix.astype(np.float32), SR)
def db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
m = vo_mask > 0
frz = (rain_t > 50.2) & (rain_t < 51.8)
print('mix.wav', DUR, 's | VO RMS', round(db(VOX[m]), 1), 'dB | music-under-VO', round(db(bus[m]), 1),
      'dB | freeze window (50.2–51.8) total RMS', round(db(mix[int(50.2 * SR):int(51.8 * SR)]), 1), 'dB (bed only)')
