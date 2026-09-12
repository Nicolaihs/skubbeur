"""Load and represent the YAML configuration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

import yaml


def _parse_time(value: str | time) -> time:
    if isinstance(value, time):
        return value
    parts = str(value).split(":")
    if len(parts) == 2:
        return time(hour=int(parts[0]), minute=int(parts[1]))
    if len(parts) == 3:
        return time(hour=int(parts[0]), minute=int(parts[1]), second=int(parts[2]))
    raise ValueError(f"Invalid time format: {value}")


def _minutes_before(end_time: time, minutes_before: int) -> time:
    """Absolute time that is `minutes_before` earlier than end_time."""
    end_dt = datetime.combine(date.today(), end_time)
    return (end_dt - timedelta(minutes=minutes_before)).time()


def _resolve_config_path(value: str | None, config_dir: Path) -> str | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str(config_dir / path)


@dataclass(frozen=True)
class Slot:
    start: time
    end: time
    image: str
    sound: str

    def contains(self, moment: time) -> bool:
        if self.start <= self.end:
            return self.start <= moment <= self.end
        return moment >= self.start or moment <= self.end

    def midpoint_minutes(self) -> float:
        """Minutes-past-midnight of the slot's midpoint, for angle calculations."""
        start_minutes = self.start.hour * 60 + self.start.minute + self.start.second / 60
        end_minutes = self.end.hour * 60 + self.end.minute + self.end.second / 60
        if end_minutes < start_minutes:
            end_minutes += 24 * 60
        return (start_minutes + end_minutes) / 2


@dataclass(frozen=True)
class Config:
    end_time: time
    slots: list[Slot]
    total_time: int = 60
    title: str | None = None
    fallback_sound: str | None = None
    siren_sound: str | None = None


def load_config(path: str | Path, now: datetime | None = None) -> Config:
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    raw_total_time = raw.get("total_time", 60)
    total_time = min(60, max(1, int(raw_total_time))) if raw_total_time is not None else 60

    raw_end_time = raw.get("end_time")
    if raw_end_time is not None and str(raw_end_time).strip() != "":
        end_time = _parse_time(raw_end_time)
    else:
        current_dt = now or datetime.now()
        end_time = (current_dt + timedelta(minutes=total_time)).time().replace(microsecond=0)

    raw_title = raw.get("title")
    title = str(raw_title).strip() if raw_title is not None else None
    if title == "":
        title = None

    slots = [
        Slot(
            start=_minutes_before(end_time, slot["start"]),
            end=_minutes_before(end_time, slot["end"]),
            image=slot["image"],
            sound=_resolve_config_path(slot["sound"], config_path.parent),
        )
        for slot in raw.get("slots", [])
    ]

    return Config(
        end_time=end_time,
        slots=slots,
        total_time=total_time,
        title=title,
        fallback_sound=_resolve_config_path(raw.get("fallback_sound"), config_path.parent),
        siren_sound=_resolve_config_path(raw.get("siren_sound"), config_path.parent),
    )

