import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from src.audio.tts_engine import RenderedTurnAudio
from src.config import StudioConfig
from src.story.gemini_writer import EpisodeScript
from src.utils.logger import get_logger

logger = get_logger("VideoComposer")


def _format_srt_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hrs = ms // 3_600_000
    ms %= 3_600_000
    mins = ms // 60_000
    ms %= 60_000
    secs = ms // 1000
    ms %= 1000
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


class VideoComposer:
    def __init__(self, config: StudioConfig):
        self.config = config

    def write_srt(self, turns: List[RenderedTurnAudio], srt_path: Path) -> Path:
        lines: List[str] = []
        for idx, turn in enumerate(turns, start=1):
            start_str = _format_srt_timestamp(turn.start_time)
            end_str = _format_srt_timestamp(turn.start_time + turn.duration)
            speaker_name = "Бублик" if turn.speaker == "bublik" else "Пиксель"
            lines.append(f"{idx}\n{start_str} --> {end_str}\n[{speaker_name}] {turn.text}\n")
        srt_path.write_text("\n".join(lines), encoding="utf-8")
        return srt_path

    def compile_mp4(
        self,
        script: EpisodeScript,
        turns: List[RenderedTurnAudio],
        frames_dir: Path,
        master_wav: Path,
    ) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        base_name = f"avrora_cartoon_{stamp}"
        mp4_path = self.config.output_dir / f"{base_name}.mp4"
        srt_path = self.config.output_dir / f"{base_name}.srt"
        meta_path = self.config.output_dir / f"{base_name}.json"

        self.write_srt(turns, srt_path)

        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(self.config.fps),
            "-i", str(frames_dir / "frame_%05d.png"),
            "-i", str(master_wav),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(mp4_path),
        ]

        logger.info(f"Сборка финального MP4 через FFmpeg: {mp4_path.name}")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

        metadata = {
            "video_file": mp4_path.name,
            "srt_file": srt_path.name,
            "resolution": f"{self.config.width}x{self.config.height}",
            "fps": self.config.fps,
            "title": script.title,
            "hook_caption": script.hook_caption,
            "description": script.description,
            "hashtags": script.hashtags,
            "created_at_utc": stamp,
        }
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Готово! Ролик и метаданные сохранены в {self.config.output_dir}")
        return mp4_path
