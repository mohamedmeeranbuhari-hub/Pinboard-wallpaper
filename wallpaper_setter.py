import ctypes
import os

def set_wallpaper(image_path):
    abs_path = os.path.abspath(image_path)
    if not os.path.exists(abs_path):
        print(f"Error: Wallpaper file does not exist at {abs_path}")
        return False

    # SPI_SETDESKWALLPAPER = 20
    # SPIF_UPDATEINIFILE (1) | SPIF_SENDWININICHANGE (2) = 3
    result = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
    if result:
        print(f"Desktop background updated successfully to: {abs_path}")
        return True
    else:
        print("Failed to set desktop wallpaper.")
        return False
