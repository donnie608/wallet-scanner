print("MINIMAL CARD NEW VERSION RUNNING")
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

def format_number(n, decimals=2):
    return f"{n:,.{decimals}f}"

def format_compact(n):
    abs_n = abs(n)
    if abs_n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    elif abs_n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    elif abs_n >= 1_000:
        return f"{n/1_000:.2f}K"
    else:
        return f"{n:.2f}"

def draw_bold_text(draw, position, text, font, fill):
    x, y = position
    draw.text((x, y), text, font=font, fill=fill)
    draw.text((x+1, y), text, font=font, fill=fill)
    draw.text((x, y+1), text, font=font, fill=fill)
    draw.text((x+1, y+1), text, font=font, fill=fill)

def reduce_opacity(img, opacity):
    alpha = img.split()[3]
    alpha = alpha.point(lambda p: int(p * opacity))
    img.putalpha(alpha)
    return img

# =========================
# FULL CARD (UNCHANGED)
# =========================
def create_card(token_name, wallet, tokens, cost, value, profit, roi,
                logo_path=None, token_symbol=None,
                buy_count=0, sell_count=0,
                sol_price_usd=0):

    tokens_str = format_compact(tokens)
    roi_str = format_number(roi, 2)

    wallet_short = wallet[:6] + "..." + wallet[-4:]

    profit_color = (0, 255, 120) if profit >= 0 else (255, 80, 80)

    width, height = 800, 450

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE_DIR, "position_card.png")
    font_path = os.path.join(BASE_DIR, "Inter.ttf")
    logo_file = os.path.join(BASE_DIR, "logo.png")

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    roi_color = (0, 255, 120) if roi > 1 else (255, 80, 80) if roi < 1 else (120, 120, 120)

    glow = Image.new("RGBA", (width + 80, height + 80), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.rounded_rectangle(
        (40, 40, width + 40, height + 40),
        radius=50,
        fill=(*roi_color, 255)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    img.paste(glow, (-40, -40), glow)

    card = Image.new("RGBA", (width, height))
    draw_card = ImageDraw.Draw(card)

    for y in range(height):
        r = int(80 + (y / height) * 60)
        g = int(30 + (y / height) * 30)
        b = int(140 + (y / height) * 100)
        draw_card.line((0, y, width, y), fill=(r, g, b))

    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width, height), radius=40, fill=255)
    img.paste(card, (0, 0), mask)

    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(font_path, 42)
        symbol_font = ImageFont.truetype(font_path, 22)
        label_font = ImageFont.truetype(font_path, 18)
        value_font = ImageFont.truetype(font_path, 28)
        small_font = ImageFont.truetype(font_path, 16)
        roi_font = ImageFont.truetype(font_path, 32)
    except:
        title_font = ImageFont.load_default()
        symbol_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        roi_font = ImageFont.load_default()

    draw.text((40, 30), token_name, fill=(255, 255, 255), font=title_font)

    if token_symbol:
        draw.text((40, 80), f"${token_symbol}", fill=(180, 200, 255), font=symbol_font)

    if sell_count == 0:
        activity_text = f"{buy_count} Buys • No Sells"
    else:
        activity_text = f"{buy_count} Buys • {sell_count} Sells"

    combined_text = f"{wallet_short}   {activity_text}"
    draw.text((40, 110), combined_text, fill=(200, 200, 220), font=small_font)

    draw.line((40, 140, width - 40, 140), fill=(120, 120, 160), width=2)

    cost_usd = cost * sol_price_usd
    value_usd = value * sol_price_usd
    profit_usd = profit * sol_price_usd

    draw.text((50, 170), "Tokens", fill=(200, 200, 220), font=label_font)
    draw.text((50, 205), tokens_str, fill=(255, 255, 255), font=value_font)

    draw.text((50, 270), "Cost (SOL)", fill=(200, 200, 220), font=label_font)
    draw.text((50, 305), f"{cost:.4f} SOL (${cost_usd:.2f})", fill=(255, 255, 255), font=value_font)

    draw.text((400, 170), "Value (SOL)", fill=(200, 200, 220), font=label_font)
    draw.text((400, 205), f"{value:.4f} SOL (${value_usd:.2f})", fill=(255, 255, 255), font=value_font)

    draw.text((400, 270), "Profit (SOL)", fill=(200, 200, 220), font=label_font)
    draw.text((400, 305), f"{profit:.4f} SOL (${profit_usd:.2f})", fill=profit_color, font=value_font)

    pill_w, pill_h = 180, 70
    pill_x = (width - pill_w) // 2
    pill_y = 370

    pill_color = (0, 200, 100) if roi > 1 else (220, 60, 60) if roi < 1 else (40, 40, 40)

    draw.rounded_rectangle(
        (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
        radius=35,
        fill=pill_color
    )

    draw.text((pill_x + 65, pill_y + 8), "ROI", fill=(255, 255, 255), font=label_font)

    roi_value = f"{roi_str}x"
    draw_bold_text(draw, (pill_x + 40, pill_y + 28), roi_value, roi_font, (255, 255, 255))

    img.save(output_path)

# =========================
# MINIMAL ROI CARD (FIXED FOR REAL)
# =========================
def create_minimal_card(token_name, profit, roi,
                        logo_path=None, token_symbol=None,
                        sol_price_usd=0):

    width, height = 800, 450
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE_DIR, "minimal_card.png")
    font_path = os.path.join(BASE_DIR, "Inter.ttf")

    img = Image.new("RGBA", (width, height))

    roi_color = (0, 255, 180) if roi > 1 else (255, 80, 80)

    # background
    draw_bg = ImageDraw.Draw(img)
    for y in range(height):
        draw_bg.line((0, y, width, y),
                     fill=(40 + y//6, 20 + y//12, 80 + y//3))

    draw = ImageDraw.Draw(img)

    try:
        roi_font = ImageFont.truetype(font_path, 140)
        sub_font = ImageFont.truetype(font_path, 44)
        title_font = ImageFont.truetype(font_path, 80)  # 🔥 BIG jump
    except:
        roi_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # ===== TITLE (VISIBLY BIGGER) =====
    title = f"{token_name} (${token_symbol})" if token_symbol else token_name
    draw.text((40, 30), title, font=title_font, fill=(220, 220, 255))

    # ===== ROI CENTER (REAL) =====
    roi_text = f"{roi:.2f}x"
    bbox = draw.textbbox((0, 0), roi_text, font=roi_font)
    roi_w = bbox[2] - bbox[0]
    roi_h = bbox[3] - bbox[1]

    roi_x = (width - roi_w) // 2
    roi_y = (height - roi_h) // 2

    # glow
    for r, alpha in [(6,100),(14,50),(28,25)]:
        glow = Image.new("RGBA", (width, height), (0,0,0,0))
        g = ImageDraw.Draw(glow)
        g.text((roi_x, roi_y),
               roi_text, font=roi_font,
               fill=(*roi_color, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(r))
        img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)

    # shadow
    draw.text((roi_x, roi_y + 10),
              roi_text, font=roi_font,
              fill=(0,0,0,130))

    # main ROI
    draw.text((roi_x, roi_y),
              roi_text, font=roi_font,
              fill=(240,255,255))

    # ===== PROFIT (CENTERED + CLEAR GAP) =====
    profit_usd = profit * sol_price_usd
    profit_text = f"{profit:.2f} SOL (${profit_usd:.2f})"

    p_bbox = draw.textbbox((0, 0), profit_text, font=sub_font)
    p_w = p_bbox[2] - p_bbox[0]

    profit_x = (width - p_w) // 2
    profit_y = roi_y + roi_h + 70  # 🔥 VERY noticeable spacing

    draw.text(
        (profit_x, profit_y),
        profit_text,
        font=sub_font,
        fill=roi_color
    )

    img.save(output_path)
