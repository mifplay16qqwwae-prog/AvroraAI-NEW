import shutil
import unittest
import wave
import numpy as np

from src.animation.renderer import FrameRenderer
from src.audio.sound_fx import SoundDesigner
from src.audio.tts_engine import RenderedTurnAudio
from src.config import StudioConfig
from src.story.gemini_writer import DialogueTurn, EpisodeScript, ScenePlan
from src.video.composer import VideoComposer


class TestAvroraPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.config = StudioConfig()
        self.config.width = 720
        self.config.height = 1280
        self.config.fps = 12

    def test_script_validation(self) -> None:
        script = EpisodeScript(
            title="Тест Wi-Fi",
            hook_caption="Осторожно, Wi-Fi!",
            description="Ролик про Бублика и Пикселя",
            hashtags=["#AvroraVPN", "#мультфильм"],
            scenes=[
                ScenePlan(
                    scene_id=1,
                    location="cafe_wifi",
                    transition="none",
                    show_avrora_badge=False,
                    turns=[
                        DialogueTurn(
                            speaker="bublik",
                            text="Пиксель, почему интернет так тормозит?",
                            bublik_emotion="shocked",
                            bublik_action="panic",
                            sfx="alert",
                        )
                    ],
                ),
                ScenePlan(
                    scene_id=2,
                    location="cyber_room",
                    transition="crossfade",
                    show_avrora_badge=True,
                    turns=[
                        DialogueTurn(
                            speaker="pixel",
                            text="Включаю AvroraVPN — теперь связь защищена и летает!",
                            pixel_emotion="happy",
                            pixel_action="point",
                            sfx="chime",
                        )
                    ],
                ),
            ],
        )
        self.assertEqual(len(script.scenes), 2)

    def test_audio_and_frames_render(self) -> None:
        wav_path = self.config.temp_dir / "test_voice.wav"
        sr = 24000
        t = np.linspace(0, 1.2, int(sr * 1.2), endpoint=False)
        tone = (np.sin(2 * np.pi * 440 * t) * 12000).astype(np.int16)
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(tone.tobytes())

        script = EpisodeScript(
            title="Тестовый выпуск",
            hook_caption="Бублик в сети",
            description="Описание",
            hashtags=["#AvroraVPN"],
            scenes=[
                ScenePlan(
                    scene_id=1,
                    location="cyber_room",
                    turns=[
                        DialogueTurn(
                            speaker="bublik",
                            text="Привет! Проверяем анимацию Бублика!",
                            bublik_emotion="happy",
                            bublik_action="wave",
                            sfx="pop",
                        )
                    ],
                ),
                ScenePlan(
                    scene_id=2,
                    location="space_station",
                    turns=[
                        DialogueTurn(
                            speaker="pixel",
                            text="AvroraVPN работает даже на орбите!",
                            pixel_emotion="idea",
                            pixel_action="jump",
                            sfx="chime",
                        )
                    ],
                ),
            ],
        )

        turns = [
            RenderedTurnAudio(
                scene_id=1,
                turn_index=0,
                speaker="bublik",
                text="Привет! Проверяем анимацию Бублика!",
                wav_path=wav_path,
                start_time=0.2,
                duration=1.2,
                mouth_envelope=[0.7] * 15,
                bublik_emotion="happy",
                pixel_emotion="neutral",
                bublik_action="wave",
                pixel_action="idle",
                sfx="pop",
            ),
            RenderedTurnAudio(
                scene_id=2,
                turn_index=1,
                speaker="pixel",
                text="AvroraVPN работает даже на орбите!",
                wav_path=wav_path,
                start_time=1.6,
                duration=1.2,
                mouth_envelope=[0.8] * 15,
                bublik_emotion="happy",
                pixel_emotion="idea",
                bublik_action="idle",
                pixel_action="jump",
                sfx="chime",
            ),
        ]

        master_wav = self.config.temp_dir / "test_master.wav"
        SoundDesigner(self.config).build_master_audio(turns, 3.0, master_wav)
        self.assertTrue(master_wav.exists())

        frames_dir = self.config.temp_dir / "test_frames"
        n_frames = FrameRenderer(self.config).render_all_frames(script, turns, 3.0, frames_dir)
        self.assertEqual(n_frames, 36)

        if shutil.which("ffmpeg") is not None:
            mp4 = VideoComposer(self.config).compile_mp4(script, turns, frames_dir, master_wav)
            self.assertTrue(mp4.exists())


if __name__ == "__main__":
    unittest.main()
