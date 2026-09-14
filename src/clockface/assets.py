"""Download/cache slot images and load slot sounds."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pygame
import requests
from PIL import Image, ImageSequence

from clockface.config import Config

CACHE_DIR = Path(".cache/images")
DEFAULT_FRAME_DURATION_MS = 100


@dataclass
class SlotImage:
    """One or more frames of a slots image, e.g. from an animated GIF."""

    frames: list[pygame.Surface]
    durations_ms: list[int]

    def current_frame(self, ticks_ms: int) -> pygame.Surface:
        if len(self.frames) == 1:
            return self.frames[0]
        total = sum(self.durations_ms)
        elapsed = ticks_ms % total
        for frame, duration in zip(self.frames, self.durations_ms):
            if elapsed < duration:
                return frame
            elapsed -= duration
        return self.frames[-1]


def get_cached_image_path(url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(url).suffix or ".img"
    cache_path = CACHE_DIR / f"{hashlib.md5(url.encode()).hexdigest()}{suffix}"
    if not cache_path.exists():
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        cache_path.write_bytes(response.content)
    return cache_path


def load_slot_images(config: Config) -> dict[int, SlotImage]:
    images: dict[int, SlotImage] = {}
    for index, slot in enumerate(config.slots):
        try:
            path = get_cached_image_path(slot.image)
            images[index] = _load_slot_image(path)
        except (requests.RequestException, pygame.error, OSError) as exc:
            print(f"Warning: could not load image for slot {index} ({slot.image}): {exc}")
    return images


def _load_slot_image(path: Path) -> SlotImage:
    with Image.open(path) as pil_image:
        if not getattr(pil_image, "is_animated", False):
            return SlotImage(frames=[pygame.image.load(str(path)).convert_alpha()], durations_ms=[0])

        frames: list[pygame.Surface] = []
        durations_ms: list[int] = []
        for frame in ImageSequence.Iterator(pil_image):
            rgba = frame.convert("RGBA")
            surface = pygame.image.fromstring(rgba.tobytes(), rgba.size, "RGBA")
            frames.append(surface)
            durations_ms.append(frame.info.get("duration", DEFAULT_FRAME_DURATION_MS))
        return SlotImage(frames=frames, durations_ms=durations_ms)


def load_slot_sounds(config: Config) -> dict[int, pygame.mixer.Sound]:
    sounds: dict[int, pygame.mixer.Sound] = {}
    for index, slot in enumerate(config.slots):
        try:
            sounds[index] = pygame.mixer.Sound(slot.sound)
        except pygame.error as exc:
            print(f"Warning: could not load sound for slot {index} ({slot.sound}): {exc}")
    return sounds


def load_fallback_sound(config: Config) -> pygame.mixer.Sound | None:
    return _load_optional_sound(config.fallback_sound)


def load_siren_sound(config: Config) -> pygame.mixer.Sound | None:
    return _load_optional_sound(config.siren_sound)


def _load_optional_sound(path: str | None) -> pygame.mixer.Sound | None:
    if not path:
        return None
    try:
        return pygame.mixer.Sound(path)
    except pygame.error as exc:
        print(f"Warning: could not load sound ({path}): {exc}")
        return None

