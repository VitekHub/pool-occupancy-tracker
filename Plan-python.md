### BEGIN PROMPT

You are working in a Python project that currently scrapes live pool occupancy
and appends rows to per-pool CSV files in `data/`. Each CSV row has the format:

```
<header line>
15.07.2024,Monday,14:15,42,14
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

Incremental implementation steps

Ground rules for every step below:
- After each step, the project MUST still run end-to-end without errors.
  Specifically: `python occupancy.py` and `python capacity.py` keep working
  unchanged, and `python -m pool_aggregation` (once the CLI exists from
  step 3 onward) must exit with code 0 even if the output JSON is partial or
  stubbed.
- Do NOT modify `occupancy.py` or `capacity.py` in any step.
- Write tests in the SAME step that introduces the behavior they cover.
  Running `pytest` at the end of any step must be green. Do not batch tests
  into a final "testing" step.
- Keep diffs small: one step = one small, coherent slice of the schema
  or pipeline.
- "Stubbed" fields / sections are allowed in early steps (empty dict, `null`,
  `0`, etc.) as long as the JSON is still valid and the CLI runs. Each
  subsequent step fleshes out one more area.

Step 1 — Package skeleton + dev deps.
- Create the `pool_aggregation/` package with `__init__.py`, `__main__.py`,
  and an empty `cli.py` exposing `main()` that just prints "pool_aggregation:
  noop" and returns 0. Wire `__main__.py` to call `cli.main()`.
- Create `data/aggregation/` as an empty directory (add a `.gitkeep`).
- Create `tests/` with `__init__.py` and `conftest.py` (empty for now).
- Add `requirements-dev.txt` with `pytest`.
- Test: `tests/test_smoke.py` that imports `pool_aggregation` and asserts
  `cli.main()` returns 0.
- Done when: `python -m pool_aggregation` prints the noop line and exits 0;
  `pytest` passes.

Step 2 — Config loader.
- Add `pool_aggregation/config.py` with `load_pool_config(path=...)` that
  reads `data/pool_occupancy_config.json` and returns the parsed dict.
- Add `pool_aggregation/models/pool.py` with `PoolConfig` / `PoolTypeConfig`
  dataclasses and a helper `iter_pool_types(cfg)` yielding `(pool_name,
  pool_type_name, pool_type_config)` tuples.
- Wire the CLI to load the config and iterate pool types, logging each one.
  No JSON output yet.
- Tests: `test_config.py` using a tiny fixture config under
  `tests/fixtures/config_snippet.json`, asserting iteration order and types.
- Done when: CLI prints one line per pool-type and exits 0.

Step 3 — CSV reader + empty JSON writer.
- Add `pool_aggregation/io/csv_reader.py` with `read_records(path)` returning
  `list[OccupancyRecord]` (dataclass in `models/records.py`). Each record has
  `date_str`, `day`, `time_str`, `occupancy`, `hour`.
- Add `pool_aggregation/io/json_writer.py` with `write_json(path, payload)`
  that writes deterministic UTF-8 JSON (sorted keys where order doesn't
  matter, `indent=2`, `ensure_ascii=False`).
- CLI: for each pool-type, read its CSV and write a JSON file to
  `data/aggregation/<csvFile>.json` containing only `schemaVersion`,
  `generatedAt`, `timezone`, and stub empties for the rest
  (`pool: {}`, `dataRange: null`, `currentOccupancy: null`,
  `availableWeekIds: []`, `weeklyOccupancyMap: {}`, `overallOccupancyMap: {}`).
- Tests: `test_csv_reader.py` (valid row, bad row skipped) and
  `test_json_writer.py` (roundtrip + deterministic ordering).
- Done when: running the CLI produces one valid (but near-empty) JSON file
  per pool-type on disk.

Step 4 — Prague timezone + rounding utilities.
- Add `pool_aggregation/utils/timezones.py`: `PRAGUE = ZoneInfo("Europe/Prague")`,
  `now_prague(clock=None)`, `hour_start(date_str, hour, tz=PRAGUE)` returning
  an aware datetime, `to_iso8601(dt)`.
- Add `pool_aggregation/utils/rounding.py`: `py_round(x)` matching Python's
  built-in `round`, and `weighted_average(values)` applying the four weight
  tiers from rule 4 (returns `0` when `sum(w_i) == 0`).
- CLI now fills `generatedAt` with a real Prague-offset ISO8601 timestamp.
- Tests: `test_timezones.py` (DST boundary both directions), `test_rounding.py`
  (each weight tier + all-zero + mixed list).
- Done when: JSON still valid, `generatedAt` is timezone-aware ISO8601.

Step 5 — Static `pool` block + `dataRange`.
- Populate the `pool` object from config: `name`, `poolType`, static
  `maximumCapacity`, `totalLanes` (null for outside pools),
  `weekdaysOpeningHours`, `weekendOpeningHours`, `todayClosed`,
  `temporarilyClosed`.
- Compute `dataRange` from the CSV (min/max record timestamps as ISO8601 in
  Prague tz). Null when the CSV is empty.
- Tests: `test_pool_block.py` (inside vs outside pool, `totalLanes` null path),
  `test_data_range.py` (empty CSV → null, populated CSV → correct bounds).
- Done when: JSON has correct static metadata for every pool-type.

Step 6 — Bucketing helpers + `availableWeekIds`.
- Add `pool_aggregation/aggregation/bucketing.py` with `week_id(date)`
  returning the ISO Monday for a given record's date (`yyyy-MM-dd`), and
  `bucket_records(records)` returning a `{(weekId, day, hour): [records]}`
  map.
- Compute `availableWeekIds`: ascending Mondays from the earliest observed
  week through the current Prague week, INCLUDING empty weeks. Pass the
  clock in so tests can pin "now".
- Tests: `test_bucketing.py` (week boundary Sunday→Monday, DST weeks),
  `test_available_week_ids.py` (padding empty weeks, current week forced in).
- Done when: `availableWeekIds` is populated and monotonically ascending.

Step 7 — `maximumCapacity` resolution.
- Add `pool_aggregation/io/capacity_reader.py` with a cached
  `load_hourly_capacity(filename)` returning `{(date_str, hour_str): int}`.
- Add `pool_aggregation/aggregation/capacity.py` with
  `resolve_max_capacity(pool_type_config, date_str, hour_str)` mirroring
  `get_max_allowed` from `occupancy.py` (hourly CSV hit, else fallback to
  static `maximumCapacity`).
- No schema change yet — subsequent steps consume this helper.
- Tests: `test_capacity_reader.py` (parses "HH:00:00" and "HH:00"),
  `test_capacity_resolution.py` (hit, miss-falls-back, no `hourlyMaxCapacity`
  configured).
- Done when: helper is importable and covered by tests. CLI output unchanged.

Step 8 — `weeklyOccupancyMap` hour buckets (core fields).
- Build `weeklyOccupancyMap[weekId].days[day].hours[hour]` with:
  `day`, `hour`, `date`, `minOccupancy`, `maxOccupancy`, `averageOccupancy`,
  `maximumCapacity` (from step 7), `utilizationRate`, `remainingCapacity`.
  Leave `totalLanes` and `openLanes` unset for now (or hardcoded `null`).
- Only emit hours/days/weeks that actually have data.
- Tests: `test_weekly.py` covering averaging rounding, remainingCapacity,
  utilizationRate, and the "only emit populated" rule.
- Done when: a fixture CSV produces the expected week/day/hour tree.

Step 9 — `totalLanes` + `openLanes` on hour buckets.
- Add `totalLanes` to each hour bucket (pool's `totalLanes` from config,
  `null` for outside pools).
- Add `openLanes`: `round((resolved maximumCapacity * totalLanes) /
  pool's static maximumCapacity)`; `null` when `totalLanes` is `null` or the
  static `maximumCapacity` is 0.
- Tests extend `test_weekly.py` and add `test_open_lanes.py` covering the
  rounding formula, outside-pool null propagation, and divide-by-zero guard.
- Done when: hour buckets include both fields with correct values.

Step 10 — `maxDayValues` and `maxWeekValues`.
- Populate `maxDayValues.utilizationRate` per day (max over that day's hours)
  and `maxWeekValues.utilizationRate` per week (max over the week's
  `maxDayValues`).
- Tests in `test_weekly.py` cover single-hour day, multi-hour day, and
  multi-day week.
- Done when: every emitted day/week has its max block.

Step 11 — `overallOccupancyMap` per `(day, hour)` stats.
- For each `(day, hour)`, gather the list of weekly `utilizationRate` values
  from step 8 and compute `averageUtilizationRate`,
  `medianUtilizationRate`, `weightedAverageUtilizationRate` using the
  helpers from step 4.
- Emit only `(day, hour)` slots that have at least one week of data.
- Tests: `test_overall.py` (odd/even medians, weight tier matrix, empty
  slot skipped).
- Done when: `overallOccupancyMap.days[day].hours[hour]` is populated.

Step 12 — `overallOccupancyMap` max rollups.
- Add `maxDayValues` per day (max per metric across the day's hours) and
  `maxOverallValues` (max per metric across all `(day, hour)`).
- Tests extend `test_overall.py`.
- Done when: both max blocks are present and consistent with the hourly data.

Step 13 — `currentOccupancy`.
- Build the `currentOccupancy` block: `null` if no records for Prague's
  current date; otherwise latest record today with `occupancy`, `time`,
  `timestamp`, resolved `maximumCapacity`, `totalLanes`, `openLanes`,
  `currentUtilizationRate`, and `averageUtilizationRate` sourced from
  `overallOccupancyMap.days[<today's weekday>].hours[<current hour>]`
  (fallback `0` if missing).
- Inject the clock via CLI/tests so "today" is deterministic.
- Tests: `test_current.py` covering null-today, populated-today, fallback
  `averageUtilizationRate`, and outside-pool `totalLanes`/`openLanes` null.
- Done when: the JSON's `currentOccupancy` reflects the latest CSV row for
  today.

Step 14 — End-to-end CLI snapshot test.
- Add `tests/test_cli.py` that runs the CLI against a tiny fixture
  (`tests/fixtures/sample_occupancy.csv`, `sample_hourly_capacity.csv`,
  `config_snippet.json`) into a `tmp_path` output dir with a pinned clock,
  and asserts the produced JSON equals an expected snapshot committed under
  `tests/fixtures/expected_<pool>.json`.
- Done when: the full pipeline is covered by a single deterministic test.

Step 15 — GitHub Actions integration.
- Update `.github/workflows/schedule.yml`:
  - In the `track-occupancy` job, add a step "Run aggregation" after
    "Run pool tracker" and before "Commit and push if changed" that runs
    `python -m pool_aggregation`.
  - Extend the `git add` line in the commit step to include
    `data/aggregation/` so the generated JSON is committed with the CSVs.
- Do not alter the scraper's or capacity script's own code paths.
- Done when: the workflow file parses (YAML lint) and the new steps are
  present in both jobs. Verify locally that the command still runs clean
  (`python -m pool_aggregation` exits 0 on the real repo data).

Across all steps: tests must stay hermetic (no network, injected clock,
tmp_path for I/O), and the JSON field names/types must match the schema
above exactly — the downstream dashboard consumes this JSON with no
renaming layer.

### END PROMPT
