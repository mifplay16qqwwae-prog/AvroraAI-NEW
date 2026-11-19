import json
import random
import re
import time
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from src.config import StudioConfig
from src.utils.logger import get_logger

logger = get_logger("GeminiWriter")


class DialogueTurn(BaseModel):
    speaker: Literal["bublik", "pixel"]
    text: str = Field(..., min_length=3, max_length=180)
    bublik_emotion: Literal["neutral", "happy", "shocked", "worried", "smug", "idea"] = "neutral"
    pixel_emotion: Literal["neutral", "happy", "shocked", "worried", "smug", "idea"] = "neutral"
    bublik_action: Literal["idle", "wave", "point", "jump", "panic", "walk"] = "idle"
    pixel_action: Literal["idle", "wave", "point", "jump", "panic", "walk"] = "idle"
    sfx: Literal["none", "pop", "whoosh", "alert", "chime"] = "none"


class ScenePlan(BaseModel):
    scene_id: int
    location: Literal["cyber_room", "cafe_wifi", "night_city", "space_station", "server_vault"]
    transition: Literal["none", "crossfade", "slide_left"] = "crossfade"
    show_avrora_badge: bool = False
    turns: List[DialogueTurn] = Field(..., min_length=1, max_length=4)


class EpisodeScript(BaseModel):
    title: str
    hook_caption: str
    description: str
    hashtags: List[str]
    scenes: List[ScenePlan] = Field(..., min_length=2, max_length=4)


SYSTEM_PROMPT = """
Ты — сценарист вирусных коротких 2D-мультфильмов (20-35 секунд) для TikTok и YouTube Shorts на русском языке.
Главные герои:
1. Бублик (bublik) — круглый синий герой, эмоциональный, любопытный, иногда попадает в нелепые ситуации с интернетом, пингом, публичным Wi-Fi или заблокированными сайтами.
2. Пиксель (pixel) — умный оранжевый робот-помощник, изобретательный, спокойный, всегда находит технологичное решение.

Задача:
Напиши смешной, динамичный мини-сюжет из 3 сцен (всего 5-7 коротких реплик суммарно, чтобы ролик уложился в 22-35 секунд).
В каждой серии органично, с юмором и без занудства упомяни сервис AvroraVPN как надёжный щит для быстрого и безопасного соединения (например, когда тормозит игра, не грузится ролик или страшно сидеть через открытый Wi-Fi в кафе).

Доступные локации: cyber_room, cafe_wifi, night_city, space_station, server_vault.
Доступные эмоции: neutral, happy, shocked, worried, smug, idea.
Доступные действия: idle, wave, point, jump, panic, walk.
Доступные звуки (sfx): none, pop, whoosh, alert, chime.

Верни ТОЛЬКО валидный JSON строго по следующей схеме без markdown-обёртки:
{
  "title": "Короткий цепляющий заголовок серии",
  "hook_caption": "Текст на обложку (до 35 символов)",
  "description": "Описание для Shorts/TikTok с призывом подписаться",
  "hashtags": ["#мультфильм", "#анимация", "#AvroraVPN", "#юмор", "#shorts"],
  "scenes": [
    {
      "scene_id": 1,
      "location": "cafe_wifi",
      "transition": "none",
      "show_avrora_badge": false,
      "turns": [
        {
          "speaker": "bublik",
          "text": "Реплика Бублика на русском языке!",
          "bublik_emotion": "shocked",
          "pixel_emotion": "neutral",
          "bublik_action": "panic",
          "pixel_action": "idle",
          "sfx": "alert"
        }
      ]
    }
  ]
}
"""


class GeminiStoryGenerator:
    def __init__(self, config: StudioConfig):
        self.config = config
        self._last_call_ts = 0.0

    def _respect_rate_limit(self) -> None:
        elapsed = time.time() - self._last_call_ts
        if elapsed < self.config.min_request_interval_sec:
            sleep_for = self.config.min_request_interval_sec - elapsed
            logger.info(f"Соблюдение лимита Gemini Free Tier: пауза {sleep_for:.1f} сек...")
            time.sleep(sleep_for)

    def generate_script(self, topic_hint: Optional[str] = None) -> EpisodeScript:
        if not self.config.gemini_api_key:
            raise RuntimeError(
                "Не задан GEMINI_API_KEY! Укажите его в .env или в Secrets репозитория GitHub."
            )

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.config.gemini_api_key)

        themes = [
            "Бублик пытается скачать редкое обновление игры в кофейне через открытый Wi-Fi",
            "Бублик и Пиксель на космической станции пытаются посмотреть любимый стрим без лагов",
            "В ночном кибер-городе хакер-вирус пытается перехватить данные Бублика, но Пиксель включает AvroraVPN",
            "Бублик жалуется на высокий пинг в финале турнира, а Пиксель настраивает турбо-маршрут",
            "В дата-центре Бублик случайно нажимает красную кнопку, и только шифрование спасает ситуацию",
        ]
        chosen_theme = topic_hint or random.choice(themes)
        user_prompt = f"Придумай новый оригинальный выпуск. Тема: {chosen_theme}. Язык: ТОЛЬКО русский."

        last_error: Optional[Exception] = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                self._respect_rate_limit()
                logger.info(f"Запрос сценария у {self.config.gemini_model} (попытка {attempt}/{self.config.max_retries})...")
                response = client.models.generate_content(
                    model=self.config.gemini_model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.85,
                        response_mime_type="application/json",
                    ),
                )
                self._last_call_ts = time.time()
                raw_text = (response.text or "").strip()
                raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.IGNORECASE).strip()
                data = json.loads(raw_text)
                script = EpisodeScript.model_validate(data)
                logger.info(f"Сценарий успешно сгенерирован: «{script.title}» ({len(script.scenes)} сцен)")
                return script
            except Exception as exc:
                last_error = exc
                wait_sec = 6 * attempt
                logger.warning(f"Ошибка Gemini API на попытке {attempt}: {exc}. Повтор через {wait_sec} сек...")
                time.sleep(wait_sec)

        raise RuntimeError(f"Не удалось сгенерировать сценарий после {self.config.max_retries} попыток: {last_error}")
