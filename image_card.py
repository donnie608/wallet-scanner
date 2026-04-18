from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

print("🔥 IMAGE_CARD FILE LOADED 🔥")

# =========================
# HELPERS
# =========================
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
# FULL CARD (LOCKED)
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

    roi_color = (0, 255, 120) if roi > 0 else (255, 80, 80) if roi < 0 else (120, 120, 120)

    # GLOW
    glow = Image.new("RGBA", (width + 80, height + 80), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.rounded_rectangle(
        (40, 40, width + 40, height + 40),
        radius=50,
        fill=(*roi_color, 255)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    img.paste(glow, (-40, -40), glow)

    # GRADIENT
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

    # TOKEN LOGO
    try:
        size = 120
        x = width - size - 20
        y = 20

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

    # HEADER
    draw.text((40, 30), token_name, fill=(255, 255, 255), font=title_font)

    if token_symbol:
        draw.text((40, 80), f"${token_symbol}", fill=(180, 200, 255), font=symbol_font)

    activity_text = f"{buy_count} Buys • {sell_count} Sells" if sell_count else f"{buy_count} Buys • No Sells"
    draw.text((40, 110), f"{wallet_short}   {activity_text}", fill=(200, 200, 220), font=small_font)

    draw.line((40, 140, width - 40, 140), fill=(120, 120, 160), width=2)

    # VALUES
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

    # ROI
    pill_w, pill_h = 180, 70
    pill_x = (width - pill_w) // 2
    pill_y = 370

    pill_color = (0, 200, 100) if roi > 0 else (220, 60, 60) if roi < 0 else (40, 40, 40)

    draw.rounded_rectangle(
        (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
        radius=35,
        fill=pill_color
    )

    draw.text((pill_x + 65, pill_y + 8), "ROI", fill=(255, 255, 255), font=label_font)

    roi_value = f"{roi_str}x"
    draw_bold_text(draw, (pill_x + 40, pill_y + 28), roi_value, roi_font, (255, 255, 255))

    # BRAND LOGO
    try:
        brand_logo = Image.open(logo_file).convert("RGBA")
        brand_logo = brand_logo.resize((150, 150), Image.LANCZOS)
        brand_logo = reduce_opacity(brand_logo, 0.85)

        x = width - 150 - 30
        y = height - 150 + 25

        img.paste(brand_logo, (x, y), brand_logo)
    except:
        pass

    img.save(output_path)


# =========================
# MINIMAL CARD (RESTORED)
# =========================
def create_minimal_card(token_name, profit, roi,
                        logo_path=None, token_symbol=None,
                        sol_price_usd=0):

    width, height = 800, 450
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE_DIR, "minimal_card.png")
    font_path = os.path.join(BASE_DIR, "Inter.ttf")
    brand_logo_path = os.path.join(BASE_DIR, "logo.png")

    img = Image.new("RGBA", (width, height), (0,0,0,255))

    # ROI COLOR
    if roi > 0:
        roi_color = (0, 255, 120)
    elif roi < 0:
        roi_color = (255, 80, 80)
    else:
        roi_color = (120, 120, 120)

    # ===== NEON BORDER =====
    border = Image.new("RGBA", (width, height), (0,0,0,0))

    margin = 12
    radius = 36

    for blur, alpha, expand in [
        (30, 40, 6),
        (20, 70, 4),
        (10, 120, 2),
    ]:
        temp = Image.new("RGBA", (width, height), (0,0,0,0))
        t_draw = ImageDraw.Draw(temp)

        t_draw.rounded_rectangle(
            (margin-expand, margin-expand, width-margin+expand, height-margin+expand),
            radius=radius,
            outline=(*roi_color, alpha),
            width=3
        )

        temp = temp.filter(ImageFilter.GaussianBlur(blur))
        border = Image.alpha_composite(border, temp)

    sharp = Image.new("RGBA", (width, height), (0,0,0,0))
    s_draw = ImageDraw.Draw(sharp)

    s_draw.rounded_rectangle(
        (margin, margin, width-margin, height-margin),
        radius=radius,
        outline=roi_color,
        width=2
    )

    border = Image.alpha_composite(border, sharp)
    img = Image.alpha_composite(img, border)

    draw = ImageDraw.Draw(img)

    try:
        roi_font = ImageFont.truetype(font_path, 150)
        sub_font = ImageFont.truetype(font_path, 42)
        title_font = ImageFont.truetype(font_path, 36)
    except:
        roi_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # HEADER
    title = f"{token_name} (${token_symbol})" if token_symbol else token_name
    bbox = draw.textbbox((0,0), title, font=title_font)

    tx = (width - (bbox[2]-bbox[0])) // 2
    ty = 30

    for dx, dy in [(0,0),(1,0),(0,1),(1,1)]:
        draw.text((tx+dx, ty+dy), title, font=title_font, fill=(220,220,255))

    # SEPARATOR
    line_y = ty + (bbox[3]-bbox[1]) + 15
    draw.line((60, line_y, width - 60, line_y), fill=(100, 100, 120), width=2)

    # ROI
    roi_text = f"{roi:.2f}x"
    bbox = draw.textbbox((0,0), roi_text, font=roi_font)
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]

    x = (width - w)//2
    y = (height - h)//2 - 40

    for r, alpha in [(4,140),(10,70),(20,30)]:
        glow = Image.new("RGBA", (width, height), (0,0,0,0))
        g = ImageDraw.Draw(glow)
        g.text((x,y), roi_text, font=roi_font, fill=(*roi_color, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(r))
        img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)

    draw.text((x, y+10), roi_text, font=roi_font, fill=(0,0,0,150))
    draw.text((x, y), roi_text, font=roi_font, fill=roi_color)

    # PROFIT
    profit_usd = profit * sol_price_usd
    sign = "+" if profit > 0 else ""
    profit_text = f"{sign}{profit:.2f} SOL (${sign}{profit_usd:.2f})"
    bbox = draw.textbbox((0,0), profit_text, font=sub_font)

    draw.text(((width-(bbox[2]-bbox[0]))//2, y+h+60),
              profit_text, font=sub_font, fill=roi_color)

    # TOKEN LOGO
    try:
        if logo_path and os.path.exists(logo_path):
            size = 100
            logo = Image.open(logo_path).convert("RGBA").resize((size,size))
            mask = Image.new("L",(size,size),0)
            ImageDraw.Draw(mask).ellipse((0,0,size,size),fill=255)
            logo.putalpha(mask)
            img.paste(logo,(30,height-size-30),logo)
    except:
        pass

    # BRAND LOGO
    try:
        if os.path.exists(brand_logo_path):
            size = 100
            brand = Image.open(brand_logo_path).convert("RGBA").resize((size,size))
            img.paste(brand,(width-size-30,height-size-30),brand)
    except:
        pass

    img.save(output_path)

def create_eth_card(token_name, wallet, tokens, cost_usd, value_usd, profit_usd, roi,
                    logo_path=None, token_symbol=None,
                    buy_count=0, sell_count=0):

    tokens_str = format_compact(tokens)
    roi_str = format_number(roi, 2)

    wallet_short = wallet[:6] + "..." + wallet[-4:]
    profit_color = (0, 255, 120) if profit_usd >= 0 else (255, 80, 80)

    width, height = 800, 450

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE_DIR, "position_card.png")
    font_path = os.path.join(BASE_DIR, "Inter.ttf")
    logo_file = os.path.join(BASE_DIR, "logo.png")

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    roi_color = (0, 255, 120) if roi > 0 else (255, 80, 80) if roi < 0 else (120, 120, 120)

    # GLOW
    glow = Image.new("RGBA", (width + 80, height + 80), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.rounded_rectangle(
        (40, 40, width + 40, height + 40),
        radius=50,
        fill=(*roi_color, 255)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    img.paste(glow, (-40, -40), glow)

    # GRADIENT
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

    # TOKEN LOGO
    try:
        size = 120
        x = width - size - 20
        y = 20

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

    # HEADER
    draw.text((40, 30), token_name, fill=(255, 255, 255), font=title_font)

    if token_symbol:
        draw.text((40, 80), f"${token_symbol}", fill=(180, 200, 255), font=symbol_font)

    activity_text = f"{buy_count} Buys • {sell_count} Sells" if sell_count else f"{buy_count} Buys • No Sells"
    draw.text((40, 110), f"{wallet_short}   {activity_text}", fill=(200, 200, 220), font=small_font)

    draw.line((40, 140, width - 40, 140), fill=(120, 120, 160), width=2)

    # VALUES
    draw.text((50, 170), "Tokens", fill=(200, 200, 220), font=label_font)
    draw.text((50, 205), tokens_str, fill=(255, 255, 255), font=value_font)

    draw.text((50, 270), "Cost (USD)", fill=(200, 200, 220), font=label_font)
    draw.text((50, 305), f"${cost_usd:.2f}", fill=(255, 255, 255), font=value_font)

    draw.text((400, 170), "Value (USD)", fill=(200, 200, 220), font=label_font)
    draw.text((400, 205), f"${value_usd:.2f}", fill=(255, 255, 255), font=value_font)

    draw.text((400, 270), "Profit (USD)", fill=(200, 200, 220), font=label_font)
    draw.text((400, 305), f"${profit_usd:.2f}", fill=profit_color, font=value_font)

    # ROI
    pill_w, pill_h = 180, 70
    pill_x = (width - pill_w) // 2
    pill_y = 370

    pill_color = (0, 200, 100) if roi > 0 else (220, 60, 60) if roi < 0 else (40, 40, 40)

    draw.rounded_rectangle(
        (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
        radius=35,
        fill=pill_color
    )

    draw.text((pill_x + 65, pill_y + 8), "ROI", fill=(255, 255, 255), font=label_font)
    draw_bold_text(draw, (pill_x + 40, pill_y + 28), f"{roi_str}x", roi_font, (255, 255, 255))

    # BRAND LOGO
    try:
        brand_logo = Image.open(logo_file).convert("RGBA")
        brand_logo = brand_logo.resize((150, 150), Image.LANCZOS)
        brand_logo = reduce_opacity(brand_logo, 0.85)

        x = width - 150 - 30
        y = height - 150 + 25

        img.paste(brand_logo, (x, y), brand_logo)
    except:
        pass

def create_minimal_eth_card(token_name, profit_usd, roi,
                             logo_path=None, token_symbol=None):

    width, height = 800, 450
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE_DIR, "minimal_card.png")
    font_path = os.path.join(BASE_DIR, "Inter.ttf")
    brand_logo_path = os.path.join(BASE_DIR, "logo.png")

    img = Image.new("RGBA", (width, height), (0, 0, 0, 255))

    if roi > 0:
        roi_color = (0, 255, 120)
    elif roi < 0:
        roi_color = (255, 80, 80)
    else:
        roi_color = (120, 120, 120)

    # NEON BORDER
    border = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    margin = 12
    radius = 36

    for blur, alpha, expand in [(30, 40, 6), (20, 70, 4), (10, 120, 2)]:
        temp = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        t_draw = ImageDraw.Draw(temp)
        t_draw.rounded_rectangle(
            (margin - expand, margin - expand, width - margin + expand, height - margin + expand),
            radius=radius,
            outline=(*roi_color, alpha),
            width=3
        )
        temp = temp.filter(ImageFilter.GaussianBlur(blur))
        border = Image.alpha_composite(border, temp)

    sharp = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(sharp)
    s_draw.rounded_rectangle(
        (margin, margin, width - margin, height - margin),
        radius=radius,
        outline=roi_color,
        width=2
    )
    border = Image.alpha_composite(border, sharp)
    img = Image.alpha_composite(img, border)

    draw = ImageDraw.Draw(img)

    try:
        roi_font = ImageFont.truetype(font_path, 150)
        sub_font = ImageFont.truetype(font_path, 42)
        title_font = ImageFont.truetype(font_path, 36)
    except:
        roi_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # HEADER
    title = f"{token_name} (${token_symbol})" if token_symbol else token_name
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tx = (width - (bbox[2] - bbox[0])) // 2
    ty = 30
    for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        draw.text((tx + dx, ty + dy), title, font=title_font, fill=(220, 220, 255))

    # SEPARATOR
    line_y = ty + (bbox[3] - bbox[1]) + 15
    draw.line((60, line_y, width - 60, line_y), fill=(100, 100, 120), width=2)

    # ROI
    roi_text = f"{roi:.2f}x"
    bbox = draw.textbbox((0, 0), roi_text, font=roi_font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (width - w) // 2
    y = (height - h) // 2 - 40

    for r, alpha in [(4, 140), (10, 70), (20, 30)]:
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        g = ImageDraw.Draw(glow)
        g.text((x, y), roi_text, font=roi_font, fill=(*roi_color, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(r))
        img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)
    draw.text((x, y + 10), roi_text, font=roi_font, fill=(0, 0, 0, 150))
    draw.text((x, y), roi_text, font=roi_font, fill=roi_color)

    # PROFIT
    sign = "+" if profit_usd > 0 else ""
    profit_text = f"{sign}${profit_usd:.2f}"
    bbox = draw.textbbox((0, 0), profit_text, font=sub_font)
    draw.text(
        ((width - (bbox[2] - bbox[0])) // 2, y + h + 60),
        profit_text, font=sub_font, fill=roi_color
    )

    # TOKEN LOGO
    try:
        if logo_path and os.path.exists(logo_path):
            size = 100
            logo = Image.open(logo_path).convert("RGBA").resize((size, size))
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
            logo.putalpha(mask)
            img.paste(logo, (30, height - size - 30), logo)
    except:
        pass

    # BRAND LOGO
    try:
        if os.path.exists(brand_logo_path):
            size = 100
            brand = Image.open(brand_logo_path).convert("RGBA").resize((size, size))
            img.paste(brand, (width - size - 30, height - size - 30), brand)
    except:
        pass

    img.save(output_path)
