"""Deterministic color and type tools for Studio Lab. No Flask."""

from __future__ import annotations

import hashlib
import math

INK = "#101418"

_HUE_OFFSETS = (0.0, 24.0, 48.0, 172.0, 208.0)
_SATS = (0.58, 0.52, 0.46, 0.50, 0.42)
_LIGHTS = (0.30, 0.42, 0.54, 0.66, 0.78)

__all__ = [
    "INK",
    "contrast_ratio",
    "palette_from_seed",
    "passes_aa",
    "type_scale",
]


def _clamp(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    raw = color.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(channel * 2 for channel in raw)
    if len(raw) != 6:
        raise ValueError(f"Invalid hex color: {color}")
    try:
        return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    except ValueError as exc:
        raise ValueError(f"Invalid hex color: {color}") from exc


def _hue_to_rgb(p: float, q: float, t: float) -> float:
    if t < 0:
        t += 1
    if t > 1:
        t -= 1
    if t < 1 / 6:
        return p + (q - p) * 6 * t
    if t < 1 / 2:
        return q
    if t < 2 / 3:
        return p + (q - p) * (2 / 3 - t) * 6
    return p


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    h = ((h % 360) + 360) % 360 / 360.0
    s = _clamp(s, 0.0, 1.0)
    l = _clamp(l, 0.0, 1.0)
    if s == 0:
        channel = int(math.floor(l * 255.0 + 0.5))
        return f"#{channel:02x}{channel:02x}{channel:02x}"
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = _hue_to_rgb(p, q, h + 1 / 3)
    g = _hue_to_rgb(p, q, h)
    b = _hue_to_rgb(p, q, h - 1 / 3)
    return "#{:02x}{:02x}{:02x}".format(
        int(math.floor(r * 255.0 + 0.5)),
        int(math.floor(g * 255.0 + 0.5)),
        int(math.floor(b * 255.0 + 0.5)),
    )


def _linearize(channel: int) -> float:
    srgb = channel / 255.0
    if srgb <= 0.04045:
        return srgb / 12.92
    return ((srgb + 0.055) / 1.055) ** 2.4


def _relative_luminance(color: str) -> float:
    red, green, blue = _hex_to_rgb(color)
    return 0.2126 * _linearize(red) + 0.7152 * _linearize(green) + 0.0722 * _linearize(blue)


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Return the WCAG 2 contrast ratio between two sRGB hex colors."""
    lighter = max(_relative_luminance(hex_a), _relative_luminance(hex_b))
    darker = min(_relative_luminance(hex_a), _relative_luminance(hex_b))
    return (lighter + 0.05) / (darker + 0.05)


def passes_aa(hex_a: str, hex_b: str, large: bool = False) -> bool:
    """Return True when the pair meets WCAG AA (4.5:1, or 3:1 for large text)."""
    threshold = 3.0 if large else 4.5
    return contrast_ratio(hex_a, hex_b) >= threshold


def type_scale(base_px: float = 16, ratio: float = 1.25, steps: int = 6) -> list[float]:
    """Return a modular type scale: base * ratio ** i, rounded to 2 decimal places."""
    if steps < 1:
        raise ValueError("steps must be at least 1")
    return [round(base_px * (ratio**i), 2) for i in range(steps)]


def palette_from_seed(seed: str) -> list[str]:
    """Return five #rrggbb colors derived from SHA-256(seed).

    Each swatch uses a fixed hue offset from the hashed base hue, with
    saturation and lightness pinned near a studio-friendly ramp. Values are
    hashed so the same seed always yields the same five colors.
    """
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    base_hue = (digest[0] << 8 | digest[1]) % 360
    colors: list[str] = []
    for index in range(5):
        hue = (base_hue + _HUE_OFFSETS[index] + digest[2 + index] / 255.0 * 36.0 - 18.0) % 360.0
        sat = _clamp(_SATS[index] + digest[8 + index] / 255.0 * 0.10 - 0.05, 0.28, 0.78)
        light = _clamp(_LIGHTS[index] + digest[14 + index] / 255.0 * 0.08 - 0.04, 0.18, 0.86)
        colors.append(_hsl_to_hex(hue, sat, light))
    return colors
