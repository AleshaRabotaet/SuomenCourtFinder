"""Registry of venues covered by the finder.

Every entry names a fetcher module (by attribute name in `fetchers`) plus
whatever config that fetcher needs, and the venue-level metadata shown in
the frontend and used for the "book here" redirect link.

Adding a venue that runs on an already-supported engine (play.fi, Cintoia)
is just a new dict here - no new code required.
"""

VENUES = [
    {
        "name": "Smash-Espoo (Olarin Tennishalli)",
        "city": "Espoo",
        "address": "Olarinniityntie 8, 02210 Espoo",
        "booking_url": "https://play.fi/smashcenter/booking/booking-calendar?BookingCalForm%5Bp_laji%5D=7",
        "fetcher": "playfi",
        "playfi_slug": "smashcenter",
        "playfi_location": "1",
        "playfi_sport": "7",
        "days_ahead": 14,
    },
    {
        "name": "Tapiolan Tennispuisto",
        "city": "Espoo",
        "address": "Tuulikuja 1, 02100 Espoo",
        "booking_url": "https://tennispuisto.cintoia.com/",
        "fetcher": "cintoia",
        "cintoia_customerid": "tennispuisto-rTVILEOT",
        "cintoia_origin": "https://tennispuisto.cintoia.com",
        "days_ahead": 14,
    },
    {
        "name": "Martinmäen Tenniskeskus (Cherry Arena / Aktia Tennishall)",
        "city": "Espoo",
        "address": "Martinkallio 4, 02270 Espoo",
        "booking_url": "https://evs.feel.cintoia.com/",
        "fetcher": "cintoia",
        "cintoia_customerid": "evs-4FD8m7rCa7wOuCADvzZZ",
        "cintoia_origin": "https://evs.feel.cintoia.com",
        "days_ahead": 14,
    },
]
