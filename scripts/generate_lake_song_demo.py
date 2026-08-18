"""Generate a gentle C-major folk/electronic demo and save it as WAV."""
from pathlib import Path
import numpy as np
from scipy.io import wavfile

SR = 44100
BPM = 74
BEAT = 60.0 / BPM
BARS = 32
TOTAL_SECONDS = BARS * 4 * BEAT

OUT = Path(__file__).resolve().parents[1] / "audio" / "lake_song_demo.wav"

# C major, gentle folk-style progression.
CHORDS = [
    [60, 64, 67],  # C
    [57, 60, 64],  # Am
    [53, 57, 60],  # F
    [55, 59, 62],  # G
] * 8

# Simple singable melody: MIDI note, beats. None = rest.
MELODY = [
    (60, 1), (62, 1), (64, 1), (67, 1),
    (67, 2), (64, 1), (62, 1),
    (60, 1), (62, 1), (64, 2),
    (67, 1), (69, 1), (67, 2),
    (65, 1), (64, 1), (62, 1), (60, 1),
    (60, 2), (64, 1), (67, 1),
    (69, 1), (67, 1), (64, 2),
    (62, 1), (64, 1), (60, 2),
]


def midi_to_hz(note):
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def add_tone(audio, start_beat, duration_beats, note, amplitude, waveform="sine"):
    start = int(start_beat * BEAT * SR)
    length = int(duration_beats * BEAT * SR)
    if start >= len(audio) or length <= 0:
        return
    end = min(start + length, len(audio))
    n = end - start
    t = np.arange(n) / SR
    f = midi_to_hz(note)

    if waveform == "soft":
        wave = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(4 * np.pi * f * t)
        wave /= 1.22
    else:
        wave = np.sin(2 * np.pi * f * t)

    attack = min(int(0.04 * SR), n // 3)
    release = min(int(0.18 * SR), n // 3)
    env = np.ones(n)
    if attack:
        env[:attack] = np.linspace(0, 1, attack)
    if release:
        env[-release:] *= np.linspace(1, 0, release)
    audio[start:end] += amplitude * wave * env


def main():
    samples = int(TOTAL_SECONDS * SR)
    audio = np.zeros(samples, dtype=np.float64)

    # Warm sustained chords, two beats per chord change.
    for bar in range(BARS):
        chord = CHORDS[bar % len(CHORDS)]
        start_beat = bar * 4
        for note in chord:
            add_tone(audio, start_beat, 4, note, 0.075, "soft")
            add_tone(audio, start_beat + 2, 2, note + 12, 0.025, "sine")

    # Repeating melody phrase with a gentle octave lift every 8 bars.
    beat_pos = 0.0
    for bar in range(BARS):
        octave = 12 if bar >= 16 else 0
        phrase = MELODY[bar % 8 * 3: bar % 8 * 3 + 3]
        if not phrase:
            phrase = MELODY[:3]
        local = 0.0
        for note, beats in phrase:
            add_tone(audio, bar * 4 + local, beats * 0.92, note + octave, 0.16, "soft")
            local += beats
        beat_pos += 4

    # Light pulse/bass on beat 1 of each bar.
    for bar in range(BARS):
        root = CHORDS[bar % 4][0] - 12
        add_tone(audio, bar * 4, 1.6, root, 0.08, "sine")
        add_tone(audio, bar * 4 + 2, 0.8, root, 0.045, "sine")

    # Gentle fade-in/out and normalization.
    fade = int(1.2 * SR)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(audio))
    if peak:
        audio = audio / peak * 0.88

    stereo = np.column_stack((audio, audio * 0.97))
    wavfile.write(OUT, SR, np.int16(stereo * 32767))
    print(f"Generated: {OUT}")
    print(f"Duration: {TOTAL_SECONDS:.1f} seconds, tempo: {BPM} BPM, key: C major")


if __name__ == "__main__":
    main()
