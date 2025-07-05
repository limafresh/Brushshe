# import math
from PIL import Image, ImageDraw


class BhComposer:
    def __init__(
        self,
        width: int,
        height: int,
        *args,
        **kwargs,
    ):
        self.width = width  # Real image width.
        self.height = height  # Real image height.

        self.tree = {}  # Empty

        self.background_color_1 = "#F0F0F0"
        self.background_color_2 = "#D0D0D0"
        self.background_size = 256
        self.background_tile_size = 16
        self.background_tile_image = self.generate_tile_image()

        self.l_image = None
        self.background_image = None

    def generate_tile_image(self):
        image_bg = Image.new("RGB", (self.background_size, self.background_size), self.background_color_1)
        draw = ImageDraw.Draw(image_bg)

        d = 0
        dr = self.background_size // self.background_tile_size
        for i_ in range(0, dr):
            for j_ in range(d % 2, dr, 2):
                draw.rectangle(
                    (
                        i_ * self.background_tile_size,
                        j_ * self.background_tile_size,
                        i_ * self.background_tile_size + self.background_tile_size - 1,
                        j_ * self.background_tile_size + self.background_tile_size - 1,
                    ),
                    fill=self.background_color_2,
                    outline=None,
                )
            d += 1

        return image_bg

    def get_background_tile_image(self):
        return self.background_tile_image

    def get_background_tile_size(self):
        return self.background_size

    def set_l_image(self, image: Image):
        self.l_image = image
        self.width = image.width
        self.height = image.height

    def get_compose_image(self, x1, y1, x2, y2):
        if self.l_image is None:
            return

        if x1 is None:
            x1 = 0
        if y1 is None:
            y1 = 0
        if x2 is None:
            x2 = self.width - 1
        if y2 is None:
            y2 = self.height - 1

        w = x2 - x1 + 1
        h = y2 - y1 + 1

        if self.background_image is None or w != self.background_image.width or h != self.background_image.height:
            # Background image MUST be RGB (without alpha) for optimization on tk (and ctk).
            self.background_image = Image.new("RGB", (w, h), self.background_color_1)
            for i_ in range(0, w - 1, self.background_size):
                for j_ in range(0, h - 1, self.background_size):
                    self.background_image.paste(self.background_tile_image, (i_, j_))

        image = self.background_image.copy()

        if self.l_image.mode == "RGBA":
            image.paste(self.l_image, (0, 0), self.l_image)
        else:
            image.paste(self.l_image, (0, 0))

        return image
