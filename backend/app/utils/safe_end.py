import io
from PIL import Image, ImageOps

MAX_SIDE = 1536  # safe for CPU + fast

def load_image_safe(image_bytes: bytes) -> Image.Image:
    # Open safely
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)  # fix rotated images

    # Convert to RGB no matter what (handles RGBA/CMYK/L/P)
    img = img.convert("RGB")

    # Resize huge images (prevents memory issues)
    w, h = img.size
    m = max(w, h)
    if m > MAX_SIDE:
        scale = MAX_SIDE / m
        img = img.resize((int(w * scale), int(h * scale)))

    return img