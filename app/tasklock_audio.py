"""Original, royalty-free synthesized TaskLock reminder tones (no external audio assets)."""
from pathlib import Path
from math import sin, pi, exp
import struct
import wave

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
    "Brass Fanfare": [(0,.34,392),(.38,.34,523),(.76,.38,659),(1.22,.72,784),(2.10,.30,659),(2.48,.78,784)],
    "Trombone Groove": [(0,.38,196),(.47,.28,233.08),(.88,.50,261.63),(1.53,.26,196),(1.88,.66,293.66)],
    "Drumline Call": [(0,.17,110),(.23,.14,170),(.43,.16,110),(.64,.14,170),(.86,.25,98),(1.26,.15,170),(1.49,.14,170),(1.75,.34,110)],
    "Synthwave Lift": [(0,.22,261.63),(.24,.22,329.63),(.48,.22,392),(.72,.35,523.25),(1.19,.22,392),(1.45,.22,523.25),(1.72,.62,659.25)],
    "String Serenade": [(0,.80,392),(.65,.85,440),(1.35,.90,523.25),(2.10,1.05,587.33)],
    "Piano Cascade": [(0,.65,659.25),(.26,.65,523.25),(.52,.65,440),(.78,.65,392),(1.16,.90,523.25),(1.58,1.05,659.25)],
    "Marimba Steps": [(0,.28,523.25),(.32,.28,659.25),(.64,.38,783.99),(1.10,.28,659.25),(1.43,.30,523.25),(1.80,.62,392)],
    "Electric Guitar Hook": [(0,.31,329.63),(.35,.31,392),(.73,.52,440),(1.36,.22,392),(1.63,.29,329.63),(2.02,.67,523.25)],
}
INSTRUMENTS = {
    "Digital Pulse": "digital", "Soft Chime": "bell", "Urgent Alert": "digital",
    "Neon Flight": "synth", "Midnight Bell": "bell", "Blue Horizon": "synth",
    "Arcade Dash": "digital", "Sunrise": "bell", "Cyber Signal": "digital",
    "Orbit Rise": "synth", "Deep Focus": "soft", "Aurora Ping": "bell",
    "Brass Fanfare": "trumpet", "Trombone Groove": "trombone",
    "Drumline Call": "drums", "Synthwave Lift": "synth",
    "String Serenade": "strings", "Piano Cascade": "piano",
    "Marimba Steps": "marimba", "Electric Guitar Hook": "guitar",
}
TONES = tuple(SCORES) + ("Custom WAV", "Silent")


def _voice(instrument: str, frequency: float, x: float) -> float:
    """Small additive synth; approximates timbres, not sampled real instruments."""
    p = 2 * pi * frequency * x
    if instrument == "trumpet":
        return sin(p) + .62 * sin(2*p) + .28 * sin(3*p) + .12 * sin(4*p)
    if instrument == "trombone":
        return sin(p) + .52 * sin(2*p) + .22 * sin(3*p)
    if instrument == "drums":
        falling = 2*pi*frequency*(x + .09*(1-exp(-18*x)))
        return 1.3*sin(falling)*exp(-11*x) + .48*sin(2*pi*3700*x)*sin(2*pi*1700*x)*exp(-24*x)
    if instrument == "synth":
        return sin(p) + .35*sin(2*p) + .22*sin(3*p)
    if instrument == "strings":
        vibrato = .0035*sin(2*pi*5.4*x)
        return sin(p + vibrato*p) + .32*sin(2*p) + .16*sin(3*p)
    if instrument == "piano":
        return (sin(p) + .23*sin(2*p) + .10*sin(3*p))*exp(-2.1*x)
    if instrument == "marimba":
        return (sin(p) + .35*sin(3.9*p) + .13*sin(6.2*p))*exp(-5*x)
    if instrument == "guitar":
        return (sin(p) + .48*sin(2*p) + .25*sin(3*p) + .12*sin(4*p))*exp(-1.6*x)
    if instrument == "bell":
        return sin(p) + .18*sin(2.4*p)
    if instrument == "soft":
        return sin(p) + .05*sin(2*p)
    return sin(p) + .11*sin(2*p)


def create_tone(name: str, destination: Path, volume: float = .44):
    score = SCORES[name]
    instrument = INSTRUMENTS[name]
    rate = 22050
    duration = max(start + length for start, length, _ in score) + .18
    pcm = bytearray()
    for i in range(int(rate * duration)):
        t = i / rate
        sample = 0.0
        for start, length, freq in score:
            x = t - start
            if 0 <= x < length:
                attack = .075 if instrument == "strings" else (.003 if instrument in ("drums","marimba") else .018)
                release = .12 if instrument in ("drums","marimba") else .17
                fade = min(1, x / attack) * min(1, (length-x) / release)
                sample += fade * _voice(instrument, freq, x)
        pcm.extend(struct.pack('<h', int(max(-1, min(1, sample * volume * .42)) * 32767)))
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
