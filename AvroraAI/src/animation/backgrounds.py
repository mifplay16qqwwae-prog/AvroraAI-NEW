import math
from PIL import Image, ImageDraw


def draw_location_background(width: int, height: int, location: str, t: float) -> Image.Image:
    """Рисует детализированную анимированную локацию в формате 9:16 с параллаксом."""
    img = Image.new("RGBA", (width, height), (18, 22, 38, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    if location == "cafe_wifi":
        for y in range(0, height, 8):
            ratio = y / height
            r = int(48 + 38 * ratio)
            g = int(34 + 26 * ratio)
            b = int(52 + 30 * ratio)
            draw.rectangle([0, y, width, y + 8], fill=(r, g, b, 255))

        win_margin = int(width * 0.08)
        win_top = int(height * 0.14)
        win_bottom = int(height * 0.56)
        draw.rounded_rectangle(
            [win_margin, win_top, width - win_margin, win_bottom],
            radius=36,
            fill=(28, 45, 82, 255),
            outline=(190, 145, 95, 255),
            width=10,
        )
        for i in range(6):
            bx = win_margin + 60 + i * 140
            bh = 140 + (i % 3) * 65
            draw.rectangle([bx, win_bottom - bh, bx + 95, win_bottom - 6], fill=(18, 28, 54, 255))
            glow = int(180 + 70 * math.sin(t * 2.5 + i))
            draw.rectangle([bx + 20, win_bottom - bh + 25, bx + 45, win_bottom - bh + 55], fill=(255, 215, 110, glow))

        cx, cy = int(width * 0.80), int(height * 0.22)
        for ring in range(1, 4):
            pulse = 180 if (int(t * 3) % 3 + 1) >= ring else 60
            r = ring * 26
            draw.arc([cx - r, cy - r, cx + r, cy + r], start=225, end=315, fill=(90, 220, 255, pulse), width=7)

        floor_y = int(height * 0.72)
        draw.rectangle([0, floor_y, width, height], fill=(74, 48, 32, 255))
        draw.line([0, floor_y, width, floor_y], fill=(120, 82, 54, 255), width=6)

    elif location == "space_station":
        draw.rectangle([0, 0, width, height], fill=(8, 12, 28, 255))
        for i in range(45):
            sx = int((i * 197 + t * (8 + (i % 4) * 5)) % width)
            sy = int((i * 313) % int(height * 0.74))
            alpha = int(140 + 115 * math.sin(t * 3.0 + i))
            size = 3 + (i % 3)
            draw.ellipse([sx, sy, sx + size, sy + size], fill=(230, 245, 255, alpha))

        cx, cy = width // 2, int(height * 0.34)
        rad = int(width * 0.34)
        draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(20, 95, 195, 255), outline=(120, 145, 175, 255), width=16)
        cloud_shift = int(math.sin(t * 0.6) * 35)
        draw.ellipse([cx - 140 + cloud_shift, cy - 60, cx + 40 + cloud_shift, cy + 10], fill=(240, 250, 255, 170))
        draw.ellipse([cx - 30 - cloud_shift, cy + 40, cx + 150 - cloud_shift, cy + 100], fill=(240, 250, 255, 150))

        floor_y = int(height * 0.72)
        draw.rectangle([0, floor_y, width, height], fill=(42, 52, 72, 255))
        for x in range(0, width, 120):
            draw.line([x, floor_y, x - 40, height], fill=(70, 88, 118, 255), width=4)

    elif location == "night_city":
        for y in range(0, height, 10):
            ratio = y / height
            draw.rectangle([0, y, width, y + 10], fill=(int(15 + 25 * ratio), int(12 + 18 * ratio), int(45 + 55 * ratio), 255))

        buildings = [(40, 420, 210), (230, 310, 230), (480, 380, 220), (720, 290, 280)]
        for idx, (bx, top_y, bw) in enumerate(buildings):
            draw.rectangle([bx, top_y, bx + bw, int(height * 0.73)], fill=(18, 24, 48, 255), outline=(0, 210, 255, 120), width=3)
            neon_color = (255, 65, 180, 210) if idx % 2 == 0 else (0, 235, 210, 210)
            draw.rounded_rectangle([bx + 25, top_y + 50, bx + bw - 25, top_y + 115], radius=12, outline=neon_color, width=5)

        drone_x = int((width * 0.5) + math.sin(t * 1.4) * (width * 0.32))
        drone_y = int(height * 0.22 + math.cos(t * 2.8) * 18)
        draw.rounded_rectangle([drone_x - 45, drone_y - 16, drone_x + 45, drone_y + 16], radius=10, fill=(55, 70, 95, 255))
        draw.ellipse([drone_x - 10, drone_y - 10, drone_x + 10, drone_y + 10], fill=(0, 255, 200, 230))

        floor_y = int(height * 0.72)
        draw.rectangle([0, floor_y, width, height], fill=(24, 28, 46, 255))

    elif location == "server_vault":
        draw.rectangle([0, 0, width, height], fill=(12, 22, 34, 255))
        for i in range(4):
            rx = int(width * (0.10 + i * 0.22))
            draw.rounded_rectangle([rx, int(height * 0.16), rx + 150, int(height * 0.72)], radius=14, fill=(24, 38, 56, 255), outline=(45, 95, 140, 255), width=4)
            for row in range(8):
                ly = int(height * 0.20) + row * 72
                blink = (int(t * 6) + i + row) % 3 == 0
                led_col = (0, 255, 160, 255) if blink else (40, 120, 180, 180)
                draw.ellipse([rx + 25, ly, rx + 43, ly + 18], fill=led_col)
                draw.rectangle([rx + 60, ly + 4, rx + 125, ly + 14], fill=(55, 85, 115, 220))

        floor_y = int(height * 0.72)
        draw.rectangle([0, floor_y, width, height], fill=(20, 32, 48, 255))

    else:
        draw.rectangle([0, 0, width, height], fill=(22, 20, 44, 255))
        glow_alpha = int(170 + 70 * math.sin(t * 2.0))
        draw.line([0, int(height * 0.12), width, int(height * 0.12)], fill=(140, 90, 255, glow_alpha), width=14)
        mon_x, mon_y = int(width * 0.24), int(height * 0.34)
        draw.rounded_rectangle([mon_x, mon_y, mon_x + 560, mon_y + 310], radius=24, fill=(16, 26, 46, 255), outline=(70, 130, 240, 255), width=8)
        pts = []
        for px in range(mon_x + 30, mon_x + 530, 20):
            py = mon_y + 155 + int(math.sin((px * 0.03) + t * 5.0) * 45)
            pts.append((px, py))
        if len(pts) > 1:
            draw.line(pts, fill=(0, 235, 190, 240), width=6)

        floor_y = int(height * 0.72)
        draw.rectangle([0, floor_y, width, height], fill=(34, 30, 58, 255))

    return img
