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
# FULL CARD (ORIGINAL)
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
    glow_draw.rounded_rectangle((40, 40, width + 40, height + 40), radius=50, fill=(*roi_color, 255))
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

    activity_text = f"{buy_count} Buys • {sell_count} Sells" if sell_count else f"{buy_count} Buys • No Sells"
    draw.text((40, 110), f"{wallet_short}   {activity_text}", fill=(200, 200, 220), font=small_font)

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
    draw.rounded_rectangle((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h), radius=35, fill=pill_color)

    draw.text((pill_x + 65, pill_y + 8), "ROI", fill=(255, 255, 255), font=label_font)
    draw_bold_text(draw, (pill_x + 40, pill_y + 28), f"{roi_str}x", roi_font, (255, 255, 255))

    img.save(output_path)


# =========================
# MINIMAL CARD
# =========================
def create_minimal_card(profit, roi):

    width, height = 600, 300

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE_DIR, "position_card.png")
    font_path = os.path.join(BASE_DIR, "Inter.ttf")

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        draw.line((0, y, width, y), fill=(50, 20 + y//5, 100 + y//3))

    try:
        roi_font = ImageFont.truetype(font_path, 110)
        profit_font = ImageFont.truetype(font_path, 42)
    except:
        roi_font = ImageFont.load_default()
        profit_font = ImageFont.load_default()

    roi_color = (0, 255, 120) if roi > 1 else (255, 80, 80)
    profit_color = (0, 255, 120) if profit >= 0 else (255, 80, 80)

    draw_bold_text(draw, (120, 70), f"{format_number(roi)}x", roi_font, roi_color)
    draw.text((140, 200), f"{'+' if profit >= 0 else ''}{format_number(profit)} SOL",
              fill=profit_color, font=profit_font)

    img.save(output_path)
