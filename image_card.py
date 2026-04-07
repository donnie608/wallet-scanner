from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

print("🔥 IMAGE_CARD FILE LOADED 🔥")

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

    width, height = 800, 450
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    draw.text((50, 200), "FULL CARD (UNCHANGED)", fill=(255,255,255))
    img.save("position_card.png")

# =========================
# WOW MINIMAL CARD
# =========================
def create_minimal_card(token_name, profit, roi,
                        logo_path=None, token_symbol=None,
                        sol_price_usd=0):

    width, height = 800, 450
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE_DIR, "minimal_card.png")
    font_path = os.path.join(BASE_DIR, "Inter.ttf")
    brand_logo_path = os.path.join(BASE_DIR, "logo.png")

    img = Image.new("RGBA", (width, height))

    # ROI color logic
    if roi > 1:
        base_color = (0, 255, 140)
        dark_color = (0, 180, 110)
    elif roi < 1:
        base_color = (255, 90, 90)
        dark_color = (200, 60, 60)
    else:
        base_color = (60, 60, 60)
        dark_color = (20, 20, 20)

    # ===== BACKGROUND =====
    draw_bg = ImageDraw.Draw(img)
    for y in range(height):
        draw_bg.line((0, y, width, y),
                     fill=(50 + y//6, 20 + y//12, 100 + y//3))

    # ===== RADIAL ENERGY =====
    energy = Image.new("RGBA", (width, height), (0,0,0,0))
    e_draw = ImageDraw.Draw(energy)
    cx, cy = width//2, height//2

    for r in range(0, 300, 10):
        alpha = int(80 * (1 - r/300))
        e_draw.ellipse((cx-r, cy-r, cx+r, cy+r),
                       fill=(*base_color, alpha))

    energy = energy.filter(ImageFilter.GaussianBlur(40))
    img = Image.alpha_composite(img, energy)

    draw = ImageDraw.Draw(img)

    try:
        roi_font = ImageFont.truetype(font_path, 150)
        sub_font = ImageFont.truetype(font_path, 42)
        title_font = ImageFont.truetype(font_path, 36)
    except:
        roi_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # ===== TITLE CENTERED =====
    title = f"{token_name} (${token_symbol})" if token_symbol else token_name
    bbox = draw.textbbox((0,0), title, font=title_font)
    draw.text(((width-(bbox[2]-bbox[0]))//2, 30),
              title, font=title_font, fill=(220,220,255))

    # ===== ROI TEXT =====
    roi_text = f"{roi:.2f}x"
    bbox = draw.textbbox((0,0), roi_text, font=roi_font)
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]

    x = (width - w)//2
    y = (height - h)//2 - 20

    # ===== GRADIENT TEXT =====
    mask = Image.new("L", (width, height), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.text((x,y), roi_text, font=roi_font, fill=255)

    gradient = Image.new("RGBA", (width, height))
    g_draw = ImageDraw.Draw(gradient)

    for i in range(height):
        ratio = i / height
        r = int(base_color[0]*(1-ratio) + dark_color[0]*ratio)
        g = int(base_color[1]*(1-ratio) + dark_color[1]*ratio)
        b = int(base_color[2]*(1-ratio) + dark_color[2]*ratio)
        g_draw.line((0,i,width,i), fill=(r,g,b))

    img.paste(gradient, (0,0), mask)

    # ===== TIGHT GLOW =====
    for r, alpha in [(4,120),(8,60),(16,30)]:
        glow = Image.new("RGBA", (width, height), (0,0,0,0))
        g = ImageDraw.Draw(glow)
        g.text((x,y), roi_text, font=roi_font,
               fill=(*base_color, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(r))
        img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)

    # ===== EDGE HIGHLIGHT =====
    draw.text((x, y-2), roi_text,
              font=roi_font,
              fill=(255,255,255,60))

    # ===== SHADOW =====
    draw.text((x, y+10), roi_text,
              font=roi_font,
              fill=(0,0,0,150))

    # ===== PROFIT =====
    profit_usd = profit * sol_price_usd
    profit_text = f"{profit:.2f} SOL (${profit_usd:.2f})"
    bbox = draw.textbbox((0,0), profit_text, font=sub_font)

    draw.text(((width-(bbox[2]-bbox[0]))//2, y+h+60),
              profit_text, font=sub_font, fill=base_color)

    # ===== TOKEN LOGO =====
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

    # ===== BRAND LOGO =====
    try:
        if os.path.exists(brand_logo_path):
            size = 100
            brand = Image.open(brand_logo_path).convert("RGBA").resize((size,size))
            img.paste(brand,(width-size-30,height-size-30),brand)
    except:
        pass

    img.save(output_path)
