/* Mirrors studio.py: SHA-256 seed, HSL palette, WCAG contrast, pairings, CSS/SCSS tokens, type scale. */

const INK = "#101418";
const HUE_OFFSETS = [0, 24, 48, 172, 208];
const SATS = [0.58, 0.52, 0.46, 0.5, 0.42];
const LIGHTS = [0.3, 0.42, 0.54, 0.66, 0.78];
const TYPE_RATIOS = {
  "minor-third": 1.2,
  "major-third": 1.25,
  "perfect-fourth": 1.333,
  "perfect-fifth": 1.5,
};

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

function passesAaa(hexA, hexB, large = false) {
  return contrastRatio(hexA, hexB) >= (large ? 4.5 : 7);
}

function cssVariables(palette) {
  const tokens = palette.map((color, index) => `--studio-${index + 1}: ${color};`);
  tokens.push(`--studio-ink: ${INK};`);
  return `:root { ${tokens.join(" ")} }`;
}

function scssMap(palette) {
  const tokens = palette.map((color, index) => `"${index + 1}": ${color}`);
  tokens.push(`"ink": ${INK}`);
  return `$studio: (${tokens.join(", ")});`;
}

function bestOnInk(palette, ink = INK) {
  let hex = palette[0];
  let ratio = contrastRatio(hex, ink);
  for (let index = 1; index < palette.length; index += 1) {
    const next = contrastRatio(palette[index], ink);
    if (next > ratio) {
      hex = palette[index];
      ratio = next;
    }
  }
  return { hex, ratio, aa: passesAa(hex, ink), aaa: passesAaa(hex, ink) };
}

function recommendBody(palette) {
  const consecutive = pairingTable(palette).slice(palette.length);
  return consecutive.find((row) => row.aa) || null;
}

function pairingTable(palette, ink = INK) {
  const row = (fg, bg) => {
    const ratio = contrastRatio(fg, bg);
    return { fg, bg, ratio, aa: passesAa(fg, bg), aaa: passesAaa(fg, bg) };
  };
  const rows = palette.map((color) => row(color, ink));
  for (let index = 0; index < palette.length - 1; index += 1) {
    rows.push(row(palette[index], palette[index + 1]));
  }
  return rows;
}

function typeScale(basePx = 16, ratio = 1.25, steps = 6) {
  if (steps < 1) {
    throw new Error("steps must be at least 1");
  }
  const sizes = [];
  for (let index = 0; index < steps; index += 1) {
    sizes.push(Math.round(basePx * ratio ** index * 100) / 100);
  }
  return sizes;
}

function ratioLabel(name) {
  const text = name.replace(/-/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function formatPx(size) {
  return size === Math.floor(size) ? String(Math.floor(size)) : String(size);
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
    setBadge(card.querySelector("[data-swatch-aaa]"), passesAaa(hex, INK), "AAA pass", "AAA fail");
    setBadge(
      card.querySelector("[data-swatch-aa-large]"),
      passesAa(hex, INK, true),
      "AA large pass",
      "AA large fail",
    );
    setBadge(
      card.querySelector("[data-swatch-aaa-large]"),
      passesAaa(hex, INK, true),
      "AAA large pass",
      "AAA large fail",
    );
  });
}

function renderPairing(rows) {
  const body = document.querySelector("[data-pairing-body]");
  if (!body) return;
  body.innerHTML = rows
    .map((pair) => {
      const aaClass = pair.aa ? "aa-pass" : "aa-fail";
      const aaaClass = pair.aaa ? "aa-pass" : "aa-fail";
      return `<tr>
        <td><span class="pair-chip" style="background: ${pair.fg}"></span>${pair.fg}</td>
        <td><span class="pair-chip" style="background: ${pair.bg}"></span>${pair.bg}</td>
        <td>${pair.ratio.toFixed(2)}:1</td>
        <td><span class="${aaClass}">${pair.aa ? "Pass" : "Fail"}</span></td>
        <td><span class="${aaaClass}">${pair.aaa ? "Pass" : "Fail"}</span></td>
      </tr>`;
    })
    .join("");
}

function renderCss(css) {
  const node = document.querySelector("[data-css-variables]");
  if (node) node.textContent = css;
}

function renderScss(scss) {
  const node = document.querySelector("[data-scss-map]");
  if (node) node.textContent = scss;
}

function renderBestOnInk(best) {
  const root = document.querySelector("[data-best-on-ink]");
  if (!root || !best) return;
  const chip = root.querySelector("[data-best-chip]");
  const hexNode = root.querySelector("[data-best-hex]");
  const ratioNode = root.querySelector("[data-best-ratio]");
  if (chip) chip.style.background = best.hex;
  if (hexNode) hexNode.textContent = best.hex;
  if (ratioNode) ratioNode.textContent = best.ratio.toFixed(2);
  setBadge(root.querySelector("[data-best-aa]"), best.aa, "AA pass", "AA fail");
  setBadge(root.querySelector("[data-best-aaa]"), best.aaa, "AAA pass", "AAA fail");
}

function renderBodyPair(pair) {
  const root = document.querySelector("[data-body-pair]");
  if (!root) return;
  if (!pair) {
    root.hidden = true;
    return;
  }
  root.hidden = false;
  const preview = root.querySelector("[data-body-preview]");
  const fgNode = root.querySelector("[data-body-fg]");
  const bgNode = root.querySelector("[data-body-bg]");
  const ratioNode = root.querySelector("[data-body-ratio]");
  if (preview) {
    preview.style.color = pair.fg;
    preview.style.background = pair.bg;
  }
  if (fgNode) fgNode.textContent = pair.fg;
  if (bgNode) bgNode.textContent = pair.bg;
  if (ratioNode) ratioNode.textContent = pair.ratio.toFixed(2);
  setBadge(root.querySelector("[data-body-aa]"), pair.aa, "AA pass", "AA fail");
  setBadge(root.querySelector("[data-body-aaa]"), pair.aaa, "AAA pass", "AAA fail");
}

function renderTypeScale(sizes, name) {
  const heading = document.querySelector("[data-type-heading]");
  if (heading) heading.textContent = `${ratioLabel(name)} from 16px.`;
  const root = document.querySelector("[data-type-scale]");
  if (!root) return;
  root.innerHTML = sizes
    .map(
      (size) =>
        `<div class="type-row"><span>${formatPx(size)}px</span><p style="font-size: ${size}px">Asteria Studio</p></div>`,
    )
    .join("");
}

function resolveRatio(name) {
  return TYPE_RATIOS[name] ? name : "major-third";
}

async function compose(seed, ratioName) {
  const digest = await sha256Bytes(seed);
  const colors = paletteFromDigest(digest);
  const ratioKey = resolveRatio(ratioName);
  renderPalette(colors);
  renderPairing(pairingTable(colors));
  renderBestOnInk(bestOnInk(colors));
  renderBodyPair(recommendBody(colors));
  renderCss(cssVariables(colors));
  renderScss(scssMap(colors));
  renderTypeScale(typeScale(16, TYPE_RATIOS[ratioKey], 6), ratioKey);
}

function bindCopyButton(button, source) {
  if (!button || !source) return;
  button.addEventListener("click", async () => {
    const text = source.textContent || "";
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.textContent = "Copy";
      }, 1600);
    } catch {
      button.textContent = "Copy failed";
      window.setTimeout(() => {
        button.textContent = "Copy";
      }, 1600);
    }
  });
}

function initCopyButtons() {
  bindCopyButton(document.querySelector("[data-copy-css]"), document.querySelector("[data-css-variables]"));
  bindCopyButton(document.querySelector("[data-copy-scss]"), document.querySelector("[data-scss-map]"));
}

function initLab() {
  initCopyButtons();

  const form = document.querySelector("[data-lab-form]");
  const input = document.querySelector("[data-lab-seed]");
  const ratioSelect = document.querySelector("[data-lab-ratio]");
  if (!form || !input || !window.crypto?.subtle) return;

  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get("seed");
  if (fromUrl && !input.value) {
    input.value = fromUrl;
  }
  const ratioFromUrl = params.get("ratio");
  if (ratioSelect && ratioFromUrl && TYPE_RATIOS[ratioFromUrl]) {
    ratioSelect.value = ratioFromUrl;
  }

  const currentRatio = () => resolveRatio(ratioSelect ? ratioSelect.value : "major-third");

  const run = () => {
    const seed = input.value.trim() || "asteria";
    compose(seed, currentRatio());
  };

  const syncUrl = (seed, ratioName) => {
    const url = new URL(window.location.href);
    url.searchParams.set("seed", seed);
    url.searchParams.set("ratio", ratioName);
    window.history.replaceState({}, "", url);
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const seed = input.value.trim() || "asteria";
    input.value = seed;
    const ratioName = currentRatio();
    if (ratioSelect) ratioSelect.value = ratioName;
    syncUrl(seed, ratioName);
    compose(seed, ratioName);
  });

  input.addEventListener("input", run);
  if (ratioSelect) {
    ratioSelect.addEventListener("change", () => {
      const seed = input.value.trim() || "asteria";
      const ratioName = currentRatio();
      syncUrl(seed, ratioName);
      compose(seed, ratioName);
    });
  }
  run();
}

initLab();
