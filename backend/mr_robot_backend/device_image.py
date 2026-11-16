"""Convert the local model's PNG to a fixed-size little-endian RGB565 frame."""
import base64
import io
import struct


def image_pixels(png, side):
    # Only the optional board preview needs Pillow. The browser keeps the original PNG.
    from PIL import Image, ImageOps

    with Image.open(io.BytesIO(base64.b64decode(png, validate=True)), formats=["PNG"]) as image:
        if image.size != (512, 512) or side != 300:
            raise ValueError("unsupported_image_size")
        resampled = ImageOps.fit(image.convert("RGB"), (side, side), Image.Resampling.LANCZOS)
        return b"".join(struct.pack("<H", ((r & 0xf8) << 8) | ((g & 0xfc) << 3) | (b >> 3))
                        for r, g, b in resampled.get_flattened_data())
