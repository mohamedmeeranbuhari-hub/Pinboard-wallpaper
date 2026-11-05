import os
import random
import math
from PIL import Image, ImageOps, ImageFilter, ImageDraw

def create_storyboard_wallpaper(images_dir, output_path, canvas_size=(1920, 1080)):
    canvas_w, canvas_h = canvas_size
    valid_exts = {'.png', '.jpg', '.jpeg', '.webp'}
    image_files = [f for f in os.listdir(images_dir) 
                   if os.path.splitext(f)[1].lower() in valid_exts and f != 'wallpaper.jpg']
    
    num_images = len(image_files)
    if num_images == 0:
        print("No images found to place on the storyboard.")
        return None
        
    print(f"📌 Placing all {num_images} images onto the storyboard...")

    # Background: Moody artist studio wall / dark corkboard tone
    canvas = Image.new('RGBA', canvas_size, color='#16171a')

    # Add very subtle organic gradient/vignette to canvas
    vignette = Image.new('RGBA', canvas_size, (0, 0, 0, 0))
    vig_draw = ImageDraw.Draw(vignette)
    vig_draw.rectangle([0, 0, canvas_w, canvas_h], fill=(12, 13, 15, 230))
    canvas = Image.alpha_composite(canvas, vignette)

    # 1. Calculate Grid Anchors to distribute across the whole 1920x1080 screen
    # Aspect ratio ~16:9
    aspect = canvas_w / canvas_h
    cols = max(1, int(round(math.sqrt(num_images * aspect))))
    rows = max(1, int(math.ceil(num_images / cols)))

    cell_w = canvas_w / cols
    cell_h = canvas_h / rows

    # Base target dimension for photos (scales down automatically as image count grows)
    base_target_w = int(cell_w * 1.35)
    base_target_h = int(cell_h * 1.35)

    # Generate anchor slots with generous jitter
    anchors = []
    for r in range(rows):
        for c in range(cols):
            cx = (c + 0.5) * cell_w
            cy = (r + 0.5) * cell_h
            
            # Organic jitter (offset up to 35% of cell size)
            jx = random.uniform(-cell_w * 0.35, cell_w * 0.35)
            jy = random.uniform(-cell_h * 0.35, cell_h * 0.35)
            
            anchors.append((cx + jx, cy + jy))

    # Shuffle both anchors and images for true randomness
    random.shuffle(anchors)
    random.shuffle(image_files)

    for idx, img_file in enumerate(image_files):
        img_path = os.path.join(images_dir, img_file)
        anchor_x, anchor_y = anchors[idx % len(anchors)]

        try:
            with Image.open(img_path) as raw_img:
                raw_img = raw_img.convert('RGBA')

                # NO CROPPING: Preserve 100% of the image aspect ratio
                # Scale multiplier: some photos slightly larger hero anchors, some smaller
                scale_mult = random.choice([0.85, 0.95, 1.0, 1.1, 1.25])
                tw = max(120, int(base_target_w * scale_mult))
                th = max(120, int(base_target_h * scale_mult))
                
                raw_img.thumbnail((tw, th), Image.Resampling.LANCZOS)
                w, h = raw_img.size

                # Add a crisp physical photo border (polaroid / white photo print style)
                border_px = max(6, min(14, int(min(w, h) * 0.035)))
                framed_img = ImageOps.expand(raw_img, border=border_px, fill='#fcfcfc')
                fw, fh = framed_img.size

                # Subtle organic tilt: -14 to +14 degrees
                angle = random.uniform(-14.0, 14.0)
                rotated_img = framed_img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
                rw, rh = rotated_img.size

                # Render realistic soft physical drop shadow
                shadow_pad = 20
                shadow_canvas = Image.new('RGBA', (rw + shadow_pad * 2, rh + shadow_pad * 2), (0, 0, 0, 0))
                # Create shadow silhouette from alpha mask
                alpha_mask = rotated_img.split()[3]
                shadow_shape = Image.new('RGBA', (rw, rh), (0, 0, 0, 125))
                shadow_canvas.paste(shadow_shape, (shadow_pad + 3, shadow_pad + 6), mask=alpha_mask)
                blurred_shadow = shadow_canvas.filter(ImageFilter.GaussianBlur(radius=10))

                # Placement on canvas centered around anchor point
                top_left_x = int(anchor_x - (rw / 2))
                top_left_y = int(anchor_y - (rh / 2))

                # Paste shadow first, then the photo
                canvas.paste(blurred_shadow, (top_left_x - shadow_pad, top_left_y - shadow_pad), mask=blurred_shadow)
                canvas.paste(rotated_img, (top_left_x, top_left_y), mask=rotated_img)

        except Exception as e:
            print(f"Skipping {img_file}: {e}")

    final_image = canvas.convert('RGB')
    final_image.save(output_path, quality=95)
    print(f"✨ Storyboard generated with all {num_images} images: {output_path}")
    return output_path

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(current_dir, "wallpaper.jpg")
    create_storyboard_wallpaper(current_dir, out)
