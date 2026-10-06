// Render Instagram profile picture variants. Usage: node render_avatar.mjs <variant> out.jpg
import { createRequire } from 'node:module';
const require = createRequire('/opt/node22/lib/node_modules/');
const { chromium } = require('playwright');

const BG = '#0B3D2E', BRASS = '#C9A84C', CREAM = '#F5F3E8';
const S = 1080;

// Dimple-Raster, optional mit ausgespartem Band fuer Text
const dimples = (skip = null) => {
  let o = '', r = 62, dx = 168, dy = 146;
  for (let row = -4; row <= 4; row++)
    for (let col = -4; col <= 4; col++) {
      const x = 540 + col * dx + (row % 2 ? dx / 2 : 0), y = 540 + row * dy;
      if (Math.hypot(x - 540, y - 540) >= 432 - r - 14) continue;
      if (skip && y + r > skip[0] && y - r < skip[1]) continue;
      o += `<circle cx="${x}" cy="${y}" r="${r}"/>`;
    }
  return o;
};

const ballFace = (inner = '', skip = null) => `<svg width="${S}" height="${S}" viewBox="0 0 1080 1080">
  <circle cx="540" cy="540" r="468" fill="${BRASS}"/>
  <circle cx="540" cy="540" r="432" fill="${CREAM}"/>
  <g fill="#CFCAB2">${dimples(skip)}</g>
  ${inner}
</svg>`;

const shell = (inner, extraCss = '') => `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:${S}px;height:${S}px;background:${BG};overflow:hidden}
body{display:flex;align-items:center;justify-content:center;
     font-family:Inter,system-ui,sans-serif;position:relative}
${extraCss}
</style></head><body>${inner}</body></html>`;

const VARIANTS = {
  // 1 — Monogramm: fett, zentriert, Messing-Strich darunter
  monogram: shell(
    `<div class="wrap"><div class="gv">gv</div><div class="rule"></div></div>`,
    `.wrap{display:flex;flex-direction:column;align-items:center;transform:translateY(-34px)}
     .gv{font-size:500px;font-weight:900;color:${CREAM};letter-spacing:-.06em;line-height:.8}
     .rule{width:190px;height:24px;background:${BRASS};border-radius:12px;margin-top:52px}`),

  // 1b — Monogramm mit Schriftzug darueber
  'monogram-text': shell(
    `<div class="wrap"><div class="name">golf vibies</div><div class="gv">gv</div></div>`,
    `.wrap{display:flex;flex-direction:column;align-items:center;transform:translateY(6px)}
     .name{font-size:104px;font-weight:700;color:${BRASS};letter-spacing:.10em;
           margin-bottom:8px;white-space:nowrap}
     .gv{font-size:470px;font-weight:900;color:${CREAM};letter-spacing:-.06em;line-height:.86}`),

  // 2 — Fahne im Loch, Silhouette
  flag: shell(`<svg width="${S}" height="${S}" viewBox="0 0 1080 1080">
      <path d="M0 790 Q540 660 1080 790 L1080 1080 L0 1080 Z" fill="${CREAM}" opacity=".16"/>
      <ellipse cx="438" cy="795" rx="78" ry="26" fill="#06251B"/>
      <rect x="424" y="196" width="30" height="604" rx="15" fill="${CREAM}"/>
      <path d="M454 212 L862 330 L454 448 Z" fill="${BRASS}"/>
      <circle cx="700" cy="788" r="52" fill="${CREAM}"/>
    </svg>`),

  // 3 — Golfball pur
  ball: shell(ballFace()),

  // 3b — Golfball mit Schriftzug
  'ball-text': shell(ballFace(
    `<text x="540" y="574" text-anchor="middle" fill="${BG}"
       font-family="Inter, sans-serif" font-size="104" font-weight="700"
       letter-spacing="6">golf vibies</text>`, [452, 616])),

  // 3c — Golfball mit Monogramm
  'ball-gv': shell(ballFace(
    `<text x="540" y="672" text-anchor="middle" fill="${BG}"
       font-family="Inter, sans-serif" font-size="400" font-weight="900"
       letter-spacing="-22">gv</text>`, [330, 700])),
};

const [, , variant, out] = process.argv;
if (!VARIANTS[variant]) { console.error('Unbekannte Variante:', variant); process.exit(1); }
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: S, height: S }, deviceScaleFactor: 1 });
await page.setContent(VARIANTS[variant], { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: out, type: 'jpeg', quality: 92 });
await browser.close();
console.log(out);
