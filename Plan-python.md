### BEGIN PROMPT

You are working in a Python project that currently scrapes live pool occupancy
and appends rows to per-pool CSV files in `data/`. Each CSV row has the format:

```
<header line>
15.7.2024,Monday,14:15,42,14
```

Columns: `date (d.M.yyyy, Europe/Prague), day (English weekday name),
time (HH:mm), occupancy (int), hour (int 0-23)`.

This plan deliberately works against the ORIGINAL CSVs in `data/` (not the new
files in `data/new/`). The existing `occupancy.py` and `capacity.py`
scripts MUST be left untouched. Build a parallel pipeline in a new package —
duplicated code between the old scripts and the new package is acceptable and
expected.

Your task: in addition to the CSV, produce one pre-computed JSON file per
`(pool, pool_type)` that a downstream Nuxt dashboard can consume directly,
eliminating all client-side aggregation. Re-emit the JSON on the same cadence
as the CSV is updated. Store this JSON file in `data/aggregation`.

All times are Europe/Prague. Week boundary is Monday (ISO weekday 1). Day names
are English (`Monday`..`Sunday`) — match the CSV exactly.

Output one JSON object per pool file with this exact shape (keys are
camelCase; do not rename):

```jsonc
{
  "schemaVersion": 1,
  "generatedAt": "<ISO8601 with Prague offset>",
  "timezone": "Europe/Prague",
  "pool": {
    "name": "<pool display name>",
    "poolType": "inside" | "outside",
    "maximumCapacity": <int>,             // static pool-level capacity from config
    "totalLanes": <int | null>,           // null for outside pools
    "weekdaysOpeningHours": "<e.g. 6-22>",
    "weekendOpeningHours": "<e.g. 8-21>",
    "todayClosed": <bool>,
    "temporarilyClosed": "<d.M.yyyy - d.M.yyyy> | null"
  },
  "dataRange": {
    "firstRecordAt": "<ISO8601>",
    "lastRecordAt": "<ISO8601>"
  },
  "currentOccupancy": {                  // null if no records today
    "occupancy": <int>,                  // latest today's reading
    "time": "HH:mm",
    "timestamp": "<ISO8601>",
    "currentUtilizationRate": <int 0-100>,
    "averageUtilizationRate": <int 0-100>,  // overall average for (today's weekday, current hour)
    "maximumCapacity": <int>,               // resolved per (date, hour) - see "maximumCapacity resolution" below
    "totalLanes": <int | null>,             // null for outside pools; otherwise the pool's totalLanes
    "openLanes": <int | null>,              // round((resolved per (date, hour) maximumCapacity * totalLanes) / pool's static `maximumCapacity`); null if not applicable
  },
  "availableWeekIds": ["yyyy-MM-dd", ...],  // Monday of each week, ascending, incl. empty weeks up to current week
  "weeklyOccupancyMap": {
    "<weekId yyyy-MM-dd>": {
      "maxWeekValues": { "utilizationRate": <int> },
      "days": {
        "Monday": {
          "maxDayValues": { "utilizationRate": <int> },
          "hours": {
            "6": {
              "day": "Monday",
              "hour": 6,
              "date": "<ISO8601 start of that hour in Prague>",
              "minOccupancy": <int>,
              "maxOccupancy": <int>,
              "averageOccupancy": <int>,       // round(sum/count)
              "maximumCapacity": <int>,        // resolved per (date, hour) - see "maximumCapacity resolution" below
              "totalLanes": <int | null>,      // null for outside pools; otherwise the pool's totalLanes
              "openLanes": <int | null>,       // round((resolved per (date, hour) maximumCapacity * totalLanes) / pool's static `maximumCapacity`); null if not applicable
              "utilizationRate": <int>,        // round(averageOccupancy / maximumCapacity * 100)
              "remainingCapacity": <int>       // maximumCapacity - averageOccupancy
            }
            // ...only include hours with at least one sample
          }
        }
        // ...only include days with data
      }
    }
  },
  "overallOccupancyMap": {
    "maxOverallValues": {
      "averageUtilizationRate": <int>,
      "weightedAverageUtilizationRate": <int>,
      "medianUtilizationRate": <int>
    },
    "days": {
      "Monday": {
        "maxDayValues": {
          "averageUtilizationRate": <int>,
          "weightedAverageUtilizationRate": <int>,
          "medianUtilizationRate": <int>
        },
        "hours": {
          "6": {
            "averageUtilizationRate": <int>,
            "weightedAverageUtilizationRate": <int>,
            "medianUtilizationRate": <int>
          }
        }
      }
    }
  }
}
```

**maximumCapacity resolution** — used both inside `weeklyOccupancyMap` hour
buckets and inside `currentOccupancy`.

- If the pool's config has a `hourlyMaxCapacity` key, read the CSV at
  `data/<hourlyMaxCapacity>` and look up the row matching `(Date, Hour)`
  (normalize `HH:00:00` -> `HH:00`). Use the `Maximum Occupancy` column value
  as `maximumCapacity` for that hour bucket.
- Otherwise — or when no row matches that `(date, hour)` — fall back to the
  pool's static `maximumCapacity` from the pool config.

The top-level `pool.maximumCapacity` is always the static config value and is
unaffected by this resolution.

Computation rules — follow exactly, because the dashboard's existing reference
implementation rounds and weights in this specific way:

1. Bucket every CSV record by `(weekId, day, hour)` where `weekId` is the
   ISO date of that record's Monday (`yyyy-MM-dd`).
2. Per-bucket weekly stats (goes into `weeklyOccupancyMap[...].days[day].hours[hour]`):
   - `minOccupancy = min(occupancy)`
   - `maxOccupancy = max(occupancy)`
   - `averageOccupancy = round(sum(occupancy) / count)`  (standard round-half-to-even or round-half-up is fine; match Python's built-in `round`)
   - `maximumCapacity` = resolved per (date, hour) — see the resolution section above.
   - `totalLanes` = the pool's `totalLanes` from config (`null` for outside pools).
   - `openLanes` = round((resolved per (date, hour) `maximumCapacity` * `totalLanes`) / pool's static `maximumCapacity`); null if not applicable
   - `utilizationRate = round(averageOccupancy / maximumCapacity * 100)`
   - `remainingCapacity = maximumCapacity - averageOccupancy`
   - `date` = ISO8601 timestamp for the start of that hour in Europe/Prague.
3. `maxDayValues.utilizationRate` for a week/day = max of that day's
   hourly `utilizationRate` values. `maxWeekValues.utilizationRate` = max across
   the week's `maxDayValues`.
4. For the overall map, for each `(day, hour)`, collect the list
   `W = [utilizationRate from each week that has that (day, hour)]`:
   - `averageUtilizationRate = round(mean(W))`
   - `medianUtilizationRate = round(median(W))` (for even length, mean of the two middles, then round)
   - `weightedAverageUtilizationRate = round(sum(w_i * r_i) / sum(w_i))` with
     per-sample weights:
     - `r_i == 0` -> `0`
     - `0 < r_i < 1` -> `0.1`
     - `1 <= r_i < 10` -> `0.5`
     - `r_i >= 10` -> `1`
     - If `sum(w_i) == 0`, emit `0`.
5. `maxDayValues.<metric>` per overall day = max of that metric across hours.
   `maxOverallValues.<metric>` = max across all `(day, hour)`.
6. Only emit hours with data; only emit days with at least one hour; only emit
   weeks with at least one day. Hour keys are strings (`"6"`).
7. `availableWeekIds`: ascending list of Monday ISO dates from the earliest
   observed week through the current week (Prague "today"), INCLUDING weeks
   with zero data. The current week must appear even if partial / empty.
8. `currentOccupancy`:
   - `null` if no records for Prague's current date.
   - Otherwise, use the latest record for today: set `occupancy`, `time`,
     `timestamp`.
   - `maximumCapacity` = resolved for (today's date, current hour) — same
     resolution rules as above.
   - `totalLanes` = the pool's `totalLanes` from config (`null` for outside pools).
   - `openLanes` = round((resolved per (date, hour) `maximumCapacity` * `totalLanes`) / pool's static `maximumCapacity`); null if not applicable
   - `currentUtilizationRate = round(occupancy / maximumCapacity * 100)` using
     the resolved `maximumCapacity`.
   - `averageUtilizationRate` = the `averageUtilizationRate` value from
     `overallOccupancyMap.days[<today's weekday>].hours[<current hour>]`, or
     `0` if no history exists for that slot.
9. All timestamps in the output must be timezone-aware ISO8601 with the
   Europe/Prague offset (`+01:00` / `+02:00` depending on DST).
10. The JSON must be valid UTF-8, deterministic (stable key order where your
    tooling allows), and re-generated fully from the CSV on each write — do not
    try to incrementally patch it.

Project structure — create a new package alongside the existing flat scripts.
Do NOT modify `occupancy.py` or `capacity.py`. Duplicated helpers between the
new package and the old scripts are intentional and acceptable. The tree below
is rooted at the repository root (there is no literal folder named `project/`):

```
project/
  occupancy.py                  # existing - do not modify
  capacity.py                   # existing - do not modify
  data/                         # existing - source CSVs live here
    aggregation/                # NEW - generated JSON output destination
  pool_aggregation/             # NEW - Python package for the new pipeline
    __init__.py
    __main__.py                 # enables `python -m pool_aggregation`
    cli.py                      # entry point: read configs, loop pools, write JSON
    config.py                   # load data/pool_occupancy_config.json
    models/
      __init__.py
      pool.py                   # dataclasses: PoolConfig, PoolTypeConfig
      records.py                # dataclasses: OccupancyRecord, HourBucket
      output.py                 # dataclasses/TypedDicts mirroring the JSON schema
    io/
      __init__.py
      csv_reader.py             # parse data/<csvFile> into OccupancyRecord list
      capacity_reader.py        # parse data/<hourlyMaxCapacity> into a (date,hour)->int lookup
      json_writer.py            # deterministic UTF-8 JSON writer into data/aggregation/
    aggregation/
      __init__.py
      bucketing.py              # (weekId, day, hour) bucketing, week id helpers
      weekly.py                 # weeklyOccupancyMap + maxWeekValues / maxDayValues
      overall.py                # overallOccupancyMap (mean/median/weighted) + max rollups
      current.py                # currentOccupancy block (incl. totalLanes, openLanes)
      capacity.py               # maximumCapacity resolution
    utils/
      __init__.py
      timezones.py              # Prague tz helpers, ISO8601 formatting, DST-safe hour starts
      rounding.py               # shared round / weighted-average helpers
  tests/                        # NEW
    __init__.py
    conftest.py                 # pytest fixtures (tmp_path CSVs, fake clock)
    fixtures/
      sample_occupancy.csv
      sample_hourly_capacity.csv
      config_snippet.json
    test_csv_reader.py
    test_capacity_reader.py
    test_bucketing.py
    test_weekly.py
    test_overall.py
    test_current.py
    test_capacity_resolution.py # maximumCapacity fallback logic
    test_json_writer.py
    test_cli.py                 # end-to-end: csv -> json on disk
  requirements-dev.txt          # add pytest (and freeze any new test deps)
```

Deliver:
- A new `pool_aggregation` package that, given a pool config and its CSV path,
  returns the JSON structure above and writes it to
  `data/aggregation/<csvFile>.json`.
- A CLI entry (`python -m pool_aggregation`) that loops every pool in
  `data/pool_occupancy_config.json` and regenerates the JSON for each, reading
  only the original CSVs in `data/`.
- Keep `occupancy.py` and `capacity.py` unchanged. Re-implement any shared
  logic (config loading, Prague tz handling, hourly capacity CSV parsing, etc.)
  inside `pool_aggregation/` — do not try to import from the legacy scripts.
- Update `.github/workflows/schedule.yml`: add a step after the existing
  "Run pool tracker" step (and before "Commit and push if changed") that runs
  `python -m pool_aggregation`. Extend the `git add` line in the commit step
  to also include `data/aggregation/` so the generated JSON is committed
  alongside the CSVs. The `daily-capacity` job should similarly run the new
  CLI after `capacity.py` so JSON reflects any capacity refresh on the same
  day. Do not alter the scraper's own code path.
- Unit tests covering:
  - weekly bucketing across DST transitions
  - median of even and odd length lists
  - the four weighted-average weight tiers, including the all-zero case
  - `availableWeekIds` padding for empty weeks
  - `currentOccupancy = null` when today has no records
  - `maximumCapacity` resolution: hourly CSV hit, hourly CSV miss (falls back
    to pool's static `maximumCapacity`), and pool without `hourlyMaxCapacity`
    configured (always uses the static value)
  - `totalLanes` propagation: present for inside pools, `null` for outside
    pools, in both `weeklyOccupancyMap` hour buckets and `currentOccupancy`
  - `openLanes` rounding formula, plus null propagation when `totalLanes` is
    missing
  - end-to-end CLI test: given a tiny fixture CSV + config, the generated
    JSON on disk matches an expected snapshot
- Run tests with `pytest`. Keep tests hermetic — no network, no real clock;
  pass the "now" timestamp in as a parameter / fixture where needed.

Do not change the CSV format or the existing scraping cadence. Match field
names and types exactly as specified — the dashboard consumes this JSON
directly with no renaming layer.

### END PROMPT
