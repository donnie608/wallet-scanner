from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

print("🔥 IMAGE_CARD FILE LOADED 🔥")

def create_card(token_name, wallet, tokens, cost, value, profit, roi,
                logo_path=None, token_symbol=None,
                buy_count=0, sell_count=0,
                sol_price_usd=0):

    width, height = 800, 450
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    draw.text((50, 200), "FULL CARD (UNCHANGED)", fill=(255,255,255))
    img.save("position_card.png")


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
    if roi > 1:
        roi_color = (0, 255, 120)
    elif roi < 1:
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

    # ===== TITLE (BOLD EFFECT) =====
    title = f"{token_name} (${token_symbol})" if token_symbol else token_name
    bbox = draw.textbbox((0,0), title, font=title_font)

    tx = (width - (bbox[2]-bbox[0])) // 2
    ty = 30

    # fake bold (same method as full card)
    for dx, dy in [(0,0),(1,0),(0,1),(1,1)]:
        draw.text((tx+dx, ty+dy),
                  title,
                  font=title_font,
                  fill=(220,220,255))

    # ===== SEPARATOR LINE =====
    line_y = ty + (bbox[3]-bbox[1]) + 15

    draw.line(
        (60, line_y, width - 60, line_y),
        fill=(100, 100, 120),
        width=2
    )

    # ===== ROI =====
    roi_text = f"{roi:.2f}x"
    bbox = draw.textbbox((0,0), roi_text, font=roi_font)
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]

    x = (width - w)//2
    y = (height - h)//2 - 40

    for r, alpha in [(4,140),(10,70),(20,30)]:
        glow = Image.new("RGBA", (width, height), (0,0,0,0))
        g = ImageDraw.Draw(glow)
        g.text((x,y), roi_text, font=roi_font,
               fill=(*roi_color, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(r))
        img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)

    draw.text((x, y+10), roi_text,
              font=roi_font,
              fill=(0,0,0,150))

    draw.text((x, y),
              roi_text,
              font=roi_font,
              fill=roi_color)

    # ===== PROFIT =====
    profit_usd = profit * sol_price_usd
    profit_text = f"{profit:.2f} SOL (${profit_usd:.2f})"
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
