"""Angle and position math for the analog clock face."""

from __future__ import annotations

import math
from datetime import datetime, time, timedelta
from typing import Literal

from clockface.config import Slot


def hand_angle_degrees(
    hour: int, minute: int, second: int, hand: Literal["hour", "minute", "second"]
) -> float:
    """Degrees clockwise from 12 oclock."""
    if hand == "second":
        return second * 6
    if hand == "minute":
        return minute * 6 + second * 0.1
    hour_12 = hour % 12
    return hour_12 * 30 + minute * 0.5


def point_on_circle(center: tuple[float, float], radius: float, angle_degrees: float) -> tuple[float, float]:
    angle_radians = math.radians(angle_degrees - 90)
    x = center[0] + radius * math.cos(angle_radians)
    y = center[1] + radius * math.sin(angle_radians)
    return (x, y)


def slot_midpoint_angle(slot: Slot) -> float:
    """Angle matching where the minute hand points, since slots live within one hour."""
    minute = slot.midpoint_minutes() % 60
    return minute * 6


def _target_datetime(now: datetime, target_time: time) -> datetime:
    """Combine target_time with nows date, adjusting for midnight wrap if needed."""
    dt = now.replace(
        hour=target_time.hour,
        minute=target_time.minute,
        second=target_time.second,
        microsecond=0,
    )
    if (now - dt).total_seconds() > 12 * 3600:
        dt += timedelta(days=1)
    elif (dt - now).total_seconds() > 12 * 3600:
        dt -= timedelta(days=1)
    return dt


def countdown_fraction(now: datetime, end_time: time, total_time_minutes: int = 60) -> float | None:
    """Fraction (0-1) of the clock face remaining before end_time, or None if not in countdown."""
    end_moment = _target_datetime(now, end_time)
    remaining_seconds = (end_moment - now).total_seconds()
    if remaining_seconds < 0 or remaining_seconds > total_time_minutes * 60:
        return None
    return remaining_seconds / 3600


BLINK_WINDOW_SECONDS = 5 * 60
ALARM_WINDOW_SECONDS = 5 * 60


def is_final_blink_phase(now: datetime, end_time: time, total_time_minutes: int = 60) -> bool:
    """True during the last 5 minutes (or total_time if shorter) before end_time."""
    end_moment = _target_datetime(now, end_time)
    remaining_seconds = (end_moment - now).total_seconds()
    blink_window = min(BLINK_WINDOW_SECONDS, total_time_minutes * 60)
    return 0 <= remaining_seconds <= blink_window


def seconds_since_end(now: datetime, end_time: time) -> float | None:
    """Seconds elapsed since end_time if within the 5-minute alarm window, else None."""
    end_moment = _target_datetime(now, end_time)
    elapsed_seconds = (now - end_moment).total_seconds()
    if elapsed_seconds < 0 or elapsed_seconds > ALARM_WINDOW_SECONDS:
        return None
    return elapsed_seconds
