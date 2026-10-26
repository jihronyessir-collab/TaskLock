"""Original royalty-free synthesized TaskLock notification tones (no external assets)."""
from pathlib import Path
from math import sin, pi, exp
import struct
import wave

TONES = (
    "Digital Pulse", "Soft Chime", "Urgent Alert", "Neon Flight", "Midnight Bell",
    "Blue Horizon", "Arcade Dash", "Sunrise", "Cyber Signal", "Orbit Rise",
    "Deep Focus", "Aurora Ping", "Custom WAV", "Silent",
)
SCORES = {
    "Digital Pulse": [(0, .22, 660), (.34, .22, 880), (.68, .27, 990), (1.18, .22, 660), (1.50, .22, 880), (1.83, .38, 1100)],
    "Soft Chime": [(0, .95, 523), (.62, .95, 659), (1.24, 1.1, 784)],
    "Urgent Alert": [(0, .28, 740), (.36, .28, 740), (.72, .30, 988), (1.10, .28, 740), (1.5, .32, 988), (1.92, .32, 988)],
    "Neon Flight": [(0, .28, 392), (.3, .28, 494), (.60, .28, 587), (.92, .40, 784), (1.44, .24, 659), (1.72, .54, 988)],
    "Midnight Bell": [(0, 1.2, 392), (.83, 1.14, 493.88), (1.69, 1.00, 587.33)],
    "Blue Horizon": [(0, .43, 440), (.48, .43, 554), (.96, .44, 659), (1.45, .80, 880)],
    "Arcade Dash": [(0, .14, 660), (.18, .14, 880), (.36, .14, 988), (.54, .14, 1318), (.82, .22, 988), (1.1, .22, 1174), (1.44, .48, 1568)],
    "Sunrise": [(0, .9, 392), (.45, .9, 523), (.90, .95, 659), (1.35, 1.1, 784)],
    "Cyber Signal": [(0,.17,988),(.23,.17,1319),(.52,.34,1047),(1.01,.22,1480)],
    "Orbit Rise": [(0,.35,330),(.36,.35,440),(.72,.35,554),(1.08,.60,740)],
    "Deep Focus": [(0,.75,246.94),(.55,.85,329.63),(1.10,.95,392)],
    "Aurora Ping": [(0,.55,783.99),(.44,.60,1046.50),(1.10,.70,880)],
}


def create_tone(name: str, destination: Path, volume: float = .44):
    score = SCORES[name]
    rate = 22050
    duration = max(start + length for start, length, _ in score) + .18
    pcm = bytearray()
    for i in range(int(rate * duration)):
        t = i / rate
        sample = 0.0
        for start, length, freq in score:
            x = t - start
            if 0 <= x < length:
                fade = min(1, x / .022) * min(1, (length-x) / .17)
                sample += fade * (sin(2*pi*freq*x) + .11*sin(4*pi*freq*x))
        pcm.extend(struct.pack('<h', int(max(-1, min(1, sample * volume * .55)) * 32767)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destination), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(pcm)


def ensure_tones(folder: Path):
    for name in SCORES:
        path = folder / (name.replace(' ', '_') + '.wav')
        if not path.exists():
            create_tone(name, path)
