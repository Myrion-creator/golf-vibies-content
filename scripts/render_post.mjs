// Render an Instagram asset from a JSON spec. Usage: node render_post.mjs spec.json out.jpg
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire('/opt/node22/lib/node_modules/');
const { chromium } = require('playwright');

const SIZES = { post: [1080, 1350], square: [1080, 1080], story: [1080, 1920], reel_cover: [1080, 1920] };
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function buildHtml(spec) {
  const [w, h] = SIZES[spec.kind || 'post'];
  const s = h / 1350;
  const px = (n) => Math.round(n * s);
  const bg = spec.bg || '#0B3D2E';
  const accent = spec.accent || '#C9A84C';
  const photo = spec.photo || '';
  const centered = (spec.layout || 'center') === 'center';
  return `<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:${w}px;height:${h}px;background:${bg}}
body{font-family:Inter,system-ui,sans-serif;color:#F5F3E8;display:flex;flex-direction:column;
     justify-content:${centered ? 'center' : 'flex-end'};padding:${px(84)}px;position:relative;overflow:hidden}
.photo{position:absolute;inset:0;background:url('${photo}') center/cover no-repeat}
.scrim{position:absolute;inset:0;background:${centered
   ? 'radial-gradient(ellipse at center,rgba(0,0,0,.30) 0%,rgba(0,0,0,.55) 100%)'
   : 'linear-gradient(180deg,rgba(0,0,0,.10) 0%,rgba(0,0,0,.22) 45%,rgba(0,0,0,.80) 100%)'}}
.inner{position:relative;z-index:2;text-align:${centered ? 'center' : 'left'}}
.kicker{font-size:${px(26)}px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:${accent};margin-bottom:${px(20)}px}
.headline{font-size:${px(spec.headlineSize || 78)}px;font-weight:800;line-height:1.04;letter-spacing:-.02em;text-wrap:balance}
.rule{width:${px(96)}px;height:${px(6)}px;background:${accent};margin:${px(32)}px ${centered ? 'auto' : '0'}}
.footer{font-size:${px(28)}px;font-weight:600;letter-spacing:.06em;opacity:.92}
</style></head><body>
${photo ? '<div class="photo"></div>' : ''}<div class="scrim"></div>
<div class="inner">
${spec.kicker ? `<div class="kicker">${esc(spec.kicker)}</div>` : ''}
<div class="headline">${esc(spec.headline)}</div>
<div class="rule"></div>
${spec.footer ? `<div class="footer">${esc(spec.footer)}</div>` : ''}
</div></body></html>`;
}

const [, , specPath, outPath] = process.argv;
const spec = JSON.parse(readFileSync(specPath, 'utf8'));
const [w, h] = SIZES[spec.kind || 'post'];
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
await page.setContent(buildHtml(spec), { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
const isJpeg = /\.jpe?g$/i.test(outPath);
await page.screenshot({ path: outPath, type: isJpeg ? 'jpeg' : 'png', ...(isJpeg ? { quality: 90 } : {}) });
await browser.close();
console.log(`${outPath} ${w}x${h}`);
