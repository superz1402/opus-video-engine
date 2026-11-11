#!/usr/bin/env python3
"""music.py — original hot-jazz big-band score for the rubber-hose demo, synthesised
in numpy (no sample libraries on this machine). 120 BPM, beat = 0.5 s; every accent
sits on the same beat grid the picture breathes to. Sections follow timeline.json.
The band STOP at 50.0–52.0 is literal silence here — only the projector bed (mix.py)
sounds inside it. Output: out/score.wav (48 kHz stereo)."""
import json, os
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, 'timeline.json')))
SR = 48000
DUR = TL['dur']
N = int(DUR * SR)
BEAT = 0.5
R = np.random.default_rng(1931)
buf = np.zeros((N, 2))

def put(x, t, gain=1.0, pan=0.0):
    i = int(t * SR); n = min(len(x), N - i)
    if n <= 0: return
    gl, gr = gain * np.cos((pan + 1) * np.pi / 4), gain * np.sin((pan + 1) * np.pi / 4)
    buf[i:i + n, 0] += x[:n] * gl; buf[i:i + n, 1] += x[:n] * gr

def tt(d): return np.arange(int(d * SR)) / SR
def mf(m): return 440.0 * 2 ** ((m - 69) / 12)

# ————— instruments —————
def piano(m, d=.5, vel=.5):
    t = tt(d + .35); f = mf(m); x = np.zeros_like(t)
    for h, a in [(1, 1), (2, .55), (3, .3), (4, .18), (5, .1), (6, .06)]:
        x += a * np.sin(2 * np.pi * f * h * t) * np.exp(-t / (.5 / h + .12))
    return x / 2.2 * vel

def clarinet(m, d=.5, vel=.5):
    t = tt(d + .08); f = mf(m)
    vib = 1 + .004 * np.sin(2 * np.pi * 5.4 * t) * np.clip(t / .12, 0, 1)
    x = np.zeros_like(t)
    for h, a in [(1, 1), (3, .42), (5, .18), (7, .08), (2, .06)]:
        x += a * np.sin(2 * np.pi * f * h * t * vib)
    env = np.clip(t / .03, 0, 1) * np.exp(-np.clip(t - d, 0, None) / .05) * (1 - .18 * np.clip((t - d * .8) / (d * .2 + 1e-6), 0, 1))
    return x / 1.8 * env * vel

def trumpet(m, d=.4, vel=.5, mute=False, glide=0.0):
    t = tt(d + .1); f = mf(m)
    if glide: f = f * (1 + glide * np.exp(-t / .07))
    x = np.zeros_like(t)
    for h in range(1, 9):
        a = (1 / h) * (1.6 if 2 <= h <= 4 else 1.0)
        if mute: a *= (0.35 + 0.65 * abs(np.sin(np.pi * h / 3)))
        x += a * np.sin(2 * np.pi * f * h * t)
    env = np.clip(t / .018, 0, 1) * np.exp(-np.clip(t - d, 0, None) / .06)
    if mute: env *= (.8 + .2 * np.sin(2 * np.pi * 9 * t))
    return x / 2.6 * env * vel

def trombone(m, d=.5, vel=.5):
    t = tt(d + .12); f = mf(m) * (1 - .012 * np.exp(-t / .09))  # smear up into the note
    x = np.zeros_like(t)
    for h, a in [(1, 1), (2, .7), (3, .45), (4, .28), (5, .16), (6, .1)]:
        x += a * np.sin(2 * np.pi * f * h * t)
    env = np.clip(t / .045, 0, 1) * np.exp(-np.clip(t - d, 0, None) / .08)
    return x / 2.2 * env * vel

def tuba(m, d=.45, vel=.6):
    t = tt(d + .06); f = mf(m)
    x = np.sin(2 * np.pi * f * t) + .55 * np.sin(2 * np.pi * 2 * f * t) + .3 * np.sin(2 * np.pi * 3 * f * t) + .12 * np.sin(2 * np.pi * 4 * f * t)
    env = np.clip(t / .025, 0, 1) * np.exp(-np.clip(t - d * .75, 0, None) / .07)
    return x / 1.9 * env * vel

def banjo(m, d=.3, vel=.4):
    f = mf(m); per = max(2, int(SR / f)); n = int((d + .25) * SR)
    b = R.uniform(-1, 1, per); out = np.zeros(n); cur = b.copy(); idx = 0
    for i in range(n):
        out[i] = cur[idx]; nxt = cur[(idx + 1) % per]; cur[idx] = .5 * (cur[idx] + nxt) * .996; idx = (idx + 1) % per
    return out * vel

def xylo(m, d=.3, vel=.5):
    t = tt(d + .3); f = mf(m)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / .09) + .4 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t / .04)
    return x * vel

def woodblock(fr=2400, vel=.4):
    t = tt(.09); x = np.sin(2 * np.pi * fr * t) * np.exp(-t / .016) + .5 * np.sin(2 * np.pi * fr * 1.52 * t) * np.exp(-t / .009)
    return x * vel

def brush(d=.5, vel=.3):
    t = tt(d); n = R.standard_normal(len(t))
    # cheap lowpass by cumulative smoothing
    k = 24; n = np.convolve(n, np.ones(k) / k, 'same')
    return n * np.sin(np.pi * t / d) ** 1.5 * vel * 2.2

def snare_hit(vel=.5):
    t = tt(.16); n = R.standard_normal(len(t)); k = 8; n = np.convolve(n, np.ones(k) / k, 'same')
    return (n * np.exp(-t / .05) + .7 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / .03)) * vel

def kick(vel=.6):
    t = tt(.22); f = 130 * np.exp(-t / .05) + 42
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .09) * vel

def cymbal(d=.8, vel=.4):
    t = tt(d); x = np.zeros_like(t)
    for f, a in [(3200, .5), (4700, .4), (6100, .35), (8300, .25), (11300, .18)]:
        x += a * np.sin(2 * np.pi * f * t + R.random() * 6) * np.exp(-t / (d * .4))
    n = R.standard_normal(len(t)); x += .3 * n * np.exp(-t / .05)
    return x * vel

def slide_whistle(f0, f1, d, vel=.3):
    t = tt(d); f = f0 * (f1 / f0) ** (t / d)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + .15 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)
    e = np.minimum(1, t / .03) * np.minimum(1, (d - t) / .06)
    return x * e * vel

def chord(midis, inst, t, d, vel, pan=0.0):
    for m in midis: put(inst(m, d, vel), t, 1.0, pan)

# ————— harmony helpers (MIDI) —————
# chords as (root, [tones]) in close position around octave 3–4
CH = {
    'F':  (41, [53, 57, 60]), 'Bb': (46, [58, 62, 65]), 'C7': (48, [55, 58, 64]),
    'Dm': (50, [57, 62, 65]), 'G':  (43, [55, 59, 62]), 'D7': (50, [57, 60, 66]),
    'Gm': (43, [55, 58, 62]), 'A7': (45, [55, 57, 61]),
}
def oompah(t, name, vel=.8):
    root, tones = CH[name]
    put(tuba(root, .42, .5 * vel), t, 1.0, -.15)
    put(tuba(root + 7, .42, .42 * vel), t + BEAT, 1.0, -.15)
    for b_ in (1, 3):
        for m in tones: put(banjo(m, .3, .16 * vel), t + b_ * BEAT, 1.0, .2)
def stride(t, name, vel=.7):
    root, tones = CH[name]
    put(piano(root + 12, .3, .34 * vel), t, 1.0, -.2)
    for m in tones: put(piano(m, .3, .2 * vel), t + BEAT, 1.0, -.1)
    put(piano(root + 19, .3, .3 * vel), t + 2 * BEAT, 1.0, -.2)
    for m in tones: put(piano(m + 12, .3, .18 * vel), t + 3 * BEAT, 1.0, -.1)
def brushes_bar(t, vel=.8):
    for b_ in range(4): put(brush(.42, .16 * vel), t + b_ * BEAT, 1.0, .1)
    put(snare_hit(.2 * vel), t + 2 * BEAT, 1.0, .1)

# ————— the theme (original; beats are offsets within the phrase) —————
# (beat, midi, len_beats) — a syncopated 4-bar phrase in F
THEME = [
    (0, 65, 1), (1, 69, .5), (1.5, 72, .5), (2, 77, 1.5), (3.5, 76, .5),
    (4, 74, 1), (5, 70, .5), (5.5, 69, .5), (6, 67, 1), (7, 69, .5), (7.5, 72, .5),
    (8, 65, 1), (9, 69, .5), (9.5, 72, .5), (10, 75, 1.5), (11.5, 74, .5),
    (12, 72, 2.5), (14.5, 69, .5), (15, 65, 1),
]
def theme(t0, inst, vel=.5, shift=0, pan=0.0, until=None):
    for b_, m, ln in THEME:
        if until is not None and b_ >= until: continue
        put(inst(m + shift, ln * BEAT * .96, vel), t0 + b_ * BEAT, 1.0, pan)

K = TL['k']

# ————— S_title 0–4: fanfare + theme head —————
chord([53, 57, 60, 65], piano, 0, .5, .5); put(tuba(41, .5, .7), 0); put(cymbal(.9, .35), 0, 1.0, .3); put(kick(.7), 0)
theme(0.0, lambda m, d, v: trumpet(m, d, v), .42)
for i in range(4): oompah(i * 2 * BEAT * 2 / 2, 'F' if i % 2 == 0 else 'F', .7) if False else None
for bar_i in range(2):
    oompah(bar_i * 4 * BEAT, 'F', .75)
put(slide_whistle(700, 1500, .45), 3.4, 1.0, -.2)

# ————— S_lane 4–19: ragtime vamp under the narration —————
for bar_i, t0 in enumerate(np.arange(4.0, 18.9, 4 * BEAT)):
    name = 'F' if bar_i % 2 == 0 else 'C7'
    oompah(t0, name, .62); put(brush(.45, .13), t0 + BEAT, 1.0, .1); put(brush(.45, .13), t0 + 3 * BEAT, 1.0, .1)
# sparse clarinet comments in the line's breaths
for t0, m in [(6.5, 72), (7.5, 69), (10.5, 74), (11.5, 72), (15.0, 77), (16.5, 76), (17.5, 74)]:
    put(clarinet(m, .8, .3), t0, 1.0, .15)

# ————— S_dinner 19–29.92: the theme, warm —————
theme(19.0, clarinet, .44, 0, .1)
for bar_i, t0 in enumerate(np.arange(19.0, 29.9, 4 * BEAT)):
    stride(t0, ['F', 'Bb', 'F', 'C7'][bar_i % 4], .6); brushes_bar(t0, .55)
put(cymbal(.7, .3), K['kiss'] + .25, 1.0, .3)
for i, m in enumerate([77, 81, 84, 89]): put(piano(m, .4, .3), K['kiss'] + .3 + i * .09, 1.0, .2)   # kiss gliss

# ————— S_doorway 29.92–43: brighter, trumpet answers —————
theme(30.0, lambda m, d, v: trumpet(m, d, v, mute=False), .36, 0, -.1)
for bar_i, t0 in enumerate(np.arange(30.0, 42.9, 4 * BEAT)):
    oompah(t0, ['F', 'Bb', 'C7', 'F'][bar_i % 4], .8); brushes_bar(t0, .7)
for t0 in (38.13, 38.63):  # the car's honks, played by the trumpet as written
    put(trumpet(70, .3, .55), t0, 1.0, .25); put(trumpet(70, .3, .4), t0, 1.0, .1)

# ————— S_news 43–50: roll, then a muted fragment —————
for i in range(9): put(snare_hit(.16), 43.0 + i * .11, 1.0, .1)
theme(44.5, lambda m, d, v: trumpet(m, d, v * .8, mute=True), .3, -12, .1, until=8)   # half-phrase only: nothing may ring into the 50.0 band stop
for bar_i, t0 in enumerate(np.arange(44.0, 49.9, 4 * BEAT)):
    oompah(t0, 'F' if bar_i % 2 == 0 else 'C7', .45)

# ————— S_stop 50–52: NOTHING. The band has stopped. —————

# ————— S_clock + allegation 52–73: lone tuba, low clarinet —————
for t0, m in [(53.0, 41), (55.5, 43), (58.5, 41), (61.0, 38), (64.0, 41), (67.0, 43), (70.0, 41)]:
    put(tuba(m, 1.6, .34), t0, 1.0, -.2)
for t0, m in [(59.0, 53), (63.0, 51), (67.5, 53)]:
    put(clarinet(m, 2.6, .2), t0, 1.0, .15)
put(trombone(46, 1.8, .22), 65.0, 1.0, 0)

# ————— S_desk 73–88.5: xylophone + muted trumpet —————
XY = [(0, 77, .5), (.5, 76, .5), (1, 74, .5), (1.5, 72, .5), (2, 74, 1), (3, 69, 1),
      (4, 72, .5), (4.5, 74, .5), (5, 76, .5), (5.5, 77, .5), (6, 76, 1), (7, 74, 1)]
for rep in range(2):
    for b_, m, ln in XY: put(xylo(m, ln * BEAT, .3), 73.5 + rep * 8 * BEAT + b_ * BEAT, 1.0, .15)
for bar_i, t0 in enumerate(np.arange(73.0, 88.4, 4 * BEAT)):
    stride(t0, ['F', 'Dm', 'Bb', 'C7'][bar_i % 4], .5); brushes_bar(t0, .5)
theme(80.0, lambda m, d, v: trumpet(m, d, v * .7, mute=True), .26, 0, -.15)

# ————— S_doors 88.5–104: theme restated, full band —————
theme(88.5, clarinet, .42, 0, .1)
theme(96.5, lambda m, d, v: trumpet(m, d, v), .4, 0, -.1)
for bar_i, t0 in enumerate(np.arange(88.5, 103.9, 4 * BEAT)):
    oompah(t0, ['F', 'Bb', 'F', 'C7'][bar_i % 4], .8); stride(t0, ['F', 'Bb', 'F', 'C7'][bar_i % 4], .55); brushes_bar(t0, .65)
DOOR_OPEN = [99.03, 100.53, 102.03, 103.53]
for i, t0 in enumerate(DOOR_OPEN):  # a brass stab as each door swings
    chord([53, 57, 60], lambda m, d, v: trombone(m, d, v), t0, .6, .3); put(cymbal(.5, .2), t0, 1.0, .3)

# ————— S_outro 104–116: out-chorus in G, final hit, coda —————
theme(104.0, lambda m, d, v: trumpet(m, d, v), .44, 2, -.05)
for bar_i, t0 in enumerate(np.arange(104.0, 111.9, 4 * BEAT)):
    oompah(t0, 'G' if bar_i % 2 == 0 else 'D7', .85); brushes_bar(t0, .75)
    put(kick(.5), t0); put(kick(.5), t0 + 2 * BEAT)
chord([55, 59, 62, 67], piano, 112.5, 1.4, .5); put(tuba(43, 1.2, .6), 112.5); put(cymbal(1.4, .35), 112.5, 1.0, .3)
for i, m in enumerate([67, 62, 59]): put(clarinet(m, 1.1, .26), 113.4 + i * .45, 1.0, .1)
put(piano(55, 1.8, .3), 114.8); put(piano(59, 1.8, .26), 114.8); put(piano(62, 1.8, .26), 114.8)

mx = np.max(np.abs(buf)) or 1
buf = buf / mx * .9
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
sf.write(os.path.join(HERE, 'out', 'score.wav'), buf.astype(np.float32), SR)
print('score.wav', DUR, 's | peak', round(float(mx), 3), '| stop check 50–52 RMS dB:',
      round(float(20 * np.log10(np.sqrt(np.mean(buf[int(50.2 * SR):int(51.8 * SR)] ** 2)) + 1e-12)), 1))
