import os
import random
from PIL import Image, ImageOps, ImageDraw, ImageFilter

def crop_to_fill(img, target_w, target_h):
    """Aspect-cover crop with LANCZOS resampling to perfectly fill the card."""
    img = img.convert('RGBA')
    w, h = img.size
    scale = max(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))

def round_corners_and_style(img, radius=18, border_color=(255, 255, 255, 35)):
    """Apply smooth rounded corners and a sleek subtle glass/border stroke."""
    w, h = img.size
    
    # 2x supersampling for ultra smooth anti-aliased corners
    scale = 2
    mask = Image.new('L', (w * scale, h * scale), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle((0, 0, w * scale - 1, h * scale - 1), radius=radius * scale, fill=255)
    mask = mask.resize((w, h), Image.Resampling.LANCZOS)
    
    styled = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    styled.paste(img, (0, 0), mask=mask)
    
    # Draw subtle modern border
    border_draw = ImageDraw.Draw(styled)
    border_draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, outline=border_color, width=1)
    
    return styled, mask

def get_bento_templates(canvas_w=1920, canvas_h=1080):
    """Generates modern editorial Bento Grid layout slots."""
    margin = 36
    gap = 16
    usable_w = canvas_w - (margin * 2)
    usable_h = canvas_h - (margin * 2)
    
    # --- Template 1: Asymmetric Magazine Editorial (8 Cards) ---
    t1 = []
    # Left Hero Column
    col1_w = int(usable_w * 0.28)
    h1_a = int(usable_h * 0.61)
    h1_b = usable_h - h1_a - gap
    t1.append((margin, margin, col1_w, h1_a))
    t1.append((margin, margin + h1_a + gap, col1_w, h1_b))
    
    # Center Column
    col2_x = margin + col1_w + gap
    col2_w = int(usable_w * 0.38)
    h2_top = int(usable_h * 0.32)
    h2_bot = int(usable_h * 0.32)
    h2_mid = usable_h - h2_top - h2_bot - (gap * 2)
    t1.append((col2_x, margin, col2_w, h2_top))
    
    # Split middle slot into 2 squares
    mid_sub_w = (col2_w - gap) // 2
    t1.append((col2_x, margin + h2_top + gap, mid_sub_w, h2_mid))
    t1.append((col2_x + mid_sub_w + gap, margin + h2_top + gap, col2_w - mid_sub_w - gap, h2_mid))
    t1.append((col2_x, margin + h2_top + h2_mid + (gap * 2), col2_w, h2_bot))
    
    # Right Column
    col3_x = col2_x + col2_w + gap
    col3_w = canvas_w - margin - col3_x
    h3_a = int(usable_h * 0.46)
    h3_b = usable_h - h3_a - gap
    t1.append((col3_x, margin, col3_w, h3_a))
    t1.append((col3_x, margin + h3_a + gap, col3_w, h3_b))
    
    # --- Template 2: Modern 4-Column Mosaic (9 Cards) ---
    t2 = []
    col_w = (usable_w - (3 * gap)) // 4
    
    # Col 0
    t2.append((margin, margin, col_w, int(usable_h * 0.58)))
    t2.append((margin, margin + int(usable_h * 0.58) + gap, col_w, usable_h - int(usable_h * 0.58) - gap))
    
    # Col 1
    c1_x = margin + col_w + gap
    t2.append((c1_x, margin, col_w, int(usable_h * 0.38)))
    t2.append((c1_x, margin + int(usable_h * 0.38) + gap, col_w, usable_h - int(usable_h * 0.38) - gap))
    
    # Col 2
    c2_x = c1_x + col_w + gap
    t2.append((c2_x, margin, col_w, int(usable_h * 0.65)))
    t2.append((c2_x, margin + int(usable_h * 0.65) + gap, col_w, usable_h - int(usable_h * 0.65) - gap))
    
    # Col 3
    c3_x = c2_x + col_w + gap
    t2.append((c3_x, margin, col_w, int(usable_h * 0.45)))
    c3_sub_h = (usable_h - int(usable_h * 0.45) - (gap * 2)) // 2
    t2.append((c3_x, margin + int(usable_h * 0.45) + gap, col_w, c3_sub_h))
    t2.append((c3_x, margin + int(usable_h * 0.45) + (gap * 2) + c3_sub_h, col_w, usable_h - int(usable_h * 0.45) - (gap * 2) - c3_sub_h))

    # --- Template 3: Grand Centerpiece Showcase (7 Cards) ---
    t3 = []
    side_w = int(usable_w * 0.25)
    center_w = usable_w - (side_w * 2) - (gap * 2)
    
    # Left
    h_side = (usable_h - gap) // 2
    t3.append((margin, margin, side_w, h_side))
    t3.append((margin, margin + h_side + gap, side_w, usable_h - h_side - gap))
    
    # Center Giant Showcase + Lower Anchor
    center_x = margin + side_w + gap
    h_main = int(usable_h * 0.68)
    t3.append((center_x, margin, center_w, h_main))
    t3.append((center_x, margin + h_main + gap, center_w, usable_h - h_main - gap))
    
    # Right
    right_x = center_x + center_w + gap
    h_r1 = int(usable_h * 0.32)
    h_r2 = int(usable_h * 0.34)
    h_r3 = usable_h - h_r1 - h_r2 - (gap * 2)
    t3.append((right_x, margin, side_w, h_r1))
    t3.append((right_x, margin + h_r1 + gap, side_w, h_r2))
    t3.append((right_x, margin + h_r1 + h_r2 + (gap * 2), side_w, h_r3))

    return [t1, t2, t3]

def create_bento_wallpaper(images_dir, output_path, canvas_size=(1920, 1080)):
    valid_exts = {'.png', '.jpg', '.jpeg', '.webp'}
    image_files = [f for f in os.listdir(images_dir) if os.path.splitext(f)[1].lower() in valid_exts]
    
    if not image_files:
        print(f"No images found in {images_dir}")
        return None
        
    random.shuffle(image_files)
    
    # Pick one of the beautiful Bento templates
    templates = get_bento_templates(canvas_size[0], canvas_size[1])
    slots = random.choice(templates)
    
    # Build luxurious atmospheric background:
    # 1. Base dark charcoal
    canvas = Image.new('RGBA', canvas_size, color='#0f1013')
    
    # 2. Add an ambient blurred glow from one of the pins for cohesion
    try:
        sample_path = os.path.join(images_dir, image_files[0])
        with Image.open(sample_path) as ambient_sample:
            ambient = ambient_sample.convert('RGBA')
            ambient = ambient.resize(canvas_size, Image.Resampling.LANCZOS)
            ambient = ambient.filter(ImageFilter.GaussianBlur(radius=80))
            # Darken the ambient glow so it is moody and subtle
            darkener = Image.new('RGBA', canvas_size, (15, 16, 19, 185))
            ambient = Image.alpha_composite(ambient, darkener)
            canvas = Image.alpha_composite(canvas, ambient)
    except Exception as e:
        print(f"Ambient background fallback: {e}")

    # Process and place images into each Bento box
    used_count = min(len(slots), len(image_files))
    for i in range(used_count):
        x, y, w, h = slots[i]
        img_file = image_files[i % len(image_files)]
        img_path = os.path.join(images_dir, img_file)
        
        try:
            with Image.open(img_path) as source_img:
                # 1. Crop to fill the slot with aspect-cover
                card = crop_to_fill(source_img, w, h)
                
                # 2. Round corners and apply subtle modern border
                styled_card, card_mask = round_corners_and_style(card, radius=18)
                
                # 3. Soft drop shadow
                shadow = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow)
                shadow_draw.rounded_rectangle((4, 6, w + 14, h + 16), radius=20, fill=(0, 0, 0, 110))
                shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))
                
                # Paste shadow then card onto canvas
                canvas.paste(shadow, (x - 10, y - 10), mask=shadow)
                canvas.paste(styled_card, (x, y), mask=card_mask)
        except Exception as e:
            print(f"Failed to process {img_file}: {e}")

    final_image = canvas.convert('RGB')
    final_image.save(output_path, quality=96)
    print(f"✨ Successfully generated Bento Gallery wallpaper: {output_path}")
    return output_path

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output = os.path.join(current_dir, "wallpaper.jpg")
    create_bento_wallpaper(current_dir, output)
