// Render index.html frame by frame with headless Chromium and pipe the frames
// into ffmpeg.
//
//   node tools/render.mjs --out build/video.mp4 [--fps 30] [--from 0] [--to 91]
//   node tools/render.mjs --stills 3,12,40 --out build/stills
//
// FFMPEG may point at an ffmpeg binary; defaults to `ffmpeg` on PATH.
import { spawn } from "node:child_process";
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

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => (a.startsWith("--") ? [...acc, [a.slice(2), all[i + 1]]] : acc), []),
);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const fps = Number(args.fps || 30);
const ffmpeg = process.env.FFMPEG || "ffmpeg";

const browser = await chromium.launch({ args: ["--force-color-profile=srgb", "--font-render-hinting=none"] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.join(root, "index.html")).href + "?render=1");
await page.evaluate(() => window.fontsReady);
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.DURATION);

async function frame(t) {
  await page.evaluate((tt) => window.seek(tt), t);
  return page.screenshot({ type: "jpeg", quality: 94, animations: "disabled", caret: "initial" });
}

if (args.stills) {
  mkdirSync(args.out, { recursive: true });
  for (const s of args.stills.split(",")) {
    const t = Number(s);
    await page.evaluate((tt) => window.seek(tt), t);
    await page.screenshot({ path: path.join(args.out, `t${t.toFixed(2).padStart(6, "0")}.png`) });
  }
  await browser.close();
  process.exit(0);
}

const from = Number(args.from || 0);
const to = Math.min(Number(args.to || duration), duration);
const f0 = Math.round(from * fps), f1 = Math.round(to * fps);
mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
const ff = spawn(ffmpeg, [
  "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
  "-c:v", "libx264", "-preset", args.preset || "slow", "-crf", args.crf || "18", "-pix_fmt", "yuv420p",
  "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart",
  args.out,
], { stdio: ["pipe", "inherit", "inherit"] });
const done = new Promise((res, rej) => ff.on("close", (c) => (c === 0 ? res() : rej(new Error("ffmpeg exit " + c)))));

const started = Date.now();
for (let f = f0; f < f1; f++) {
  const buf = await frame(f / fps);
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
  if ((f - f0) % 150 === 0) {
    const el = (Date.now() - started) / 1000;
    console.log(`[${args.out}] frame ${f - f0}/${f1 - f0}  ${el.toFixed(0)}s`);
  }
}
ff.stdin.end();
await done;
await browser.close();
console.log(`[${args.out}] done: ${f1 - f0} frames in ${((Date.now() - started) / 1000).toFixed(0)}s`);
