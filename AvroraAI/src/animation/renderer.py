import textwrap
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw

from src.animation.backgrounds import draw_location_background
from src.animation.characters import draw_bublik, draw_pixel
from src.audio.tts_engine import RenderedTurnAudio
from src.config import StudioConfig
from src.story.gemini_writer import EpisodeScript, ScenePlan
from src.utils.font_loader import get_cyrillic_font


class FrameRenderer:
    def __init__(self, config: StudioConfig):
        self.config = config
        self.font_sub = get_cyrillic_font(int(config.width * 0.044), config.assets_dir / "fonts")
        self.font_badge = get_cyrillic_font(int(config.width * 0.032), config.assets_dir / "fonts")
        self.font_title = get_cyrillic_font(int(config.width * 0.038), config.assets_dir / "fonts")

    def _draw_avrora_promo_overlay(self, draw: ImageDraw.ImageDraw, show_full_banner: bool) -> None:
        w, h = self.config.width, self.config.height
        pill_w, pill_h = int(w * 0.34), int(h * 0.034)
        px = (w - pill_w) // 2
        py = int(h * 0.045)
        draw.rounded_rectangle([px, py, px + pill_w, py + pill_h], radius=22, fill=(14, 24, 48, 200), outline=(0, 235, 205, 230), width=3)
        draw.text((px + pill_w // 2, py + pill_h // 2), "AvroraVPN", fill=(240, 252, 255, 255), font=self.font_badge, anchor="mm")

        if show_full_banner:
            bw, bh = int(w * 0.84), int(h * 0.068)
            bx = (w - bw) // 2
            by = int(h * 0.10)
            draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=24, fill=(12, 28, 62, 235), outline=(0, 240, 200, 255), width=4)
            draw.text(
                (w // 2, by + bh // 2),
                "AvroraVPN • Быстрый и безопасный интернет",
                fill=(255, 255, 255, 255),
                font=self.font_badge,
                anchor="mm",
            )

    def _draw_subtitles(self, draw: ImageDraw.ImageDraw, speaker: str, text: str) -> None:
        w, h = self.config.width, self.config.height
        lines = textwrap.wrap(text, width=28)
        if not lines:
            return

        line_h = int(self.config.width * 0.056)
        box_h = len(lines) * line_h + 44
        box_w = int(w * 0.88)
        bx = (w - box_w) // 2
        by = int(h * 0.77)

        border_col = (70, 175, 255, 255) if speaker == "bublik" else (255, 150, 45, 255)
        label = "Бублик" if speaker == "bublik" else "Пиксель"

        draw.rounded_rectangle([bx, by, bx + box_w, by + box_h], radius=26, fill=(12, 16, 30, 225), outline=border_col, width=4)
        draw.rounded_rectangle([bx + 24, by - 22, bx + 190, by + 16], radius=14, fill=border_col)
        draw.text((bx + 107, by - 3), label, fill=(15, 20, 35, 255), font=self.font_badge, anchor="mm")

        for idx, line in enumerate(lines):
            ty = by + 34 + idx * line_h
            draw.text((w // 2, ty), line, fill=(255, 255, 255, 255), font=self.font_sub, anchor="mt")

    def render_single_frame(
        self,
        t: float,
        scene: ScenePlan,
        active_turn: Optional[RenderedTurnAudio],
        last_turn: Optional[RenderedTurnAudio],
        scale_factor: float = 1.0,
    ) -> Image.Image:
        w, h = self.config.width, self.config.height
        frame = draw_location_background(w, h, scene.location, t)
        draw = ImageDraw.Draw(frame, "RGBA")

        state = active_turn or last_turn
        bublik_mouth = 0.0
        pixel_mouth = 0.0
        b_emo = state.bublik_emotion if state else "happy"
        p_emo = state.pixel_emotion if state else "happy"
        b_act = state.bublik_action if state else "wave"
        p_act = state.pixel_action if state else "idle"

        if active_turn is not None:
            local_t = max(0.0, t - active_turn.start_time)
            env_idx = min(len(active_turn.mouth_envelope) - 1, int(local_t * self.config.fps))
            mouth_val = active_turn.mouth_envelope[env_idx]
            if active_turn.speaker == "bublik":
                bublik_mouth = mouth_val
            else:
                pixel_mouth = mouth_val

        floor_y = int(h * 0.72)
        char_scale = (w / 1080.0) * scale_factor

        draw_bublik(
            draw=draw,
            cx=int(w * 0.30),
            base_y=floor_y,
            t=t,
            mouth_open=bublik_mouth,
            emotion=b_emo,
            action=b_act,
            scale=char_scale,
        )
        draw_pixel(
            draw=draw,
            cx=int(w * 0.72),
            base_y=floor_y,
            t=t,
            mouth_open=pixel_mouth,
            emotion=p_emo,
            action=p_act,
            scale=char_scale,
        )

        mention_in_text = bool(active_turn and "avrora" in active_turn.text.lower())
        self._draw_avrora_promo_overlay(draw, show_full_banner=(scene.show_avrora_badge or mention_in_text))

        if active_turn is not None:
            self._draw_subtitles(draw, active_turn.speaker, active_turn.text)

        return frame.convert("RGB")

    def render_all_frames(
        self,
        script: EpisodeScript,
        turns: List[RenderedTurnAudio],
        total_duration: float,
        frames_dir: Path,
    ) -> int:
        frames_dir.mkdir(parents=True, exist_ok=True)
        scene_map: Dict[int, ScenePlan] = {s.scene_id: s for s in script.scenes}

        total_frames = int(total_duration * self.config.fps)
        transition_frames = int(0.35 * self.config.fps)

        current_scene = script.scenes[0]
        prev_scene = current_scene
        scene_switch_frame = -999
        last_turn: Optional[RenderedTurnAudio] = turns[0] if turns else None

        for frame_idx in range(total_frames):
            t = frame_idx / float(self.config.fps)

            active_turn: Optional[RenderedTurnAudio] = None
            for turn in turns:
                if turn.start_time <= t <= (turn.start_time + turn.duration):
                    active_turn = turn
                    last_turn = turn
                    break

            target_scene_id = (active_turn or last_turn).scene_id if (active_turn or last_turn) else script.scenes[0].scene_id
            target_scene = scene_map.get(target_scene_id, script.scenes[0])

            if target_scene.scene_id != current_scene.scene_id:
                prev_scene = current_scene
                current_scene = target_scene
                scene_switch_frame = frame_idx

            img_curr = self.render_single_frame(t, current_scene, active_turn, last_turn)

            since_switch = frame_idx - scene_switch_frame
            if 0 <= since_switch < transition_frames and prev_scene.scene_id != current_scene.scene_id:
                alpha = since_switch / float(transition_frames)
                img_prev = self.render_single_frame(t, prev_scene, active_turn, last_turn)
                img_curr = Image.blend(img_prev, img_curr, alpha)

            frame_path = frames_dir / f"frame_{frame_idx:05d}.png"
            img_curr.save(frame_path, format="PNG", compress_level=1)

        return total_frames
