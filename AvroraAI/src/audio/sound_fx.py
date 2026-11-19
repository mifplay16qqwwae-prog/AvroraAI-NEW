import wave
from pathlib import Path
from typing import List
import numpy as np

from src.audio.tts_engine import RenderedTurnAudio
from src.config import StudioConfig


class SoundDesigner:
    """Генерирует фоновую музыку, звуковые эффекты и сводит единую звуковую дорожку эпизода."""

    def __init__(self, config: StudioConfig, sample_rate: int = 24000):
        self.config = config
        self.sr = sample_rate

    def _generate_sfx(self, sfx_type: str) -> np.ndarray:
        if sfx_type == "pop":
            dur = 0.14
            t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
            freq = np.linspace(320, 920, len(t))
            env = np.exp(-t * 24)
            return (0.35 * np.sin(2 * np.pi * np.cumsum(freq) / self.sr) * env).astype(np.float32)

        if sfx_type == "whoosh":
            dur = 0.35
            t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
            noise = np.random.uniform(-1.0, 1.0, len(t))
            env = np.sin(np.pi * t / dur) ** 2
            kernel = np.ones(18) / 18.0
            filtered = np.convolve(noise, kernel, mode="same")
            return (0.32 * filtered * env).astype(np.float32)

        if sfx_type == "alert":
            dur = 0.32
            t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
            tone = np.where(t < 0.16, np.sin(2 * np.pi * 660 * t), np.sin(2 * np.pi * 880 * t))
            env = np.exp(-t * 6)
            return (0.28 * tone * env).astype(np.float32)

        if sfx_type == "chime":
            dur = 0.45
            t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
            chord = (
                np.sin(2 * np.pi * 523.25 * t)
                + 0.8 * np.sin(2 * np.pi * 659.25 * t)
                + 0.7 * np.sin(2 * np.pi * 783.99 * t)
            ) / 2.5
            env = np.exp(-t * 5.5)
            return (0.30 * chord * env).astype(np.float32)

        return np.zeros(1, dtype=np.float32)

    def _generate_bg_music(self, total_duration: float) -> np.ndarray:
        n_samples = int(total_duration * self.sr)
        t = np.linspace(0, total_duration, n_samples, endpoint=False)

        chords = [
            [261.63, 329.63, 392.00],
            [220.00, 261.63, 329.63],
            [174.61, 220.00, 261.63],
            [196.00, 246.94, 293.66],
        ]
        bar_idx = (t.astype(int)) % 4
        music = np.zeros(n_samples, dtype=np.float32)

        for idx, notes in enumerate(chords):
            mask = bar_idx == idx
            for freq in notes:
                music[mask] += np.sin(2 * np.pi * freq * t[mask])

        beat_phase = (t * 2.0) % 1.0
        pulse = 0.65 + 0.35 * np.exp(-beat_phase * 6.0)
        music = (music / 3.0) * pulse * 0.085

        fade_len = min(int(0.8 * self.sr), n_samples // 4)
        if fade_len > 0:
            music[:fade_len] *= np.linspace(0.0, 1.0, fade_len)
            music[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)

        return music.astype(np.float32)

    def build_master_audio(self, turns: List[RenderedTurnAudio], total_duration: float, out_wav: Path) -> Path:
        n_samples = int(total_duration * self.sr)
        mix = self._generate_bg_music(total_duration)

        for turn in turns:
            start_idx = int(turn.start_time * self.sr)

            if turn.sfx != "none":
                sfx_data = self._generate_sfx(turn.sfx)
                sfx_start = max(0, start_idx - int(0.1 * self.sr))
                end_sfx = min(n_samples, sfx_start + len(sfx_data))
                mix[sfx_start:end_sfx] += sfx_data[: end_sfx - sfx_start]

            with wave.open(str(turn.wav_path), "rb") as wf:
                raw = wf.readframes(wf.getnframes())
            voice_samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            end_voice = min(n_samples, start_idx + len(voice_samples))
            mix[start_idx:end_voice] *= 0.45
            mix[start_idx:end_voice] += voice_samples[: end_voice - start_idx] * 0.95

        peak = float(np.max(np.abs(mix))) if len(mix) > 0 else 1.0
        if peak > 0.95:
            mix = mix * (0.95 / peak)

        pcm16 = (mix * 32767.0).astype(np.int16)
        with wave.open(str(out_wav), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sr)
            wf.writeframes(pcm16.tobytes())

        return out_wav
