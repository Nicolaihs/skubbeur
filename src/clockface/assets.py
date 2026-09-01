"""Download/cache slot images and load slot sounds."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pygame
import requests

from clockface.config import Config

CACHE_DIR = Path(".cache/images")


def get_cached_image_path(url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(url).suffix or ".img"
    cache_path = CACHE_DIR / f"{hashlib.md5(url.encode()).hexdigest()}{suffix}"
    if not cache_path.exists():
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        cache_path.write_bytes(response.content)
    return cache_path


def load_slot_images(config: Config) -> dict[int, pygame.Surface]:
    images: dict[int, pygame.Surface] = {}
    for index, slot in enumerate(config.slots):
        try:
            path = get_cached_image_path(slot.image)
            images[index] = pygame.image.load(str(path)).convert_alpha()
        except (requests.RequestException, pygame.error) as exc:
            print(f"Warning: could not load image for slot {index} ({slot.image}): {exc}")
    return images


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

