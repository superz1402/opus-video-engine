# runs/ — workflow run records

Every GitHub Actions workflow in this repo commits a structured record of
each run here:

```
runs/<workflow>/<run-id>/
  status.json        run id, job status, inputs, headline numbers
  <stem>.words.json  (voice runs) merged word timings — the caption contract
  <stem>.timing.json (voice runs) per-block durations/starts
  probe.json         (render runs) ffprobe of the master
  contact-sheet.jpg  (render runs) one QA sheet, kept ≤ ~500 KB so an
                     agent can see the cut through git alone
```

Rules (AGENTS.md §Run records): records are append-only; media never goes
in git (audio → run artifacts, videos → GitHub Releases; the single
contact-sheet exception above is deliberate QA evidence). `runs/**`
matches no workflow's push-trigger paths, so a record commit can never
retrigger a workflow. To read a result: open the newest
`runs/<workflow>/*/status.json`.
