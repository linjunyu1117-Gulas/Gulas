"""
Taiwan Indie Folk Ambient Music Generator
Uses Karplus-Strong plucked string synthesis + ambient pad layers
Produces a ~3-minute loopable ambient folk track
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, filtfilt
import os

SAMPLE_RATE = 44100
OUTPUT = "/home/user/Gulas/assets/music/taiwan_folk_ambient.wav"

def karplus_strong(freq, duration, decay=0.995, stretch=0.5, sample_rate=SAMPLE_RATE):
    """Plucked string synthesis using Karplus-Strong algorithm."""
    n_samples = int(duration * sample_rate)
    buf_size = int(sample_rate / freq)
    buf = np.random.uniform(-0.5, 0.5, buf_size)
    output = np.zeros(n_samples)
    for i in range(n_samples):
        output[i] = buf[0]
        avg = decay * ((1 - stretch) * buf[0] + stretch * buf[1])
        buf = np.roll(buf, -1)
        buf[-1] = avg
    return output

def envelope(signal, attack=0.01, decay=0.1, sustain=0.7, release=0.3, sample_rate=SAMPLE_RATE):
    """ADSR envelope."""
    n = len(signal)
    env = np.ones(n)
    a = int(attack * sample_rate)
    d = int(decay * sample_rate)
    r = int(release * sample_rate)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if d > 0 and a + d < n:
        env[a:a+d] = np.linspace(1, sustain, d)
    if a + d < n:
        env[a+d:n-r] = sustain
    if r > 0 and r < n:
        env[-r:] = np.linspace(sustain, 0, r)
    return signal * env

def sine_wave(freq, duration, amplitude=0.3, sample_rate=SAMPLE_RATE):
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
    return amplitude * np.sin(2 * np.pi * freq * t)

def pad_tone(freq, duration, amplitude=0.15, sample_rate=SAMPLE_RATE):
    """Soft ambient pad using multiple harmonics with slow vibrato."""
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
    vibrato = 1 + 0.002 * np.sin(2 * np.pi * 0.3 * t)
    wave = (
        amplitude * np.sin(2 * np.pi * freq * vibrato * t) +
        amplitude * 0.5 * np.sin(2 * np.pi * freq * 2 * vibrato * t) +
        amplitude * 0.25 * np.sin(2 * np.pi * freq * 3 * t)
    )
    # Soft attack/release
    attack = int(2.0 * sample_rate)
    release = int(2.0 * sample_rate)
    if len(wave) > attack + release:
        wave[:attack] *= np.linspace(0, 1, attack)
        wave[-release:] *= np.linspace(1, 0, release)
    return wave

def lowpass(signal, cutoff=3000, sample_rate=SAMPLE_RATE):
    b, a = butter(4, cutoff / (sample_rate / 2), btype='low')
    return filtfilt(b, a, signal)

def reverb_simple(signal, room_size=0.4, sample_rate=SAMPLE_RATE):
    """Simple comb filter reverb."""
    delay_ms = [37, 53, 67, 83, 113, 131]
    output = signal.copy().astype(np.float64)
    for d in delay_ms:
        delay_samples = int(d * sample_rate / 1000)
        if delay_samples < len(signal):
            delayed = np.zeros_like(signal, dtype=np.float64)
            delayed[delay_samples:] = signal[:-delay_samples] * room_size
            output += delayed
    peak = np.max(np.abs(output))
    if peak > 0:
        output = output / peak * 0.8
    return output

# ── Pentatonic scale in A minor (A, C, D, E, G) ───────────────────────────────
# Frequencies for guitar fingerpicking melody
PENTATONIC = {
    'A3': 220.00, 'C4': 261.63, 'D4': 293.66, 'E4': 329.63,
    'G4': 392.00, 'A4': 440.00, 'C5': 523.25, 'D5': 587.33,
    'E5': 659.25, 'G5': 783.99,
    'A2': 110.00, 'E3': 164.81, 'G3': 196.00,  # bass strings
}

def note(name, dur, decay=0.996):
    n = int(dur * SAMPLE_RATE)
    sig = karplus_strong(PENTATONIC[name], dur + 1.5, decay=decay)[:n]
    return sig

def silence(dur):
    return np.zeros(int(dur * SAMPLE_RATE))

print("Generating Taiwan Indie Folk Ambient Track...")
print("(Using Karplus-Strong plucked string synthesis)")

# ── Build a 16-bar fingerpicking pattern ──────────────────────────────────────
bpm = 72
beat = 60 / bpm          # seconds per beat
bar  = beat * 4

# Melody phrase A (8 bars)
def phrase_a():
    return np.concatenate([
        note('E4', beat*1.5), note('D4', beat*0.5),
        note('C4', beat*1.0), note('A3', beat*1.0),
        note('E4', beat*2.0),
        note('G4', beat*1.0), note('E4', beat*1.0),
        note('D4', beat*1.5), note('C4', beat*0.5),
        note('A3', beat*3.0),
        silence(beat*1.0),
        note('C4', beat*1.0), note('D4', beat*1.0),
        note('E4', beat*2.0), note('G4', beat*2.0),
        note('A4', beat*4.0),
    ])

# Melody phrase B (8 bars)
def phrase_b():
    return np.concatenate([
        note('A4', beat*2.0), note('G4', beat*1.0), note('E4', beat*1.0),
        note('D4', beat*1.5), note('C4', beat*0.5), note('A3', beat*2.0),
        note('C4', beat*1.0), note('D4', beat*1.0), note('E4', beat*2.0),
        note('G4', beat*4.0),
        note('E4', beat*1.5), note('D4', beat*0.5), note('C4', beat*2.0),
        note('A3', beat*2.0), silence(beat*2.0),
    ])

# Bass pattern (low open strings)
def bass_pattern(bars=4):
    b = []
    for _ in range(bars):
        b.append(note('A2', beat*2.0, decay=0.998))
        b.append(note('E3', beat*1.0, decay=0.998))
        b.append(note('A2', beat*0.5, decay=0.998))
        b.append(note('G3', beat*0.5, decay=0.998))
    return np.concatenate(b)

# Build 3-minute track structure
# Intro (16 bars melody A) → Main (16 bars A+bass) → Bridge (8 bars B) → Outro (8 bars A fade)
print("  Building melody phrases...")
mel_a = phrase_a()
mel_b = phrase_b()
bass_4  = bass_pattern(4)
bass_8  = bass_pattern(8)
bass_16 = bass_pattern(16)

# Pad chords (A minor, C major, G major, D minor progression)
TRACK_DURATION = bar * 48   # ~3 min 12 sec at 72 BPM
print(f"  Track duration: {TRACK_DURATION:.1f}s")

print("  Generating ambient pads...")
pad_am = pad_tone(220.0, TRACK_DURATION, amplitude=0.12)   # A
pad_c  = pad_tone(261.63, TRACK_DURATION, amplitude=0.08)  # C
pad_e  = pad_tone(164.81, TRACK_DURATION, amplitude=0.06)  # E (harmony)

print("  Composing track...")
# Total samples
N = int(TRACK_DURATION * SAMPLE_RATE)

track = np.zeros(N)

# Lay down melody with structure
mel_a_samples = len(mel_a)
mel_b_samples = len(mel_b)
bass_8_samples = len(bass_8)

pos = 0
# Intro: melody A x2 (soft)
for _ in range(2):
    end = min(pos + mel_a_samples, N)
    track[pos:end] += mel_a[:end-pos] * 0.55
    pos = end % N if end < N else N
    if pos >= N: break

# Main: melody A + bass x2
for _ in range(2):
    if pos >= N: break
    end = min(pos + mel_a_samples, N)
    track[pos:end] += mel_a[:end-pos] * 0.7
    # overlap bass
    b_end = min(pos + bass_8_samples, N)
    track[pos:b_end] += bass_8[:b_end-pos] * 0.45
    pos = end % N if end < N else N

# Bridge: melody B + bass
if pos < N:
    end = min(pos + mel_b_samples, N)
    track[pos:end] += mel_b[:end-pos] * 0.65
    b_end = min(pos + bass_8_samples, N)
    track[pos:b_end] += bass_8[:b_end-pos] * 0.4
    pos = end

# Outro: melody A fading
if pos < N:
    end = min(pos + mel_a_samples, N)
    fade = np.linspace(0.6, 0.0, end - pos)
    track[pos:end] += mel_a[:end-pos] * fade

# Add pads across full track
track[:len(pad_am)] += pad_am[:N]
track[:len(pad_c)]  += pad_c[:N]
track[:len(pad_e)]  += pad_e[:N]

print("  Applying reverb and EQ...")
track = lowpass(track, cutoff=8000)
track = reverb_simple(track, room_size=0.35)

# Master fade in/out
fade_in  = int(3.0 * SAMPLE_RATE)
fade_out = int(4.0 * SAMPLE_RATE)
track[:fade_in]  *= np.linspace(0, 1, fade_in)
track[-fade_out:] *= np.linspace(1, 0, fade_out)

# Normalize to -1dB
peak = np.max(np.abs(track))
track = track / peak * 0.89

# Convert to 16-bit PCM
audio = (track * 32767).astype(np.int16)

print(f"  Saving WAV: {OUTPUT}")
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
wavfile.write(OUTPUT, SAMPLE_RATE, audio)

size = os.path.getsize(OUTPUT) / 1024 / 1024
print(f"Done! File: {OUTPUT} ({size:.1f} MB, {TRACK_DURATION:.0f}s)")
