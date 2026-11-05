import sys
import os
import shutil
import zipfile
import ctypes
from storyboard_collage import create_storyboard_wallpaper
from wallpaper_setter import set_wallpaper

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_WALLPAPER = os.path.join(PROJECT_DIR, 'wallpaper.jpg')
DOWNLOADS_WALLPAPER_DIR = os.path.expanduser('~/Downloads/dynamic_wallpaper')
VALID_EXTS = {'.png', '.jpg', '.jpeg', '.webp'}

def get_screen_resolution():
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        if w > 0 and h > 0:
            return (w, h)
    except Exception:
        pass
    return (1920, 1080)

def extract_zip_to_project(zip_path):
    extracted_count = 0
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for item in z.infolist():
                ext = os.path.splitext(item.filename)[1].lower()
                if ext in VALID_EXTS:
                    filename = os.path.basename(item.filename)
                    if filename:
                        dest_path = os.path.join(PROJECT_DIR, filename)
                        with z.open(item) as src, open(dest_path, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        extracted_count += 1
        os.remove(zip_path)
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}")
    return extracted_count

def sync_from_downloads():
    if not os.path.exists(DOWNLOADS_WALLPAPER_DIR):
        return

    imported = 0
    for root, dirs, files in os.walk(DOWNLOADS_WALLPAPER_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            if ext == '.zip':
                c = extract_zip_to_project(full_path)
                imported += c
            elif ext in VALID_EXTS:
                dest = os.path.join(PROJECT_DIR, f)
                if not os.path.exists(dest):
                    try:
                        shutil.copy2(full_path, dest)
                        imported += 1
                    except Exception:
                        pass
    if imported > 0:
        print(f"🎉 Auto-imported {imported} new image(s) from Downloads!")

def main():
    sync_from_downloads()

    # Process any dragged-and-dropped files or ZIPs
    dropped_files = sys.argv[1:]
    if dropped_files:
        print(f"Processing {len(dropped_files)} dropped item(s)...")
        for file_path in dropped_files:
            if not os.path.isfile(file_path):
                continue
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.zip':
                c = extract_zip_to_project(file_path)
                print(f"Extracted {c} images from ZIP: {os.path.basename(file_path)}")
            elif ext in VALID_EXTS:
                filename = os.path.basename(file_path)
                dest = os.path.join(PROJECT_DIR, filename)
                if os.path.abspath(file_path) == os.path.abspath(dest):
                    continue
                try:
                    shutil.copy2(file_path, dest)
                    print(f"Added image: {filename}")
                except Exception as e:
                    print(f"Skipped {filename}: {e}")

    screen_size = get_screen_resolution()
    print(f"\n🎨 Building Messy Storyboard Wallpaper ({screen_size[0]}x{screen_size[1]})...")
    result = create_storyboard_wallpaper(PROJECT_DIR, OUTPUT_WALLPAPER, canvas_size=screen_size)

    if result:
        print("\n🖼️ Setting Windows wallpaper...")
        set_wallpaper(result)

    print("\n✅ Storyboard updated! Enjoy your new wallpaper.")

if __name__ == "__main__":
    main()
