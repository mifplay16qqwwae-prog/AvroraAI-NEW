import asyncio
import math
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import List
import numpy as np

from src.config import StudioConfig
from src.story.gemini_writer import EpisodeScript
from src.utils.logger import get_logger

logger = get_logger("TTSEngine")


@dataclass
class RenderedTurnAudio:
    scene_id: int
    turn_index: int
    speaker: str
    text: str
    wav_path: Path
    start_time: float
    duration: float
    mouth_envelope: List[float]
    bublik_emotion: str
    pixel_emotion: str
    bublik_action: str
    pixel_action: str
    sfx: str


class RussianVoiceSynthesizer:
    def __init__(self, config: StudioConfig):
        self.config = config

    async def _synthesize_mp3(self, text: str, voice: str, out_mp3: Path) -> None:
        import edge_tts
        communicate = edge_tts.Communicate(text=text, voice=voice, rate="+6%")
        await communicate.save(str(out_mp3))

    def _mp3_to_wav_and_envelope(self, mp3_path: Path, wav_path: Path) -> tuple[float, List[float]]:
        cmd = [
            "ffmpeg", "-y", "-i", str(mp3_path),
            "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le",
            str(wav_path),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        with wave.open(str(wav_path), "rb") as wf:
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        duration = max(0.4, len(samples) / float(sample_rate))

        total_video_frames = max(1, int(math.ceil(duration * self.config.fps)))
        samples_per_frame = max(1, len(samples) // total_video_frames)

        envelope: List[float] = []
        for idx in range(total_video_frames):
            chunk = samples[idx * samples_per_frame : (idx + 1) * samples_per_frame]
            if len(chunk) == 0:
                envelope.append(0.0)
            else:
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                openness = min(1.0, max(0.0, (rms - 0.015) * 7.5))
                envelope.append(openness)

        return duration, envelope

    def synthesize_episode(self, script: EpisodeScript) -> List[RenderedTurnAudio]:
        results: List[RenderedTurnAudio] = []
        current_time = 0.4

        async def _run_all() -> None:
            nonlocal current_time
            turn_counter = 0
            for scene in script.scenes:
                for turn in scene.turns:
                    voice = (
                        self.config.voice_bublik
                        if turn.speaker == "bublik"
                        else self.config.voice_pixel
                    )
                    mp3_path = self.config.temp_dir / f"turn_{turn_counter:02d}.mp3"
                    wav_path = self.config.temp_dir / f"turn_{turn_counter:02d}.wav"

                    logger.info(f"Озвучка [{turn.speaker}]: {turn.text}")
                    await self._synthesize_mp3(turn.text, voice, mp3_path)
                    duration, envelope = self._mp3_to_wav_and_envelope(mp3_path, wav_path)

                    results.append(
                        RenderedTurnAudio(
                            scene_id=scene.scene_id,
                            turn_index=turn_counter,
                            speaker=turn.speaker,
                            text=turn.text,
                            wav_path=wav_path,
                            start_time=current_time,
                            duration=duration,
                            mouth_envelope=envelope,
                            bublik_emotion=turn.bublik_emotion,
                            pixel_emotion=turn.pixel_emotion,
                            bublik_action=turn.bublik_action,
                            pixel_action=turn.pixel_action,
                            sfx=turn.sfx,
                        )
                    )
                    current_time += duration + 0.28
                    turn_counter += 1

        asyncio.run(_run_all())
        return results
