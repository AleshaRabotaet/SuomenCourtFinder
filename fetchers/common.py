"""Shared types and helpers used by every venue fetcher.

Each fetcher module exposes a `fetch(venue) -> list[dict]` function that
returns slots normalized to:

    {"court": str, "date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM", "available": True}

`run_all.py` adds the venue-level fields (name, address, booking_url) and
writes the combined result to data/availability.json.
"""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

HELSINKI = ZoneInfo("Europe/Helsinki")


def today_helsinki() -> dt.date:
    return dt.datetime.now(HELSINKI).date()


def date_range(start: dt.date, days: int) -> list[dt.date]:
    return [start + dt.timedelta(days=i) for i in range(days)]
