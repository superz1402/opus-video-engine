#!/usr/bin/env python3
"""Single source of truth for the Urban Sketch 2-min demo.
Reads the Actions voice timings + WordBoundary words, places the six lines on
the film timeline (voice never stretched), chunks captions from REAL word
timings, finds the story-beat word offsets the picture/score lock to, and
writes timeline.json + timeline.js + cues.json. Asserts the caption hold rule
and the 120 s +/- 6 s duration window."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
VA = os.path.join(HERE, 'voice', 'actions')
timing = json.load(open(os.path.join(VA, 'voice-input.timing.json')))
words = json.load(open(os.path.join(VA, 'voice-input.words.json')))
lines = json.load(open(os.path.join(HERE, 'lines.json')))

BLOCKS = ['b001', 'b002', 'b003', 'b004', 'b005', 'b006']
# film placement: intro page-open, then gaps (page-turn beat before L4)
INTRO = 4.2
GAPS = [0.35, 0.35, 3.80, 0.60, 0.35]   # after L1..L5
OUTRO = 13.76

starts, t = [], INTRO
for i, b in enumerate(BLOCKS):
    starts.append(t)
    t += timing[b]['dur']
    if i < 5:
        t += GAPS[i]
DUR = t + OUTRO
print(f"DUR = {DUR:.2f}s  (target 120 +/- 6)")
assert 114.0 <= DUR <= 126.0, DUR

voice = []
for i, b in enumerate(BLOCKS):
    voice.append({
        'id': lines[i]['id'], 'block': b,
        'start': round(starts[i], 3), 'dur': round(timing[b]['dur'], 3),
        'srcStart': round(timing[b]['start'], 3),
        'text': lines[i]['text'],
    })

# ---- word offsets (film time) for story beats the picture locks to ----
# words.json entries are absolute in the joined WAV; block b00k starts at timing[b]['start'].
def word_time(block_idx, needle, occurrence=1):
    b = BLOCKS[block_idx]
    lo, hi = timing[b]['start'], timing[b]['start'] + timing[b]['dur']
    hits = [w for w in words if lo - 0.01 <= w['t'] < hi and w['w'].strip('.,:—-').lower() == needle.lower()]
    assert len(hits) >= occurrence, (b, needle, len(hits))
    w = hits[occurrence - 1]
    return round(starts[block_idx] + (w['t'] - lo), 3)

beats = {
    'baarish':      word_time(0, 'Baarish'),
    'sheeshe':      word_time(0, 'sheeshe'),
    'gulabi':       word_time(1, 'Gulabi'),
    'kandhe':       word_time(1, 'kandhe'),
    'kiss':         word_time(1, 'kiss'),
    'dinnerKhatam': word_time(1, 'Dinner'),
    'darwaze':      word_time(1, 'darwaze'),
    'gaadi':        word_time(1, 'gaadi'),
    'friedRice':    word_time(2, 'fried'),
    'dedhSaal':     word_time(3, 'Dedh'),
    'photoBann':    word_time(3, 'photo'),
    'intelligence': word_time(3, 'intelligence'),
    'agent':        word_time(3, 'agent'),
    'sabootTable':  word_time(4, 'saboot'),
    'ekEk':         word_time(4, 'ek-ek'),
    'recordPar':    word_time(4, 'record'),
    'kahaGaya':     word_time(4, 'kaha'),
    'chaarKhano':   word_time(5, 'chaar'),
    'neev':         word_time(5, 'neev'),
}
print('beats:', json.dumps(beats, indent=0))

# ---- caption cues from real word timings ----
# chunk each block's words into phrases at punctuation or ~7 words; wrap <=44 chars.
def block_words(i):
    b = BLOCKS[i]
    lo, hi = timing[b]['start'], timing[b]['start'] + timing[b]['dur']
    return [{'w': w['w'], 't0': starts[i] + (w['t'] - lo), 't1': starts[i] + (w['t'] - lo) + w['d']}
            for w in words if lo - 0.01 <= w['t'] < hi]

def wrap(text, width=44):
    out, cur = [], ''
    for wd in text.split():
        if len(cur) + 1 + len(wd) > width and cur:
            out.append(cur); cur = wd
        else:
            cur = (cur + ' ' + wd).strip()
    if cur: out.append(cur)
    return out

cues = []
for i in range(6):
    ws = block_words(i)
    groups, cur = [], []
    for w in ws:
        clen = len(' '.join(x['w'] for x in cur))
        if cur and clen + 1 + len(w['w']) > 44:   # never let a chunk outgrow one margin line
            groups.append(cur); cur = []
        cur.append(w)
        clen = len(' '.join(x['w'] for x in cur))
        ends = w['w'].endswith(('.', ':', '?', '—')) or w['w'].endswith(',')
        if (ends and len(cur) >= 3 and clen >= 18) or len(cur) >= 8:
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    for g in groups:
        text = ' '.join(w['w'] for w in g)
        wl = wrap(text, 44)
        assert len(wl) == 1, (text, wl)   # single-line chunks for the two-slot margin strip
        cues.append({'t0': round(g[0]['t0'], 3), 't1': round(g[-1]['t1'], 3), 'text': text})
# Two-slot rolling captions (STYLE.md S4): a cue stays on its margin slot until
# the slot is reused two cues later, so every cue's display time satisfies
# hold >= max(1.8 s, speech + 0.6 s) even in continuous narration.
def assign_slots(cs):
    for j, c in enumerate(cs):
        c['slot'] = j % 2
        c['tEnd'] = round(cs[j + 2]['t0'], 3) if j + 2 < len(cs) else round(min(DUR - 0.4, c['t1'] + 2.0), 3)
    return cs
cues = assign_slots(cues)
def violations(cs):
    return [c for c in cs if (c['tEnd'] - c['t0']) < max(1.8, (c['t1'] - c['t0']) + 0.6) - 0.05]
bad = violations(cues)
while bad:  # merge the first offending cue with its successor and retry
    j = cues.index(bad[0])
    if j + 1 >= len(cues): break
    cues[j]['text'] += ' ' + cues[j + 1]['text']; cues[j]['t1'] = cues[j + 1]['t1']
    del cues[j + 1]
    cues = assign_slots(cues)
    bad = violations(cues)
assert not bad, bad
for c in cues:
    assert len(wrap(c["text"], 44)) == 1, c
    c['hold'] = round(c['tEnd'] - c['t0'], 2)
print(f"{len(cues)} caption cues (two-slot rolling), all holds OK")

# ---- sound events for the mixer (picture-locked) ----
EV = []
def ev(t, type, **kw): EV.append({'t': round(t, 3), 'type': type, **kw})
ev(0.5, 'pen', dur=1.7, gain=0.5)                      # corner note writing
ev(4.4, 'pen', dur=5.6, gain=0.8)                      # street draw-on
ev(8.2, 'brush', dur=2.2, gain=0.7)                    # sky wash
ev(9.6, 'brush', dur=3.4, gain=0.9)                    # main wash front
ev(beats['gulabi'] - 0.1, 'brush', dur=1.0, gain=0.8)  # pink bloom
ev(beats['kiss'], 'tick', gain=0.5)                    # kiss tick
ev(beats['darwaze'], 'pen', dur=1.2, gain=0.5)         # doorway draw
ev(beats['gaadi'] + 0.4, 'cardoor', gain=0.8)
ev(beats['friedRice'], 'packets', dur=2.6, gain=0.7)
ev(starts[3] - 3.3, 'pageturn', dur=2.4, gain=1.0)
ev(starts[3] + 0.2, 'pen', dur=5.5, gain=0.6)          # cold re-sketch
ev(starts[3] + 6.5, 'pen', dur=3.5, gain=0.45)         # annotations
ev(beats['sabootTable'], 'pen', dur=1.6, gain=0.6)    # desk draw
for k in range(5):
    ev(beats['sabootTable'] + 1.8 + k * 1.7, 'card', gain=0.7)
ev(beats['chaarKhano'] - 1.2, 'pen', dur=4.5, gain=0.6)  # panels ruling
ev(DUR - 1.2, 'drip', gain=0.7)
EV.sort(key=lambda e: e['t'])

TL = {'dur': round(DUR, 3), 'voice': voice, 'beats': beats, 'cues': cues, 'EV': EV,
      'voiceName': 'hi-IN-SwaraNeural', 'rate': '+12%'}
json.dump(TL, open(os.path.join(HERE, 'timeline.json'), 'w'), indent=1, ensure_ascii=False)
with open(os.path.join(HERE, 'timeline.js'), 'w') as f:
    f.write('window.TL = ' + json.dumps(TL, ensure_ascii=False) + ';\n')
srt_cues = []
for j, c in enumerate(cues):  # .srt export: classic non-overlapping windows
    end = cues[j + 1]['t0'] if j + 1 < len(cues) else c['tEnd']
    srt_cues.append({'t0': c['t0'], 't1': round(max(end, c['t1'] + 0.3), 3), 'text': c['text']})
json.dump(srt_cues, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('timeline.json / timeline.js / cues.json written')
