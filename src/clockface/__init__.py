"""Fullscreen analog clock with a red countdown pie and slot markers."""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime
from pathlib import Path

import pygame

from clockface.assets import load_fallback_sound, load_siren_sound, load_slot_images, load_slot_sounds
from clockface.config import Config, load_config
from clockface.geometry import countdown_fraction, hand_angle_degrees, is_final_blink_phase, seconds_since_end
from clockface.render import (
    BACKGROUND,
    SLOT_MARKER_MARGIN,
    create_title_font,
    draw_alarm_flash,
    draw_face,
    draw_hands,
    draw_slot_markers,
    draw_ticks_and_numbers,
    draw_title,
)

FPS = 30
BLINK_PERIOD_MS = 400
SIREN_MIN_DELAY_SECONDS = 5
SIREN_MAX_DELAY_SECONDS = 20


def _bundled_resource_path(relative_path: str) -> Path:
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir is None:
        return Path(relative_path)
    return Path(bundle_dir) / relative_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fullscreen countdown clockface")
    parser.add_argument(
        "config",
        nargs="?",
        default=_bundled_resource_path("config.yaml"),
        help="Path to the YAML config file (default: the bundled config.yaml)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Clockface")
    clock = pygame.time.Clock()

    config = load_config(args.config)
    images = load_slot_images(config)
    sounds = load_slot_sounds(config)
    fallback_sound = load_fallback_sound(config)
    siren_sound = load_siren_sound(config)

    width, height = screen.get_size()
    center = (width / 2, height / 2)
    radius = min(width, height) * 0.3
    # Minute-hand scale (full lap per hour) matches the fraction*360 sweep below.
    end_angle = hand_angle_degrees(0, config.end_time.minute, config.end_time.second, "minute")

    title_font = create_title_font(max(28, int(min(width, height) * 0.06))) if config.title else None
    title_y = max(30.0, (center[1] - radius - SLOT_MARKER_MARGIN) / 2)

    next_siren_at_elapsed = 0.0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    _play_active_slot_sound(config, sounds, fallback_sound)

        now = datetime.now()
        red_fraction = countdown_fraction(now, config.end_time, config.total_time)
        elapsed_since_end = seconds_since_end(now, config.end_time)

        blink_visible = True
        if is_final_blink_phase(now, config.end_time, config.total_time):
            blink_visible = (pygame.time.get_ticks() // BLINK_PERIOD_MS) % 2 == 0

        if elapsed_since_end is not None:
            if siren_sound is not None and elapsed_since_end >= next_siren_at_elapsed:
                siren_sound.play()
                next_siren_at_elapsed = elapsed_since_end + random.uniform(
                    SIREN_MIN_DELAY_SECONDS, SIREN_MAX_DELAY_SECONDS
                )
            draw_alarm_flash(screen, pygame.time.get_ticks())
        else:
            next_siren_at_elapsed = 0.0
            screen.fill(BACKGROUND)

        if config.title and title_font is not None:
            draw_title(screen, config.title, title_font, center[0], title_y, max_width=width * 0.9)

        draw_face(screen, center, radius, red_fraction, end_angle, blink_visible)
        draw_ticks_and_numbers(screen, center, radius)
        draw_slot_markers(screen, center, radius, config, images, red_fraction is not None, pygame.time.get_ticks())
        draw_hands(screen, center, radius, now)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


def _play_active_slot_sound(
    config: Config,
    sounds: dict[int, pygame.mixer.Sound],
    fallback_sound: pygame.mixer.Sound | None,
) -> None:
    now_time = datetime.now().time()
    for index, slot in enumerate(config.slots):
        if slot.contains(now_time):
            sound = sounds.get(index)
            if sound is not None:
                sound.play()
            return
    if fallback_sound is not None:
        fallback_sound.play()

