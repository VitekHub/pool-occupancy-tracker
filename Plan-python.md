### BEGIN PROMPT

You are working in a Python project that currently scrapes live pool occupancy
and appends rows to per-pool CSV files. Each CSV row has the format:

```
<header line>
15.7.2024,Monday,14:15,42,14
```

Columns: `date (d.M.yyyy, Europe/Prague), day (English weekday name),
time (HH:mm), occupancy (int), hour (int 0-23)`.

Your task: in addition to the CSV, produce one pre-computed
JSON file per `(pool, pool_type)` that a downstream Nuxt dashboard can consume
directly, eliminating all client-side aggregation. Re-emit the JSON on the same
cadence as the CSV is updated. Store this JSON file in `data/aggregation`

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
    "maximumCapacity": <int>,
    "totalLanes": <int | null>,          // null for outside pools
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
    "averageUtilizationRate": <int 0-100>  // overall average for (today's weekday, current hour)
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
              "maximumCapacity": <int>,
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

Computation rules — follow exactly, because the dashboard's existing reference
implementation rounds and weights in this specific way:

1. Bucket every CSV record by `(weekId, day, hour)` where `weekId` is the
   ISO date of that record's Monday (`yyyy-MM-dd`).
2. Per-bucket weekly stats (goes into `weeklyOccupancyMap[...].days[day].hours[hour]`):
   - `minOccupancy = min(occupancy)`
   - `maxOccupancy = max(occupancy)`
   - `averageOccupancy = round(sum(occupancy) / count)`  (standard round-half-to-even or round-half-up is fine; match Python's built-in `round`)
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
   - `currentUtilizationRate = round(occupancy / maximumCapacity * 100)`.
   - `averageUtilizationRate` = the `averageUtilizationRate` value from
     `overallOccupancyMap.days[<today's weekday>].hours[<current hour>]`, or
     `0` if no history exists for that slot.
9. All timestamps in the output must be timezone-aware ISO8601 with the
   Europe/Prague offset (`+01:00` / `+02:00` depending on DST).
10. The JSON must be valid UTF-8, deterministic (stable key order where your
    tooling allows), and re-generated fully from the CSV on each write — do not
    try to incrementally patch it.

Deliver:
- A module that, given a pool config and its CSV path, returns the JSON
  structure above (and writes it next to the CSV with a `.json` extension).
- Wire it into whatever existing step emits the CSV so both outputs stay in
  sync.
- Unit tests covering: weekly bucketing across DST transitions, median of even
  and odd length lists, the four weighted-average weight tiers including the
  all-zero case, `availableWeekIds` padding for empty weeks, and
  `currentOccupancy = null` when today has no records.

Do not change the CSV format or the existing scraping cadence. Match field
names and types exactly as specified — the dashboard consumes this JSON
directly with no renaming layer.

### END PROMPT