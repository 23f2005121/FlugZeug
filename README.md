# ✈️ FlugZeug — One Day at Germany's Three Biggest Hubs

Analysing a single day of real air traffic at **Frankfurt (EDDF)**, **Munich (EDDM)** and **Berlin Brandenburg (EDDB)** — extracted from open ADS-B data — to ask a simple question:

> **What does one ordinary day of flights reveal about how Germany's major airports actually work, and how Lufthansa competes at them?**

The analysis is built end to end from self-extracted data: pull → clean → enrich → analyse → visualise. No pre-made dataset, no delay/passenger figures assumed — only what flight-movement data can honestly show.

---

## Table of contents
- [Key findings](#key-findings)
- [Results](#results)
- [Data sources](#data-sources)
- [How it works](#how-it-works)
- [Repository structure](#repository-structure)
- [Running it yourself](#running-it-yourself)
- [The 3D flight-network map](#the-3d-flight-network-map)
- [Limitations](#limitations)
- [Possible extensions](#possible-extensions)
- [Tech stack](#tech-stack)
- [Data attribution & licensing](#data-attribution--licensing)

---

## Key findings

Based on **2,766 aircraft movements** across the three airports on **19 August 2026** (a normal weekday).

| Airport | Movements | Lufthansa mainline | Lufthansa Group | True long-haul (>4,000 km) |
|---|--:|--:|--:|--:|
| Frankfurt (EDDF) | 1,290 | ~46% | ~58% | 16.1% |
| Munich (EDDM) | 936 | ~47% | ~60% | 8.8% |
| Berlin (EDDB) | 540 | 6% | 21% | 2.0% |

1. **They aren't 24/7 airports — the law shuts them off.** All three go essentially dark between **23:00 and 05:00** (only ~1–1.5% of movements fall in that window), the result of a court-ordered **night flight ban**. The whole operation is compressed into ~18 hours, forcing sharp daytime peaks. Because every German hub shares this rule, it's a **level playing field within Germany**, not a Frankfurt handicap.
2. **They're European machines with a thin long-haul layer.** By number of flights, all three are dominated by short-haul European routes (60–70%). Frankfurt reaches furthest — genuine long-haul is **8× more common at Frankfurt than at Berlin**.
3. **Lufthansa dominates where it builds a hub, and competes where it doesn't.** At its Frankfurt and Munich fortresses the Lufthansa Group runs ~58–60% of movements; at Berlin — a point-to-point, low-cost capital airport — it runs just **21%**, and the airport is led by **Ryanair, easyJet and Eurowings**.

**In one line:** *Germany's big hubs all close for six hours a night by law, so that's not what separates them — what separates them is structure: Frankfurt and Munich are Lufthansa hub-and-spoke fortresses reaching worldwide, while Berlin is a low-cost, point-to-point European airport where Lufthansa is a minor player.*

---

## Results

### When does each airport fly?
The six-hour night flight ban is clearly visible: traffic collapses to near-zero overnight and is packed into the day.

![Hourly aircraft movements at the three hubs, with the 23:00–05:00 night ban shaded](chart1_rhythm.png)

### Whose airport is it?
Lufthansa Group carriers (blue) tower over Frankfurt and Munich but barely register at Berlin, where low-cost carriers lead. All three panels share the same x-axis so the comparison is honest.

![Top airlines by share of movements at each airport](chart3_airlines.png)

### Where do the flights go?
Mostly Europe everywhere; Frankfurt has the largest intercontinental share.

![Domestic / Europe / Intercontinental split of movements per airport](chart2_reach.png)

> Note: the "Intercontinental" split above is continent-based and counts Turkey/North-Africa leisure routes, which flatters Berlin. Measured by true great-circle distance (>4,000 km), Berlin does almost no long-haul (2.0%) versus Frankfurt's 16.1%.

---

## Data sources

| Source | Used for | Notes |
|---|---|---|
| **[OpenSky Network](https://opensky-network.org/)** | Flight movements (departures + arrivals) | Free for non-commercial/research use. ADS-B tracking data — **no schedules, delays, or passenger/revenue figures.** OAuth2 client-credentials auth. |
| **[OurAirports](https://ourairports.com/)** | Airport → country, continent, coordinates | Public-domain reference data. |
| **[OpenFlights](https://openflights.org/data.html)** | Airline ICAO code → name | Community reference data (with hand corrections for a few stale/mislabelled entries). |

**Why not Flightradar24?** A consumer FR24 subscription has no bulk API and its data isn't for redistribution — it's great for a per-flight 3D visual (KML → Google Earth) but not for programmatic extraction, which is the skill this project is meant to show.

---

## How it works

A two-stage pipeline:

**Stage 1 — Extraction (`fetch_flights.py`)**
Authenticates to OpenSky (OAuth2), pulls a full day of departures and arrivals for all three airports via the `/flights/departure` and `/flights/arrival` endpoints, and writes one tidy `flights_raw.csv`.

**Stage 2 — Enrichment & analysis (`enrich_analyze.py`)**
- Derives each movement's **hour** (local time), the **other endpoint** airport, and its **direction**.
- Joins **airline** from the callsign prefix (ICAO code → name), with explicit hand corrections and a stated **Lufthansa Group** definition (`DLH, CLH, EWG, GEC, DLA, OCN, BEL, SWR, AUA`).
- Joins the other airport's **country, continent, and coordinates**, then classifies **reach** (Domestic / Europe / Intercontinental) and computes **great-circle distance**.
- Produces the three charts, a `flights_enriched.csv`, and a `routes_for_kepler.csv` for the 3D map.

---

## Repository structure

```
.
├── fetch_flights.py          # Stage 1: pull raw movements from OpenSky
├── enrich_analyze.py         # Stage 2: clean, enrich, analyse, plot
├── credentials.json          # your OpenSky client_id/secret  (gitignored!)
├── airports.csv              # OurAirports reference (downloaded)
├── airlines.dat              # OpenFlights reference (downloaded)
├── flights_raw.csv           # output of Stage 1
├── flights_enriched.csv      # output of Stage 2
├── routes_for_kepler.csv     # arc data for the 3D map
├── chart1_rhythm.png         # hourly traffic + night ban
├── chart2_reach.png          # reach split
└── chart3_airlines.png       # airline concentration
```

---

## Running it yourself

### 1. Prerequisites
```bash
pip install requests pandas matplotlib tzdata
```
> Install into the **same Python** you run the scripts with (e.g. `python3.12 -m pip install ...`).

### 2. Get OpenSky credentials
Create a free [OpenSky account](https://opensky-network.org/), then create an **API client** to obtain a `client_id` and `client_secret`. Put them in `credentials.json`:
```json
{ "client_id": "your_client_id", "client_secret": "your_client_secret" }
```
> ⚠️ Add `credentials.json` to `.gitignore` **before** you push. Never commit secrets.

### 3. Download the reference data
```bash
curl -L -o airports.csv https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv
curl -L -o airlines.dat https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat
```

### 4. Run the pipeline
```bash
python3 fetch_flights.py      # -> flights_raw.csv
python3 enrich_analyze.py     # -> enriched CSV, kepler CSV, 3 charts
```
> To analyse a different day, change the `DATE` variable in `fetch_flights.py` (use a normal weekday; avoid weekends and public holidays).

---

## The 3D flight-network map

Open [kepler.gl/demo](https://kepler.gl/demo), drag in `routes_for_kepler.csv`, and add an **Arc layer**:
- **Source:** `home_lat`, `home_lon`
- **Target:** `o_lat`, `o_lon`
- **Color by:** `reach`
- **Height / weight by:** `flights`

The result is Frankfurt, Munich and Berlin throwing arcs across a 3D globe — Frankfurt's worldwide reach obvious next to Berlin's tight European cluster.

---

## Limitations

- **Coverage:** OpenSky is crowd-sourced from volunteer ground receivers, so a small share of flights can be missing, and ~17% of movements had no confidently geolocatable other-airport. A few extreme distance values are estimation artefacts.
- **One day:** this is a single weekday snapshot, not a seasonal or annual average.
- **No economics:** flight-movement data shows *what flies*, not revenue, prices, passengers, or profit. Any competitive-economics reading here is a **hypothesis to test with other data**, not a proven claim.
- **Airline labels:** derived from crowd-sourced references; a small "unmatched" bucket is left honestly unlabelled rather than guessed.

---

## Possible extensions

- Add **aircraft type** (OpenSky aircraft database, `icao24` → type) to test whether widebodies really cluster on long-haul routes.
- Extend to **multiple days** to separate weekday/weekend patterns and smooth out coverage gaps.
- Add **Düsseldorf** or **Hamburg** for a broader comparison of hub vs point-to-point airports.
- Layer in a **single-flight 3D track** (FR24 KML → Google Earth) as a detail visual.

---

## Tech stack

**Python** · pandas · NumPy · Matplotlib · OpenSky REST API (OAuth2) · kepler.gl

---

## Data attribution & licensing

- Flight data © **The OpenSky Network** — used under its non-commercial/research terms. Please cite OpenSky if you reuse this.
- Airport data from **OurAirports** (public domain).
- Airline data from **OpenFlights** (Open Database License).

Project code is free to reuse for learning and non-commercial purposes. Reference datasets remain under their respective licenses.

---

*Built as an independent data project — extracting and analysing open aviation data from scratch.*