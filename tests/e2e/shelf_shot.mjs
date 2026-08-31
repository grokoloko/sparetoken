import pkg from '../../.anon-secrets/pw/node_modules/playwright-core/index.js';
const { chromium } = pkg;
import { mkdirSync } from 'node:fs';

const dir = '/tmp/sparetoken-lp';
mkdirSync(dir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const shots = [];
for (const [name, size] of [
  ['desktop', { width: 1280, height: 900 }],
  ['mobile', { width: 390, height: 844 }],
]) {
  const page = await browser.newPage({ viewport: size });
  await page.goto('http://127.0.0.1:8799/?utm_source=pw&utm_medium=visual&utm_campaign=shelf&utm_content=qa', {
    waitUntil: 'domcontentloaded',
    timeout: 20000,
  });
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${dir}/${name}-top.png`, fullPage: false });
  await page.locator('#mercado').scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
  await page.locator('#mercado').screenshot({ path: `${dir}/${name}-mercado.png` });
  const junk = await page.locator('.shelf-card-open').count();
  const rail = await page.locator('.shelf-rail li').count();
  const cards = await page.locator('.shelf-card').count();
  shots.push({ name, junk, rail, cards, url: page.url() });
  await page.close();
}
await browser.close();
console.log(JSON.stringify({ dir, shots }, null, 2));
