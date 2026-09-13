"""Fullscreen analog clock with a red countdown pie and slot markers."""

from __future__ import annotations

import argparse
import asyncio
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


def _is_web() -> bool:
    return sys.platform == "emscripten"


def _web_config_paths() -> list[Path]:
    paths = sorted(Path(".").glob("config_*.yaml"))
    default_path = Path("config.yaml")
    if default_path.exists():
        paths.insert(0, default_path)
    return paths


async def _select_web_config(screen: pygame.Surface) -> Path:
    config_paths = _web_config_paths()
    if not config_paths:
        raise FileNotFoundError("No config.yaml or config_*.yaml files found")

    width, height = screen.get_size()
    title_font = create_title_font(max(28, int(min(width, height) * 0.07)))
    option_font = pygame.font.SysFont("sans", max(22, int(min(width, height) * 0.04)))
    selected = 0
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_LEFT):
                    selected = (selected - 1) % len(config_paths)
                elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                    selected = (selected + 1) % len(config_paths)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return config_paths[selected]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index in range(len(config_paths)):
                    option_rect = pygame.Rect(0, 0, width * 0.8, option_font.get_height() + 24)
                    option_rect.center = (width / 2, height * 0.42 + index * (option_rect.height + 12))
                    if option_rect.collidepoint(event.pos):
                        return config_paths[index]

        screen.fill(BACKGROUND)
        heading = title_font.render("Choose a clock", True, (245, 245, 245))
        screen.blit(heading, heading.get_rect(center=(width / 2, height * 0.2)))
        for index, config_path in enumerate(config_paths):
            option_rect = pygame.Rect(0, 0, width * 0.8, option_font.get_height() + 24)
            option_rect.center = (width / 2, height * 0.42 + index * (option_rect.height + 12))
            color = (200, 30, 30) if index == selected else (60, 60, 60)
            pygame.draw.rect(screen, color, option_rect, border_radius=8)
            label = "Default" if config_path.name == "config.yaml" else config_path.stem.removeprefix("config_")
            text = option_font.render(label, True, (245, 245, 245))
            screen.blit(text, text.get_rect(center=option_rect.center))
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)


async def main() -> None:
    args = _parse_args()

    pygame.init()
    pygame.mixer.init()

    screen_flags = 0 if _is_web() else pygame.FULLSCREEN
    screen = pygame.display.set_mode((960, 720) if _is_web() else (0, 0), screen_flags)
    pygame.display.set_caption("Clockface")
    clock = pygame.time.Clock()

    config_path = await _select_web_config(screen) if _is_web() else args.config
    config = load_config(config_path)
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
        await asyncio.sleep(0)

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

