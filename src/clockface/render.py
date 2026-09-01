"""All pygame drawing routines for the clock face."""

from __future__ import annotations

from datetime import datetime

import pygame

from clockface.config import Config
from clockface.geometry import hand_angle_degrees, point_on_circle, slot_midpoint_angle

BACKGROUND = (20, 20, 20)
FACE_COLOR = (235, 235, 235)
RED = (200, 30, 30)
HOUR_HAND_COLOR = (20, 20, 20)
MINUTE_HAND_COLOR = (20, 20, 20)
SECOND_HAND_COLOR = (170, 20, 20)
TICK_COLOR = (60, 60, 60)

SLOT_MARKER_MARGIN = 40
SLOT_MARKER_SIZE = 80

ALARM_FLASH_COLORS = [(255, 196, 0), (255, 90, 90)]
ALARM_FLASH_PERIOD_MS = 600


def draw_face(
    surface: pygame.Surface,
    center: tuple[float, float],
    radius: float,
    red_fraction: float | None,
    end_angle: float,
    blink_visible: bool = True,
) -> None:
    pygame.draw.circle(surface, FACE_COLOR, center, radius)
    if red_fraction and blink_visible:
        sweep_degrees = red_fraction * 360
        start_angle = end_angle - sweep_degrees
        points = [center]
        steps = max(2, int(sweep_degrees // 2))
        for i in range(steps + 1):
            angle = start_angle + sweep_degrees * i / steps
            points.append(point_on_circle(center, radius, angle))
        pygame.draw.polygon(surface, RED, points)


def draw_alarm_flash(surface: pygame.Surface, ticks_ms: int) -> None:
    """Fill the whole screen with an alternating, kid-friendly flash color."""
    color = ALARM_FLASH_COLORS[(ticks_ms // ALARM_FLASH_PERIOD_MS) % len(ALARM_FLASH_COLORS)]
    surface.fill(color)


def draw_ticks_and_numbers(surface: pygame.Surface, center: tuple[float, float], radius: float) -> None:
    for hour in range(12):
        angle = hour * 30
        inner = point_on_circle(center, radius - 15, angle)
        outer = point_on_circle(center, radius, angle)
        pygame.draw.line(surface, TICK_COLOR, inner, outer, 3)


def draw_hands(surface: pygame.Surface, center: tuple[float, float], radius: float, now: datetime) -> None:
    hour_angle = hand_angle_degrees(now.hour, now.minute, now.second, "hour")
    minute_angle = hand_angle_degrees(now.hour, now.minute, now.second, "minute")
    second_angle = hand_angle_degrees(now.hour, now.minute, now.second, "second")

    pygame.draw.line(surface, HOUR_HAND_COLOR, center, point_on_circle(center, radius * 0.5, hour_angle), 6)
    pygame.draw.line(surface, MINUTE_HAND_COLOR, center, point_on_circle(center, radius * 0.75, minute_angle), 4)
    pygame.draw.line(surface, SECOND_HAND_COLOR, center, point_on_circle(center, radius * 0.85, second_angle), 2)
    pygame.draw.circle(surface, HOUR_HAND_COLOR, center, 8)


def draw_slot_markers(
    surface: pygame.Surface,
    center: tuple[float, float],
    radius: float,
    config: Config,
    images: dict[int, pygame.Surface],
    in_countdown: bool,
) -> None:
    if not in_countdown:
        return
    for index, slot in enumerate(config.slots):
        image = images.get(index)
        if image is None:
            continue
        angle = slot_midpoint_angle(slot)
        marker_center = point_on_circle(center, radius + SLOT_MARKER_MARGIN + SLOT_MARKER_SIZE / 2, angle)
        scaled = pygame.transform.smoothscale(image, (SLOT_MARKER_SIZE, SLOT_MARKER_SIZE))
        rect = scaled.get_rect(center=marker_center)
        surface.blit(scaled, rect)
