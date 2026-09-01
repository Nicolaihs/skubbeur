"""Fullscreen analog clock with a red countdown pie and slot markers."""

from __future__ import annotations

import argparse
import random
from datetime import datetime

import pygame

from clockface.assets import load_fallback_sound, load_siren_sound, load_slot_images, load_slot_sounds
from clockface.config import Config, load_config
from clockface.geometry import countdown_fraction, hand_angle_degrees, is_final_blink_phase, seconds_since_end
from clockface.render import (
    BACKGROUND,
    draw_alarm_flash,
    draw_face,
    draw_hands,
    draw_slot_markers,
    draw_ticks_and_numbers,
)

DEFAULT_CONFIG_PATH = "config.yaml"
FPS = 30
BLINK_PERIOD_MS = 400
SIREN_MIN_DELAY_SECONDS = 5
SIREN_MAX_DELAY_SECONDS = 20


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fullscreen countdown clockface")
    parser.add_argument(
        "config",
        nargs="?",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to the YAML config file (default: {DEFAULT_CONFIG_PATH})",
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
    end_angle = hand_angle_degrees(0, config.end_time.minute, 0, "minute")

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
        red_fraction = countdown_fraction(now, config.end_time)
        elapsed_since_end = seconds_since_end(now, config.end_time)

        blink_visible = True
        if is_final_blink_phase(now, config.end_time):
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

        draw_face(screen, center, radius, red_fraction, end_angle, blink_visible)
        draw_ticks_and_numbers(screen, center, radius)
        draw_slot_markers(screen, center, radius, config, images, red_fraction is not None)
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

