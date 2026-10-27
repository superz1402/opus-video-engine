# SCRIPT-GATE — smoke test of the adopted Script Standard (2026-10-27)

The Script Standard (`docs/script-standard.md`, adopted by the owner
2026-10-27) was wired into the engine with a mechanical gate
(`engine/script_gate.py`, CI: `.github/workflows/script-gate.yml`). As
the adoption smoke test, the gate was run against this project's locked
script (`voice-input.txt`) — the script the scripting study had already
diagnosed as the stale one. **Expected result: FAIL. A gate that passed
this script would be broken.**

Command (target = the local reference build's measured 88 s runtime):

```
python3 engine/script_gate.py projects/centipede-vs-human/voice-input.txt \
    --target-seconds 88 \
    --report projects/centipede-vs-human/script-gate-report.txt \
    --json    projects/centipede-vs-human/script-gate-report.json
# exit code 1
```

## Result: FAIL — 5 hard-failing checks (full report: script-gate-report.txt)

| Check | Verdict | Evidence |
|---|---|---|
| T1p hook heuristic | PASS | no answer-markers in the opening lines (panel scoring is the scorer's job) |
| T3 question ladder | **FAIL** | 0 spoken questions in all 8 blocks |
| T5 template repetition | **FAIL** | adjacent Its…/Yours… comparison openers in blocks 2 and 6 — comparison used as structure |
| T6 jagged edge | **FAIL** | flat stretch (block 1, lengths 4/2/4); 0 fragments in blocks 2, 3, 4, 6, 7; a 21-word sentence (block 5); a two-em-dash sentence (block 4). Median 8 words and σ 5.19 pass — the failure is local, not global |
| T9 pivot ration | PASS | 1 pivot (block 1), within the ≤2/episode ration; earned/hollow is the scorer's call |
| T10 delivery markup | **FAIL** | zero markup of any kind — no `[PAUSE]` in any block, no `[ASIDE]`, no `**emphasis**` |
| T11 slop lint | PASS | 0 blacklist hits |
| PACE | **FAIL** | 229 words at the 88 s target = 156 wpm implied, outside the 125–145 law (the study measured ≈162 wpm on the build's own timings — same disease) |

## What this proves and what it does not

- The mechanical panel catches, from text alone, the exact failure modes
  the study diagnosed by ear: no questions, template rhythm, missing
  fragments, no performed pauses, over-band pace.
- It does **not** re-score the script artistically: T1 (hook panel), T2
  (four killers), T4 (but/therefore joints — this storyboard predates the
  fields), T7 (so-what), T8 (agency) and T12 (number audit) remain
  independent-scorer checks, recorded in a project's score sheet.
- This project's script is NOT retroactively failed as a production: the
  centipede film shipped as an engine test before the standard existed.
  The gate binds the *next* script that enters P1.5.
