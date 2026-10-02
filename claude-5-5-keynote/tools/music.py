"""Synthesize the 40 s soundtrack (numpy/scipy, no samples).

120 BPM, 20 bars, D major. Quiet intro while the dots appear, a drop on the
orange flood (beat 16), a breakdown on the black flood (beat 56), and a
last chorus when the black contracts into the end card (beat 64). Every hit
uses the same beat numbers as index.html, so pops, bars, the price strike,
the page push and the floods all land on the frame they happen.

    python3 tools/music.py build/music.wav
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sawtooth, sosfilt

SR = 48000
BPM = 120
BEAT = 60 / BPM
BEATS = 80
DUR = BEATS * BEAT
N = int(SR * DUR)
rng = np.random.default_rng(120)


def T(b):
    return b * BEAT


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def bus():
    return np.zeros((2, N))


def place(buf, sig, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= N or i < 0:
        return
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4
        sig = np.vstack([sig * np.cos(a), sig * np.sin(a)]) * np.sqrt(2)
    n = min(sig.shape[1], N - i)
    buf[:, i : i + n] += sig[:, :n] * gain


def adsr(n, a, d, s, r, sustain_len):
    t = np.arange(n) / SR
    env = np.where(t < a, t / max(a, 1e-4), 1.0)
    env = np.where((t >= a) & (t < a + d), 1 - (1 - s) * (t - a) / max(d, 1e-4), env)
    env = np.where(t >= a + d, s, env)
    return env * (1 - np.clip((t - sustain_len) / r, 0, 1))


def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


# ---------------------------------------------------------------- instruments
def supersaw(m, length, cutoff, voices=5, spread=0.16, a=0.01, d=0.25, s=0.75, r=0.25):
    n = int((length + r) * SR)
    t = np.arange(n) / SR
    out = np.zeros((2, n))
    for v in range(voices):
        k = (v - (voices - 1) / 2) / ((voices - 1) / 2)
        f = hz(m) * 2 ** (spread * k / 12)
        x = sawtooth(2 * np.pi * (f * t + rng.random()))
        ang = (0.7 * k + 1) * np.pi / 4
        out[0] += x * np.cos(ang)
        out[1] += x * np.sin(ang)
    out = np.vstack([lp(out[c], cutoff, 2) for c in range(2)])
    return out * adsr(n, a, d, s, r, length) / voices


def pluck(m, dur=0.32, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    x = np.zeros(n)
    for k in range(1, 9):
        if f * k > 12000:
            break
        x += (1 / k) * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (7 + 9 * k * bright))
    return x * np.minimum(t / 0.002, 1)


def pulse(m, dur, duty=0.25):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ph = (hz(m) * t) % 1.0
    x = np.where(ph < duty, 1.0, -1.0) - (2 * duty - 1)
    env = np.minimum(t / 0.002, 1) * np.clip((dur - t) / 0.008, 0, 1) * np.exp(-t * 2.0)
    return lp(x, 6500) * env


def bell(m, dur=2.5, index=1.8):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    mod = index * np.exp(-t / 0.5) * np.sin(2 * np.pi * f * 3.5 * t)
    x = np.sin(2 * np.pi * f * t + mod) + 0.25 * np.sin(2 * np.pi * f * 2.001 * t) * np.exp(-t / 0.4)
    return x * np.minimum(t / 0.003, 1) * np.exp(-t / 0.9)


def kick(level=1.0):
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 47 + 150 * np.exp(-t / 0.028)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.21)
    click = hp(rng.standard_normal(n), 2500) * np.exp(-t / 0.004) * 0.35
    return np.tanh(2.0 * (x + click)) * level


def clap():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    noise = bp(rng.standard_normal(n), 1000, 6000)
    env = np.exp(-t / 0.07) * (1 + 0.7 * np.exp(-((t - 0.011) ** 2) / 1e-5) + 0.6 * np.exp(-((t - 0.022) ** 2) / 1e-5))
    return noise * env * 0.7 + np.sin(2 * np.pi * 210 * t) * np.exp(-t / 0.03) * 0.35


def snare(level=1.0):
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    noise = bp(rng.standard_normal(n), 1800, 9000) * np.exp(-t / 0.06)
    body = np.sin(2 * np.pi * (180 + 60 * np.exp(-t / 0.01)) * t) * np.exp(-t / 0.05)
    return (noise * 0.7 + body * 0.5) * level


def hat(open_=False):
    n = int((0.3 if open_ else 0.07) * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 8000, 4) * np.exp(-t / (0.09 if open_ else 0.018))


def crash():
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 4500, 2) * np.exp(-t / 0.7)
    x += hp(rng.standard_normal(n), 9000, 2) * np.exp(-t / 0.25) * 0.5
    return x


def bass_note(m, dur, drive=1.6):
    n = int((dur + 0.02) * SR)
    t = np.arange(n) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.3 * sawtooth(2 * np.pi * f * t)
    x = lp(x, 900)
    return np.tanh(drive * x) * adsr(n, 0.004, 0.08, 0.75, 0.02, dur)


def riser(length):
    n = int(length * SR)
    t = np.arange(n) / SR
    p = t / length
    noise = bp(rng.standard_normal(n), 1500, 10000)
    sweep = np.sin(2 * np.pi * np.cumsum(220 * 10 ** p) / SR) * 0.25
    return (noise * 0.6 + sweep) * p ** 2.4 * np.minimum((length - t) / 0.02, 1)


def impact(dur=3.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 40 + 34 * np.exp(-t / 0.12)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    noise = lp(rng.standard_normal(n), 1200) * np.exp(-t / 0.25) * 0.6
    return np.tanh(1.4 * (boom + noise))


def pop(m):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    f = hz(m) * (1 + 1.2 * np.exp(-t / 0.01))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.08) * np.minimum(t / 0.001, 1)


def thud():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * (70 + 80 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.08)
    x += lp(rng.standard_normal(n), 2500) * np.exp(-t / 0.015) * 0.6
    return np.tanh(2 * x)


def tick():
    n = int(0.025 * SR)
    t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 2000, 7000) * np.exp(-t / 0.003)
    return x + np.sin(2 * np.pi * 2600 * t) * np.exp(-t / 0.003) * 0.4


def zip_(length, f0, f1):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / length)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / length) ** 2


def swish(length=0.3):
    n = int(length * SR)
    t = np.arange(n) / SR
    return bp(rng.standard_normal(n), 2500, 9000) * np.sin(np.pi * t / length) ** 2


def blip(f=1600, dur=0.05):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t / 0.015)


# ---------------------------------------------------------------- harmony
V = {
    "Dadd9": [50, 57, 64, 66, 69], "D": [50, 57, 62, 66, 69], "A": [45, 52, 61, 64, 69], "Asus4": [45, 52, 62, 64, 69],
    "Bm": [47, 54, 62, 66, 71], "G": [43, 50, 59, 62, 67], "Gmaj7": [43, 50, 59, 66, 71],
}
ROOT = {"Dadd9": 38, "D": 38, "A": 33, "Asus4": 33, "Bm": 35, "G": 31, "Gmaj7": 31}
LOOP = ["D", "A", "Bm", "G"]

CH = [(0, 8, "Dadd9"), (8, 12, "Gmaj7"), (12, 14, "Asus4"), (14, 16, "A")]
CH += [(b, b + 4, LOOP[k % 4]) for k, b in enumerate(range(16, 56, 4))]
CH += [(56, 60, "Bm"), (60, 62, "G"), (62, 64, "A")]
CH += [(b, b + 2, LOOP[k % 4]) for k, b in enumerate(range(64, 72, 2))]
CH += [(72, 80, "Dadd9")]


def chord_at(b):
    for a, e, c in CH:
        if a <= b < e:
            return c
    return "D"


def kick_on(b):
    return 16 <= b < 55 or 64 <= b < 72


pad, keys, lead, bass, drums, fx = (bus() for _ in range(6))
duck = np.ones(N)


def add_kick(t, level=1.0):
    place(drums, kick(level), t, 0.55)
    i = int(t * SR)
    n = min(int(0.3 * SR), N - i)
    duck[i : i + n] = np.minimum(duck[i : i + n], 1 - 0.5 * level * np.exp(-np.arange(n) / SR / 0.12))


# pads: warm, three voices, brighter in the choruses
for a, e, c in CH:
    if a < 8:
        cut, lvl, att = 800, 0.40, 1.8
    elif a < 16:
        cut, lvl, att = 900 + 2400 * (a - 8) / 8, 0.34, 0.05
    elif a < 40:
        cut, lvl, att = 2600, 0.28, 0.02
    elif a < 56:
        cut, lvl, att = 3400, 0.28, 0.02
    elif a < 64:
        cut, lvl, att = 1000, 0.24, 0.4
    elif a < 72:
        cut, lvl, att = 3800, 0.30, 0.02
    else:
        cut, lvl, att = 2400, 0.42, 0.02
    rel = 3.0 if a >= 72 else 0.25
    for m in V[c]:
        place(pad, supersaw(m, T(e - a) - (0 if a >= 72 else 0.03), cut, voices=3, spread=0.1, a=att, r=rel), T(a), lvl * (0.8 if m < 50 else 1.0))

# keys: 8th arps from beat 8, 16ths in the last chorus
PAT = [0, 2, 1, 3, 2, 4, 3, 1]
for s in range(BEATS * 4):
    b = s / 4
    if 8 <= b < 16:
        if s % 2:
            continue
        lvl, bright = 0.05 + 0.10 * (b - 8) / 8, 0.3 + 0.7 * (b - 8) / 8
    elif 16 <= b < 55:
        if s % 2:
            continue
        lvl, bright = 0.12, 1.0
    elif 64 <= b < 72:
        lvl, bright = (0.10 if s % 2 else 0.14), 1.0
    else:
        continue
    tones = sorted({x for x in V[chord_at(b)] if x >= 59})
    tones += [x + 12 for x in tones]
    m = tones[PAT[(s // (1 if b >= 64 else 2)) % 8] % len(tones)]
    place(keys, pluck(m, 0.3, bright), T(b), lvl, pan=0.4 * np.sin(s * 0.7))

# lead motif over D A Bm G
MOTIF = {"D": [(0, 78), (0.75, 81), (1.5, 78), (2.5, 76)], "A": [(0, 76), (0.75, 73), (1.5, 76), (2.5, 81)],
         "Bm": [(0, 74), (0.75, 78), (1.5, 81), (2.5, 83)], "G": [(0, 83), (0.75, 81), (1.5, 79), (2.5, 78)]}
for a, e, c in CH:
    if (24 <= a < 40) or (44 <= a < 48):
        for off, m in MOTIF[c]:
            place(lead, pluck(m, 0.6, 0.45), T(a + off), 0.16, pan=0.1)
            place(lead, bell(m + 12, 0.8, 0.8), T(a + off), 0.025, pan=-0.1)

# bass: off-beat 8ths in the grooves, long notes elsewhere
for s in range(BEATS * 2):
    b = s / 2
    r = ROOT[chord_at(b)]
    if 16 <= b < 55 or 64 <= b < 72:
        if s % 2 == 1:
            place(bass, bass_note(r + (12 if s % 8 == 7 else 0), T(0.42)), T(b), 0.42)
for b, m, d in [(8, 31, 3.9), (12, 33, 3.9), (56, 35, 3.9), (60, 31, 1.9), (62, 33, 1.9), (72, 38, 7.5)]:
    place(bass, bass_note(m, T(d), drive=1.1), T(b), 0.34)

# drums
for b in range(BEATS):
    t = T(b)
    if kick_on(b):
        add_kick(t)
        if b % 2 == 1:
            place(drums, clap(), t, 0.24)
        place(drums, hat(True), t + BEAT / 2, 0.06, pan=0.2)
        if 40 <= b < 55 or 64 <= b < 72:
            for q in (0.25, 0.75):
                place(drums, hat(), t + q * BEAT, 0.045, pan=-0.3)
for k in range(16):  # roll into the drop
    place(drums, snare(0.3 + 0.7 * k / 15), T(14 + k * 0.125), 0.15)
for k in range(16):  # roll into the last chorus
    place(drums, snare(0.3 + 0.7 * k / 15), T(62 + k * 0.125), 0.14)
for b in (16, 40, 64, 72):
    place(drums, crash(), T(b), 0.16)

# ---------------------------------------------------------------- picture sync
# hook dots (big = low) and the end-card dots
for i, m in enumerate((69, 74, 81)):
    place(fx, pop(m), T(i), 0.30)
    place(fx, bell(m + 12, 1.2, 0.6), T(i), 0.05)
for b, m in [(64, 69), (65, 74), (66.8, 86)]:
    place(fx, pop(m), T(b), 0.26)
for b in (3, 8):
    place(fx, swish(0.35), T(b), 0.035)
# big dot travels into the decimal slot and lands
place(fx, zip_(T(2.4), 260, 900), T(8.75), 0.05)
place(fx, bell(86, 1.6, 1.4), T(11.1), 0.22)
place(fx, pop(81), T(11.1), 0.22)
place(fx, swish(0.3), T(10.25), 0.03)
# orange flood: riser into the drop, then a sweep down as it contracts
place(fx, riser(T(2)), T(14), 0.22)
place(fx, impact(), T(16), 0.5)
for m in V["D"] + [V["D"][3] + 12]:
    place(keys, supersaw(m, 0.3, 5500, voices=3, spread=0.1, d=0.12, s=0.5, r=0.25), T(16), 0.22)
place(fx, zip_(T(1.5), 1400, 260), T(16), 0.05)
# chart bars draw; price strike and new price
for b in (25, 25.5, 26, 41, 41.5):
    place(fx, zip_(0.7, 300, 1100), T(b), 0.05)
place(fx, swish(0.3), T(33.5), 0.08)
place(fx, bell(86, 1.2, 2.0), T(34), 0.11)
# page push
place(fx, riser(T(1.5)), T(38), 0.12)
place(fx, swish(0.75), T(39.5), 0.12)
place(fx, impact(1.5), T(40), 0.3)
# bar → prompt bar, send button, badges
place(fx, zip_(T(1.5), 200, 700), T(47), 0.06)
place(fx, pop(84), T(48.5), 0.22)
for i, m in enumerate((74, 76, 78, 79, 81, 83, 85, 86)):
    place(fx, pluck(m, 0.4, 0.8), T(49.5 + i * 0.5), 0.15, pan=-0.4 + 0.11 * i)
place(fx, bell(90, 1.4, 1.2), T(53.5), 0.08)
# black flood → breakdown
place(fx, riser(T(1)), T(55), 0.2)
place(fx, impact(3.0), T(56), 0.2)
place(fx, bell(81, 2.0, 1.0), T(56.5), 0.12)
for b, m in [(58, 78), (59.5, 74), (61, 71)]:
    place(fx, bell(m, 2.5, 0.8), T(b), 0.07)
# black contracts → last chorus
place(fx, riser(T(2)), T(62), 0.16)
place(fx, impact(), T(64), 0.5)
for m in V["D"] + [V["D"][3] + 12]:
    place(keys, supersaw(m, 0.3, 5500, voices=3, spread=0.1, d=0.12, s=0.5, r=0.25), T(64), 0.22)
# final chord
place(fx, impact(3.5), T(72), 0.4)
for m, dt, g in [(81, 0.0, 0.15), (86, 0.12, 0.12), (90, 0.24, 0.09), (93, 0.36, 0.07)]:
    place(fx, bell(m, 4.0, 1.4), T(72) + dt, g, pan=(m - 87) / 12)

# ---------------------------------------------------------------- mix
pad *= duck
keys *= duck ** 0.4
lead *= duck ** 0.3
bass *= duck ** 0.8


def reverb(x, secs=2.2, damp=6000):
    n = int(secs * SR)
    t = np.arange(n) / SR
    ir = np.vstack([lp(rng.standard_normal(n), damp) * np.exp(-t / (secs / 5.5)) for _ in range(2)])
    ir[:, : int(0.01 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    return np.vstack([fftconvolve(x[c], ir[c])[:N] for c in range(2)])


pad *= 1.3
keys *= 3.5
lead *= 3.5
drums *= 0.8
send = pad * 0.25 + keys * 0.4 + lead * 0.45 + fx * 0.45 + drums * 0.05
wet = reverb(send)
mix = pad + keys + lead + bass + drums + fx * 0.9 + wet * 0.45
mix = np.vstack([hp(mix[c], 30) for c in range(2)])

t = np.arange(N) / SR
mix *= np.minimum(t / 0.02, 1) * np.clip((DUR - t) / 1.5, 0, 1)
mix /= np.percentile(np.abs(mix), 99.95)
mix = np.tanh(mix * 0.95)
mix *= 10 ** (-1.0 / 20) / np.max(np.abs(mix))

for name, b in [("pad", pad), ("keys", keys), ("lead", lead), ("bass", bass), ("drums", drums), ("fx", fx), ("wet", wet)]:
    print(f"{name:6s} rms {20 * np.log10(np.sqrt((b ** 2).mean()) + 1e-12):6.1f} dB")
for a, b, label in [(0, 8, "hook"), (8, 16, "title"), (16, 40, "opus"), (40, 56, "sonnet"), (56, 64, "breakdown"),
                    (64, 72, "chorus"), (72, 80, "end")]:
    seg = mix[:, int(T(a) * SR) : int(T(b) * SR)]
    print(f"{label:10s} {T(a):5.1f}-{T(b):5.1f}s  rms {20 * np.log10(np.sqrt((seg ** 2).mean())):6.1f} dBFS")

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
wavfile.write(out, SR, (mix.T * 32767).astype(np.int16))
print("wrote", out)
