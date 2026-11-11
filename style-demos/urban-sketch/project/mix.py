#!/usr/bin/env python3
"""Mix for the Urban Sketch 2-min demo: Swara voice blocks (Actions Edge-TTS)
placed on the shared timeline + an original jazz waltz in Dm (walking bass,
brushes, piano, flute & clarinet leads — the style's sound family) and
procedural foley driven by timeline EV events (pen, brush, rain, page turn,
cards, drip). Output: out/mix.wav 48 kHz stereo. Voice is never stretched."""
import json, os
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, butter, lfilter

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, 'timeline.json')))
SR = 48000
DUR = TL['dur']
N = int(DUR * SR)
rng = np.random.default_rng(2025)

def lp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), 'low'); return lfilter(b, a, x)
def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, lo, hi, order=2):
    return hp(lp(x, hi, order), lo, order)

mixL = np.zeros(N); mixR = np.zeros(N)
def add(sig, at, gain=1.0, pan=0.0, bus=None):
    i = int(at * SR); n = min(len(sig), N - i)
    if n <= 0: return
    gl, gr = gain * np.cos((pan + 1) * np.pi / 4), gain * np.sin((pan + 1) * np.pi / 4)
    if bus is not None:
        bus[0][i:i + n] += sig[:n] * gl; bus[1][i:i + n] += sig[:n] * gr
    else:
        mixL[i:i + n] += sig[:n] * gl; mixR[i:i + n] += sig[:n] * gr

musL = np.zeros(N); musR = np.zeros(N); MUS = (musL, musR)

# ---------------- voice ----------------
src, sr0 = sf.read(os.path.join(HERE, 'voice', 'actions', 'voice-input.audio.wav'))
assert sr0 == 24000, sr0
src = resample_poly(src.astype(np.float64), 2, 1)
for v in TL['voice']:
    a = int(v['srcStart'] * SR); b = int((v['srcStart'] + v['dur']) * SR)
    blk = src[a:b].copy()
    peak = np.max(np.abs(blk)) or 1.0
    blk = blk / peak * 0.82
    add(blk, v['start'], gain=0.95, pan=0.0)

# ---------------- synthesis helpers (all vectorised) ----------------
def ks_pluck(freq, dur=0.6, vel=0.2, damp=0.996):
    """Karplus-Strong via IIR: noise burst into a feedback delay."""
    n = int(dur * SR); p = max(2, int(round(SR / freq)))
    x = np.zeros(n); x[:p] = rng.uniform(-1, 1, p)
    a = np.zeros(p + 2); a[0] = 1.0; a[p] = -0.5 * damp; a[p + 1] = -0.5 * damp
    y = lfilter([1.0], a, x)
    env = np.exp(-np.arange(n) / SR * 2.2)
    return y * env * vel

def bass_note(midi, dur=0.5, vel=0.30):
    f = 440 * 2 ** ((midi - 69) / 12)
    n = int(dur * SR); t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) * 0.85 + np.sin(2 * np.pi * 2 * f * t) * 0.30 + np.sin(2 * np.pi * 3 * f * t) * 0.12)
    env = (1 - np.exp(-t * 60)) * np.exp(-t * 3.4)
    return lp(y * env, 620) * vel

def wind_note(midi, dur=1.0, vel=0.16, kind='flute'):
    f = 440 * 2 ** ((midi - 69) / 12)
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.0035 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t * 3, 0, 1)
    ph = 2 * np.pi * f * np.cumsum(vib) / SR
    if kind == 'flute':
        y = np.sin(ph) * 0.9 + np.sin(2 * ph) * 0.28 + np.sin(3 * ph) * 0.07
        y += rng.standard_normal(n) * 0.012
    else:  # clarinet: odd harmonics, softer
        y = np.sin(ph) * 0.85 + np.sin(3 * ph) * 0.30 + np.sin(5 * ph) * 0.08
        y = lp(y, 1150)
    env = np.clip(t * 14, 0, 1) * np.clip((dur - t) * 7, 0, 1)
    return y * env * vel

def noise_burst(dur, kind='brush', vel=0.12):
    n = int(dur * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    if kind == 'brush':
        y = bp(nz, 3400, 8200); env = np.clip(t * 9, 0, 1) * np.exp(-t * 5.5)
    elif kind == 'tick':
        y = hp(nz, 6800); env = np.exp(-t * 130)
    elif kind == 'pen':
        y = bp(nz, 1600, 7500)
        gate = 0.55 + 0.45 * np.sin(2 * np.pi * 27 * t + rng.uniform(0, 6)) * np.sin(2 * np.pi * 3.1 * t)
        env = np.clip(t * 30, 0, 1) * np.clip((dur - t) * 9, 0, 1) * np.clip(gate, 0.15, 1)
    elif kind == 'swish':
        y = bp(nz, 500, 2600); env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    elif kind == 'paper':
        y = hp(bp(nz, 1800, 7000), 900); env = np.exp(-t * 55)
    else:
        y = nz; env = np.exp(-t * 8)
    return y * env * vel

# ---------------- the waltz ----------------
BEAT = 0.44; BAR = BEAT * 3
CH = {  # root midi, piano voicing
    'Dm': (38, [62, 65, 69]), 'Gm': (43, [62, 67, 70]), 'A7': (45, [61, 64, 67]),
    'F':  (41, [65, 69, 72]), 'Bb': (46, [62, 70, 74]),
}
SECTIONS = [  # (t0, t1, progression, density) density: 0 sparse, 1 full
    (0.9,   19.05, ['Dm', 'Dm', 'Gm', 'A7', 'Dm', 'Gm', 'Dm', 'A7'], 1),
    (19.05, 41.10, ['Dm', 'F', 'Gm', 'A7', 'Dm', 'Gm', 'Bb', 'A7'], 1),
    (41.10, 47.88, ['Dm', 'Gm', 'Dm', 'A7'], 1),
    (51.68, 72.84, ['Dm', 'Dm', 'Gm', 'A7'], 0),
    (72.84, 88.01, ['Dm', 'Gm', 'Dm', 'A7'], 0),
    (88.01, 112.0, ['Dm', 'Gm', 'F', 'A7', 'Dm', 'Gm', 'Dm', 'A7', 'Dm'], 1),
]
for (t0, t1, prog, dens) in SECTIONS:
    nbars = int((t1 - t0) / BAR)
    for bar in range(nbars):
        bt = t0 + bar * BAR
        root, tones = CH[prog[bar % len(prog)]]
        nxt = CH[prog[(bar + 1) % len(prog)]][0]
        # walking bass: root, fifth/third, chromatic approach to next root
        add(bass_note(root, 0.5, 0.30 if dens else 0.27), bt, bus=MUS)
        add(bass_note(root + (7 if bar % 2 else 4), 0.42, 0.22), bt + BEAT, bus=MUS)
        add(bass_note(nxt + (12 if nxt < root else -1 if nxt > root + 2 else 14), 0.42, 0.22), bt + 2 * BEAT, bus=MUS)
        # brushes: swirl on 1, ticks on 2 & 3
        add(noise_burst(0.5, 'brush', 0.11 if dens else 0.08), bt, bus=MUS)
        add(noise_burst(0.07, 'tick', 0.05), bt + BEAT, bus=MUS)
        add(noise_burst(0.07, 'tick', 0.05), bt + 2 * BEAT, bus=MUS)
        # piano stabs on 2 & 3
        if dens or bar % 2 == 0:
            for beat_i in (1, 2):
                for m in tones:
                    add(ks_pluck(440 * 2 ** ((m - 69) / 12), 0.55, 0.075), bt + beat_i * BEAT + rng.uniform(-0.008, 0.008), bus=MUS)
# leads (original lines, hand-placed on the grid)
for (tt, m, d) in [(11.9, 74, 0.8), (12.75, 77, 0.8), (13.6, 81, 1.7), (15.4, 79, 0.8), (16.25, 77, 0.8), (17.1, 76, 1.6)]:
    add(wind_note(m, d, 0.15, 'flute'), tt, bus=MUS)
for (tt, m, d) in [(30.3, 69, 0.8), (31.15, 72, 0.8), (32.0, 74, 1.6), (34.8, 72, 0.8), (35.65, 69, 1.4)]:
    add(wind_note(m, d, 0.13, 'clarinet'), tt, bus=MUS)
for (tt, m, d) in [(92.5, 74, 0.8), (93.35, 77, 0.8), (94.2, 81, 1.7), (96.1, 84, 0.8), (96.95, 81, 1.6),
                   (98.7, 79, 0.8), (99.55, 77, 0.8), (100.4, 76, 1.7), (102.9, 74, 2.8)]:
    add(wind_note(m, d, 0.15, 'flute'), tt, bus=MUS)
# pizzicato ticks under the street scene
pt = 41.3
while pt < 47.6:
    add(ks_pluck(440 * 2 ** (([74, 77, 81, 79][int(pt * 2) % 4] - 69) / 12), 0.3, 0.06), pt, bus=MUS)
    pt += BEAT

# music ducking: under voice, deep under the whisper, out for the silent bar
tt_all = np.arange(N) / SR
duck = np.ones(N)
for v in TL['voice']:
    m = (tt_all > v['start'] - 0.25) & (tt_all < v['start'] + v['dur'] + 0.3)
    duck[m] = np.minimum(duck[m], 0.5)
duck[(tt_all > 23.9) & (tt_all < 28.6)] = 0.26                       # the whisper: brushes nearly alone
duck[(tt_all > 47.83) & (tt_all < 51.73)] = 0.0                      # one bar of true silence (music)
duck[tt_all > 110.5] *= np.clip(1 - (tt_all[tt_all > 110.5] - 110.5) / 6.0, 0.25, 1)
from scipy.ndimage import uniform_filter1d
duck = uniform_filter1d(duck, size=int(0.18 * SR))
musL *= duck; musR *= duck
mixL += musL; mixR += musR

# ---------------- ambience ----------------
room = lp(rng.standard_normal(N), 220)
room_env = np.full(N, 0.012); room_env[(tt_all > 47.83) & (tt_all < 51.73)] = 0.0
add(room * room_env, 0, 1.0)
rain = bp(rng.standard_normal(N), 900, 2600)
rain_env = np.zeros(N)
seg = (tt_all > 9.6) & (tt_all < 47.9)
rain_env[seg] = 0.045 * np.clip((tt_all[seg] - 9.6) / 1.6, 0, 1) * np.clip((47.9 - tt_all[seg]) / 0.8, 0, 1)
add(rain * rain_env, 0, 1.0, pan=-0.1); add(rain * rain_env * 0.9, 0.02, 1.0, pan=0.15)
drop_rng = np.random.default_rng(7)
for _ in range(150):  # droplet ticks on the awning
    dt_ = drop_rng.uniform(10.2, 47.6)
    f = drop_rng.uniform(1800, 4200); n = int(0.03 * SR); tt = np.arange(n) / SR
    add(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 160) * drop_rng.uniform(0.008, 0.03), dt_, pan=drop_rng.uniform(-0.7, 0.7))

# ---------------- foley from EV ----------------
for e in TL['EV']:
    ty, at, gn = e['type'], e['t'], e.get('gain', 0.7)
    if ty == 'pen':
        add(noise_burst(e.get('dur', 1.0), 'pen', 0.16 * gn), at, pan=-0.05)
    elif ty == 'brush':
        add(noise_burst(e.get('dur', 1.5), 'swish', 0.20 * gn), at)
    elif ty == 'tick':
        add(noise_burst(0.06, 'tick', 0.5 * gn), at)
    elif ty == 'cardoor':
        n = int(0.16 * SR); tt = np.arange(n) / SR
        add(np.sin(2 * np.pi * (150 - 700 * tt) * tt) * np.exp(-tt * 26) * 0.5 * gn, at)
        add(noise_burst(0.04, 'paper', 0.3 * gn), at + 0.02)
    elif ty == 'packets':
        for k in range(5):
            add(noise_burst(0.05, 'paper', 0.4 * gn), at + k * (e.get('dur', 2.6) / 5) + rng.uniform(0, 0.08), pan=rng.uniform(-0.4, 0.4))
    elif ty == 'pageturn':
        add(noise_burst(e.get('dur', 2.4) * 0.55, 'swish', 0.5 * gn), at)
        add(lp(noise_burst(0.5, 'brush', 0.3 * gn), 900), at + 1.15)
        add(noise_burst(0.3, 'paper', 0.35 * gn), at + 2.05)
    elif ty == 'card':
        n = int(0.1 * SR); tt = np.arange(n) / SR
        add(np.sin(2 * np.pi * 165 * tt) * np.exp(-tt * 42) * 0.34 * gn, at)
        add(noise_burst(0.04, 'paper', 0.3 * gn), at)
    elif ty == 'drip':
        n = int(0.24 * SR); tt = np.arange(n) / SR
        add(np.sin(2 * np.pi * (1450 - 2400 * tt) * tt) * np.exp(-tt * 15) * 0.22 * gn, at)

mix = np.stack([mixL, mixR], axis=1)
peak = np.max(np.abs(mix)) or 1.0
if peak > 0.92: mix *= 0.92 / peak
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
sf.write(os.path.join(HERE, 'out', 'mix.wav'), mix, SR)
print(f"mix.wav written: {DUR:.2f}s, peak {peak:.3f}")
