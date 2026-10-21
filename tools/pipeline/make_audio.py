"""Synthesises Velisect placeholder audio: a rifle shot and a seamless fluorescent hum loop."""
import math
import os
import random
import struct
import wave

OUT = r"C:\Users\adanr\OneDrive\Documents\Unreal Projects\Velisect\SourceArt\Audio"
RATE = 48000
os.makedirs(OUT, exist_ok=True)
rng = random.Random(42)


def write(name, samples):
    peak = max(abs(s) for s in samples) or 1.0
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(s / peak * 0.89 * 32767)) for s in samples))


def lowpass(samples, cutoff):
    a = 1 - math.exp(-2 * math.pi * cutoff / RATE)
    y, out = 0.0, []
    for s in samples:
        y += a * (s - y)
        out.append(y)
    return out


# Rifle shot: sharp crack, a low body thump and a roomy tail.
n = int(0.9 * RATE)
noise = [rng.uniform(-1, 1) for _ in range(n)]
crack = [noise[i] * math.exp(-i / (0.004 * RATE)) for i in range(n)]
body = lowpass([noise[i] * math.exp(-i / (0.05 * RATE)) for i in range(n)], 2500)
thump = [math.sin(2 * math.pi * (70 - 25 * i / n) * i / RATE) * math.exp(-i / (0.07 * RATE)) for i in range(n)]
tail = lowpass([noise[(i * 7) % n] * math.exp(-i / (0.28 * RATE)) for i in range(n)], 900)
shot = [1.0 * crack[i] + 1.6 * body[i] + 1.3 * thump[i] + 0.55 * tail[i] for i in range(n)]
write("S_RifleShot.wav", shot)

# Fluorescent hum: 120 Hz mains buzz with harmonics; every partial completes whole cycles in the loop length.
seconds = 6
n = seconds * RATE
hum = []
for i in range(n):
    t = i / RATE
    s = (0.55 * math.sin(2 * math.pi * 120 * t) + 0.3 * math.sin(2 * math.pi * 240 * t)
         + 0.18 * math.sin(2 * math.pi * 360 * t) + 0.08 * math.sin(2 * math.pi * 600 * t)
         + 0.05 * math.copysign(1.0, math.sin(2 * math.pi * 120 * t)))
    s *= 1 + 0.06 * math.sin(2 * math.pi * 0.5 * t)  # slow waver, 3 full cycles per loop
    hum.append(s)
hiss = lowpass([rng.uniform(-1, 1) for _ in range(n)], 4000)
fade = int(0.5 * RATE)
for i in range(fade):  # crossfade the hiss so the loop point is seamless
    k = i / fade
    hiss[i] = hiss[i] * k + hiss[n - fade + i] * (1 - k)
hum = [hum[i] + 0.04 * hiss[i] for i in range(n)]
write("S_FluorescentHum.wav", hum)
print("audio written", os.listdir(OUT))
