"""Fetcher for the Cintoia Falcon booking engine.

Cintoia's own web app is a Firebase SPA, but the data it renders comes from
two plain, unauthenticated endpoints we can hit directly:

  1. Firebase Realtime Database REST read, giving a date -> S3 file index:
       GET https://falcon-328a1.firebaseio.com/freeindex/<customerid>/public.json
  2. A per-day JSON file on S3 (URL comes from #1) listing free blocks per
     court id:
       {"<courtId>": [{"s": "HHMM", "e": "HHMM", "p": <price_cents>}, ...]}

Court display names come from a callable Cloud Function (`ui-get`,
q=getResources). That endpoint is flaky (empirically returns `{}` on some
calls for no discernible reason), so we retry a few times. If it still comes
back empty, fetch() raises rather than silently falling back to raw court
ids for every court - the caller (run_all.py) isolates that as a per-venue
error for this run, and the next 30-minute cron run retries from scratch.

Multiple Finnish tennis clubs run on this same shared backend (confirmed:
Tapiolan Tennispuisto, Martinmäen Tenniskeskus / Cherry Arena / Aktia
tennishall, Rosegarden, and Talin/Taivallahden Tenniskeskus), so this one
fetcher covers all of them - just pass a different `cintoia_customerid` per
venue.

Some backends host more than one physical venue (e.g. Tali and Taivallahti
share one Cintoia customer) or mix in non-tennis resources (e.g. Rosegarden
also has padel courts and ball machines). `getResources` tags every court
with a `category`, so a venue can pass `cintoia_categories` - a list of the
category values it should claim - to pull in only its own subset.
"""
from __future__ import annotations

import time

import requests

from .common import MAX_DAYS_AHEAD, date_range, polite_sleep, today_helsinki

FIREBASE_BASE = "https://falcon-328a1.firebaseio.com"
FUNCTIONS_BASE = "https://europe-west1-falcon-328a1.cloudfunctions.net"

# Scoped to one process (one run_all.py invocation / one cron run). Some
# venues share a single Cintoia backend (e.g. Tali + Taivallahti both use
# customerid "tali-..."), so caching by customerid/url here avoids hitting
# that backend twice in the same run.
_resources_cache: dict[str, dict] = {}
_free_index_cache: dict[str, dict] = {}
_day_cache: dict[str, dict] = {}


def _get_resources(session: requests.Session, customerid: str, origin: str) -> dict:
    for attempt in range(6):
        try:
            resp = session.post(
                f"{FUNCTIONS_BASE}/ui-get",
                json={"data": {"q": "getResources", "customerid": customerid}},
                headers={"Origin": origin, "User-Agent": "Mozilla/5.0 (compatible; SuomenCourtFinder/1.0)"},
                timeout=15,
            )
            resp.raise_for_status()
            result = resp.json().get("result") or {}
            if result:
                return result
        except requests.RequestException:
            pass
        time.sleep(1.5)
    return {}


def _free_index(session: requests.Session, customerid: str) -> dict:
    resp = session.get(f"{FIREBASE_BASE}/freeindex/{customerid}/public.json", timeout=20)
    resp.raise_for_status()
    return resp.json() or {}


def _hhmm(raw: str) -> str:
    return f"{raw[:2]}:{raw[2:]}"


def fetch(venue: dict) -> list[dict]:
    """venue needs: cintoia_customerid, cintoia_origin.

    Optional: cintoia_categories - only include courts whose `category`
    (from getResources) is in this list. Omit to include every court on
    the backend, as before.
    """
    session = requests.Session()
    customerid = venue["cintoia_customerid"]
    categories = venue.get("cintoia_categories")

    if customerid not in _resources_cache:
        resources = _get_resources(session, customerid, venue["cintoia_origin"])
        if not resources:
            raise RuntimeError(f"getResources returned no data for customerid={customerid!r}")
        _resources_cache[customerid] = resources
    resources = _resources_cache[customerid]

    if customerid not in _free_index_cache:
        _free_index_cache[customerid] = _free_index(session, customerid)
    free_index = _free_index_cache[customerid]

    wanted_dates = {d.strftime("%Y%m%d") for d in date_range(today_helsinki(), MAX_DAYS_AHEAD)}

    slots: list[dict] = []
    fetched_any = False
    for date_key, entry in free_index.items():
        if date_key not in wanted_dates:
            continue
        url = entry.get("key")
        if not url:
            continue
        if url not in _day_cache:
            if fetched_any:
                polite_sleep()
            fetched_any = True
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            _day_cache[url] = resp.json() or {}
        day_data = _day_cache[url]
        date_iso = f"{date_key[0:4]}-{date_key[4:6]}-{date_key[6:8]}"

        for court_id, blocks in day_data.items():
            resource = resources.get(court_id) or {}
            if categories is not None and resource.get("category") not in categories:
                continue
            court_name = resource.get("displayName") or f"Court {court_id[:6]}"
            for block in blocks:
                slots.append(
                    {
                        "court": court_name,
                        "date": date_iso,
                        "start": _hhmm(block["s"]),
                        "end": _hhmm(block["e"]),
                        "available": True,
                    }
                )
    return slots
