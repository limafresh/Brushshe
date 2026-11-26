# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math
import random

from PIL import Image, ImageChops, ImageColor, ImageDraw

directions = ["Vertically", "Horizontally", "Diagonally", "Radially", "Rings", "Noise"]


def gradient_fill(
    x: float, y: float, image: Image.Image, color_1: str, color_2: str, direction: str
) -> Image.Image | None:
    if direction not in directions:
        raise ValueError("Unknown direction")

    if not (0 <= x < image.width and 0 <= y < image.height):
        return

    start_color = ImageColor.getrgb(color_1)
    end_color = ImageColor.getrgb(color_2)
    threshold = 50

    temp = image.copy()

    fill_color = (255, 0, 255, 255) if image.mode == "RGBA" else (255, 0, 255)
    try:
        ImageDraw.floodfill(temp, (x, y), fill_color, thresh=threshold)
    except Exception:
        return

    diff = ImageChops.difference(image.convert("RGB"), temp.convert("RGB"))
    mask = diff.convert("L").point(lambda p: 255 if p != 0 else 0)

    bbox = mask.getbbox()
    if not bbox:
        return
    min_x, min_y, max_x, max_y = bbox

    gradient = Image.new(image.mode, image.size)
    for j in range(min_y, max_y + 1):
        for i in range(min_x, max_x + 1):
            if 0 <= i < mask.width and 0 <= j < mask.height and mask.getpixel((i, j)) == 255:
                if direction == "Vertically":
                    ratio = (j - min_y) / max(1, (max_y - min_y))
                elif direction == "Horizontally":
                    ratio = (i - min_x) / max(1, (max_x - min_x))
                elif direction == "Diagonally":
                    ratio = ((i - min_x) + (j - min_y)) / max(1, (max_x - min_x + max_y - min_y))
                elif direction == "Radially":
                    cx = (min_x + max_x) // 2
                    cy = (min_y + max_y) // 2
                    max_dist = math.hypot(max_x - cx, max_y - cy)
                    ratio = math.hypot(i - cx, j - cy) / max(1, max_dist)
                elif direction == "Rings":
                    cx = (min_x + max_x) // 2
                    cy = (min_y + max_y) // 2
                    ratio = abs(math.sin(math.hypot(i - cx, j - cy) / 10))
                elif direction == "Noise":
                    ratio = random.random()

                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)

                if image.mode == "RGBA":
                    gradient.putpixel((i, j), (r, g, b, 255))
                else:
                    gradient.putpixel((i, j), (r, g, b))

    filled = Image.composite(gradient, image, mask)

    return filled
