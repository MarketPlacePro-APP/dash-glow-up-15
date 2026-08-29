#!/usr/bin/env node
import fs from 'node:fs';
import process from 'node:process';
import { chromium } from 'playwright';

const src = process.env.TLWB_KPI_SRC || '/Users/seanwilliams/.openclaw/workspace-main/dash-glow-up-15';
const username = process.env.TLWB_KPI_AUTH_USERNAME;
const password = process.env.TLWB_KPI_AUTH_PASSWORD;
const bases = (process.env.TLWB_QA_BASES || 'https://tlwb-kpi.vercel.app').split(',').map(x => x.trim()).filter(Boolean);
if (!username || !password) throw new Error('Protected dashboard verification credentials are missing');

const adapter = fs.readFileSync(`${src}/src/data/executiveAdapters.ts`, 'utf8');
const marker = 'export const activeMarketingMarkets: ActiveMarketingMarket[] = [';
const block = adapter.split(marker, 2)[1]?.split('];', 1)[0];
if (!block) throw new Error('Could not parse active Marketing roster');
const markets = [...new Set([...block.matchAll(/market:\s*'([^']+)'/g)].map(match => match[1]))];
if (!markets.length) throw new Error('Current Marketing roster is empty');
const stateNames = '(alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|new york|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|wisconsin|wyoming)';
const stateCodes = /\b(al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy|dc|ind)\b/g;
const normalizeMarket = value => String(value).toLowerCase()
  .replace(/wpb/g, 'west palm beach')
  .replace(/fort meyers/g, 'fort myers')
  .replace(/\bsaint\b/g, 'st')
  .replace(new RegExp(`(?:,\\s*|\\s+)${stateNames}\\s*$`), '')
  .replace(stateCodes, '')
  .replace(/[^a-z]+/g, ' ')
  .replace(/\s+/g, ' ')
  .trim();

const browser = await chromium.launch({ headless: true });
const results = [];
try {
  for (const base of bases) {
    for (const viewport of [{ name: 'desktop', width: 1440, height: 1000 }, { name: 'mobile', width: 390, height: 844 }]) {
      const context = await browser.newContext({ viewport, httpCredentials: { username, password } });
      for (const route of ['/marketing', '/preview']) {
        const page = await context.newPage();
        const consoleErrors = [];
        const pageErrors = [];
        page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
        page.on('pageerror', error => pageErrors.push(String(error)));
        const response = await page.goto(`${base}${route}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.locator('h1').first().waitFor({ state: 'visible', timeout: 15000 });
        const headings = await page.locator('h4').allTextContents();
        const missing = [];
        for (const market of markets) {
          const key = normalizeMarket(market);
          const count = headings.filter(text => normalizeMarket(text.trim()) === key).length;
          const minimum = route === '/marketing' ? 2 : 1;
          if (count < minimum) missing.push({ market, count, minimum });
        }
        const metrics = await page.evaluate(() => ({
          innerWidth: window.innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        }));
        if (response?.status() !== 200) throw new Error(`${base}${route} returned ${response?.status()}`);
        if (missing.length) throw new Error(`${base}${route} dropped market headings: ${JSON.stringify(missing)}`);
        if (metrics.scrollWidth > metrics.innerWidth) throw new Error(`${base}${route} document overflow: ${JSON.stringify(metrics)}`);
        if (consoleErrors.length || pageErrors.length) throw new Error(`${base}${route} runtime errors: ${JSON.stringify({ consoleErrors, pageErrors })}`);
        results.push({ base, route, viewport: viewport.name, status: response.status(), marketCount: markets.length, metrics });
        await page.close();
      }
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log(JSON.stringify({ status: 'ok', markets, checks: results }, null, 2));
