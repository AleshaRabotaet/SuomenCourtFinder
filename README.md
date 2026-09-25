# SuomenCourtFinder

Find a free tennis court right now in Espoo/Helsinki, across several private
halls, without checking each one's own booking site by hand.

**Live site:** enable GitHub Pages for this repo (Settings → Pages → Deploy
from branch → `main` / `/docs`) and it serves `docs/index.html`.

## How it works

- `fetchers/` — one adapter per booking engine. Each returns a list of
  normalized slots: `{court, date, start, end, available}`.
  - `playfi.py` — scrapes the plain server-rendered HTML calendar used by
    play.fi (Smash-Espoo / Olarin Tennishalli).
  - `cintoia.py` — reads the public Firebase Realtime Database index + S3
    JSON files that back the Cintoia Falcon booking app. This one engine
    covers multiple clubs (Tapiolan Tennispuisto, Martinmäen Tenniskeskus /
    Cherry Arena / Aktia Tennishall) — same code, different `customerid`.
- `fetchers/venues.py` — the list of covered venues and which fetcher/config
  each one uses. Adding a venue on an already-supported engine is just a new
  entry here.
- `fetchers/run_all.py` — runs every venue's fetcher, isolates failures (one
  broken source doesn't take down the rest), and writes
  `docs/data/availability.json`.
- `.github/workflows/refresh.yml` — GitHub Actions cron (every 30 min) that
  runs the fetchers and commits the updated JSON.
- `docs/index.html` — static, mobile-first page that reads
  `docs/data/availability.json` and renders it. No backend, no build step.
  Booking itself redirects to the venue's own site (no online payment here).

Data and site live together under `docs/` because GitHub Pages only serves
from the repo root or `/docs` on a branch — keeping them together avoids any
cross-origin fetch or extra hosting step.

## Running the fetchers locally

```bash
pip install -r requirements.txt
python -m fetchers.run_all
```

Writes `docs/data/availability.json`. Open `docs/index.html` via a local
server (e.g. `python -m http.server` from `docs/`) to preview — opening the
file directly won't `fetch()` local JSON due to `file://` restrictions.

## Adding a venue

1. Figure out which engine it uses. Open its booking calendar and check:
   is the HTML itself full of slot data (→ play.fi-like), or does it load
   via JS from a Firebase/API backend (→ maybe Cintoia, check for
   `cintoia.com` in the page source or `falcon-328a1` in its JS bundle)?
2. If it matches an existing engine, add an entry to `fetchers/venues.py`
   with that engine's config keys (see the two existing entries).
3. If it's a new engine, add `fetchers/<engine>.py` with a `fetch(venue)`
   function returning the normalized slot list, register it in
   `FETCHERS` in `run_all.py`, then add the venue entry.

## Not in v1

- Municipal/city courts (Helsinki and others expose an open Respa/Varaamo
  REST API for this — no reverse engineering needed, easy to add later).
- Actual booking/payment through this site — every slot links out to the
  venue's own booking page instead.
- Notifications when a slot opens up.
