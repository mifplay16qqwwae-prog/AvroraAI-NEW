import argparse
import shutil
import sys
from pathlib import Path

from src.animation.renderer import FrameRenderer
from src.audio.sound_fx import SoundDesigner
from src.audio.tts_engine import RussianVoiceSynthesizer
from src.config import StudioConfig
from src.story.gemini_writer import GeminiStoryGenerator
from src.utils.logger import get_logger
from src.video.composer import VideoComposer

logger = get_logger("AvroraStudio")


def run_studio(topic: str | None = None, keep_temp: bool = False) -> Path:
    config = StudioConfig()

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg не найден в системе! Установите ffmpeg перед запуском.")

    if config.temp_dir.exists():
        shutil.rmtree(config.temp_dir)
    config.temp_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = config.temp_dir / "frames"

    writer = GeminiStoryGenerator(config)
    script = writer.generate_script(topic_hint=topic)

    tts = RussianVoiceSynthesizer(config)
    turns = tts.synthesize_episode(script)

    raw_end = max((t.start_time + t.duration for t in turns), default=22.0) + 0.8
    total_duration = min(config.max_duration_sec, max(config.min_duration_sec, raw_end))
    logger.info(f"Итоговая длительность мультфильма: {total_duration:.2f} сек")

    sound = SoundDesigner(config)
    master_wav = config.temp_dir / "master_audio.wav"
    sound.build_master_audio(turns, total_duration, master_wav)

    renderer = FrameRenderer(config)
    total_frames = renderer.render_all_frames(script, turns, total_duration, frames_dir)
    logger.info(f"Отрисовано {total_frames} кадров ({config.width}x{config.height} @ {config.fps} FPS)")

    composer = VideoComposer(config)
    mp4_path = composer.compile_mp4(script, turns, frames_dir, master_wav)

    if not keep_temp and config.temp_dir.exists():
        shutil.rmtree(config.temp_dir)

    return mp4_path


def main() -> None:
    parser = argparse.ArgumentParser(description="AvroraAI — автономная студия 2D-мультфильмов")
    parser.add_argument("--topic", type=str, default=None, help="Необязательная тема серии")
    parser.add_argument("--keep-temp", action="store_true", help="Не удалять временные кадры и WAV")
    args = parser.parse_args()

    try:
        out = run_studio(topic=args.topic, keep_temp=args.keep_temp)
        print(f"SUCCESS: {out}")
    except Exception as exc:
        logger.error(f"Сбой генерации: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
