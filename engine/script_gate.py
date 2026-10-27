#!/usr/bin/env python3
"""script_gate.py — the mechanical half of the Script Standard gate.

Implements the measurable checks of docs/script-standard.md (§5) against a
narration script / voice-input file, so a stale script fails in CI before
it can reach the voice stage (AGENTS.md stage P1.5, hard rule 11):

  T1p  Self-resolving-hook heuristic on block 1 (§1.1): a first line that
       contains its own answer ("because", "which means", ...) is a
       summary, not a hook. Heuristic only — the scored 5-candidate hook
       panel (T1) and four-killers audit (T2) belong to the independent
       scorer. Concept: Jakeschincariol/youtube-agent-skill (MIT).
  T3   Spoken questions: >= 1 genuine question per block/scene.
  T5   Template proxies: no repeated first-word opener in adjacent
       blocks; A/B comparison-template chaining (adjacent sentences
       opening on possessives: Its/Yours/...) is flagged as structure.
  T6   Jagged edge (§3): sentence-length sigma >= 4.5, median 8-14 words,
       no sentence > 20 words (a *built* escalating list is the only
       exception and needs scorer sign-off), no 3 consecutive sentences
       within +/-2 words of each other, >= 2 fragments (<= 4 words) per
       block, no sentence with two em-dash insertions (§3.3).
  T9   Contrast-pivot ration: "not X - it's Y" pivots <= 1 per block,
       <= 2 per episode (the earned/hollow quality test is the scorer's).
  T10  Delivery markup: >= 1 [PAUSE] per block; [ASIDE] / [SLOW] /
       **emphasis** counts reported (voice stage must perform them, §4).
  T11  Slop lint: zero hits against the §6 blacklist.
  Pace §4 pacing-law sanity: word count -> duration at 125/135/145 wpm;
       with a target duration (--target-seconds or a TARGET_SECONDS:
       directive) the implied wpm must land inside 125-145.

Checks T1 (panel), T2, T4 (but/therefore chain), T7 (so-what), T8
(agency ratio) and T12 (number audit) are judgement calls and stay with
the independent scorer — this script never certifies them. Gate
integrity: the writer never scores their own script; a self-scored
rubric total caps at 15/20 (standard §5).

Usage:
  python3 engine/script_gate.py SCRIPT [--target-seconds N]
                                     [--report PATH] [--json PATH]

Exit code: 0 = no hard FAIL, 1 = at least one hard FAIL, 2 = usage/IO.
Stdlib only.
"""

import argparse
import json
import math
import re
import statistics
import sys

# ---------------------------------------------------------------- parsing

DIRECTIVE_RE = re.compile(r"^\s*(VOICE|RATE|TARGET_SECONDS)\s*:\s*(.*)$", re.I)
MARKUP_TAG_RE = re.compile(
    r"\[(?:PAUSE(?::short)?|ASIDE|/ASIDE|SLOW|/SLOW)\]|\[\[rate:[^\]]*\]\]",
    re.I,
)
DECIMAL_GUARD = "\x00"


def parse_script(text):
    """Return (blocks, directives) where blocks are raw narration strings,
    one per blank-line-separated block (= one scene in engine convention)."""
    directives = {}
    kept = []
    for line in text.splitlines():
        m = DIRECTIVE_RE.match(line)
        if m:
            directives[m.group(1).upper()] = m.group(2).strip()
            continue
        if line.lstrip().startswith(("#", ">")):  # markdown headers/quotes
            continue
        kept.append(line)
    body = "\n".join(kept)
    blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
    return blocks, directives


def count_markup(blocks):
    raw = "\n\n".join(blocks)
    counts = {
        "pause": len(re.findall(r"\[PAUSE(?::short)?\]", raw, re.I)),
        "pause_short": len(re.findall(r"\[PAUSE:short\]", raw, re.I)),
        "aside": len(re.findall(r"\[ASIDE\]", raw, re.I)),
        "slow": len(re.findall(r"\[SLOW\]", raw, re.I)),
        "rate": len(re.findall(r"\[\[rate:", raw, re.I)),
        "emphasis": len(re.findall(r"\*\*[^*]+\*\*", raw)),
    }
    per_block_pause = [
        len(re.findall(r"\[PAUSE(?::short)?\]", b, re.I)) for b in blocks
    ]
    return counts, per_block_pause


def strip_markup(text):
    text = MARKUP_TAG_RE.sub(" ", text)
    return text.replace("**", "")


def split_sentences(block_text):
    """Naive sentence split: protects decimals, splits on . ! ? …"""
    t = re.sub(r"(\d)\.(\d)", r"\1" + DECIMAL_GUARD + r"\2", block_text)
    parts = re.split(r"(?<=[.!?…])\s+", t.strip())
    out = []
    for p in parts:
        p = p.replace(DECIMAL_GUARD, ".").strip()
        if p:
            out.append(p)
    return out


def words_of(sentence):
    return [w for w in re.findall(r"[^\s]+", sentence)
            if re.search(r"[A-Za-z0-9]", w)]


# ------------------------------------------------------------------ checks

SLOP_PHRASES = [
    # meta-narration / YouTuber filler
    "in this video", "today we will", "we'll be looking at",
    "let's dive in", "lets dive in", "let's delve", "let's explore",
    "let's unpack", "without further ado", "welcome back", "hey guys",
    "smash that subscribe", "stay tuned", "you won't believe",
    "you wont believe", "let that sink in", "read that again",
    "this changes everything",
    # throat-clearing openers (flagged anywhere; opener use is the crime)
    "it is important to note", "in a world where", "when it comes to",
    "at the end of the day",
    # dead transitions
    "furthermore", "additionally", "moreover", "with that in mind",
    "that said",
    # significance inflation
    "crucial", "pivotal", "game-changer", "game changer",
    "revolutionary", "remarkable", "testament to", "plays a vital role",
    "serves as a reminder",
    # bloated verbs
    "serves as", "stands as", "boasts", "represents a", "marks a",
    # banned metaphor verbs / fake-depth participles
    "unpacked", "distilled", "woven", "layered", "baked in",
    "bolted on", "crystallised", "crystallized", "sculpted", "anchored",
    "highlighting its importance", "paving the way",
]
SLOP_WORDS = ["delve"]  # single-word slop, matched on word boundaries

HOOK_ANSWER_MARKERS = [
    "because", "which means", "so that", "that's why", "thats why",
    "this means", ", meaning ",
]

POSSESSIVE_OPENERS = {"its", "yours", "his", "hers", "theirs", "ours"}


def find_pivots(sentences):
    """Indices of sentences forming a 'not X - it's Y' contrast pivot."""
    hits = set()
    for i, s in enumerate(sentences):
        low = " " + s.lower() + " "
        if re.search(r"\bnot\s+(a\s+|an\s+|the\s+|just\s+|only\s+)?[^.!?]{0,80}?\b(it's|it is)\b", low):
            hits.add(i)
        elif "— it's" in low or "— it is" in low or "-- it's" in low:
            hits.add(i)
        elif (re.search(r"\bnot\b", low) and i + 1 < len(sentences)
              and re.match(r"\s*(it's|it is)\b", sentences[i + 1].lower())):
            hits.add(i)  # pivot spans this sentence and the next
    return sorted(hits)


class Check:
    def __init__(self, cid, title):
        self.id, self.title = cid, title
        self.status = "PASS"  # PASS | WARN | FAIL
        self.lines = []

    def fail(self, msg):
        self.status = "FAIL"
        self.lines.append(msg)

    def warn(self, msg):
        if self.status == "PASS":
            self.status = "WARN"
        self.lines.append(msg)

    def info(self, msg):
        self.lines.append(msg)


def run_checks(blocks, directives, target_seconds):
    checks = []
    markup, per_block_pause = count_markup(blocks)
    clean_blocks = [strip_markup(b) for b in blocks]
    block_sents = [split_sentences(b) for b in clean_blocks]
    all_sents = [s for bs in block_sents for s in bs]
    all_lens = [len(words_of(s)) for s in all_sents]
    total_words = sum(all_lens)

    # ---- T1p: self-resolving hook heuristic (block 1, first 2 sentences)
    c = Check("T1p", "Hook: self-resolving heuristic (standard 1.1)")
    if block_sents and block_sents[0]:
        hook = " ".join(block_sents[0][:2]).lower()
        found = [m for m in HOOK_ANSWER_MARKERS if m in hook]
        if found:
            c.fail(f"block 1 opens with its own answer (markers: "
                   f"{', '.join(found)}) - a summary, not a hook")
        else:
            c.info("no answer markers in the opening lines (heuristic only; "
                   "the scored hook panel is the scorer's job)")
        n = len(words_of(block_sents[0][0]))
        if not (9 <= n <= 24):
            c.warn(f"first line is {n} words (standard: 9-24 for a <=5 s hook)")
    else:
        c.fail("no narration blocks found")
    checks.append(c)

    # ---- T3: spoken questions per block
    c = Check("T3", "Question ladder: >= 1 spoken question per block")
    q_counts = [sum(1 for s in bs if s.rstrip('\"\'”’').endswith("?"))
                for bs in block_sents]
    for i, q in enumerate(q_counts, 1):
        if q == 0:
            c.fail(f"block {i}: 0 spoken questions")
    if c.status == "PASS":
        c.info(f"questions per block: {q_counts}")
    checks.append(c)

    # ---- T5: opener / template proxies
    c = Check("T5", "Template repetition: openers + comparison chaining")
    first_words = []
    for bs in block_sents:
        first_words.append(words_of(bs[0])[0].strip(".,!?\"'").lower()
                           if bs and words_of(bs[0]) else "")
    for i in range(1, len(first_words)):
        if first_words[i] and first_words[i] == first_words[i - 1]:
            c.fail(f"blocks {i} and {i + 1} open on the same word "
                   f"('{first_words[i]}') - adjacent opener pattern repeat")
    pairs = 0
    for bi, bs in enumerate(block_sents, 1):
        openers = [(words_of(s)[0].strip(".,!?\"'").lower()
                    if words_of(s) else "") for s in bs]
        for j in range(1, len(openers)):
            if openers[j] in POSSESSIVE_OPENERS and \
               openers[j - 1] in POSSESSIVE_OPENERS:
                pairs += 1
                c.info(f"block {bi}: adjacent comparison-template openers "
                       f"('{openers[j - 1]}...' / '{openers[j]}...')")
    if pairs >= 2:
        c.fail(f"{pairs} adjacent possessive-opener pairs - the A/B "
               f"comparison is being used as structure, not a device (2.4)")
    elif pairs == 1:
        c.warn("1 adjacent possessive-opener pair (comparison chaining)")
    checks.append(c)

    # ---- T6: jagged edge
    c = Check("T6", "Jagged edge: sentence rhythm (standard 3)")
    if all_lens:
        med = statistics.median(all_lens)
        sigma = statistics.pstdev(all_lens) if len(all_lens) > 1 else 0.0
        c.info(f"sentences: {len(all_lens)} | median {med:.0f} words | "
               f"sigma {sigma:.2f} | min {min(all_lens)} | max {max(all_lens)}")
        if sigma < 4.5:
            c.fail(f"sigma {sigma:.2f} < 4.5 - rhythm is flat (drone zone)")
        if not (8 <= med <= 14):
            c.fail(f"median sentence {med:.0f} words, outside 8-14")
        for bi, bs in enumerate(block_sents, 1):
            lens = [len(words_of(s)) for s in bs]
            for si, n in enumerate(lens, 1):
                if n > 20:
                    c.fail(f"block {bi} sentence {si}: {n} words (> 20 cap; "
                           f"a built list needs scorer sign-off)")
            for si in range(len(lens) - 2):
                trio = lens[si:si + 3]
                if max(trio) - min(trio) <= 2:
                    c.fail(f"block {bi} sentences {si + 1}-{si + 3}: lengths "
                           f"{trio} within +/-2 words - flat stretch")
            frags = sum(1 for n in lens if n <= 4)
            if frags < 2:
                c.fail(f"block {bi}: {frags} fragment(s) <= 4 words "
                       f"(need >= 2 per scene)")
            for si, s in enumerate(bs, 1):
                if s.count("—") + s.count("--") >= 2:
                    c.fail(f"block {bi} sentence {si}: two em-dash "
                           f"insertions - split it (3.3)")
    checks.append(c)

    # ---- T9: pivot ration
    c = Check("T9", "Contrast pivots: <= 1 per block, <= 2 per episode")
    total_pivots = 0
    for bi, bs in enumerate(block_sents, 1):
        p = find_pivots(bs)
        total_pivots += len(p)
        if len(p) > 1:
            c.fail(f"block {bi}: {len(p)} negative pivots (ration: 1)")
        elif p:
            c.info(f"block {bi}: 1 pivot at sentence {p[0] + 1} "
                   f"(earned/hollow test is the scorer's)")
    if total_pivots > 2:
        c.fail(f"{total_pivots} pivots in the episode (ration: 2)")
    elif c.status == "PASS":
        c.info(f"{total_pivots} pivot(s) total - within ration")
    checks.append(c)

    # ---- T10: delivery markup
    c = Check("T10", "Delivery markup the voice stage must perform (4)")
    c.info(f"[PAUSE] x{markup['pause']} (short x{markup['pause_short']}) | "
           f"[ASIDE] x{markup['aside']} | [SLOW] x{markup['slow']} | "
           f"**emphasis** x{markup['emphasis']} | rate marks x{markup['rate']}")
    for i, n in enumerate(per_block_pause, 1):
        if n == 0:
            c.fail(f"block {i}: no [PAUSE] - a flat one-speed read fails 4")
    if markup["aside"] == 0:
        c.warn("no [ASIDE] anywhere (character cadence may still require one)")
    if markup["emphasis"] == 0:
        c.warn("no **emphasis** marks anywhere")
    checks.append(c)

    # ---- T11: slop lint
    c = Check("T11", "Slop lint: section-6 blacklist, zero tolerance")
    norm = re.sub(r"\s+", " ", " ".join(clean_blocks).lower())
    norm = norm.replace("’", "'").replace("‘", "'")
    hits = []
    for phrase in SLOP_PHRASES:
        if phrase.replace("’", "'") in norm:
            hits.append(phrase)
    for w in SLOP_WORDS:
        if re.search(r"\b" + re.escape(w) + r"\b", norm):
            hits.append(w)
    if hits:
        for h in sorted(set(hits)):
            c.fail(f"blacklist hit: '{h}'")
    else:
        c.info("0 blacklist hits (character-bible exceptions, if any, are "
               "logged in the score sheet, not here)")
    checks.append(c)

    # ---- Pace sanity
    c = Check("PACE", "Pacing-law sanity: 125-145 wpm (standard 4)")
    if total_words:
        d125, d145 = total_words / 125 * 60, total_words / 145 * 60
        c.info(f"{total_words} words -> {d145:.0f}-{d125:.0f} s of speech "
               f"at 145-125 wpm (pauses excluded)")
        tgt = target_seconds
        if tgt is None and "TARGET_SECONDS" in directives:
            try:
                tgt = float(directives["TARGET_SECONDS"])
            except ValueError:
                tgt = None
        if tgt:
            wpm = total_words / tgt * 60
            if 125 <= wpm <= 145:
                c.info(f"implied pace at {tgt:.0f} s target: {wpm:.0f} wpm - in band")
            else:
                c.fail(f"implied pace at {tgt:.0f} s target: {wpm:.0f} wpm, "
                       f"outside 125-145 - fix by casting/rate/script, "
                       f"never by time-stretch")
        else:
            c.warn("no target duration given - pace reported, not enforced "
                   "(pass --target-seconds or a TARGET_SECONDS: directive)")
    checks.append(c)

    return checks, {
        "blocks": len(blocks),
        "sentences": len(all_sents),
        "words": total_words,
        "sentence_length_median": (statistics.median(all_lens)
                                   if all_lens else 0),
        "sentence_length_sigma": (statistics.pstdev(all_lens)
                                  if len(all_lens) > 1 else 0.0),
        "markup": markup,
        "questions_per_block": q_counts,
        "total_pivots": total_pivots,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("script", help="narration script / voice-input file")
    ap.add_argument("--target-seconds", type=float, default=None,
                    help="target runtime; implied wpm must land in 125-145")
    ap.add_argument("--report", help="also write the text report here")
    ap.add_argument("--json", help="also write machine-readable results here")
    args = ap.parse_args(argv)

    try:
        with open(args.script, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"script_gate: cannot read {args.script}: {e}", file=sys.stderr)
        return 2

    blocks, directives = parse_script(text)
    checks, stats = run_checks(blocks, directives, args.target_seconds)

    out = []
    out.append(f"SCRIPT GATE - {args.script}")
    out.append(f"blocks (scenes): {stats['blocks']} | sentences: "
               f"{stats['sentences']} | words: {stats['words']}")
    out.append("=" * 72)
    n_fail = 0
    for c in checks:
        if c.status == "FAIL":
            n_fail += 1
        out.append(f"[{c.status:4}] {c.id:4} {c.title}")
        for line in c.lines:
            out.append(f"       - {line}")
    out.append("=" * 72)
    verdict = "FAIL" if n_fail else "PASS"
    out.append(f"VERDICT: {verdict} "
               f"({n_fail} hard fail(s), {len(checks)} checks)")
    out.append("Note: T1 panel, T2, T4, T7, T8, T12 are scorer checks and "
               "are NOT certified by this script.")
    report = "\n".join(out) + "\n"
    print(report, end="")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report)
    if args.json:
        payload = {
            "script": args.script,
            "verdict": verdict,
            "hard_fails": n_fail,
            "stats": stats,
            "checks": [{"id": c.id, "title": c.title, "status": c.status,
                        "notes": c.lines} for c in checks],
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
