# import math
from PIL import Image, ImageChops, ImageDraw, ImageFilter


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
        self.ants_tile_size = 16
        self.mask_type = 0
        self.background_tile_image = self.generate_tile_image()
        self.ants_tile_image = self.generate_ants_image()

        self.l_image = None
        self.background_image = None

        self.ants_image = None
        self.ants_position = 0
        self.ants_position_update = False

        self.mask_img = None  # Must be gray image (L mode)

    def inc_ants_position(self):
        self.ants_position += 4
        if self.ants_position >= 15:
            self.ants_position = 0
        self.ants_position_update = True

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

    def generate_ants_image(self):
        white = 255

        image_bg = Image.new("L", (self.background_size, self.background_size), 0)
        image_ants = Image.new("L", (self.ants_tile_size, self.ants_tile_size), 0)
        draw_ants = ImageDraw.Draw(image_ants)

        draw_ants.line((-2, 18, 18, -2), fill=white, width=6)
        draw_ants.line((-6, 6, 6, -6), fill=white, width=6)
        draw_ants.line((10, 22, 22, 10), fill=white, width=6)

        dr = self.background_size // self.ants_tile_size
        for i_ in range(0, dr):
            for j_ in range(0, dr):
                image_bg.paste(image_ants, (i_ * self.ants_tile_size, j_ * self.ants_tile_size))

        return image_bg

    def get_background_tile_image(self):
        return self.background_tile_image

    def get_background_tile_size(self):
        return self.background_size

    def set_l_image(self, image: Image):
        self.l_image = image
        self.width = image.width
        self.height = image.height

    def set_mask_image(self, image: Image):
        self.mask_img = image

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

        if self.mask_img is not None:
            # TODO: Add mask cache.
            tmp_mask_img = self.mask_img.copy()

            if tmp_mask_img.mode != "L":
                tmp_mask_img.convert("L")

            if self.mask_type == 0:
                tmp_mask_img2 = ImageChops.invert(tmp_mask_img)
                tmp_mask_img = ImageChops.multiply(tmp_mask_img2, Image.new("L", (w, h), 128))
                tmp_image = Image.new("RGBA", (w, h), (255, 0, 0, 127))
                image.paste(tmp_image, (0, 0), tmp_mask_img)
            else:
                # TODO: Need optimization.
                tmp_image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                tmp_mask_img2 = ImageChops.invert(tmp_mask_img).filter(ImageFilter.CONTOUR)
                tmp_mask_img3 = ImageChops.invert(tmp_mask_img2)

                tmp_image.paste(tmp_mask_img2, (0, 0), tmp_mask_img3)

                if (self.ants_position_update is True
                        or self.ants_image is None
                        or w != self.ants_image.width
                        or h != self.ants_image.height):

                    self.ants_image = Image.new("L", (w, h), 0)
                    self.ants_position_update = False
                    for i_ in range(0, w, self.background_size):
                        for j_ in range(0, h - 1, self.background_size):
                            self.ants_image.paste(self.ants_tile_image, (i_ - self.ants_position, j_))

                tmp_image_3 = tmp_image.convert("L")
                tmp_image_2 = ImageChops.add(tmp_image_3, self.ants_image)
                image.paste(tmp_image_2, (0, 0), tmp_image)

        return image
