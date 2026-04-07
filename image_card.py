from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import math

def create_minimal_card(token_name, profit, roi,
                        logo_path=None, token_symbol=None,
                        sol_price_usd=0):

    width, height = 800, 450

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE_DIR, "minimal_card.png")
    font_path = os.path.join(BASE_DIR, "Inter.ttf")
    logo_file = os.path.join(BASE_DIR, "logo.png")

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    roi_color = (0, 255, 180) if roi > 1 else (255, 80, 80)

    # ===== BACKGROUND GRADIENT =====
    bg = Image.new("RGBA", (width, height))
    draw_bg = ImageDraw.Draw(bg)

    for y in range(height):
        r = int(40 + (y / height) * 60)
        g = int(20 + (y / height) * 20)
        b = int(80 + (y / height) * 120)
        draw_bg.line((0, y, width, y), fill=(r, g, b))

    img.paste(bg, (0, 0))

    # ===== ROI CENTER =====
    center_x = width // 2
    center_y = height // 2 - 20

    roi_text = f"{roi:.2f}x"

    try:
        roi_font = ImageFont.truetype(font_path, 140)
        sub_font = ImageFont.truetype(font_path, 40)
        title_font = ImageFont.truetype(font_path, 28)
    except:
        roi_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # ===== RADIAL SPOTLIGHT =====
    spotlight = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sp_draw = ImageDraw.Draw(spotlight)

    for r in range(0, 300, 10):
        alpha = int(80 * (1 - r / 300))
        sp_draw.ellipse(
            (center_x - r, center_y - r, center_x + r, center_y + r),
            fill=(roi_color[0], roi_color[1], roi_color[2], alpha)
        )

    spotlight = spotlight.filter(ImageFilter.GaussianBlur(40))
    img = Image.alpha_composite(img, spotlight)

    # ===== SOFT STARBURST =====
    burst = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    burst_draw = ImageDraw.Draw(burst)

    for angle in range(0, 360, 20):
        length = 300
        x = center_x + int(math.cos(math.radians(angle)) * length)
        y = center_y + int(math.sin(math.radians(angle)) * length)

        burst_draw.line(
            (center_x, center_y, x, y),
            fill=(roi_color[0], roi_color[1], roi_color[2], 25),
            width=3
        )

    burst = burst.filter(ImageFilter.GaussianBlur(25))
    img = Image.alpha_composite(img, burst)

    # ===== GLOW LAYERS =====
    for r, alpha in [(8, 80), (16, 40), (30, 20)]:
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow)
        g_draw.text(
            (center_x - 150, center_y - 70),
            roi_text,
            font=roi_font,
            fill=(roi_color[0], roi_color[1], roi_color[2], alpha)
        )
        glow = glow.filter(ImageFilter.GaussianBlur(r))
        img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)

    # ===== SHADOW =====
    draw.text(
        (center_x - 150, center_y - 60 + 8),
        roi_text,
        font=roi_font,
        fill=(0, 0, 0, 120)
    )

    # ===== MAIN TEXT =====
    draw.text(
        (center_x - 150, center_y - 60),
        roi_text,
        font=roi_font,
        fill=(240, 255, 255)
    )

    # ===== PROFIT TEXT =====
    profit_usd = profit * sol_price_usd
    profit_text = f"{'+' if profit >= 0 else ''}{profit:.2f} SOL (${profit_usd:.2f})"

    draw.text(
        (center_x - 140, center_y + 90),
        profit_text,
        font=sub_font,
        fill=roi_color
    )

    # ===== TITLE =====
    title = f"{token_name} (${token_symbol})" if token_symbol else token_name

    draw.text(
        (40, 30),
        title,
        font=title_font,
        fill=(220, 220, 255)
    )

    # ===== TOKEN LOGO =====
    try:
        size = 90
        x = width - size - 30
        y = 30

        if logo_path and os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
        else:
            logo = Image.open(logo_file).convert("RGBA")

        logo = logo.resize((size, size), Image.LANCZOS)

        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        logo.putalpha(mask)

        img.paste(logo, (x, y), logo)

    except:
        pass

    # ===== BRAND LOGO =====
    try:
        brand_logo = Image.open(logo_file).convert("RGBA")
        brand_logo = brand_logo.resize((120, 120), Image.LANCZOS)

        alpha = brand_logo.split()[3]
        alpha = alpha.point(lambda p: int(p * 0.85))
        brand_logo.putalpha(alpha)

        x = width - 140
        y = height - 120

        img.paste(brand_logo, (x, y), brand_logo)

    except:
        pass

    img.save(output_path)
