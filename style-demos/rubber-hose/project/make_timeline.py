#!/usr/bin/env python3
"""Build timeline.js / timeline.json / cues.json from the Actions voice timings.
Rubber-hose demo: Swara @ +12%, 6 blocks, 95.33 s of speech placed into a
116.0 s film (120 s target ± 6). Pads are music space only — title, car-gag
tail, a 2.2 s BAND STOP freeze before L4, and the doors/iris outro.
Voice is NEVER time-stretched. All scene cuts snap to the 0.5 s beat grid
(120 BPM = 12 frames/beat at 24 fps)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
VA = os.path.join(HERE, 'voice', 'actions')
timing = json.load(open(os.path.join(VA, 'voice-input.timing.json')))
words = json.load(open(os.path.join(VA, 'voice-input.words.json')))
blocks = [timing[k] for k in sorted(timing)]  # b001..b006
assert len(blocks) == 6

PLACE = [4.0, 19.0, 43.0, 52.0, 73.0, 88.5]   # film start of L1..L6 (beat grid)
DUR = 116.0
IDS = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6']

VO = []
for i, b in enumerate(blocks):
    VO.append({'id': IDS[i], 'start': PLACE[i], 'srcStart': b['start'], 'dur': b['dur']})

def block_words(i):
    b = blocks[i]
    return [w for w in words if b['start'] - 0.01 <= w['t'] < b['start'] + b['dur'] + 0.01]

def wt(i, pred, occurrence=0):
    """film time of the n-th word in block i matching pred(word_lower)."""
    hits = [w for w in block_words(i) if pred(w['w'].lower().strip('.,:—-'))]
    w = hits[occurrence]
    return round(PLACE[i] + (w['t'] - blocks[i]['start']), 3)

def wt_end(i, pred, occurrence=0):
    hits = [w for w in block_words(i) if pred(w['w'].lower().strip('.,:—-'))]
    w = hits[occurrence]
    return round(PLACE[i] + (w['t'] + w['d'] - blocks[i]['start']), 3)

K = {
    'glass':    wt(0, lambda w: w == 'sheeshe'),                    # push through the window glass
    'table':    wt(0, lambda w: w == 'table'),                      # "ek table par" — inside now
    'gulabi':   wt(1, lambda w: w == 'gulabi'),                     # cut to closer dinner framing
    'kandhe':   wt(1, lambda w: w == 'kandhe'),                     # hand on shoulder
    'kiss':     wt(1, lambda w: w == 'kiss'),                       # the kiss lands
    'dinnerEnd': wt(1, lambda w: w == 'dinner'),                    # cut to the doorway
    'client':   wt(1, lambda w: w == 'client'),                     # he stops to say goodbye
    'gaadi':    wt(1, lambda w: w == 'gaadi'),                      # she hops into the car
    'stamp':    wt_end(3, lambda w: w.startswith('jaayegi')),      # SABOOT No.1 stamp slams
    'intel':    wt(3, lambda w: w == 'intelligence'),               # magnifier pass
    'agent':    wt_end(3, lambda w: w == 'thi', 0),                 # "...ek agent thi."
    'ruko':     PLACE[4],                                           # "Lekin ruko." — photo set down on desk
    'deal':     wt(4, lambda w: w == 'karke'),                      # "ek-ek karke" — cards dealt per beat
    'ghadi':    wt(4, lambda w: w == 'ghadi'),                      # "ek hi ghadi par" — clock card
    'doors':    wt(5, lambda w: w == 'chaar'),                      # "chaar khano" — the four doors rise
    'neev':     wt_end(5, lambda w: w == 'hain'),                   # last word — outro begins
}
FREEZE = [50.0, 52.0]           # band stop: everything frozen, projector clatter only
SHOTS = [
    [0.0, 4.0, 'title'],
    [4.0, 19.0, 'lane'],
    [19.0, round(K['dinnerEnd'], 2), 'dinner'],
    [round(K['dinnerEnd'], 2), 43.0, 'doorway'],
    [43.0, 50.0, 'news'],
    [50.0, 73.0, 'freeze'],
    [73.0, 88.5, 'desk'],
    [88.5, DUR, 'doors'],
]

# —— subtitle cards: chunk each line's words (~2.2–3.4 s per card, break at sentence ends) ——
SUBS = []
for i in range(6):
    ws = block_words(i)
    chunks, cur = [], []
    for w in ws:
        cur.append(w)
        dur = (cur[-1]['t'] + cur[-1]['d']) - cur[0]['t']
        sent_end = w['w'].rstrip().endswith(('.', ':', 'hai.')) or w['w'] in ('hai.',)
        if (dur >= 2.1 and sent_end) or dur >= 3.3:
            chunks.append(cur); cur = []
    if cur:
        if chunks and (cur[-1]['t'] + cur[-1]['d'] - cur[0]['t']) < 1.2:
            chunks[-1].extend(cur)
        else:
            chunks.append(cur)
    for c in chunks:
        t0 = PLACE[i] + (c[0]['t'] - blocks[i]['start']) - 0.08
        t1 = PLACE[i] + (c[-1]['t'] + c[-1]['d'] - blocks[i]['start']) + 0.6
        text = ' '.join(w['w'] for w in c).replace(' — ', ' — ').replace('  ', ' ')
        SUBS.append({'t0': round(t0, 2), 't1': round(t1, 2), 'text': text})
# clamp overlaps
for a, b in zip(SUBS, SUBS[1:]):
    if a['t1'] > b['t0'] - 0.04: a['t1'] = round(b['t0'] - 0.04, 2)

# —— foley events (synthesised in mix.py) ——
EV = []
def add(t, type, **o): EV.append({'t': round(t, 3), 'type': type, **o})
add(K['glass'], 'glassTap')
for n in range(5): add(K['kandhe'] - 1.5 + n * 0.5, 'tick')          # glance chain before the whisper
add(K['kiss'] + 0.25, 'kissPop')
add(K['dinnerEnd'] - 0.1, 'chair')
t = K['dinnerEnd'] + 0.5
while t < 42.5:                                                      # shutter pops in the doorway
    add(t, 'shutter'); t += 1.0
for n in range(6): add(K['client'] + n * 0.5, 'packet', i=n)         # rice packets hand to hand, on the beat
add(K['gaadi'] - 1.2, 'honk'); add(K['gaadi'] - 0.7, 'honk')
add(K['gaadi'] + 0.3, 'hopIn')
add(43.0, 'shadeRoll', d=0.9)
add(49.3, 'shadeRoll', d=0.7)
add(FREEZE[0], 'freezeMark')
add(52.0, 'clockSpin', d=max(0.5, K['stamp'] - 52.0))
add(K['stamp'], 'stamp')
t = K['stamp'] + 1.0
while t < 71.5:                                                      # carriers' footsteps
    add(t, 'stepSoft'); t += 0.5
add(K['intel'], 'magnifier', d=2.2)
for n in range(6): add(K['deal'] + n * 0.5, 'cardDeal', i=n)
add(K['ghadi'], 'clockCard')
for n in range(4): add(K['doors'] + 1.0 + n * 1.5, 'doorCreak', i=n)
add(112.5, 'irisGrab')
EV.sort(key=lambda e: e['t'])

TL = {'dur': DUR, 'vo': VO, 'k': K, 'freeze': FREEZE, 'shots': SHOTS, 'subs': SUBS, 'ev': EV,
      'bpm': 120, 'beat': 0.5}
json.dump(TL, open(os.path.join(HERE, 'timeline.json'), 'w'), indent=1)
with open(os.path.join(HERE, 'timeline.js'), 'w') as f:
    f.write('// generated by make_timeline.py from the real Swara word timings — do not hand-edit\n')
    f.write('export const TL = ' + json.dumps(TL) + ';\n')
    f.write('export const DUR = TL.dur, VO = TL.vo, K = TL.k, SUBS = TL.subs, SHOTS = TL.shots;\n')
    f.write('export const BEAT = 0.5, BPM = 120;\n')
    f.write('export const q = t => Math.floor(t * 12 + 1e-6) / 12;\n')
    f.write('export const beats = t => t / BEAT;\n')
    f.write('export const breath = t => Math.cos(beats(q(t)) * Math.PI * 2);\n')
    f.write('export const shotAt = t => SHOTS.find(s => t >= s[0] && t < s[1]) || SHOTS[SHOTS.length - 1];\n')
json.dump([{'t0': s['t0'], 't1': s['t1'], 'text': s['text']} for s in SUBS],
          open(os.path.join(HERE, 'cues.json'), 'w'), indent=1)
print('DUR', DUR, '| K:', {k: round(v, 2) for k, v in K.items()})
print('shots:', SHOTS)
print('subs:', len(SUBS), 'cards | ev:', len(EV), 'foley events')
