from PIL import ImageTk, Image
import io
import base64
import tkinter


def _pil_to_tk(image: Image.Image):
    """
    Convert a PIL Image to a tkinter-compatible PhotoImage.

    Pillow's ImageTk.PhotoImage relies on _imagingtk (a C extension) which
    requires the PIL-Tk bridge to be initialised before SDL/pygame loads.
    When SDL is present on macOS, that bridge is broken.

    Workaround: encode the PIL image as a PNG into a BytesIO buffer and pass
    the raw bytes to tkinter.PhotoImage, which natively supports PNG (Tk 8.6+).
    This route never touches _imagingtk at all.
    """
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return tkinter.PhotoImage(data=base64.b64encode(buf.read()))


class ImageProcess:

    def __init__(self):
        return

    def generate(self, img_path, width, height):
        width = round(width)
        height = round(height)
        image_background = Image.open(img_path).convert("RGBA")
        image_background = image_background.resize((width, height), Image.LANCZOS)
        return _pil_to_tk(image_background)

    def open_img(self, img_path, width, height):
        width = round(width)
        height = round(height)
        image_background = Image.open(img_path)
        image_background = image_background.resize((width, height), Image.LANCZOS)
        return image_background

    def crop_img(self, img_path, width, height, region):
        width = round(width)
        height = round(height)
        img_opened = self.open_img(img_path, width, height)
        iw, ih = img_opened.size
        # Clamp region to image bounds to avoid "tile cannot extend outside image"
        x0 = max(0, min(round(region[0]), iw))
        y0 = max(0, min(round(region[1]), ih))
        x1 = max(0, min(round(region[2]), iw))
        y1 = max(0, min(round(region[3]), ih))
        if x1 <= x0:
            x1 = min(x0 + 1, iw)
        if y1 <= y0:
            y1 = min(y0 + 1, ih)
        img_crop = img_opened.crop((x0, y0, x1, y1))
        return _pil_to_tk(img_crop)
