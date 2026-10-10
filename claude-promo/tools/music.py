"""Synthesize the 91 s soundtrack for the promo (numpy/scipy, no samples).

120 BPM, D major. One bar = 2 s, so every scene cut in index.html lands on a
bar line: 6 s (history), 26 s (founding), 36 s (models), 72 s (products),
86 s (logo). Typing clicks follow the typed text timings in index.html.

    python3 tools/music.py build/music.wav
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
DUR = 91.0
N = int(SR * DUR)
rng = np.random.default_rng(2021)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def bus():
    return np.zeros((2, N))


def place(buf, sig, t, gain=1.0, pan=0.0):
    """Add mono or stereo `sig` into `buf` at time t (s) with equal-power pan."""
    i = int(round(t * SR))
    if i >= N:
        return
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4
        sig = np.vstack([sig * np.cos(a), sig * np.sin(a)]) * np.sqrt(2)
    n = min(sig.shape[1], N - i)
    buf[:, i : i + n] += sig[:, :n] * gain


def adsr(n, a, d, s, r, sustain_len):
    """Envelope of n samples; times in seconds."""
    t = np.arange(n) / SR
    env = np.where(t < a, t / max(a, 1e-4), 1.0)
    env = np.where((t >= a) & (t < a + d), 1 - (1 - s) * (t - a) / max(d, 1e-4), env)
    env = np.where(t >= a + d, s, env)
    rel = np.clip((t - sustain_len) / r, 0, 1)
    return env * (1 - rel)


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


# ---------------------------------------------------------------- instruments
def pad_note(m, length, cutoff, detune=0.07):
    """Soft additive 'saw' with a gentle spectral roll-off; stereo detuned."""
    rel = 2.2
    n = int((length + rel) * SR)
    t = np.arange(n) / SR
    f = hz(m)
    out = np.zeros((2, n))
    for ch, dt in enumerate((-detune, detune)):
        ff = f * 2 ** (dt / 12)
        vib = 1 + 0.0015 * np.sin(2 * np.pi * (0.2 + 0.1 * ch) * t)
        ph = 2 * np.pi * ff * np.cumsum(vib) / SR
        for k in range(1, 18):
            if ff * k > 9000:
                break
            amp = (1 / k) / (1 + (ff * k / cutoff) ** 2)
            out[ch] += amp * np.sin(k * ph + k * ch * 0.7)
    env = adsr(n, 1.1, 0.5, 0.85, rel, length)
    return out * env * 0.22


def pluck(m, dur=0.6, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * bright * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.08)
    x += 0.12 * bright * np.sin(6 * np.pi * f * t) * np.exp(-t / 0.05)
    env = np.minimum(t / 0.004, 1) * np.exp(-t / 0.2)
    return x * env


def bell(m, dur=3.0, index=2.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    mod = index * np.exp(-t / 0.6) * np.sin(2 * np.pi * f * 3.5 * t)
    x = np.sin(2 * np.pi * f * t + mod) + 0.25 * np.sin(2 * np.pi * f * 2.001 * t) * np.exp(-t / 0.5)
    return x * np.minimum(t / 0.003, 1) * np.exp(-t / 1.1)


def kick(level=1.0):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 44 + 95 * np.exp(-t / 0.035)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.26)
    click = hp(rng.standard_normal(n), 3000) * np.exp(-t / 0.003) * 0.25
    return np.tanh(1.6 * (x + click)) * level


def hat(open_=False):
    n = int((0.25 if open_ else 0.09) * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7500, 4) * np.exp(-t / (0.07 if open_ else 0.022))


def clap():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    noise = bp(rng.standard_normal(n), 900, 5200)
    env = np.exp(-t / 0.09) * (1 + 0.6 * np.exp(-((t - 0.012) ** 2) / 1e-5) + 0.5 * np.exp(-((t - 0.024) ** 2) / 1e-5))
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.045) * 0.4
    return noise * env * 0.7 + tone


def bass_note(m, dur):
    n = int((dur + 0.03) * SR)
    t = np.arange(n) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    env = adsr(n, 0.006, 0.12, 0.7, 0.03, dur)
    return np.tanh(1.4 * x) * env


def riser(length):
    n = int(length * SR)
    t = np.arange(n) / SR
    p = t / length
    noise = bp(rng.standard_normal(n), 1500, 9000)
    f = 180 * (12 ** p)
    sweep = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    return (noise * 0.6 + sweep) * p ** 2.2 * np.minimum((length - t) / 0.03, 1)


def impact():
    n = int(3.5 * SR)
    t = np.arange(n) / SR
    f = 38 + 30 * np.exp(-t / 0.15)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.1)
    noise = lp(rng.standard_normal(n), 900) * np.exp(-t / 0.35) * 0.6
    return np.tanh(1.3 * (boom + noise))


def tick():
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 1800, 6000) * np.exp(-t / 0.004)
    x += np.sin(2 * np.pi * 2400 * t) * np.exp(-t / 0.003) * 0.3
    return x * (0.8 + 0.4 * rng.random())


def whoosh(length=0.7):
    n = int(length * SR)
    t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 400, 3500)
    env = np.sin(np.pi * t / length) ** 3
    pan = np.linspace(-0.8, 0.8, n)
    a = (pan + 1) * np.pi / 4
    return np.vstack([x * env * np.cos(a), x * env * np.sin(a)]) * np.sqrt(2)


# ---------------------------------------------------------------- score
V = {
    "Dsus": [50, 57, 64, 69],
    "D": [50, 57, 62, 66, 69],
    "Dmaj9": [50, 57, 61, 64, 66, 69],
    "Bm": [47, 54, 59, 62, 66],
    "G": [43, 50, 55, 59, 62, 66],
    "A": [45, 52, 57, 61, 64],
    "Asus": [45, 52, 57, 62, 64],
    "Em9": [40, 47, 55, 59, 62, 66],
}
ROOT = {"Dsus": 38, "D": 38, "Dmaj9": 38, "Bm": 35, "G": 31, "A": 33, "Asus": 33, "Em9": 40}
CHORDS = [
    (0, 6, "Dsus"),
    (6, 10, "Bm"), (10, 14, "G"), (14, 18, "D"), (18, 22, "A"), (22, 26, "G"),
    (26, 30, "Dmaj9"), (30, 34, "G"), (34, 36, "Asus"),
    (36, 40, "D"), (40, 44, "A"), (44, 48, "Bm"), (48, 52, "G"),
    (52, 56, "D"), (56, 60, "A"), (60, 64, "Bm"), (64, 68, "G"), (68, 70, "Asus"), (70, 72, "A"),
    (72, 76, "D"), (76, 80, "A"), (80, 84, "G"),
    (84, 86, "Em9"),
    (86, 91, "Dmaj9"),
]


def chord_at(t):
    for a, b, c in CHORDS:
        if a <= t < b:
            return c
    return CHORDS[-1][2]


def cutoff_at(t):
    pts = [(0, 700), (6, 1200), (26, 2600), (27, 1600), (36, 2200), (68, 3800), (72, 4600), (83, 4200), (84, 1400), (86, 3200), (91, 1800)]
    xs, ys = zip(*pts)
    return float(np.interp(t, xs, ys))


pad, arp, bass, drums, fx, bells = bus(), bus(), bus(), bus(), bus(), bus()

# pads
for a, b, c in CHORDS:
    # pads sit under everything; they swell a little as the film builds
    lvl = 0.30 if a < 6 else 0.32 if a < 26 else 0.36 if a < 36 else 0.30 if a < 72 else 0.34 if a < 84 else 0.30
    if a >= 86:
        lvl = 0.48
    for m in V[c]:
        place(pad, pad_note(m, b - a, cutoff_at(a + 0.5)), a, lvl * (0.8 if m < 48 else 1.0))

# high shimmer in the cold open and the finale
for t0, t1, g in [(0, 6.2, 0.03), (84, 91, 0.035)]:
    n = int((t1 - t0) * SR)
    t = np.arange(n) / SR
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 0.35 * t)
    env = np.minimum(t / 2.0, 1) * np.minimum((t1 - t0 - t) / 1.5, 1).clip(0)
    sh = (np.sin(2 * np.pi * hz(86) * t) + 0.6 * np.sin(2 * np.pi * hz(81) * t * 1.0005)) * trem * env
    place(fx, sh, t0, g)


# arpeggios
def arp_notes(c):
    base = sorted({x for x in V[c] if x >= 57})
    tones = base + [x + 12 for x in base]
    return tones[:7]


PATTERN = [0, 2, 4, 1, 3, 5, 2, 6]
for step in range(int(DUR / 0.125)):
    t = step * 0.125
    c = chord_at(t)
    if 6 <= t < 26:
        if step % 2:
            continue
        lvl = 0.10 + 0.14 * (t - 6) / 20
    elif 36 <= t < 71.5:
        if step % 2:
            continue
        lvl = 0.26 if t < 52 else 0.3
    elif 72 <= t < 83:
        lvl = 0.2 if step % 2 else 0.3
    else:
        continue
    tones = arp_notes(c)
    m = tones[PATTERN[(step // (1 if t >= 72 else 2)) % 8] % len(tones)]
    place(arp, pluck(m, bright=0.7 + 0.5 * (t > 36)), t, lvl, pan=0.35 * np.sin(step * 0.9))

# bass: long notes in S1, pulsing 8ths in S3/S4
for a, b, c in CHORDS:
    r = ROOT[c]
    if 14 <= a < 26:
        place(bass, bass_note(r, b - a - 0.05), a, 0.30)
    elif 36 <= a < 84:
        for k in range(int((b - a) / 0.25)):
            t = a + k * 0.25
            if t >= 83.0 or (70.0 <= t < 72.0 and k % 2):
                continue
            place(bass, bass_note(r + (12 if k % 8 == 7 else 0), 0.22), t, 0.34 if k % 2 == 0 else 0.24)
    elif a >= 86:
        place(bass, bass_note(r, 4.5), a, 0.34)

# drums
duck = np.ones(N)


def add_kick(t, level):
    place(drums, kick(level), t, 0.55)
    i = int(t * SR)
    n = min(int(0.28 * SR), N - i)
    duck[i : i + n] = np.minimum(duck[i : i + n], 1 - 0.45 * level * np.exp(-np.arange(n) / SR / 0.09))


for beat in range(int(DUR / 0.5)):
    t = beat * 0.5
    if 14 <= t < 26 and beat % 2 == 0:
        add_kick(t, 0.55)
    if 36 <= t < 68 or 72 <= t < 83:
        add_kick(t, 0.8 if t < 52 else 0.9)
    if 68 <= t < 72:
        add_kick(t, 0.9)
        if t >= 70:
            add_kick(t + 0.25, 0.7)
    if (52 <= t < 68 or 74 <= t < 83) and beat % 4 == 2:
        place(drums, clap(), t, 0.22)
    if 44 <= t < 71.5 or 72 <= t < 83:
        place(drums, hat(), t + 0.25, 0.10, pan=0.25)
        if t >= 60:
            place(drums, hat(), t, 0.05, pan=-0.25)
    if 76 <= t < 83 and beat % 4 == 3:
        place(drums, hat(True), t + 0.25, 0.08, pan=0.3)

# S2 bell melody over Dmaj9 → G → Asus
for t, m, g in [(27.0, 78, 0.20), (28.0, 81, 0.16), (29.0, 76, 0.16), (30.0, 74, 0.18), (31.0, 78, 0.15), (32.5, 83, 0.14), (34.0, 76, 0.16), (35.0, 81, 0.13)]:
    place(bells, bell(m), t, g, pan=0.3 * np.sin(m))

# S1 milestone "tock" and S3 card whooshes
for k in range(1, 8):
    t = 6 + 2.5 * k
    place(fx, bell(93, 0.8, 0.8), t, 0.035, pan=0.2)
for k in range(1, 9):
    place(fx, whoosh(0.7), 36 + 4 * k - 0.45, 0.07)
for j in range(8):
    place(fx, pluck(86 + [0, 2, 4, 7, 9, 7, 4, 2][j], 0.4, 0.3), 72.8 + 0.28 * j, 0.05, pan=-0.6 + 0.17 * j)

# risers & impacts
for t0, t1, g in [(22.5, 26.0, 0.16), (33.0, 36.0, 0.18), (67.5, 72.0, 0.22)]:
    place(fx, riser(t1 - t0), t0, g)
for t, g in [(26.0, 0.5), (36.0, 0.45), (72.0, 0.55), (86.0, 0.6)]:
    place(fx, impact(), t, g)

# final chord sparkle
for m, dt, g in [(74, 0.0, 0.22), (81, 0.12, 0.18), (86, 0.24, 0.14), (90, 0.36, 0.10)]:
    place(bells, bell(m, 4.5, 1.6), 86.0 + dt, g, pan=(m - 82) / 12)

# typing clicks (match the typed text in index.html)
ticks = bus()
for i in range(7):
    place(ticks, tick(), 0.8 + 0.17 * i, 0.12, pan=-0.1)
for i in range(19):
    place(ticks, tick(), 2.5 + 0.065 * i, 0.08, pan=0.1)
for i in range(7):
    place(ticks, tick(), 84.2 + 0.14 * i, 0.11)

# ---------------------------------------------------------------- mix
pad *= duck
bass *= duck ** 0.7
arp *= duck ** 0.3


def reverb(x, secs=2.8, damp=5000):
    n = int(secs * SR)
    t = np.arange(n) / SR
    ir = np.vstack([lp(rng.standard_normal(n), damp) * np.exp(-t / (secs / 5.5)) for _ in range(2)])
    ir[:, : int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    return np.vstack([fftconvolve(x[c], ir[c])[:N] for c in range(2)])


send = pad * 0.35 + arp * 0.45 + bells * 0.8 + fx * 0.5 + drums * 0.08 + ticks * 0.3
wet = reverb(send)

dry = pad * 1.0 + arp * 0.9 + bass * 1.0 + drums * 1.0 + bells * 0.8 + fx * 0.9 + ticks * 1.0
mix = dry + wet * 0.55
mix = np.vstack([hp(mix[c], 28) for c in range(2)])

t = np.arange(N) / SR
mix *= np.minimum(t / 0.3, 1) * np.clip((DUR - t) / 1.2, 0, 1)
# gentle soft-clip on the top 0.05 % of peaks, then peak-normalise to -1 dBFS
mix /= np.percentile(np.abs(mix), 99.95)
mix = np.tanh(mix * 0.9)
mix *= 10 ** (-1.0 / 20) / np.max(np.abs(mix))

for name, b in [("pad", pad), ("arp", arp), ("bass", bass), ("drums", drums), ("fx", fx), ("bells", bells), ("wet", wet)]:
    print(f"{name:6s} rms {20 * np.log10(np.sqrt((b ** 2).mean()) + 1e-12):6.1f} dB")
for a, b in [(0, 6), (6, 14), (14, 26), (26, 36), (36, 52), (52, 68), (68, 72), (72, 84), (84, 86), (86, 91)]:
    seg = mix[:, int(a * SR) : int(b * SR)]
    print(f"{a:3d}-{b:3d}s  rms {20 * np.log10(np.sqrt((seg ** 2).mean())):6.1f} dBFS")

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
wavfile.write(out, SR, (mix.T * 32767).astype(np.int16))
print("wrote", out)
