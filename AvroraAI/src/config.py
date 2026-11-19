import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class StudioConfig:
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", "").strip())
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip())

    width: int = field(default_factory=lambda: int(os.getenv("VIDEO_WIDTH", "1080")))
    height: int = field(default_factory=lambda: int(os.getenv("VIDEO_HEIGHT", "1920")))
    fps: int = field(default_factory=lambda: int(os.getenv("VIDEO_FPS", "24")))

    min_duration_sec: float = 20.0
    max_duration_sec: float = 40.0
    target_duration_sec: float = field(default_factory=lambda: float(os.getenv("TARGET_DURATION_SEC", "30")))

    voice_bublik: str = field(default_factory=lambda: os.getenv("VOICE_BUBLIK", "ru-RU-DmitryNeural"))
    voice_pixel: str = field(default_factory=lambda: os.getenv("VOICE_PIXEL", "ru-RU-SvetlanaNeural"))

    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    assets_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    temp_dir: Path = field(init=False)

    min_request_interval_sec: float = 4.5
    max_retries: int = 3

    locations: Dict[str, str] = field(default_factory=lambda: {
        "cyber_room": "Уютная комната геймера и стримера с неоновой подсветкой и мониторами",
        "cafe_wifi": "Современная кофейня с открытым общественным Wi-Fi и столиками у окна",
        "night_city": "Ночной кибер-мегаполис с голограммами, неоновыми вывесками и летающими дронами",
        "space_station": "Орбитальная космическая станция с иллюминатором и видом на Землю",
        "server_vault": "Футуристичный цифровой дата-центр со световыми потоками данных",
    })

    def __post_init__(self) -> None:
        self.assets_dir = self.project_root / "assets"
        out_env = os.getenv("OUTPUT_DIR", "output/ready_to_post")
        self.output_dir = (self.project_root / out_env).resolve()
        self.temp_dir = (self.project_root / "output" / "temp").resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        if self.width < 720 or self.height < 1280:
            raise ValueError(f"Минимальное разрешение 720x1280, указано {self.width}x{self.height}")
        if self.height <= self.width:
            raise ValueError("Формат видео должен быть вертикальным 9:16 (высота > ширины)")
