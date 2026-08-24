
import os
import csv
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo   

# ---- Config -----------------------------------------------------------------
DATE = "2026-08-19"                
TZ = ZoneInfo("Europe/Berlin")     

AIRPORTS = {
    "EDDF": "Frankfurt",
    "EDDM": "Munich",
    "EDDB": "Berlin Brandenburg",
}

TOKEN_URL = ("https://auth.opensky-network.org/auth/realms/"
             "opensky-network/protocol/openid-connect/token")
API_BASE = "https://opensky-network.org/api"
OUT_FILE = "flights_raw.csv"
# -----------------------------------------------------------------------------


def get_token():
    cid = os.environ.get("OPENSKY_CLIENT_ID")
    secret = os.environ.get("OPENSKY_CLIENT_SECRET")
    if not cid or not secret:
        raise SystemExit(
            "Missing credentials. Set OPENSKY_CLIENT_ID and "
            "OPENSKY_CLIENT_SECRET first (create an API client in your "
            "OpenSky account)."
        )
    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": cid,
            "client_secret": secret,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def day_bounds(date_str):
    """Unix timestamps for local midnight-to-midnight on the given date."""
    start = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=TZ)
    begin = int(start.timestamp())
    end = begin + 24 * 3600
    return begin, end


def fetch(kind, airport, begin, end, token):
    """kind = 'departure' or 'arrival'. Returns a list of flight dicts."""
    url = f"{API_BASE}/flights/{kind}"
    params = {"airport": airport, "begin": begin, "end": end}
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(4):
        r = requests.get(url, params=params, headers=headers, timeout=60)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return []                   
        if r.status_code == 429:            
            wait = 10 * (attempt + 1)
            print(f"    rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        r.raise_for_status()
    print(f"    gave up on {kind} for {airport}")
    return []


def main():
    token = get_token()
    begin, end = day_bounds(DATE)
    print(f"Pulling {DATE} (unix {begin}-{end}) for {list(AIRPORTS)}\n")

    rows = []
    for code, name in AIRPORTS.items():
        for kind in ("departure", "arrival"):
            data = fetch(kind, code, begin, end, token)
            print(f"  {name:20s} {kind:9s}: {len(data)} flights")
            for f in data:
                rows.append({
                    "queried_airport": code,
                    "direction": kind,
                    "icao24": f.get("icao24"),
                    "callsign": (f.get("callsign") or "").strip(),
                    "dep_airport": f.get("estDepartureAirport"),
                    "arr_airport": f.get("estArrivalAirport"),
                    "firstSeen": f.get("firstSeen"),
                    "lastSeen": f.get("lastSeen"),
                })
            time.sleep(2)                   

    if not rows:
        raise SystemExit(
            "\nNo flights returned. Try a different recent weekday, or check "
            "that your credentials are valid."
        )

    with open(OUT_FILE, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nSaved {len(rows)} rows to {OUT_FILE}")


if __name__ == "__main__":
    main()