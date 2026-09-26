"""Fetcher for the play.fi booking engine (used by Smash-Espoo / Olarin Tennishalli).

The booking calendar is plain server-rendered HTML - no login, no JS needed.
Each open slot is an <a href="/<slug>/booking/create-booking?alkuaika=...&kesto=...&resid=...">
Court<br>HH:MM<br><strong>Varaa</strong></a> anchor; we just regex those out
per requested day.
"""
from __future__ import annotations

import datetime as dt
import re
from urllib.parse import unquote_plus

import requests

from .common import MAX_DAYS_AHEAD, date_range, polite_sleep, today_helsinki

BASE_URL = "https://play.fi"

SLOT_RE = re.compile(
    r'<a href="/[a-zA-Z0-9_-]+/booking/create-booking\?'
    r"alkuaika=(?P<alkuaika>[^&\"]+)&kesto=(?P<kesto>\d+)&resid=(?P<resid>\d+)\">"
    r"(?P<court>[^<]+)<br>"
)


def _fetch_day(session: requests.Session, venue_slug: str, location_id: str, sport_id: str, date: dt.date) -> list[dict]:
    params = {
        "BookingCalForm[p_laji]": sport_id,
        "BookingCalForm[p_location]": location_id,
        "BookingCalForm[p_pvm]": date.isoformat(),
        "BookingCalForm[p_calmode]": "2",
    }
    resp = session.get(f"{BASE_URL}/{venue_slug}/booking/booking-calendar", params=params, timeout=20)
    resp.raise_for_status()

    slots = []
    for m in SLOT_RE.finditer(resp.text):
        raw = unquote_plus(m.group("alkuaika"))  # "2026-09-25 16:30:00"
        start_dt = dt.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
        end_dt = start_dt + dt.timedelta(minutes=int(m.group("kesto")))
        slots.append(
            {
                "court": m.group("court").strip(),
                "date": start_dt.date().isoformat(),
                "start": start_dt.strftime("%H:%M"),
                "end": end_dt.strftime("%H:%M"),
                "available": True,
            }
        )
    return slots


def fetch(venue: dict) -> list[dict]:
    """venue needs: playfi_slug, playfi_location, playfi_sport."""
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (compatible; SuomenCourtFinder/1.0)"

    slots: list[dict] = []
    for i, date in enumerate(date_range(today_helsinki(), MAX_DAYS_AHEAD)):
        if i > 0:
            polite_sleep()
        slots.extend(
            _fetch_day(
                session,
                venue["playfi_slug"],
                venue["playfi_location"],
                venue["playfi_sport"],
                date,
            )
        )
    return slots
