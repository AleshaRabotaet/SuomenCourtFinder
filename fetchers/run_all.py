"""Runs every registered venue's fetcher and writes data/availability.json.

Each venue is fetched independently and wrapped in a try/except: if one
venue's site changed or is down, the rest of the venues still get published.
That failure is recorded in the output so the frontend can show it instead
of silently dropping the venue.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetchers import cintoia, playfi
from fetchers.venues import VENUES

FETCHERS = {
    "playfi": playfi.fetch,
    "cintoia": cintoia.fetch,
}

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "data" / "availability.json"


def main() -> None:
    venues_out = []
    all_slots = []

    for venue in VENUES:
        fetch = FETCHERS[venue["fetcher"]]
        entry = {
            "name": venue["name"],
            "city": venue["city"],
            "address": venue["address"],
            "booking_url": venue["booking_url"],
            "date_query_param": venue.get("date_query_param"),
            "status": "ok",
            "error": None,
            "slot_count": 0,
        }
        try:
            slots = fetch(venue)
            for slot in slots:
                slot["venue"] = venue["name"]
            all_slots.extend(slots)
            entry["slot_count"] = len(slots)
            print(f"[ok] {venue['name']}: {len(slots)} slots")
        except Exception as exc:  # noqa: BLE001 - one bad venue must not kill the run
            entry["status"] = "error"
            entry["error"] = f"{type(exc).__name__}: {exc}"
            print(f"[error] {venue['name']}: {entry['error']}", file=sys.stderr)
            traceback.print_exc()
        venues_out.append(entry)

    output = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "venues": venues_out,
        "slots": all_slots,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_slots)} slots across {len(venues_out)} venues to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
