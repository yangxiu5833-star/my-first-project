"""Generate a fuller gentle C-major folk/electronic demo and save it as WAV."""
from pathlib import Path
import numpy as np
from scipy.io import wavfile

SR = 44100
BPM = 74
BEAT = 60.0 / BPM
BARS = 64
TOTAL_SECONDS = BARS * 4 * BEAT

OUT = Path(__file__).resolve().parents[1] / "audio" / "lake_song_demo.wav"
OUT.parent.mkdir(parents=True, exist_ok=True)

# A warmer four-chord palette for a lake-themed folk song.
CHORDS = {
    "C": [60, 64, 67],
    "Am": [57, 60, 64],
    "F": [53, 57, 60],
    "G": [55, 59, 62],
    "Em": [52, 55, 59],
}

# Song form: intro -> verse -> chorus -> bridge -> final chorus -> outro.
FORM = [
    "C", "Am", "F", "G",                         # 1-4 intro
    "C", "Am", "F", "G", "C", "Am", "F", "G", # 5-12 verse
    "Em", "Am", "F", "G",                         # 13-16 verse lift
    "C", "G", "Am", "F", "C", "G", "F", "G",   # 17-24 chorus
    "C", "G", "Am", "F", "C", "G", "F", "G",   # 25-32 chorus
    "Am", "Em", "F", "C", "Am", "Em", "F", "G", # 33-40 bridge
    "C", "G", "Am", "F", "C", "G", "F", "G",   # 41-48 final chorus
    "C", "G", "Am", "F", "C", "G", "F", "G",   # 49-56 final chorus lift
    "C", "Am", "F", "G", "C", "Am", "F", "C",   # 57-64 outro
]

# Melody phrases in C major. Each tuple is (MIDI note, beats).
VERSE = [
    (60, 1), (62, 1), (64, 2),
    (64, 1), (62, 1), (60, 2),
    (60, 1), (64, 1), (65, 2),
    (67, 1), (65, 1), (64, 2),
]

CHORUS = [
    (67, 1), (69, 1), (72, 2),
    (72, 1), (69, 1), (67, 2),
    (65, 1), (67, 1), (69, 2),
    (67, 1), (65, 1), (64, 2),
]

BRIDGE = [
    (69, 2), (67, 1), (64, 1),
    (65, 2), (64, 1), (62, 1),
    (64, 1), (67, 1), (69, 2),
    (67, 2), (64, 2),
]

OUTRO = [
    (67, 2), (65, 1), (64, 1),
    (62, 2), (60, 2),
]


def midi_to_hz(note):
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def add_tone(audio, start_beat, duration_beats, note, amplitude, waveform="soft"):
    start = int(start_beat * BEAT * SR)
    length = int(duration_beats * BEAT * SR)
    if start >= len(audio) or length <= 0:
        return
    end = min(start + length, len(audio))
    n = end - start
    t = np.arange(n) / SR
    f = midi_to_hz(note)

    if waveform == "soft":
        wave = (
            np.sin(2 * np.pi * f * t)
            + 0.20 * np.sin(4 * np.pi * f * t)
            + 0.06 * np.sin(6 * np.pi * f * t)
        )
        wave /= 1.26
    elif waveform == "pluck":
        wave = np.sin(2 * np.pi * f * t) * np.exp(-2.8 * t)
    else:
        wave = np.sin(2 * np.pi * f * t)

    attack = min(int(0.05 * SR), n // 3)
    release = min(int(0.22 * SR), n // 3)
    env = np.ones(n)
    if attack:
        env[:attack] = np.linspace(0, 1, attack)
    if release:
        env[-release:] *= np.linspace(1, 0, release)
    audio[start:end] += amplitude * wave * env


def add_chord(audio, bar, chord_name, strength=1.0):
    start = bar * 4
    notes = CHORDS[chord_name]
    for note in notes:
        add_tone(audio, start, 4, note, 0.055 * strength, "soft")
        add_tone(audio, start + 2, 2, note + 12, 0.018 * strength, "soft")


def add_melody(audio, start_bar, bars, phrase, octave=0, amplitude=0.14):
    for bar_offset in range(bars):
        local = 0.0
        for note, beats in phrase:
            add_tone(
                audio,
                (start_bar + bar_offset) * 4 + local,
                beats * 0.90,
                note + octave,
                amplitude,
                "soft",
            )
            local += beats


def add_arpeggio(audio, start_bar, bars, amplitude=0.035):
    for bar_offset in range(bars):
        chord_name = FORM[start_bar + bar_offset]
        notes = CHORDS[chord_name]
        pattern = [notes[0], notes[1], notes[2], notes[1]]
        for beat, note in enumerate(pattern):
            add_tone(
                audio,
                (start_bar + bar_offset) * 4 + beat,
                0.72,
                note + 12,
                amplitude,
                "pluck",
            )


def add_bass(audio, start_bar, bars, amplitude=0.055):
    for bar_offset in range(bars):
        root = CHORDS[FORM[start_bar + bar_offset]][0] - 12
        bar = start_bar + bar_offset
        add_tone(audio, bar * 4, 1.5, root, amplitude, "sine")
        add_tone(audio, bar * 4 + 2, 0.9, root, amplitude * 0.55, "sine")


def add_ambient_fifth(audio, start_bar, bars):
    """Very quiet high fifths to give the arrangement an airy lake-like shimmer."""
    for bar_offset in range(bars):
        chord_name = FORM[start_bar + bar_offset]
        top = CHORDS[chord_name][2] + 12
        add_tone(
            audio,
            (start_bar + bar_offset) * 4 + 1.5,
            1.8,
            top,
            0.018,
            "soft",
        )


def main():
    samples = int(TOTAL_SECONDS * SR)
    audio = np.zeros(samples, dtype=np.float64)

    # Harmony throughout the song, with a small dynamic arc by section.
    for bar, chord_name in enumerate(FORM):
        if bar < 4:
            strength = 0.72
        elif bar < 16:
            strength = 0.88
        elif bar < 32:
            strength = 1.00
        elif bar < 40:
            strength = 0.82
        elif bar < 56:
            strength = 1.08
        else:
            strength = 0.68
        add_chord(audio, bar, chord_name, strength)

    # Intro: sparse arpeggio and atmosphere.
    add_arpeggio(audio, 0, 4, 0.030)
    add_ambient_fifth(audio, 0, 4)

    # Verse: intimate melody, gentle pulse.
    add_arpeggio(audio, 4, 12, 0.032)
    add_bass(audio, 4, 12, 0.045)
    add_melody(audio, 4, 12, VERSE, amplitude=0.115)

    # Chorus: wider melody and stronger low end.
    add_arpeggio(audio, 16, 16, 0.040)
    add_bass(audio, 16, 16, 0.060)
    add_melody(audio, 16, 16, CHORUS, octave=0, amplitude=0.155)
    add_ambient_fifth(audio, 16, 16)

    # Bridge: pull back before the final chorus.
    add_arpeggio(audio, 32, 8, 0.026)
    add_bass(audio, 32, 8, 0.042)
    add_melody(audio, 32, 8, BRIDGE, amplitude=0.105)

    # Final chorus: octave lift for a clear climax.
    add_arpeggio(audio, 40, 16, 0.045)
    add_bass(audio, 40, 16, 0.065)
    add_melody(audio, 40, 16, CHORUS, octave=12, amplitude=0.145)
    add_ambient_fifth(audio, 40, 16)

    # Outro: gradually return to the quiet opening mood.
    add_arpeggio(audio, 56, 8, 0.022)
    add_melody(audio, 56, 8, OUTRO, amplitude=0.085)

    # Gentle fade-in/out and normalization.
    fade = int(1.8 * SR)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(audio))
    if peak:
        audio = audio / peak * 0.86

    stereo = np.column_stack((audio, audio * 0.97))
    wavfile.write(OUT, SR, np.int16(stereo * 32767))
    print(f"Generated: {OUT}")
    print(f"Duration: {TOTAL_SECONDS:.1f} seconds, tempo: {BPM} BPM, key: C major")
    print("Form: intro -> verse -> chorus -> bridge -> final chorus -> outro")


if __name__ == "__main__":
    main()
