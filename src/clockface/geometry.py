"""Angle and position math for the analog clock face."""

from __future__ import annotations

import math
from datetime import datetime, time
from typing import Literal

from clockface.config import Slot


def hand_angle_degrees(
    hour: int, minute: int, second: int, hand: Literal["hour", "minute", "second"]
) -> float:
    """Degrees clockwise from 12 o'clock."""
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
    return hand_angle_degrees(0, int(minute), 0, "minute")


def countdown_fraction(now: datetime, end_time: time) -> float | None:
    """Fraction (0-1) of the last hour remaining before end_time, or None if not in it."""
    end_moment = now.replace(hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0)
    remaining_seconds = (end_moment - now).total_seconds()
    if remaining_seconds < 0 or remaining_seconds > 3600:
        return None
    return remaining_seconds / 3600


BLINK_WINDOW_SECONDS = 5 * 60
ALARM_WINDOW_SECONDS = 5 * 60


def is_final_blink_phase(now: datetime, end_time: time) -> bool:
    """True during the last 5 minutes before end_time."""
    end_moment = now.replace(hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0)
    remaining_seconds = (end_moment - now).total_seconds()
    return 0 <= remaining_seconds <= BLINK_WINDOW_SECONDS


def seconds_since_end(now: datetime, end_time: time) -> float | None:
    """Seconds elapsed since end_time if within the 5-minute alarm window, else None."""
    end_moment = now.replace(hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0)
    elapsed_seconds = (now - end_moment).total_seconds()
    if elapsed_seconds < 0 or elapsed_seconds > ALARM_WINDOW_SECONDS:
        return None
    return elapsed_seconds
