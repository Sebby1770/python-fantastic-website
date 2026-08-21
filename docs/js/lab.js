/* Mirrors studio.py: SHA-256 seed, HSL palette, WCAG contrast, mix/shade/tint, CIE76, pairings, CSS/SCSS/JSON/Tailwind/SVG tokens, type scale. */

const XYZ_D65 = [0.95047, 1, 1.08883];
const LAB_DELTA = 6 / 29;
const LAB_DELTA_CUBE = LAB_DELTA ** 3;

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

function mixHex(a, b, t) {
  const amount = clamp(Number(t), 0, 1);
  const [redA, greenA, blueA] = hexToRgb(a);
  const [redB, greenB, blueB] = hexToRgb(b);
  const mix = (left, right) => {
    const value = (left / 255) * (1 - amount) + (right / 255) * amount;
    return Math.floor(value * 255 + 0.5);
  };
  const hex = (channel) => channel.toString(16).padStart(2, "0");
  return `#${hex(mix(redA, redB))}${hex(mix(greenA, greenB))}${hex(mix(blueA, blueB))}`;
}

function shade(hexColor, amount = 0.15) {
  return mixHex(hexColor, "#000000", amount);
}

function tint(hexColor, amount = 0.15) {
  return mixHex(hexColor, "#ffffff", amount);
}

function quotePlus(value) {
  return encodeURIComponent(String(value))
    .replace(/%20/g, "+")
    .replace(/[!'()*~]/g, (char) => `%${char.charCodeAt(0).toString(16).toUpperCase()}`)
    .replace(/%2F/gi, "/");
}

function labQuery(seed, ratio = "major-third") {
  return `seed=${quotePlus(seed)}&ratio=${quotePlus(ratio)}`;
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

function passesUi(hexA, hexB) {
  return contrastRatio(hexA, hexB) >= 3;
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

function roundInt(value) {
  return Math.floor(value + 0.5);
}

function hexToHsl(color) {
  const [red, green, blue] = hexToRgb(color).map((channel) => channel / 255);
  const maxC = Math.max(red, green, blue);
  const minC = Math.min(red, green, blue);
  const light = (maxC + minC) / 2;
  let hue = 0;
  let sat = 0;
  if (maxC !== minC) {
    const delta = maxC - minC;
    const denom = 1 - Math.abs(2 * light - 1);
    sat = denom ? delta / denom : 0;
    if (maxC === red) {
      hue = ((green - blue) / delta) % 6;
      if (hue < 0) hue += 6;
    } else if (maxC === green) {
      hue = (blue - red) / delta + 2;
    } else {
      hue = (red - green) / delta + 4;
    }
    hue *= 60;
  }
  if (hue < 0) hue += 360;
  return {
    h: roundInt(hue) % 360,
    s: clamp(roundInt(sat * 100), 0, 100),
    l: clamp(roundInt(light * 100), 0, 100),
  };
}

function labF(t) {
  if (t > LAB_DELTA_CUBE) return t ** (1 / 3);
  return t / (3 * LAB_DELTA * LAB_DELTA) + 4 / 29;
}

function hexToLab(color) {
  const [red, green, blue] = hexToRgb(color);
  const r = linearize(red);
  const g = linearize(green);
  const b = linearize(blue);
  const x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b;
  const y = 0.2126729 * r + 0.7151522 * g + 0.072175 * b;
  const z = 0.0193339 * r + 0.119192 * g + 0.9503041 * b;
  const fx = labF(x / XYZ_D65[0]);
  const fy = labF(y / XYZ_D65[1]);
  const fz = labF(z / XYZ_D65[2]);
  return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
}

function deltaE76(a, b) {
  const [l1, a1, b1] = hexToLab(a);
  const [l2, a2, b2] = hexToLab(b);
  return Math.sqrt((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2);
}

function closestPair(palette) {
  if (palette.length < 2) return null;
  let bestI = 0;
  let bestJ = 1;
  let bestDelta = deltaE76(palette[0], palette[1]);
  for (let i = 0; i < palette.length; i += 1) {
    for (let j = i + 1; j < palette.length; j += 1) {
      if (i === 0 && j === 1) continue;
      const delta = deltaE76(palette[i], palette[j]);
      if (delta < bestDelta) {
        bestDelta = delta;
        bestI = i;
        bestJ = j;
      }
    }
  }
  return { a: palette[bestI], b: palette[bestJ], i: bestI, j: bestJ, delta_e: bestDelta };
}

function farthestPair(palette) {
  if (palette.length < 2) return null;
  let bestI = 0;
  let bestJ = 1;
  let bestDelta = deltaE76(palette[0], palette[1]);
  for (let i = 0; i < palette.length; i += 1) {
    for (let j = i + 1; j < palette.length; j += 1) {
      if (i === 0 && j === 1) continue;
      const delta = deltaE76(palette[i], palette[j]);
      if (delta > bestDelta) {
        bestDelta = delta;
        bestI = i;
        bestJ = j;
      }
    }
  }
  return { a: palette[bestI], b: palette[bestJ], i: bestI, j: bestJ, delta_e: bestDelta };
}

function sortByLuminance(palette) {
  return palette
    .map((color, index) => ({ color, index, lum: relativeLuminance(color) }))
    .sort((a, b) => b.lum - a.lum || a.index - b.index)
    .map((row) => row.color);
}

function svgNum(value) {
  const rounded = Math.round(value * 10000) / 10000;
  if (Math.abs(rounded - Math.round(rounded)) < 1e-9) return String(Math.round(rounded));
  return String(rounded);
}

function svgStrip(palette, width = 300, height = 48) {
  if (width < 1 || height < 1) {
    throw new Error("width and height must be at least 1");
  }
  if (!palette.length) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"></svg>`;
  }
  const sliceW = width / palette.length;
  const rects = palette.map((color, index) => {
    return `<rect x="${svgNum(index * sliceW)}" y="0" width="${svgNum(sliceW)}" height="${height}" fill="${color}"/>`;
  });
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${rects.join("")}</svg>`;
}

function jsonTokens(palette) {
  const studio = {};
  palette.forEach((color, index) => {
    studio[String(index + 1)] = color;
  });
  return JSON.stringify({ ink: INK, studio });
}

function tailwindTheme(palette) {
  const pairs = palette.map((color, index) => `${index + 1}: '${color}'`);
  pairs.push(`ink: '${INK}'`);
  return `theme: { extend: { colors: { studio: { ${pairs.join(", ")} } } } }`;
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
    const hslNode = card.querySelector("[data-swatch-hsl]");
    if (hslNode) {
      const hsl = hexToHsl(hex);
      hslNode.textContent = `${hsl.h}° ${hsl.s}% ${hsl.l}%`;
    }
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
    setBadge(card.querySelector("[data-swatch-ui]"), passesUi(hex, INK), "UI pass", "UI fail");
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

function renderJsonTokens(tokens) {
  const node = document.querySelector("[data-json-tokens]");
  if (node) node.textContent = tokens;
}

function renderTailwind(theme) {
  const node = document.querySelector("[data-tailwind-theme]");
  if (node) node.textContent = theme;
}

function renderPairCallout(root, pair, prefix) {
  if (!root) return;
  if (!pair) {
    root.hidden = true;
    return;
  }
  root.hidden = false;
  const aChip = root.querySelector(`[data-${prefix}-a-chip]`);
  const bChip = root.querySelector(`[data-${prefix}-b-chip]`);
  const aNode = root.querySelector(`[data-${prefix}-a]`);
  const bNode = root.querySelector(`[data-${prefix}-b]`);
  const deltaNode = root.querySelector(`[data-${prefix}-delta]`);
  const iNode = root.querySelector(`[data-${prefix}-i]`);
  const jNode = root.querySelector(`[data-${prefix}-j]`);
  if (aChip) aChip.style.background = pair.a;
  if (bChip) bChip.style.background = pair.b;
  if (aNode) aNode.textContent = pair.a;
  if (bNode) bNode.textContent = pair.b;
  if (deltaNode) deltaNode.textContent = pair.delta_e.toFixed(1);
  if (iNode) iNode.textContent = String(pair.i);
  if (jNode) jNode.textContent = String(pair.j);
}

function renderClosestPair(pair) {
  renderPairCallout(document.querySelector("[data-closest-pair]"), pair, "closest");
}

function renderFarthestPair(pair) {
  renderPairCallout(document.querySelector("[data-farthest-pair]"), pair, "farthest");
}

function renderLuminance(colors) {
  const row = document.querySelector("[data-luminance-row]");
  if (!row) return;
  row.innerHTML = colors
    .map(
      (color) =>
        `<div class="luminance-chip"><div class="lab-callout-swatch" style="background: ${color}"></div><p>${color}</p></div>`,
    )
    .join("");
}

function renderSvg(svg) {
  const preview = document.querySelector("[data-svg-preview]");
  const source = document.querySelector("[data-svg-strip]");
  if (preview) preview.innerHTML = svg;
  if (source) source.textContent = svg;
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

function swatchIndex(node, fallback) {
  const value = Number.parseInt(node ? node.value : String(fallback), 10);
  if (!Number.isFinite(value)) return fallback;
  return clamp(value, 0, 4);
}

function renderMixOptions(colors) {
  const selects = [document.querySelector("[data-mix-a]"), document.querySelector("[data-mix-b]")];
  selects.forEach((select) => {
    if (!select) return;
    const current = select.value;
    select.innerHTML = colors
      .map((hex, index) => `<option value="${index}">${index} · ${hex}</option>`)
      .join("");
    select.value = current;
  });
}

function renderMix(colors) {
  const root = document.querySelector("[data-mix]");
  if (!root || !colors.length) return;
  const a = swatchIndex(root.querySelector("[data-mix-a]"), 0);
  const b = swatchIndex(root.querySelector("[data-mix-b]"), 1);
  const tNode = root.querySelector("[data-mix-t]");
  const t = clamp(Number.parseFloat(tNode ? tNode.value : "0.5") || 0, 0, 1);
  const hex = mixHex(colors[a], colors[b], t);
  const ratio = contrastRatio(hex, INK);
  const chip = root.querySelector("[data-mix-chip]");
  const hexNode = root.querySelector("[data-mix-hex]");
  const ratioNode = root.querySelector("[data-mix-ratio]");
  const tLabel = root.querySelector("[data-mix-t-label]");
  if (chip) chip.style.background = hex;
  if (hexNode) hexNode.textContent = hex;
  if (ratioNode) ratioNode.textContent = ratio.toFixed(2);
  if (tLabel) tLabel.textContent = t.toFixed(2);
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
  renderJsonTokens(jsonTokens(colors));
  renderTailwind(tailwindTheme(colors));
  renderSvg(svgStrip(colors));
  renderClosestPair(closestPair(colors));
  renderFarthestPair(farthestPair(colors));
  renderLuminance(sortByLuminance(colors));
  renderMixOptions(colors);
  renderMix(colors);
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
  bindCopyButton(document.querySelector("[data-copy-json]"), document.querySelector("[data-json-tokens]"));
  bindCopyButton(document.querySelector("[data-copy-tailwind]"), document.querySelector("[data-tailwind-theme]"));
  bindCopyButton(document.querySelector("[data-copy-svg]"), document.querySelector("[data-svg-strip]"));
}

function initCopyLabLink() {
  const button = document.querySelector("[data-copy-lab-link]");
  const input = document.querySelector("[data-lab-seed]");
  const ratioSelect = document.querySelector("[data-lab-ratio]");
  if (!button) return;
  button.addEventListener("click", async () => {
    const seed = (input?.value || "").trim() || "asteria";
    const ratioName = resolveRatio(ratioSelect ? ratioSelect.value : "major-third");
    const text = `${window.location.origin}${window.location.pathname}?${labQuery(seed, ratioName)}`;
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.textContent = "Copy lab link";
      }, 1600);
    } catch {
      button.textContent = "Copy failed";
      window.setTimeout(() => {
        button.textContent = "Copy lab link";
      }, 1600);
    }
  });
}

function colorsFromDom() {
  return Array.from(document.querySelectorAll("[data-swatch-hex]"))
    .map((node) => (node.textContent || "").trim())
    .filter(Boolean);
}

function initMix() {
  const root = document.querySelector("[data-mix]");
  if (!root) return;
  const update = () => {
    const colors = colorsFromDom();
    if (colors.length) renderMix(colors);
  };
  root.addEventListener("input", update);
  root.addEventListener("change", update);
}

function initLab() {
  initCopyButtons();
  initCopyLabLink();
  initMix();

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
