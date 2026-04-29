from pool_aggregation.aggregation.overall import build_overall_map


def _week(day, hour_key, util):
    """Minimal weeklyOccupancyMap entry with a single hour bucket."""
    return {
        "maxWeekValues": {"utilizationRate": util},
        "days": {
            day: {
                "maxDayValues": {"utilizationRate": util},
                "hours": {
                    hour_key: {"utilizationRate": util},
                },
            }
        },
    }


# --- empty input ---

def test_empty_weekly_map_returns_empty():
    assert build_overall_map({}) == {}


# --- structure ---

def test_days_key_present():
    wmap = {"2024-07-15": _week("Monday", "14", 50)}
    result = build_overall_map(wmap)
    assert "days" in result


def test_day_present():
    wmap = {"2024-07-15": _week("Monday", "14", 50)}
    assert "Monday" in build_overall_map(wmap)["days"]


def test_hour_key_present():
    wmap = {"2024-07-15": _week("Monday", "14", 50)}
    assert "14" in build_overall_map(wmap)["days"]["Monday"]["hours"]


def test_hour_has_three_metrics():
    wmap = {"2024-07-15": _week("Monday", "14", 50)}
    hour = build_overall_map(wmap)["days"]["Monday"]["hours"]["14"]
    assert set(hour) == {"averageUtilizationRate", "weightedAverageUtilizationRate", "medianUtilizationRate"}


# --- single week (average == median == weighted) ---

def test_single_week_all_metrics_equal_rate():
    wmap = {"2024-07-15": _week("Monday", "14", 60)}
    hour = build_overall_map(wmap)["days"]["Monday"]["hours"]["14"]
    assert hour["averageUtilizationRate"] == 60
    assert hour["medianUtilizationRate"] == 60
    assert hour["weightedAverageUtilizationRate"] == 60


# --- multiple weeks ---

def _two_week_map(r1, r2):
    return {
        "2024-07-15": _week("Monday", "14", r1),
        "2024-07-22": _week("Monday", "14", r2),
    }


def test_average_two_weeks():
    hour = build_overall_map(_two_week_map(60, 80))["days"]["Monday"]["hours"]["14"]
    assert hour["averageUtilizationRate"] == 70


def test_average_rounding_banker():
    # (65 + 66) / 2 = 65.5 → banker's round → 66
    hour = build_overall_map(_two_week_map(65, 66))["days"]["Monday"]["hours"]["14"]
    assert hour["averageUtilizationRate"] == 66


def test_median_odd_count():
    wmap = {
        "w1": _week("Monday", "14", 10),
        "w2": _week("Monday", "14", 50),
        "w3": _week("Monday", "14", 90),
    }
    hour = build_overall_map(wmap)["days"]["Monday"]["hours"]["14"]
    assert hour["medianUtilizationRate"] == 50


def test_median_even_count():
    # median of [10, 20] = 15.0 → 15
    hour = build_overall_map(_two_week_map(10, 20))["days"]["Monday"]["hours"]["14"]
    assert hour["medianUtilizationRate"] == 15


def test_median_even_half_rounds():
    # median of [10, 11] = 10.5 → banker's round → 10
    hour = build_overall_map(_two_week_map(10, 11))["days"]["Monday"]["hours"]["14"]
    assert hour["medianUtilizationRate"] == 10


# --- weighted average weight tiers ---

def test_weighted_all_zero():
    hour = build_overall_map(_two_week_map(0, 0))["days"]["Monday"]["hours"]["14"]
    assert hour["weightedAverageUtilizationRate"] == 0


def test_weighted_tier_boundary_high():
    # both >= 10 → weight 1.0 each → simple average
    hour = build_overall_map(_two_week_map(20, 40))["days"]["Monday"]["hours"]["14"]
    assert hour["weightedAverageUtilizationRate"] == 30


def test_weighted_zero_suppressed():
    # 0 gets weight 0, 50 gets weight 1 → result is 50
    hour = build_overall_map(_two_week_map(0, 50))["days"]["Monday"]["hours"]["14"]
    assert hour["weightedAverageUtilizationRate"] == 50


# --- only emit slots with data ---

def test_only_days_with_data_emitted():
    wmap = {
        "2024-07-15": _week("Monday", "14", 50),
        "2024-07-22": _week("Tuesday", "9", 70),
    }
    days = build_overall_map(wmap)["days"]
    assert set(days.keys()) == {"Monday", "Tuesday"}


def test_only_hours_with_data_emitted():
    wmap = {
        "2024-07-15": _week("Monday", "14", 50),
        "2024-07-22": _week("Monday", "15", 70),
    }
    hours = build_overall_map(wmap)["days"]["Monday"]["hours"]
    assert set(hours.keys()) == {"14", "15"}


# --- multiple days in same week ---

def test_two_days_same_week():
    wmap = {
        "2024-07-15": {
            "maxWeekValues": {"utilizationRate": 80},
            "days": {
                "Monday": {
                    "maxDayValues": {"utilizationRate": 60},
                    "hours": {"14": {"utilizationRate": 60}},
                },
                "Tuesday": {
                    "maxDayValues": {"utilizationRate": 80},
                    "hours": {"9": {"utilizationRate": 80}},
                },
            },
        }
    }
    days = build_overall_map(wmap)["days"]
    assert days["Monday"]["hours"]["14"]["averageUtilizationRate"] == 60
    assert days["Tuesday"]["hours"]["9"]["averageUtilizationRate"] == 80


# --- maxDayValues per day ---

def test_max_day_values_key_present():
    wmap = {"2024-07-15": _week("Monday", "14", 50)}
    day = build_overall_map(wmap)["days"]["Monday"]
    assert "maxDayValues" in day


def test_max_day_values_has_three_metrics():
    wmap = {"2024-07-15": _week("Monday", "14", 50)}
    mdv = build_overall_map(wmap)["days"]["Monday"]["maxDayValues"]
    assert set(mdv) == {"averageUtilizationRate", "weightedAverageUtilizationRate", "medianUtilizationRate"}


def test_max_day_values_single_hour():
    wmap = {"2024-07-15": _week("Monday", "14", 60)}
    mdv = build_overall_map(wmap)["days"]["Monday"]["maxDayValues"]
    assert mdv["averageUtilizationRate"] == 60
    assert mdv["medianUtilizationRate"] == 60
    assert mdv["weightedAverageUtilizationRate"] == 60


def test_max_day_values_multi_hour_picks_max():
    wmap = {
        "2024-07-15": {
            "maxWeekValues": {"utilizationRate": 80},
            "days": {
                "Monday": {
                    "maxDayValues": {"utilizationRate": 80},
                    "hours": {
                        "14": {"utilizationRate": 40},
                        "15": {"utilizationRate": 80},
                    },
                }
            },
        }
    }
    mdv = build_overall_map(wmap)["days"]["Monday"]["maxDayValues"]
    assert mdv["averageUtilizationRate"] == 80


# --- maxOverallValues ---

def test_max_overall_values_key_present():
    wmap = {"2024-07-15": _week("Monday", "14", 50)}
    assert "maxOverallValues" in build_overall_map(wmap)


def test_max_overall_values_has_three_metrics():
    wmap = {"2024-07-15": _week("Monday", "14", 50)}
    mov = build_overall_map(wmap)["maxOverallValues"]
    assert set(mov) == {"averageUtilizationRate", "weightedAverageUtilizationRate", "medianUtilizationRate"}


def test_max_overall_values_single_slot():
    wmap = {"2024-07-15": _week("Monday", "14", 70)}
    mov = build_overall_map(wmap)["maxOverallValues"]
    assert mov["averageUtilizationRate"] == 70
    assert mov["medianUtilizationRate"] == 70
    assert mov["weightedAverageUtilizationRate"] == 70


def test_max_overall_values_across_days():
    wmap = {
        "2024-07-15": {
            "maxWeekValues": {"utilizationRate": 80},
            "days": {
                "Monday": {
                    "maxDayValues": {"utilizationRate": 40},
                    "hours": {"14": {"utilizationRate": 40}},
                },
                "Tuesday": {
                    "maxDayValues": {"utilizationRate": 80},
                    "hours": {"9": {"utilizationRate": 80}},
                },
            },
        }
    }
    mov = build_overall_map(wmap)["maxOverallValues"]
    assert mov["averageUtilizationRate"] == 80


def test_max_overall_values_two_weeks():
    wmap = {
        "2024-07-15": _week("Monday", "14", 30),
        "2024-07-22": _week("Monday", "14", 70),
    }
    # average of [30, 70] = 50; max across all slots = 50
    mov = build_overall_map(wmap)["maxOverallValues"]
    assert mov["averageUtilizationRate"] == 50
