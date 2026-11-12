"""Deterministic original stereo tone assets; stdlib only, no sample inputs."""
import math
import struct
import wave
from pathlib import Path


def write_tone(path, frequencies, duration=1.0, harmonics=(1.0, 0.25, 0.1), decay=3.0, echo=0.12, gain=0.5, sample_rate=24000):
    """Write bounded 16-bit PCM. Frequencies above Nyquist are rejected; partials are culled.

    duration includes the release and echo tail. Gain is peak amplitude, not perceived loudness.
    This produces a source WAV, not an engine import or an audio-audition receipt.
    """
    if not isinstance(sample_rate, int) or not 8000 <= sample_rate <= 48000:
        raise ValueError('sample_rate must be an integer in [8000,48000]')
    if not frequencies or len(frequencies) > 8 or not harmonics or len(harmonics) > 16:
        raise ValueError('Use 1-8 frequencies and 1-16 harmonic weights')
    values = [*frequencies, *harmonics, duration, decay, echo, gain]
    if any(not math.isfinite(x) for x in values): raise ValueError('All parameters must be finite')
    if not 0.05 <= duration <= 8 or not 0 <= echo <= duration/3 or not 0 <= gain <= 0.9 or not 0 <= decay <= 20:
        raise ValueError('Duration, echo, gain or decay out of bounds')
    if any(f <= 0 or f >= sample_rate/2 for f in frequencies) or any(h < 0 for h in harmonics):
        raise ValueError('Invalid frequency or harmonic weight')
    count = round(duration * sample_rate)
    dry = []
    for i in range(count):
        t = i / sample_rate
        attack = min(1.0, t / 0.018)
        release = min(1.0, (count-1-i) / (sample_rate*0.16))
        envelope = attack * release * math.exp(-decay*t/duration)
        dry.append(envelope * sum(weight * math.sin(2*math.pi*f*(h+1)*t)
                    for f in frequencies for h,weight in enumerate(harmonics) if f*(h+1) < sample_rate/2))
    delay = round(echo*sample_rate)
    frames=[]
    for i,x in enumerate(dry):
        tail = min(1.0, (count-1-i)/(sample_rate*0.12))
        left = x + (0.28*dry[i-delay] if delay and i>=delay else 0)
        right = x + (0.22*dry[i-2*delay] if delay and i>=2*delay else 0)
        frames.extend((left*tail, right*tail))
    peak=max(abs(x) for x in frames) or 1
    pcm=struct.pack('<'+'h'*len(frames),*(round(x/peak*gain*32767) for x in frames))
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(target),'wb') as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(sample_rate); out.writeframes(pcm)
    return {'frames':count,'sample_rate':sample_rate,'channels':2,'peak_limit':gain,'duration_seconds':count/sample_rate}
