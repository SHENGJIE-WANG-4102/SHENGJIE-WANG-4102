"""Synthesize the 75 s soundtrack (numpy/scipy, no samples).

128 BPM, 40 bars. F major for the intro and Opus, lifting to G major when
Sonnet arrives. Every hit below is placed on the same beat numbers that
index.html uses (`data-in` values are beats), so cuts, counters, stamps and
wipes all have a sound on the frame they happen.

    python3 tools/music.py build/music.wav
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sawtooth, sosfilt

SR = 48000
BPM = 128
BEAT = 60 / BPM
BEATS = 160
DUR = BEATS * BEAT
N = int(SR * DUR)
rng = np.random.default_rng(55)


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
    "Fsus2": [53, 60, 65, 67, 72], "F": [53, 60, 65, 69, 72], "C": [48, 55, 64, 67, 72],
    "Csus4": [48, 55, 65, 67, 72], "Dm": [50, 57, 62, 65, 69], "Bb": [46, 53, 62, 65, 70],
    "D": [50, 57, 66, 69, 74], "G": [55, 62, 67, 71, 74], "Em": [52, 59, 64, 67, 71],
    "Dsus4": [50, 57, 67, 69, 74], "Gadd9": [43, 55, 62, 67, 69, 71, 74],
}
ROOT = {"Fsus2": 41, "F": 41, "C": 36, "Csus4": 36, "Dm": 38, "Bb": 34, "D": 38, "G": 43, "Em": 40, "Dsus4": 38, "Gadd9": 43}

CH = [(0, 8, "Fsus2"), (16, 20, "F"), (20, 24, "C"), (24, 28, "Dm"), (28, 32, "Bb"), (32, 34, "Csus4"), (34, 36, "C")]
for k, b in enumerate(range(36, 84, 4)):
    CH.append((b, b + 4, ["F", "C", "Dm", "Bb"][k % 4]))
CH += [(84, 86, "Bb"), (86, 88, "D")]
for k, b in enumerate(range(88, 116, 4)):
    CH.append((b, b + 4, ["G", "D", "Em", "C"][k % 4]))
CH += [(116, 120, "C"), (120, 124, "D"), (124, 128, "Em"), (128, 132, "C"), (132, 134, "Dsus4"), (134, 136, "D"),
       (136, 140, "C"), (140, 144, "G"), (144, 148, "D"), (148, 152, "C"), (152, 160, "Gadd9")]
SLAMS = [(8, "Dm"), (10, "Bb"), (12, "F"), (14, "C")]


def chord_at(b):
    for a, e, c in CH:
        if a <= b < e:
            return c
    for a, c in SLAMS:
        if a <= b < a + 2:
            return c
    return "F"


def kick_on(b):  # same rule as kickOn() in index.html
    return (16 <= b < 124 and not (32 <= b < 36)) or (136 <= b < 152)


pad, stab, arp, bass, drums, fx, ticks, chip = (bus() for _ in range(8))
duck = np.ones(N)


def add_kick(t, level=1.0):
    place(drums, kick(level), t, 0.6)
    i = int(t * SR)
    n = min(int(0.3 * SR), N - i)
    duck[i : i + n] = np.minimum(duck[i : i + n], 1 - 0.6 * level * np.exp(-np.arange(n) / SR / 0.11))


# pads (pumping supersaw), section-dependent brightness
for a, e, c in CH:
    if a < 8:
        cut, lvl = 900, 0.36
    elif a < 36:
        cut, lvl = 2600, 0.30
    elif a < 88:
        cut, lvl = 3200, 0.30
    elif a < 124:
        cut, lvl = 4200, 0.30
    elif a < 136:
        cut, lvl = 1100, 0.40
    elif a < 152:
        cut, lvl = 4200, 0.32
    else:
        cut, lvl = 3000, 0.42
    length = T(e - a)
    att = 1.6 if a < 8 else 0.02
    rel = 2.8 if a >= 152 else 0.25
    for m in V[c]:
        place(pad, supersaw(m, length - (0 if a >= 152 else 0.03), cut, a=att, r=rel), T(a), lvl * (0.8 if m < 50 else 1.0))

# intro: 16th arp opening up from beat 2
for s in range(8, 32):
    b = s / 4
    tones = sorted(x for x in V["Fsus2"] if x >= 60) + [77, 79]
    m = tones[[0, 2, 1, 3, 2, 4, 3, 5][s % 8]]
    place(arp, pluck(m, 0.3, bright=0.3 + 0.7 * (b - 2) / 6), T(b), 0.05 + 0.13 * (b - 2) / 6, pan=0.4 * np.sin(s))

# slams: stab + hit on every word
for b, c in SLAMS:
    for m in V[c] + [V[c][2] + 12]:
        place(stab, supersaw(m, 0.32, 5000, d=0.15, s=0.5, r=0.2), T(b), 0.34)
    add_kick(T(b), 1.0)
    place(drums, clap(), T(b), 0.3)
    place(drums, crash(), T(b), 0.12)
    place(fx, impact(1.2), T(b), 0.35)
    place(bass, bass_note(ROOT[c] - 12 if ROOT[c] > 40 else ROOT[c], T(1.6)), T(b), 0.5)
    place(fx, swish(0.25), T(b + 0.25), 0.05)
place(fx, riser(T(2)), T(6), 0.2)
place(fx, riser(T(1)), T(15), 0.18)

# main arps: 8ths in the lineup/Opus, 16ths in Sonnet
PAT = [0, 2, 4, 1, 3, 5, 2, 4]
for s in range(int(BEATS * 4)):
    b = s / 4
    if 24 <= b < 32 or 36 <= b < 86:
        if s % 2:
            continue
        lvl = 0.13
    elif 88 <= b < 116 or 140 <= b < 152:
        lvl = 0.12 if s % 2 else 0.16
    else:
        continue
    c = chord_at(b)
    tones = sorted({x for x in V[c] if x >= 60}) + [x + 12 for x in sorted({x for x in V[c] if x >= 60})]
    m = tones[PAT[(s // (1 if b >= 88 else 2)) % 8] % len(tones)]
    place(arp, pluck(m, 0.28, bright=1.0), T(b), lvl, pan=0.45 * np.sin(s * 0.7))

# bass
for s in range(BEATS * 2):
    b = s / 2
    c = chord_at(b)
    r = ROOT[c]
    if 16 <= b < 32 or 136 <= b < 152:
        if s % 2 == 1:  # house off-beat bass
            place(bass, bass_note(r, T(0.42)), T(b), 0.42)
    elif 36 <= b < 86 or 88 <= b < 124:
        oct_ = 12 if s % 8 == 7 else 0
        place(bass, bass_note(r + oct_, T(0.44)), T(b), 0.40 if s % 2 else 0.30)
    elif 86 <= b < 88 and s % 2 == 0:
        place(bass, bass_note(r, T(0.9)), T(b), 0.4)
for b, m in [(124, 40), (128, 36), (132, 38)]:
    place(bass, bass_note(m, T(3.9), drive=1.1), T(b), 0.32)
place(bass, bass_note(31, T(7.5), drive=1.2), T(152), 0.42)

# drums
for b in range(BEATS):
    t = T(b)
    if kick_on(b):
        add_kick(t)
        if (36 <= b < 124 or 140 <= b < 152) and b % 2 == 1:
            place(drums, clap(), t, 0.26)
        place(drums, hat(True), t + BEAT / 2, 0.07, pan=0.2)
    if 64 <= b < 72 or 88 <= b < 124 or 140 <= b < 152:
        for q in (0.25, 0.75):
            place(drums, hat(), t + q * BEAT, 0.05, pan=-0.3)
# snare build into Opus, fill into Sonnet, roll into the finale
for k in range(16):
    place(drums, snare(0.4 + 0.6 * k / 15), T(32 + k * 0.25), 0.18)
for k in range(8):
    place(drums, snare(0.5 + 0.5 * k / 7), T(34 + k * 0.125 + 1), 0.16)
for k in range(8):
    place(drums, snare(0.6 + 0.4 * k / 7), T(86 + k * 0.25), 0.16)
for k in range(16):
    place(drums, snare(0.3 + 0.7 * k / 15), T(134 + k * 0.125), 0.15)
for b in (16, 36, 88, 140):
    place(drums, crash(), T(b), 0.16)

# ---------------------------------------------------------------- picture sync
# family dots pop (big = low, small = high)
for b0 in (4, 137):
    for i, m in enumerate((65, 72, 81)):
        place(fx, pop(m), T(b0 + i), 0.28)
# drops / impacts on section cuts
for b, g in [(16, 0.55), (36, 0.5), (88, 0.5), (124, 0.35), (140, 0.6), (152, 0.45)]:
    place(fx, impact(), T(b), g)
for b in (16, 36, 88, 140):
    for m in V[chord_at(b)] + [V[chord_at(b)][2] + 12]:
        place(stab, supersaw(m, 0.3, 5500, d=0.12, s=0.5, r=0.25), T(b), 0.24)
# colour-wipe swells into the downbeat
for b in (35, 87, 123, 135):
    place(fx, riser(T(1)), T(b), 0.22)
place(fx, riser(T(4)), T(32), 0.16)
place(fx, riser(T(4)), T(84), 0.14)
place(fx, riser(T(4)), T(132), 0.2)
# lineup columns + stamps
for i, m in enumerate((72, 76, 79)):
    place(fx, bell(m, 1.4, 1.2), T(24 + i), 0.12, pan=-0.5 + 0.5 * i)
for b in (28, 112):
    place(fx, thud(), T(b), 0.4)


def count_ticks(b0, frm, to, dur, ease_out=True, maxn=36):
    """One tick each time the on-screen counter passes a step."""
    step = (to - frm) / min(maxn, abs(to - frm))
    ts = np.linspace(0, dur, 2000)
    p = ts / dur
    v = frm + (to - frm) * ((1 - (1 - p) ** 3) if ease_out else p)
    k = np.floor((v - frm) / step)
    for j in np.nonzero(np.diff(k))[0]:
        place(ticks, tick(), T(b0) + ts[j + 1], 0.10, pan=0.15 * rng.standard_normal())


count_ticks(48, 0, 40, 0.9)
count_ticks(64, 0, 30, 0.8)
count_ticks(80, 0, 2000, 1.0)
count_ticks(96, 0, 30, 0.7)
count_ticks(98, 0, 30, 0.7)
# benchmark groups: a rising zip per group
for b in (53, 55, 57):
    place(fx, zip_(1.0, 300, 1100), T(b) + 0.2, 0.06)
# race: whoosh at the start, dings as lanes finish
place(fx, zip_(0.8, 200, 1600), T(66), 0.07)
for t, m in [(T(66) + 0.74, 91), (T(66) + 1.85, 86), (T(66) + 2.4, 79)]:
    place(fx, bell(m, 1.0, 1.0), t, 0.10)
# price: strike swish then a bright hit on the new number
for b in (73.5, 75.5, 77.5):
    place(fx, swish(0.28), T(b), 0.08)
for b, m in [(74, 84), (76, 86), (78, 88)]:
    place(fx, bell(m, 1.2, 2.2), T(b), 0.12)
# head-to-head rows
for i, b in enumerate((106, 107, 108, 109)):
    place(fx, pluck(76 + 2 * i, 0.4, 0.6), T(b), 0.12)

# chiptune bars (Pokemon fact): pulse-wave arps + badge blips + clear fanfare
for s in range(32):
    b = 116 + s / 4
    c = chord_at(b)
    tones = sorted({x for x in V[c] if x >= 60}) + [x + 12 for x in sorted({x for x in V[c] if x >= 60})]
    place(chip, pulse(tones[[0, 1, 2, 3, 2, 1, 3, 4][s % 8] % len(tones)], T(0.24), 0.25), T(b), 0.07)
for i in range(8):
    place(chip, pulse(79 + [0, 2, 4, 5, 7, 9, 11, 12][i], T(0.4), 0.125), T(117 + i * 0.5), 0.09)
for i, m in enumerate((79, 83, 86, 91, 86, 91)):
    place(chip, pulse(m, T(0.5 if i < 5 else 1.6), 0.5), T(121 + i * 0.25), 0.09)

# haiku: typing, loading blips
for i in range(18):
    place(ticks, tick(), T(125) + i / 24, 0.09)
for b in range(127, 134):
    place(fx, blip(1568 if b % 2 else 1175), T(b), 0.07)
place(fx, pop(84), T(134), 0.25)
# finale typing + closing sparkle
for i in range(57):
    place(ticks, tick(), T(148) + i / 60, 0.05)
for m, dt, g in [(79, 0.0, 0.16), (86, 0.12, 0.13), (91, 0.24, 0.10), (95, 0.36, 0.08)]:
    place(fx, bell(m, 4.0, 1.4), T(152) + dt, g, pan=(m - 87) / 12)

# ---------------------------------------------------------------- mix
pad *= duck
stab *= duck ** 0.3
bass *= duck ** 0.8
arp *= duck ** 0.4
chip *= duck ** 0.3


def reverb(x, secs=2.2, damp=6000):
    n = int(secs * SR)
    t = np.arange(n) / SR
    ir = np.vstack([lp(rng.standard_normal(n), damp) * np.exp(-t / (secs / 5.5)) for _ in range(2)])
    ir[:, : int(0.01 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    return np.vstack([fftconvolve(x[c], ir[c])[:N] for c in range(2)])


# bus gains (drums are the reference)
pad *= 1.4
stab *= 1.5
arp *= 2.0
chip *= 2.6
drums *= 0.85
send = pad * 0.25 + stab * 0.4 + arp * 0.4 + fx * 0.45 + chip * 0.25 + drums * 0.05 + ticks * 0.2
wet = reverb(send)
dry = pad + stab + arp + bass + drums + fx * 0.9 + ticks + chip
mix = dry + wet * 0.45
mix = np.vstack([hp(mix[c], 30) for c in range(2)])

t = np.arange(N) / SR
mix *= np.minimum(t / 0.05, 1) * np.clip((DUR - t) / 2.0, 0, 1)
mix /= np.percentile(np.abs(mix), 99.95)
mix = np.tanh(mix * 0.95)
mix *= 10 ** (-1.0 / 20) / np.max(np.abs(mix))

for name, b in [("pad", pad), ("stab", stab), ("arp", arp), ("bass", bass), ("drums", drums), ("fx", fx), ("chip", chip), ("ticks", ticks), ("wet", wet)]:
    print(f"{name:6s} rms {20 * np.log10(np.sqrt((b ** 2).mean()) + 1e-12):6.1f} dB")
for a, b, label in [(0, 8, "intro"), (8, 16, "slams"), (16, 36, "title+lineup"), (36, 88, "opus"), (88, 116, "sonnet"),
                    (116, 124, "chip"), (124, 136, "haiku"), (136, 152, "finale"), (152, 160, "outro")]:
    seg = mix[:, int(T(a) * SR) : int(T(b) * SR)]
    print(f"{label:13s} {T(a):5.1f}-{T(b):5.1f}s  rms {20 * np.log10(np.sqrt((seg ** 2).mean())):6.1f} dBFS")

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
wavfile.write(out, SR, (mix.T * 32767).astype(np.int16))
print("wrote", out)
