"""
山水鋼琴 — Shanshui Piano Music Generator
Additive synthesis piano tones in a meditative Chinese pentatonic scale.
Produces a ~3-minute loopable ambient piano track.
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, filtfilt
import os

SAMPLE_RATE = 44100
OUTPUT = "/home/user/Gulas/assets/music/piano_shanshui.wav"

# ── Piano synthesis ────────────────────────────────────────────────────────────
def piano_note(freq, duration, velocity=0.75, sample_rate=SAMPLE_RATE):
    """
    Additive synthesis piano tone.
    - Harmonic series with inharmonicity (B coefficient)
    - Each partial decays independently (higher = faster)
    - Brief noise burst on attack for hammer transient
    """
    n = int(duration * sample_rate)
    t = np.arange(n) / sample_rate

    # Inharmonicity grows with pitch (Railsback curve)
    B = 2.5e-5 * (freq / 130.81) ** 2

    signal = np.zeros(n)
    harmonic_amps = [1.0, 0.55, 0.30, 0.18, 0.10, 0.06, 0.04, 0.025, 0.015]
    for k, base_amp in enumerate(harmonic_amps, start=1):
        f_k = freq * k * np.sqrt(1 + B * k * k)
        # Higher partials decay 3× faster each
        tau = max(0.12, (1.8 + duration * 0.4) / (k ** 0.7))
        env = np.exp(-t / tau)
        signal += base_amp * velocity * env * np.sin(2 * np.pi * f_k * t)

    # Hammer transient: 8ms noise burst
    att = min(int(0.008 * sample_rate), n)
    signal[:att] *= np.linspace(0.0, 1.0, att)

    # Slight de-tuned sympathetic string (octave -2 cents)
    if freq < 700:
        f_sym = freq * 2 * 0.9988
        tau_sym = 0.6
        env_sym = np.exp(-t / tau_sym)
        signal += 0.04 * velocity * env_sym * np.sin(2 * np.pi * f_sym * t)

    return signal


def silence(dur, sample_rate=SAMPLE_RATE):
    return np.zeros(int(dur * sample_rate))


def reverb(signal, room=0.55, sample_rate=SAMPLE_RATE):
    """Feedback delay network reverb (longer tail than original)."""
    delays_ms = [43, 67, 89, 113, 157, 193, 229, 271]
    gains     = [0.70, 0.62, 0.55, 0.48, 0.40, 0.34, 0.28, 0.22]
    wet = np.zeros(len(signal) + int(0.35 * sample_rate), dtype=np.float64)
    wet[:len(signal)] = signal
    for d_ms, g in zip(delays_ms, gains):
        ds = int(d_ms * sample_rate / 1000)
        if ds < len(wet):
            copy_len = min(len(wet) - ds, len(signal))
            wet[ds:ds + copy_len] += signal[:copy_len] * g * room
    wet = wet[:len(signal)]
    peak = np.max(np.abs(wet))
    return wet / peak * 0.88 if peak > 0 else wet


def lowpass(signal, cutoff=7200, sample_rate=SAMPLE_RATE):
    b, a = butter(3, cutoff / (sample_rate / 2), btype='low')
    return filtfilt(b, a, signal)


def highpass(signal, cutoff=40, sample_rate=SAMPLE_RATE):
    b, a = butter(2, cutoff / (sample_rate / 2), btype='high')
    return filtfilt(b, a, signal)


# ── Chinese pentatonic scale (D major pentatonic: D E F# A B) ─────────────────
# Mountain key: gentle, open, like gazing at distant peaks
NOTES = {
    # Low register (left hand)
    'D2': 73.42,  'A2': 110.00, 'D3': 146.83, 'E3': 164.81,
    'F#3': 185.00, 'A3': 220.00, 'B3': 246.94,
    # Mid register (right hand melody)
    'D4': 293.66, 'E4': 329.63, 'F#4': 369.99,
    'A4': 440.00, 'B4': 493.88,
    'D5': 587.33, 'E5': 659.25, 'F#5': 739.99,
    'A5': 880.00, 'B5': 987.77,
}

def n(name, dur, vel=0.72):
    sig = piano_note(NOTES[name], dur + 2.0, velocity=vel)
    length = int(dur * SAMPLE_RATE)
    return sig[:length]


def chord(names, dur, vel=0.60):
    """Arpeggiated chord — stagger each note by 40ms."""
    length = int(dur * SAMPLE_RATE)
    out = np.zeros(length)
    stagger = int(0.04 * SAMPLE_RATE)
    for i, name in enumerate(names):
        sig = piano_note(NOTES[name], dur + 2.0, velocity=vel * (0.9 + 0.1 * (i == 0)))
        offset = i * stagger
        end = min(length, offset + len(sig))
        if end > offset:
            out[offset:end] += sig[:end - offset]
    return out


# ── BPM & bar structure ────────────────────────────────────────────────────────
BPM  = 60
BEAT = 60 / BPM          # 1.0 s per beat
BAR  = BEAT * 4          # 4.0 s per bar

print("Generating 山水鋼琴 Piano Track...")
print(f"  BPM={BPM}  Beat={BEAT:.2f}s  Bar={BAR:.2f}s")


# ── Phrase A — 'Mountain at Dusk' (8 bars) ────────────────────────────────────
# Sparse right-hand melody over wide open space
def phrase_a():
    return np.concatenate([
        # Bar 1-2: opening gesture, one note drifts upward
        n('A4', BEAT * 2.0, 0.65),
        silence(BEAT * 1.0),
        n('D5', BEAT * 1.5, 0.58),
        n('B4', BEAT * 3.5, 0.60),
        silence(BEAT * 1.0),
        # Bar 3-4: step down to rest
        n('A4', BEAT * 1.0, 0.55),
        n('F#4', BEAT * 1.5, 0.52),
        n('E4', BEAT * 1.0, 0.50),
        silence(BEAT * 0.5),
        n('D4', BEAT * 4.0, 0.68),
        # Bar 5-6: ascent, like cranes rising
        silence(BEAT * 1.0),
        n('E4', BEAT * 0.75, 0.55),
        n('F#4', BEAT * 0.75, 0.58),
        n('A4', BEAT * 1.0, 0.62),
        n('B4', BEAT * 1.0, 0.65),
        n('D5', BEAT * 3.5, 0.70),
        silence(BEAT * 1.0),
        # Bar 7-8: descent to close
        n('A4', BEAT * 1.5, 0.60),
        n('F#4', BEAT * 1.0, 0.55),
        n('D4', BEAT * 1.5, 0.58),
        n('A3', BEAT * 4.0, 0.72),
        silence(BEAT * 1.0),
    ])


# ── Phrase B — 'Mist on Water' (8 bars) ──────────────────────────────────────
# More flowing — sixteenth-note ripple figures
def phrase_b():
    eighth = BEAT * 0.5
    return np.concatenate([
        # Bar 1-2: gentle ripple
        n('D5', eighth, 0.52),
        n('E5', eighth, 0.50),
        n('F#5', eighth, 0.55),
        n('E5', eighth, 0.50),
        n('D5', eighth, 0.52),
        n('B4', eighth, 0.48),
        n('A4', BEAT * 2.0, 0.62),
        n('F#4', eighth, 0.48),
        n('E4', eighth, 0.45),
        n('D4', BEAT * 1.0, 0.55),
        silence(BEAT * 1.0),
        n('A4', BEAT * 2.0, 0.60),
        # Bar 3-4: floating echo
        n('B4', BEAT * 1.5, 0.58),
        n('D5', BEAT * 0.5, 0.52),
        n('E5', BEAT * 2.0, 0.65),
        n('F#5', BEAT * 1.5, 0.68),
        silence(BEAT * 0.5),
        n('E5', BEAT * 2.0, 0.62),
        # Bar 5-6: stillness returns
        silence(BEAT * 1.0),
        n('D5', BEAT * 1.5, 0.60),
        n('A4', BEAT * 1.0, 0.55),
        n('F#4', BEAT * 1.5, 0.52),
        n('D4', BEAT * 3.0, 0.65),
        silence(BEAT * 1.0),
        # Bar 7-8: resolving
        n('A3', BEAT * 1.0, 0.60),
        n('D4', BEAT * 1.0, 0.58),
        n('F#4', BEAT * 1.0, 0.55),
        n('A4', BEAT * 1.0, 0.58),
        n('D4', BEAT * 4.0, 0.70),
        silence(BEAT * 1.0),
    ])


# ── Left hand — arpeggiated bass chords (D maj pent) ─────────────────────────
def left_hand_bar(root='D3', style='open'):
    """One bar of left-hand piano (arpeggiated low chord)."""
    if style == 'open':
        return np.concatenate([
            chord(['D2', 'A2', 'D3'], BAR * 1.0, vel=0.50),
        ])
    elif style == 'moving':
        return np.concatenate([
            chord(['D2', 'A2', 'F#3'], BEAT * 2.0, vel=0.48),
            chord(['A2', 'D3', 'A3'], BEAT * 2.0, vel=0.45),
        ])
    elif style == 'high':
        return np.concatenate([
            chord(['A2', 'E3', 'A3'], BEAT * 2.0, vel=0.50),
            chord(['D3', 'A3', 'D4'], BEAT * 2.0, vel=0.48),
        ])


def left_section(bars, style='open'):
    pieces = []
    for i in range(bars):
        s = 'moving' if i % 4 == 2 else ('high' if i % 4 == 3 else 'open')
        pieces.append(left_hand_bar(style=s))
    return np.concatenate(pieces)


# ── Ambient sustain pad (soft sine harmonics, simulate piano pedal resonance) ──
def pedal_tone(freq, dur, amp=0.06, sample_rate=SAMPLE_RATE):
    t = np.linspace(0, dur, int(dur * sample_rate), endpoint=False)
    wave = (
        amp * np.sin(2 * np.pi * freq * t) +
        amp * 0.4 * np.sin(2 * np.pi * freq * 2 * t) +
        amp * 0.2 * np.sin(2 * np.pi * freq * 3 * t)
    )
    att = int(3.0 * sample_rate)
    rel = int(3.0 * sample_rate)
    if len(wave) > att + rel:
        wave[:att] *= np.linspace(0, 1, att)
        wave[-rel:] *= np.linspace(1, 0, rel)
    return wave


# ── Assemble track ─────────────────────────────────────────────────────────────
# Structure: Intro (4 bars silence + A) → Main (A+bass) x2 → Bridge (B+bass)
#            → Return A → Outro fade
# Total: ~3 min 12 sec

TRACK_BARS = 48
TRACK_DURATION = BAR * TRACK_BARS
N = int(TRACK_DURATION * SAMPLE_RATE)

print(f"  Track duration: {TRACK_DURATION:.1f}s  ({TRACK_BARS} bars)")

print("  Building phrases...")
mel_a = phrase_a()
mel_b = phrase_b()
left_8  = left_section(8)
left_16 = left_section(16)

print("  Generating pedal resonance...")
pad_d  = pedal_tone(NOTES['D2'],  TRACK_DURATION, amp=0.055)
pad_a  = pedal_tone(NOTES['A2'],  TRACK_DURATION, amp=0.040)
pad_fs = pedal_tone(NOTES['F#3'], TRACK_DURATION, amp=0.025)

print("  Composing track layout...")
track = np.zeros(N)

pos = 0

def add(sig, at, gain=1.0):
    end = min(at + len(sig), N)
    track[at:end] += sig[:end - at] * gain

# Intro: bars 0-7 — melody A alone (no bass), soft entry
add(mel_a, 0, gain=0.50)
add(mel_a, len(mel_a), gain=0.55)

# Main section: bars 16-31 — A + left hand, fuller
pos = int(BAR * 16 * SAMPLE_RATE)
add(mel_a, pos, gain=0.72)
add(left_8, pos, gain=0.60)
pos += len(mel_a)
add(mel_a, pos, gain=0.75)
add(left_8, pos, gain=0.62)
pos += len(mel_a)

# Bridge: bars 32-39 — phrase B + moving bass
add(mel_b, pos, gain=0.70)
add(left_8, pos, gain=0.58)
pos += len(mel_b)

# Return A: bars 40-47 — gentle fade back
add(mel_a, pos, gain=0.65)
add(left_8, pos, gain=0.50)

# Pedal pad through full track
track[:len(pad_d)]  += pad_d[:N]
track[:len(pad_a)]  += pad_a[:N]
track[:len(pad_fs)] += pad_fs[:N]

print("  Applying reverb and EQ...")
track = highpass(track, cutoff=35)
track = lowpass(track, cutoff=9000)
track = reverb(track, room=0.60)

# Soft fade in/out
fin  = int(4.0 * SAMPLE_RATE)
fout = int(6.0 * SAMPLE_RATE)
track[:fin]  *= np.linspace(0, 1, fin)
track[-fout:] *= np.linspace(1, 0, fout)

# Normalize to -1 dB
peak = np.max(np.abs(track))
track = track / peak * 0.89

audio = (track * 32767).astype(np.int16)

print(f"  Saving: {OUTPUT}")
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
wavfile.write(OUTPUT, SAMPLE_RATE, audio)

size = os.path.getsize(OUTPUT) / 1024 / 1024
print(f"Done! {OUTPUT}  ({size:.1f} MB, {TRACK_DURATION:.0f}s)")
