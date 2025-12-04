# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


def bh_draw_line(image_draw, x1, y1, x2, y2, color, size, brush_shape, tool):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    if brush_shape == "circle" or tool == "shape":
        image_draw_shape = image_draw.ellipse
    elif brush_shape == "square":
        image_draw_shape = image_draw.rectangle

    while True:
        # Better variant for pixel compatible.
        if size <= 1:
            image_draw.point([x1, y1], fill=color)
        else:
            image_draw_shape(
                [
                    x1 - (size - 1) // 2,
                    y1 - (size - 1) // 2,
                    x1 + size // 2,
                    y1 + size // 2,
                ],
                fill=color,
                outline=color,
            )

        if abs(x1 - x2) < 1 and abs(y1 - y2) < 1:
            break

        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy


def bh_draw_recoloring_line(image, x1, y1, x2, y2, color_from, color_to, size):
    d1 = (size - 1) // 2
    d2 = size // 2
    # dd = (d2 - d1) / 2
    max_x = image.width
    max_y = image.height

    x = x1
    y = y1
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    # It's for circuit brush, but it work too slow.
    # ((ii - x - dd) ** 2 + (jj - y - dd) ** 2 < ((d1 + d2 + .5)/2) ** 2

    # buffer = set()
    is_line = False

    while True:
        if size <= 1:
            if x >= 0 and x < max_x and y >= 0 and y < max_y and image.getpixel((x, y)) == color_from:
                image.putpixel((int(x), int(y)), color_to)
        else:
            if is_line is False:
                for ii in range(int(x - d1), int(x + d2 + 1)):
                    for jj in range(int(y - d1), int(y + d2 + 1)):
                        if ii >= 0 and ii < max_x and jj >= 0 and jj < max_y and image.getpixel((ii, jj)) == color_from:
                            image.putpixel((ii, jj), color_to)
                            # buffer.add((ii, jj))
            else:
                # Now we can check firsts or lasts lines only.

                # Checking horizontal movement.
                if sx > 0:
                    ii = int(x + d2)
                else:
                    ii = int(x - d1)

                for jj in range(int(y - d1), int(y + d2 + 1)):
                    if ii >= 0 and ii < max_x and jj >= 0 and jj < max_y and image.getpixel((ii, jj)) == color_from:
                        image.putpixel((ii, jj), color_to)
                        # buffer.add((ii, jj))

                # Checking vertical movement.
                if sy > 0:
                    jj = int(y + d2)
                else:
                    jj = int(y - d1)

                for ii in range(int(x - d1), int(x + d2 + 1)):
                    if ii >= 0 and ii < max_x and jj >= 0 and jj < max_y and image.getpixel((ii, jj)) == color_from:
                        image.putpixel((ii, jj), color_to)
                        # buffer.add((ii, jj))

        if abs(x - x2) < 1 and abs(y - y2) < 1:
            # self.draw.point([*buffer], fill=color)
            break

        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

        is_line = True
