// Render named keyframes from frames.html (or the storyboard sheet) to PNG.
//
//   node tools/stills.mjs                 # every keyframe and transition strip -> storyboard/
//   node tools/stills.mjs --sheet         # storyboard/sheet.png from sheet.html
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require("playwright"));
} catch {
  ({ chromium } = require(path.join(process.execPath, "../../lib/node_modules/playwright")));
}

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const out = path.join(root, "storyboard");
mkdirSync(out, { recursive: true });

export const KEYFRAMES = ["hook", "title", "opus", "chart", "price", "sonnet", "pokemon", "haiku", "end"];
export const STRIP = [0, 0.25, 0.5, 0.75, 1];

const browser = await chromium.launch({ args: ["--force-color-profile=srgb", "--font-render-hinting=none"] });

if (process.argv.includes("--sheet")) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.join(root, "sheet.html")).href);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => [...document.images].every((i) => i.complete));
  await page.screenshot({ path: path.join(out, "sheet.png"), fullPage: true });
} else {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.join(root, "frames.html")).href);
  await page.evaluate(() => window.ready);
  const stage = page.locator("#stage");
  const shots = [
    ...KEYFRAMES.map((f, i) => [f, 1, `kf${i + 1}-${f}.png`]),
    ...["morphA", "morphB"].flatMap((f) => STRIP.map((p, i) => [f, p, `${f}-${i + 1}.png`])),
  ];
  for (const [f, p, file] of shots) {
    await page.evaluate(([ff, pp]) => window.show(ff, pp), [f, p]);
    await stage.screenshot({ path: path.join(out, file) });
    console.log(file);
  }
}
await browser.close();
