import math
from PIL import ImageDraw


def _draw_mouth(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    openness: float,
    emotion: str,
    dark_color=(20, 26, 42, 255),
) -> None:
    if openness > 0.12:
        w = int(34 + openness * 16)
        h = int(12 + openness * 34)
        draw.ellipse([cx - w, cy - h // 2, cx + w, cy + h // 2], fill=dark_color)
        if h > 22:
            draw.ellipse([cx - w // 2, cy, cx + w // 2, cy + h // 2 - 2], fill=(235, 95, 115, 255))
    else:
        if emotion in ("happy", "smug", "idea"):
            draw.arc([cx - 34, cy - 22, cx + 34, cy + 22], start=15, end=165, fill=dark_color, width=6)
        elif emotion in ("worried", "shocked"):
            draw.arc([cx - 28, cy - 6, cx + 28, cy + 28], start=195, end=345, fill=dark_color, width=6)
        else:
            draw.line([cx - 26, cy, cx + 26, cy], fill=dark_color, width=6)


def draw_bublik(
    draw: ImageDraw.ImageDraw,
    cx: int,
    base_y: int,
    t: float,
    mouth_open: float,
    emotion: str,
    action: str,
    scale: float = 1.0,
) -> None:
    jump_offset = abs(math.sin(t * 6.0)) * 55 if action == "jump" else 0.0
    walk_sway = math.sin(t * 8.0) * 14 if action == "walk" else math.sin(t * 2.6) * 5
    panic_shake = math.sin(t * 28.0) * 8 if action == "panic" else 0.0

    body_r = int(148 * scale)
    cy = int(base_y - body_r - 65 * scale - jump_offset)
    x = int(cx + walk_sway + panic_shake)

    shadow_w = int((135 - jump_offset * 0.5) * scale)
    draw.ellipse([x - shadow_w, base_y - 16, x + shadow_w, base_y + 18], fill=(10, 14, 26, 130))

    leg_phase = math.sin(t * 8.0) * 18 if action in ("walk", "jump", "panic") else 0.0
    for side in (-1, 1):
        lx = int(x + side * 52 * scale)
        ly_top = int(cy + body_r * 0.78)
        ly_bot = int(base_y - 8 + (leg_phase * side if action == "walk" else -jump_offset * 0.4))
        draw.line([lx, ly_top, lx, ly_bot], fill=(28, 86, 175, 255), width=int(20 * scale))
        draw.rounded_rectangle(
            [lx - int(26 * scale), ly_bot - int(14 * scale), lx + int(34 * scale), ly_bot + int(14 * scale)],
            radius=12,
            fill=(245, 250, 255, 255),
            outline=(30, 110, 220, 255),
            width=4,
        )

    for side in (-1, 1):
        shoulder_x = int(x + side * (body_r - 12 * scale))
        shoulder_y = int(cy + 10 * scale)
        if action == "wave" and side == 1:
            hand_x = int(shoulder_x + 75 * scale)
            hand_y = int(shoulder_y - 95 * scale + math.sin(t * 11.0) * 28)
        elif action == "point" and side == 1:
            hand_x = int(shoulder_x + 115 * scale)
            hand_y = int(shoulder_y - 25 * scale)
        elif action == "panic":
            hand_x = int(shoulder_x + side * 70 * scale)
            hand_y = int(shoulder_y - 80 * scale + math.sin(t * 16.0 + side) * 25)
        else:
            hand_x = int(shoulder_x + side * 48 * scale)
            hand_y = int(shoulder_y + 52 * scale + math.cos(t * 3.0 + side) * 12)

        draw.line([shoulder_x, shoulder_y, hand_x, hand_y], fill=(32, 108, 215, 255), width=int(18 * scale))
        draw.ellipse(
            [hand_x - int(20 * scale), hand_y - int(20 * scale), hand_x + int(20 * scale), hand_y + int(20 * scale)],
            fill=(115, 195, 255, 255),
            outline=(24, 78, 165, 255),
            width=4,
        )

    draw.ellipse(
        [x - body_r, cy - body_r, x + body_r, cy + body_r],
        fill=(46, 138, 245, 255),
        outline=(22, 74, 160, 255),
        width=8,
    )
    draw.ellipse(
        [x - int(95 * scale), cy - int(122 * scale), x + int(55 * scale), cy - int(45 * scale)],
        fill=(110, 185, 255, 130),
    )
    ring_y = int(cy + 78 * scale)
    draw.ellipse([x - 28, ring_y - 22, x + 28, ring_y + 22], outline=(185, 230, 255, 220), width=8)

    blink = (t % 3.4) < 0.14
    eye_y = int(cy - 28 * scale)
    for side in (-1, 1):
        ex = int(x + side * 46 * scale)
        if blink:
            draw.line([ex - 24, eye_y, ex + 24, eye_y], fill=(18, 35, 70, 255), width=6)
        else:
            eye_r = int(32 * scale if emotion == "shocked" else 27 * scale)
            draw.ellipse([ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r], fill=(255, 255, 255, 255), outline=(20, 45, 95, 255), width=4)
            pupil_r = int(11 * scale if emotion == "shocked" else 14 * scale)
            draw.ellipse([ex - pupil_r + 3, eye_y - pupil_r, ex + pupil_r + 3, eye_y + pupil_r], fill=(18, 26, 48, 255))
            draw.ellipse([ex - 4, eye_y - 10, ex + 4, eye_y - 2], fill=(255, 255, 255, 255))

        brow_y = eye_y - int(36 * scale)
        tilt = 10 * side if emotion == "worried" else (-8 * side if emotion in ("smug", "idea") else 0)
        draw.line([ex - 22, brow_y + tilt, ex + 22, brow_y - tilt], fill=(16, 46, 105, 255), width=7)

    _draw_mouth(draw, x, int(cy + 26 * scale), mouth_open, emotion)


def draw_pixel(
    draw: ImageDraw.ImageDraw,
    cx: int,
    base_y: int,
    t: float,
    mouth_open: float,
    emotion: str,
    action: str,
    scale: float = 1.0,
) -> None:
    jump_offset = abs(math.sin(t * 6.5 + 0.5)) * 48 if action == "jump" else 0.0
    hover = math.sin(t * 3.2) * 6
    x = int(cx + (math.sin(t * 7.5) * 12 if action == "walk" else 0.0))

    torso_w = int(118 * scale)
    torso_h = int(126 * scale)
    torso_cy = int(base_y - 125 * scale - jump_offset + hover)

    draw.ellipse([x - int(115 * scale), base_y - 14, x + int(115 * scale), base_y + 16], fill=(10, 14, 26, 130))

    leg_swing = math.sin(t * 8.0) * 15 if action == "walk" else 0.0
    for side in (-1, 1):
        lx = int(x + side * 44 * scale)
        ly_top = int(torso_cy + torso_h // 2)
        ly_bot = int(base_y - 10 + (leg_swing * side if action == "walk" else -jump_offset * 0.35))
        draw.line([lx, ly_top, lx, ly_bot], fill=(95, 110, 130, 255), width=int(18 * scale))
        draw.rounded_rectangle(
            [lx - int(28 * scale), ly_bot - int(12 * scale), lx + int(28 * scale), ly_bot + int(12 * scale)],
            radius=8,
            fill=(235, 115, 30, 255),
            outline=(155, 65, 12, 255),
            width=4,
        )

    for side in (-1, 1):
        sx = int(x + side * (torso_w // 2 + 6))
        sy = int(torso_cy - 18 * scale)
        if action == "point" and side == -1:
            hx = int(sx - 115 * scale)
            hy = int(sy - 30 * scale)
        elif action == "wave" and side == -1:
            hx = int(sx - 80 * scale)
            hy = int(sy - 90 * scale + math.sin(t * 10.0) * 24)
        else:
            hx = int(sx + side * 46 * scale)
            hy = int(sy + 48 * scale + math.sin(t * 3.5 + side) * 10)

        draw.line([sx, sy, hx, hy], fill=(110, 125, 145, 255), width=int(15 * scale))
        draw.arc([hx - 18, hy - 18, hx + 18, hy + 18], start=30, end=330, fill=(255, 145, 45, 255), width=8)

    draw.rounded_rectangle(
        [x - torso_w // 2, torso_cy - torso_h // 2, x + torso_w // 2, torso_cy + torso_h // 2],
        radius=26,
        fill=(248, 126, 28, 255),
        outline=(175, 72, 12, 255),
        width=7,
    )
    draw.rounded_rectangle([x - 34, torso_cy - 22, x + 34, torso_cy + 26], radius=12, fill=(22, 34, 58, 255), outline=(0, 225, 210, 255), width=4)
    draw.polygon([(x, torso_cy - 12), (x + 14, torso_cy + 14), (x - 14, torso_cy + 14)], fill=(0, 235, 200, 255))

    head_w = int(156 * scale)
    head_h = int(116 * scale)
    head_cy = int(torso_cy - torso_h // 2 - head_h // 2 - 10 * scale)

    ant_top_y = int(head_cy - head_h // 2 - 42 * scale)
    draw.line([x, head_cy - head_h // 2, x, ant_top_y], fill=(130, 145, 165, 255), width=8)
    bulb_col = (0, 255, 190, 255) if emotion in ("idea", "happy") else (255, 210, 50, 255)
    draw.ellipse([x - 14, ant_top_y - 14, x + 14, ant_top_y + 14], fill=bulb_col, outline=(255, 255, 255, 255), width=3)

    draw.rounded_rectangle(
        [x - head_w // 2, head_cy - head_h // 2, x + head_w // 2, head_cy + head_h // 2],
        radius=28,
        fill=(255, 136, 34, 255),
        outline=(175, 72, 12, 255),
        width=7,
    )
    pad = int(16 * scale)
    draw.rounded_rectangle(
        [x - head_w // 2 + pad, head_cy - head_h // 2 + pad, x + head_w // 2 - pad, head_cy + head_h // 2 - pad],
        radius=18,
        fill=(18, 26, 42, 255),
    )

    blink = ((t + 1.4) % 3.8) < 0.13
    eye_y = int(head_cy - 12 * scale)
    for side in (-1, 1):
        ex = int(x + side * 36 * scale)
        if blink:
            draw.line([ex - 18, eye_y, ex + 18, eye_y], fill=(0, 235, 210, 255), width=5)
        elif emotion == "happy":
            draw.arc([ex - 18, eye_y - 12, ex + 18, eye_y + 16], start=190, end=350, fill=(0, 245, 190, 255), width=6)
        else:
            r = int(18 * scale if emotion == "shocked" else 14 * scale)
            draw.ellipse([ex - r, eye_y - r, ex + r, eye_y + r], fill=(0, 235, 220, 255))

    mouth_y = int(head_cy + 22 * scale)
    if mouth_open > 0.12:
        bars = 5
        for b in range(bars):
            bx = x - 28 + b * 14
            bh = int(6 + mouth_open * (22 if b % 2 == 0 else 14))
            draw.rectangle([bx - 4, mouth_y - bh // 2, bx + 4, mouth_y + bh // 2], fill=(0, 245, 195, 255))
    else:
        draw.arc([x - 24, mouth_y - 10, x + 24, mouth_y + 12], start=15, end=165, fill=(0, 235, 210, 255), width=5)
