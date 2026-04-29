from datetime import datetime
from zoneinfo import ZoneInfo
from pool_aggregation.utils.timezones import PRAGUE, now_prague, hour_start, to_iso8601

PRAGUE_TZ = ZoneInfo("Europe/Prague")


def test_now_prague_uses_injected_clock():
    fixed = datetime(2024, 7, 15, 14, 30, tzinfo=PRAGUE_TZ)
    result = now_prague(clock=lambda: fixed)
    assert result == fixed


def test_now_prague_is_prague_aware():
    dt = now_prague()
    assert dt.tzinfo is not None
    assert dt.tzname() in ("CET", "CEST")


def test_hour_start_summer_dst():
    # 15 Jul 2024 is CEST (+02:00)
    dt = hour_start("15.7.2024", 14)
    assert dt.year == 2024
    assert dt.month == 7
    assert dt.day == 15
    assert dt.hour == 14
    assert dt.utcoffset().total_seconds() == 7200  # +02:00


def test_hour_start_winter():
    # 15 Jan 2024 is CET (+01:00)
    dt = hour_start("15.1.2024", 9)
    assert dt.utcoffset().total_seconds() == 3600  # +01:00


def test_hour_start_dst_spring_forward():
    # 31 Mar 2024 02:00 clocks spring forward — use 03:00 which is valid CEST
    dt = hour_start("31.3.2024", 3)
    assert dt.utcoffset().total_seconds() == 7200


def test_hour_start_dst_fall_back():
    # 27 Oct 2024 — clocks fall back; 03:00 is back to CET
    dt = hour_start("27.10.2024", 3)
    assert dt.utcoffset().total_seconds() == 3600


def test_to_iso8601_includes_offset():
    dt = hour_start("15.7.2024", 14)
    iso = to_iso8601(dt)
    assert "T" in iso
    assert "+02:00" in iso


def test_to_iso8601_winter_offset():
    dt = hour_start("15.1.2024", 9)
    iso = to_iso8601(dt)
    assert "+01:00" in iso
