"""Deterministic color and type tools for Studio Lab. No Flask."""

from __future__ import annotations

import hashlib
import json
import math
from urllib.parse import quote_plus

INK = "#101418"

TYPE_RATIOS = {
    "minor-third": 1.2,
    "major-third": 1.25,
    "perfect-fourth": 1.333,
    "perfect-fifth": 1.5,
}

_HUE_OFFSETS = (0.0, 24.0, 48.0, 172.0, 208.0)
_SATS = (0.58, 0.52, 0.46, 0.50, 0.42)
_LIGHTS = (0.30, 0.42, 0.54, 0.66, 0.78)

__all__ = [
    "INK",
    "TYPE_RATIOS",
    "best_on_ink",
    "closest_pair",
    "contrast_ratio",
    "css_variables",
    "delta_e76",
    "hex_to_hsl",
    "json_tokens",
    "lab_query",
    "mix_hex",
    "palette_from_seed",
    "pairing_table",
    "passes_aa",
    "passes_aaa",
    "recommend_body",
    "scss_map",
    "shade",
    "tailwind_theme",
    "tint",
    "type_scale",
]

_XYZ_D65 = (0.95047, 1.0, 1.08883)
_LAB_DELTA = 6.0 / 29.0
_LAB_DELTA_CUBE = _LAB_DELTA**3


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


def mix_hex(a: str, b: str, t: float) -> str:
    """Linear mix of two sRGB hex colors in 0..1 (not linear-light).

    ``t`` is clamped to 0..1. Channels round like ``_hsl_to_hex``
    (``floor(x * 255 + 0.5)``), so black mixed with white at 0.5 is ``#808080``
    rather than truncated ``#7f7f7f``.
    """
    t = _clamp(float(t), 0.0, 1.0)
    red_a, green_a, blue_a = _hex_to_rgb(a)
    red_b, green_b, blue_b = _hex_to_rgb(b)

    def mix(left: int, right: int) -> int:
        mixed = (left / 255.0) * (1.0 - t) + (right / 255.0) * t
        return int(math.floor(mixed * 255.0 + 0.5))

    return f"#{mix(red_a, red_b):02x}{mix(green_a, green_b):02x}{mix(blue_a, blue_b):02x}"


def shade(hex_color: str, amount: float = 0.15) -> str:
    """Mix ``hex_color`` toward ``#000000`` by ``amount`` (clamped 0..1)."""
    return mix_hex(hex_color, "#000000", amount)


def tint(hex_color: str, amount: float = 0.15) -> str:
    """Mix ``hex_color`` toward ``#ffffff`` by ``amount`` (clamped 0..1)."""
    return mix_hex(hex_color, "#ffffff", amount)


def lab_query(seed: str, ratio: str = "major-third") -> str:
    """Return ``seed=...&ratio=...`` with ``urllib.parse.quote_plus`` encoding."""
    return f"seed={quote_plus(seed)}&ratio={quote_plus(ratio)}"


def _round_int(value: float) -> int:
    return int(math.floor(value + 0.5))


def hex_to_hsl(color: str) -> dict[str, int]:
    """Return integer HSL: hue 0..359, saturation and lightness 0..100.

    Channels are sRGB 0..1. Hue uses the standard six-sector formula, then
    ``floor(x + 0.5)`` like ``_hsl_to_hex``. Hue 360 wraps to 0.
    """
    red, green, blue = (channel / 255.0 for channel in _hex_to_rgb(color))
    max_c = max(red, green, blue)
    min_c = min(red, green, blue)
    light = (max_c + min_c) / 2.0
    if max_c == min_c:
        hue = 0.0
        sat = 0.0
    else:
        delta = max_c - min_c
        denom = 1.0 - abs(2.0 * light - 1.0)
        sat = delta / denom if denom else 0.0
        if max_c == red:
            hue = ((green - blue) / delta) % 6.0
        elif max_c == green:
            hue = (blue - red) / delta + 2.0
        else:
            hue = (red - green) / delta + 4.0
        hue *= 60.0
    if hue < 0:
        hue += 360.0
    return {
        "h": _round_int(hue) % 360,
        "s": _clamp(_round_int(sat * 100), 0, 100),
        "l": _clamp(_round_int(light * 100), 0, 100),
    }


def _srgb_to_xyz(color: str) -> tuple[float, float, float]:
    red, green, blue = _hex_to_rgb(color)
    linear_r = _linearize(red)
    linear_g = _linearize(green)
    linear_b = _linearize(blue)
    x = 0.4124564 * linear_r + 0.3575761 * linear_g + 0.1804375 * linear_b
    y = 0.2126729 * linear_r + 0.7151522 * linear_g + 0.0721750 * linear_b
    z = 0.0193339 * linear_r + 0.1191920 * linear_g + 0.9503041 * linear_b
    return x, y, z


def _lab_f(t: float) -> float:
    if t > _LAB_DELTA_CUBE:
        return t ** (1.0 / 3.0)
    return t / (3.0 * _LAB_DELTA * _LAB_DELTA) + 4.0 / 29.0


def _hex_to_lab(color: str) -> tuple[float, float, float]:
    x, y, z = _srgb_to_xyz(color)
    xn, yn, zn = _XYZ_D65
    fx = _lab_f(x / xn)
    fy = _lab_f(y / yn)
    fz = _lab_f(z / zn)
    return 116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)


def delta_e76(a: str, b: str) -> float:
    """CIE76 ΔE*ab between two sRGB hex colors (D65)."""
    l1, a1, b1 = _hex_to_lab(a)
    l2, a2, b2 = _hex_to_lab(b)
    return math.sqrt((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2)


def closest_pair(palette: list[str]) -> dict | None:
    """Return the two closest swatches by CIE76 ΔE.

    Indexes are ``i < j``. Ties keep the first pair in that scan order.
    None when the palette has fewer than two colors.
    """
    if len(palette) < 2:
        return None
    best_i = 0
    best_j = 1
    best_delta = delta_e76(palette[0], palette[1])
    for i in range(len(palette)):
        for j in range(i + 1, len(palette)):
            if i == 0 and j == 1:
                continue
            delta = delta_e76(palette[i], palette[j])
            if delta < best_delta:
                best_delta = delta
                best_i = i
                best_j = j
    return {
        "a": palette[best_i],
        "b": palette[best_j],
        "i": best_i,
        "j": best_j,
        "delta_e": best_delta,
    }


def json_tokens(palette: list[str]) -> str:
    """Compact JSON object with ``ink`` and numbered ``studio`` swatches."""
    studio = {str(index): color for index, color in enumerate(palette, start=1)}
    return json.dumps({"ink": INK, "studio": studio}, separators=(",", ":"))


def tailwind_theme(palette: list[str]) -> str:
    """One-line Tailwind ``theme.extend.colors.studio`` snippet."""
    pairs = [f"{index}: '{color}'" for index, color in enumerate(palette, start=1)]
    pairs.append(f"ink: '{INK}'")
    inner = ", ".join(pairs)
    return f"theme: {{ extend: {{ colors: {{ studio: {{ {inner} }} }} }} }}"


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


def passes_aaa(hex_a: str, hex_b: str, large: bool = False) -> bool:
    """Return True when the pair meets WCAG AAA (7:1, or 4.5:1 for large text)."""
    threshold = 4.5 if large else 7.0
    return contrast_ratio(hex_a, hex_b) >= threshold


def css_variables(palette: list[str]) -> str:
    """Return a :root block of --studio-N tokens plus --studio-ink."""
    tokens = [f"--studio-{index}: {color};" for index, color in enumerate(palette, start=1)]
    tokens.append(f"--studio-ink: {INK};")
    return ":root { " + " ".join(tokens) + " }"


def scss_map(palette: list[str]) -> str:
    """Return a $studio Sass map of numbered swatches plus ink."""
    tokens = [f'"{index}": {color}' for index, color in enumerate(palette, start=1)]
    tokens.append(f'"ink": {INK}')
    return "$studio: (" + ", ".join(tokens) + ");"


def best_on_ink(palette: list[str], ink: str = INK) -> dict:
    """Return the palette color with the highest contrast against ink.

    Ties keep the first swatch.
    """
    winner = palette[0]
    best_ratio = contrast_ratio(winner, ink)
    for color in palette[1:]:
        ratio = contrast_ratio(color, ink)
        if ratio > best_ratio:
            winner = color
            best_ratio = ratio
    return {
        "hex": winner,
        "ratio": best_ratio,
        "aa": passes_aa(winner, ink),
        "aaa": passes_aaa(winner, ink),
    }


def recommend_body(palette: list[str]) -> dict | None:
    """Return the first consecutive pairing_table pair that passes AA for body text."""
    consecutive = pairing_table(palette)[len(palette) :]
    for row in consecutive:
        if row["aa"]:
            return row
    return None


def pairing_table(palette: list[str], ink: str = INK) -> list[dict]:
    """Contrast rows for every swatch vs ink, then each consecutive pair."""

    def row(fg: str, bg: str) -> dict:
        ratio = contrast_ratio(fg, bg)
        return {
            "fg": fg,
            "bg": bg,
            "ratio": ratio,
            "aa": passes_aa(fg, bg),
            "aaa": passes_aaa(fg, bg),
        }

    rows = [row(color, ink) for color in palette]
    rows.extend(row(palette[index], palette[index + 1]) for index in range(len(palette) - 1))
    return rows


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
