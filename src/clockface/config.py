"""Load and represent the YAML configuration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

import yaml


def _parse_time(value: str) -> time:
    hour_str, minute_str = value.split(":")
    return time(hour=int(hour_str), minute=int(minute_str))


def _minutes_before(end_time: time, minutes_before: int) -> time:
    """Absolute time that is `minutes_before` earlier than end_time."""
    end_dt = datetime.combine(date.today(), end_time)
    return (end_dt - timedelta(minutes=minutes_before)).time()


@dataclass(frozen=True)
class Slot:
    start: time
    end: time
    image: str
    sound: str

    def contains(self, moment: time) -> bool:
        return self.start <= moment <= self.end

    def midpoint_minutes(self) -> float:
        """Minutes-past-midnight of the slot's midpoint, for angle calculations."""
        start_minutes = self.start.hour * 60 + self.start.minute
        end_minutes = self.end.hour * 60 + self.end.minute
        return (start_minutes + end_minutes) / 2


@dataclass(frozen=True)
class Config:
    end_time: time
    slots: list[Slot]
    fallback_sound: str | None = None
    siren_sound: str | None = None


def load_config(path: str | Path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    end_time = _parse_time(raw["end_time"])

    slots = [
        Slot(
            start=_minutes_before(end_time, slot["start"]),
            end=_minutes_before(end_time, slot["end"]),
            image=slot["image"],
            sound=slot["sound"],
        )
        for slot in raw.get("slots", [])
    ]

    return Config(
        end_time=end_time,
        slots=slots,
        fallback_sound=raw.get("fallback_sound"),
        siren_sound=raw.get("siren_sound"),
    )

