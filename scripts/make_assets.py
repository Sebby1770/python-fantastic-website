from __future__ import annotations

import math
import random
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "img"


def lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def mix(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(lerp(a, b, t) for a, b in zip(c1, c2))


def chunk(name: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)


class Canvas:
    def __init__(self, width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]):
        self.width = width
        self.height = height
        self.rows = []
        for y in range(height):
            color = mix(top, bottom, y / max(1, height - 1))
            row = bytearray()
            for _ in range(width):
                row.extend(color)
            self.rows.append(row)

    def blend_pixel(self, x: int, y: int, color: tuple[int, int, int], alpha: float) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        offset = x * 3
        row = self.rows[y]
        for channel in range(3):
            row[offset + channel] = lerp(row[offset + channel], color[channel], alpha)

    def rect(self, x: int, y: int, width: int, height: int, color: tuple[int, int, int], alpha: float) -> None:
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + width)
        y1 = min(self.height, y + height)
        for yy in range(y0, y1):
            row = self.rows[yy]
            for xx in range(x0, x1):
                offset = xx * 3
                for channel in range(3):
                    row[offset + channel] = lerp(row[offset + channel], color[channel], alpha)

    def line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: tuple[int, int, int],
        alpha: float,
        width: int = 1,
    ) -> None:
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x = x0
        y = y0
        radius = max(0, width // 2)
        while True:
            for yy in range(y - radius, y + radius + 1):
                for xx in range(x - radius, x + radius + 1):
                    self.blend_pixel(xx, yy, color, alpha)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx: int, cy: int, radius: int, color: tuple[int, int, int], alpha: float, fill: bool = False) -> None:
        r2 = radius * radius
        inner = 0 if fill else (radius - 3) * (radius - 3)
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                d2 = (x - cx) * (x - cx) + (y - cy) * (y - cy)
                if inner <= d2 <= r2:
                    self.blend_pixel(x, y, color, alpha)

    def noise(self, seed: int, amount: int, color: tuple[int, int, int], alpha: float) -> None:
        rng = random.Random(seed)
        for _ in range(amount):
            self.blend_pixel(rng.randrange(self.width), rng.randrange(self.height), color, alpha * rng.random())

    def save(self, path: Path) -> None:
        raw = b"".join(b"\x00" + bytes(row) for row in self.rows)
        payload = chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0))
        payload += chunk(b"IDAT", zlib.compress(raw, 9))
        payload += chunk(b"IEND", b"")
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + payload)


def hero() -> None:
    canvas = Canvas(1600, 1000, (18, 26, 31), (31, 66, 73))
    canvas.rect(780, 110, 520, 560, (255, 255, 255), 0.08)
    canvas.rect(830, 160, 430, 470, (14, 20, 25), 0.34)
    canvas.rect(890, 220, 300, 80, (216, 79, 66), 0.74)
    canvas.rect(930, 340, 220, 56, (197, 138, 34), 0.68)
    canvas.rect(880, 430, 360, 72, (54, 103, 177), 0.7)
    canvas.rect(980, 545, 180, 54, (23, 124, 117), 0.82)

    for i in range(18):
        y = 720 + i * 18
        canvas.line(0, y, 1600, y - 260, (255, 255, 255), 0.045, 2)
    for i in range(14):
        x = 180 + i * 110
        canvas.line(x, 1000, x + 410, 580, (255, 255, 255), 0.035, 2)

    for radius in range(150, 390, 48):
        canvas.circle(430, 380, radius, (246, 248, 243), 0.08)
    canvas.line(270, 560, 530, 280, (248, 192, 92), 0.55, 5)
    canvas.line(530, 280, 710, 430, (217, 79, 66), 0.5, 5)
    canvas.line(710, 430, 900, 250, (23, 124, 117), 0.52, 5)
    canvas.noise(42, 16000, (255, 255, 255), 0.08)
    canvas.save(OUT / "hero.png")


def work_image(path: str, seed: int, accent: tuple[int, int, int]) -> None:
    rng = random.Random(seed)
    canvas = Canvas(900, 675, (239, 243, 235), (215, 226, 224))
    canvas.rect(70, 70, 760, 535, (255, 255, 255), 0.72)
    canvas.rect(110, 115, 680, 62, (16, 20, 24), 0.92)

    for i in range(7):
        color = accent if i % 2 == 0 else (54, 103, 177)
        canvas.rect(125 + i * 92, 230 + rng.randrange(-18, 18), 52, 260 - i * 20, color, 0.76)
    for i in range(5):
        canvas.line(125, 500 - i * 44, 775, 330 - i * 20, (16, 20, 24), 0.12, 2)
    for i in range(8):
        canvas.circle(220 + i * 72, 220 + rng.randrange(-28, 28), 18, accent, 0.45, fill=True)
    canvas.noise(seed + 100, 5200, (16, 20, 24), 0.045)
    canvas.save(OUT / path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hero()
    work_image("work-northline.png", 10, (217, 79, 66))
    work_image("work-meridian.png", 18, (23, 124, 117))
    work_image("work-cobalt.png", 26, (197, 138, 34))


if __name__ == "__main__":
    main()
