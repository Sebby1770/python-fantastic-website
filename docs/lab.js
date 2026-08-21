/* Mirrors studio.py: SHA-256 seed, HSL palette, WCAG contrast, modular type scale. */

const INK = "#101418";
const HUE_OFFSETS = [0, 24, 48, 172, 208];
const SATS = [0.58, 0.52, 0.46, 0.5, 0.42];
const LIGHTS = [0.3, 0.42, 0.54, 0.66, 0.78];

function clamp(value, low, high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}

function hueToRgb(p, q, t) {
  if (t < 0) t += 1;
  if (t > 1) t -= 1;
  if (t < 1 / 6) return p + (q - p) * 6 * t;
  if (t < 1 / 2) return q;
  if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
  return p;
}

function hslToHex(h, s, l) {
  h = (((h % 360) + 360) % 360) / 360;
  s = clamp(s, 0, 1);
  l = clamp(l, 0, 1);
  const toChannel = (value) => Math.floor(value * 255 + 0.5).toString(16).padStart(2, "0");
  if (s === 0) {
    const channel = toChannel(l);
    return `#${channel}${channel}${channel}`;
  }
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  return `#${toChannel(hueToRgb(p, q, h + 1 / 3))}${toChannel(hueToRgb(p, q, h))}${toChannel(hueToRgb(p, q, h - 1 / 3))}`;
}

function paletteFromDigest(digest) {
  const baseHue = ((digest[0] << 8) | digest[1]) % 360;
  const colors = [];
  for (let index = 0; index < 5; index += 1) {
    const hue = (baseHue + HUE_OFFSETS[index] + (digest[2 + index] / 255) * 36 - 18) % 360;
    const sat = clamp(SATS[index] + (digest[8 + index] / 255) * 0.1 - 0.05, 0.28, 0.78);
    const light = clamp(LIGHTS[index] + (digest[14 + index] / 255) * 0.08 - 0.04, 0.18, 0.86);
    colors.push(hslToHex(hue, sat, light));
  }
  return colors;
}

function linearize(channel) {
  const srgb = channel / 255;
  return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
}

function hexToRgb(color) {
  let raw = String(color).trim().replace(/^#/, "");
  if (raw.length === 3) {
    raw = raw.split("").map((part) => part + part).join("");
  }
  if (raw.length !== 6) {
    throw new Error(`Invalid hex color: ${color}`);
  }
  return [parseInt(raw.slice(0, 2), 16), parseInt(raw.slice(2, 4), 16), parseInt(raw.slice(4, 6), 16)];
}

function relativeLuminance(color) {
  const [red, green, blue] = hexToRgb(color);
  return 0.2126 * linearize(red) + 0.7152 * linearize(green) + 0.0722 * linearize(blue);
}

function contrastRatio(hexA, hexB) {
  const first = relativeLuminance(hexA);
  const second = relativeLuminance(hexB);
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

function passesAa(hexA, hexB, large = false) {
  return contrastRatio(hexA, hexB) >= (large ? 3 : 4.5);
}

async function sha256Bytes(text) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return new Uint8Array(digest);
}

function setBadge(node, ok, passLabel, failLabel) {
  if (!node) return;
  node.textContent = ok ? passLabel : failLabel;
  node.className = ok ? "aa-pass" : "aa-fail";
}

function renderPalette(colors) {
  const cards = document.querySelectorAll("[data-swatch]");
  colors.forEach((hex, index) => {
    const card = cards[index];
    if (!card) return;
    const ratio = contrastRatio(hex, INK);
    const chip = card.querySelector("[data-swatch-chip]");
    const hexNode = card.querySelector("[data-swatch-hex]");
    const ratioNode = card.querySelector("[data-swatch-ratio]");
    if (chip) chip.style.background = hex;
    if (hexNode) hexNode.textContent = hex;
    if (ratioNode) ratioNode.textContent = ratio.toFixed(2);
    setBadge(card.querySelector("[data-swatch-aa]"), passesAa(hex, INK), "AA pass", "AA fail");
    setBadge(
      card.querySelector("[data-swatch-aa-large]"),
      passesAa(hex, INK, true),
      "AA large pass",
      "AA large fail",
    );
  });
}

async function compose(seed) {
  const digest = await sha256Bytes(seed);
  renderPalette(paletteFromDigest(digest));
}

function initLab() {
  const form = document.querySelector("[data-lab-form]");
  const input = document.querySelector("[data-lab-seed]");
  if (!form || !input || !window.crypto?.subtle) return;

  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get("seed");
  if (fromUrl && !input.value) {
    input.value = fromUrl;
  }

  const run = () => {
    const seed = input.value.trim() || "asteria";
    compose(seed);
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const seed = input.value.trim() || "asteria";
    input.value = seed;
    const url = new URL(window.location.href);
    url.searchParams.set("seed", seed);
    window.history.replaceState({}, "", url);
    compose(seed);
  });

  input.addEventListener("input", run);
  run();
}

initLab();
