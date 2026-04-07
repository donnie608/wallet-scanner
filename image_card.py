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

    img = Image.new("RGBA", (width, height), (0,0,0,255))  # 🔥 BLACK BACKGROUND

    # ROI COLOR
    if roi > 1:
        roi_color = (0, 255, 120)
    elif roi < 1:
        roi_color = (255, 80, 80)
    else:
        roi_color = (120, 120, 120)

    # ===== NEON BORDER =====
    border = Image.new("RGBA", (width, height), (0,0,0,0))
    b_draw = ImageDraw.Draw(border)

    margin = 10
    for i, blur in [(8,120), (16,60), (24,30)]:
        temp = Image.new("RGBA", (width, height), (0,0,0,0))
        t_draw = ImageDraw.Draw(temp)

        t_draw.rounded_rectangle(
            (margin, margin, width-margin, height-margin),
            radius=30,
            outline=(*roi_color, blur),
            width=3
        )

        temp = temp.filter(ImageFilter.GaussianBlur(i))
        border = Image.alpha_composite(border, temp)

    # sharp edge
    b_draw.rounded_rectangle(
        (margin, margin, width-margin, height-margin),
        radius=30,
        outline=roi_color,
        width=2
    )

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

    # TITLE CENTERED
    title = f"{token_name} (${token_symbol})" if token_symbol else token_name
    bbox = draw.textbbox((0,0), title, font=title_font)
    draw.text(((width-(bbox[2]-bbox[0]))//2, 30),
              title, font=title_font, fill=(200,200,220))

    # ROI POSITION
    roi_text = f"{roi:.2f}x"
    bbox = draw.textbbox((0,0), roi_text, font=roi_font)
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]

    x = (width - w)//2
    y = (height - h)//2 - 40

    # ===== ROI GLOW =====
    for r, alpha in [(4,140),(10,70),(20,30)]:
        glow = Image.new("RGBA", (width, height), (0,0,0,0))
        g = ImageDraw.Draw(glow)
        g.text((x,y), roi_text, font=roi_font,
               fill=(*roi_color, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(r))
        img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)

    # SHADOW
    draw.text((x, y+10), roi_text,
              font=roi_font,
              fill=(0,0,0,150))

    # MAIN ROI
    draw.text((x, y),
              roi_text,
              font=roi_font,
              fill=roi_color)

    # PROFIT
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
