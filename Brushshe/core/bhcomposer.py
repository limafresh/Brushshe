# import math
from PIL import (
    Image,
    # ImageColor,
    ImageDraw,
    ImageTk
)


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
        self.background_tile_image_tk = ImageTk.PhotoImage(self.background_tile_image)

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
                        j_ * self.background_tile_size + self.background_tile_size - 1
                    ),
                    fill=self.background_color_2,
                    outline=None,
                )
            d += 1

        return image_bg

    def get_background_tile_image(self):
        return self.background_tile_image

    def get_background_tile_image_tk(self):
        return self.background_tile_image_tk

    def get_background_tile_size(self):
        return self.background_size
