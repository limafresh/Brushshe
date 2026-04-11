# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math
import random

from core.bhbrush import bh_draw_recoloring_line
from core.bhhistory import BhHistory, BhPoint
from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFont
from utils import common
from utils.translator import _


class PaintTools:
    """Brush"""

    def brush(self, type="brush"):
        prev_x = None
        prev_y = None
        point_history = None

        if type == "brush":
            self.set_tool("brush", "Brush", self.brush_size, 1, 50, "pencil")
        elif type == "eraser":
            self.set_tool("eraser", "Eraser", self.eraser_size, 1, 50, "target")
        else:
            print("Warning: Incorrect brush type. Set default as.")
            self.set_tool("brush", "Brush", self.brush_size, 1, 50, "pencil")

        def paint(event):
            nonlocal prev_x, prev_y, point_history

            if self.is_brush_smoothing is False:
                x, y = self.canvas_to_pict_xy(event.x, event.y)
            else:
                if point_history is None:
                    point_history = BhHistory(limit_length=self.brush_smoothing_factor)
                xf, yf = self.canvas_to_pict_xy_f(event.x, event.y)
                point_history.add_point(BhPoint(x=xf, y=yf, pressure=1.0))
                s_point = point_history.get_smoothing_point(
                    self.brush_smoothing_factor,
                    self.brush_smoothing_quality,
                )
                if s_point is not None:
                    x = int(s_point.x)
                    y = int(s_point.y)
                else:
                    x, y = self.canvas_to_pict_xy(event.x, event.y)

            if prev_x is not None and prev_y is not None:
                self.draw_line(prev_x, prev_y, x, y)
            else:
                self.draw_line(x, y, x, y)

            prev_x, prev_y = x, y

            self.update_canvas()
            draw_brush_halo(x, y)

        def stop_paint(event):
            nonlocal prev_x, prev_y, point_history

            if prev_x is None:
                return

            self.ui.canvas.delete("tools")
            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_brush_halo(x, y)

            point_history = None
            prev_x, prev_y = (None, None)
            self.record_action()

        def move(event):
            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_brush_halo(x, y)

        def draw_brush_halo(x, y):
            self.ui.canvas.delete("tools")

            d1 = (self.tool_size - 1) // 2
            d2 = self.tool_size // 2

            # TODO: Need use the pixel perfect halo for zoom >= 2 if it doesn't too slow.

            if self.brush_shape == "circle":
                canvas_create_shape = self.ui.canvas.create_oval
            elif self.brush_shape == "square":
                canvas_create_shape = self.ui.canvas.create_rectangle

            canvas_create_shape(
                int((x - d1) * self.zoom - 1),
                int((y - d1) * self.zoom - 1),
                int((x + d2 + 1) * self.zoom),
                int((y + d2 + 1) * self.zoom),
                outline="white",
                width=1,
                tag="tools",
            )
            canvas_create_shape(
                int((x - d1) * self.zoom),
                int((y - d1) * self.zoom),
                int((x + d2 + 1) * self.zoom - 1),
                int((y + d2 + 1) * self.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
            )

        def leave(event):
            self.ui.canvas.delete("tools")

        self.ui.canvas.bind("<Button-1>", paint)
        self.ui.canvas.bind("<B1-Motion>", paint)
        self.ui.canvas.bind("<ButtonRelease-1>", stop_paint)
        self.ui.canvas.bind("<Motion>", move)
        self.ui.canvas.bind("<Leave>", leave)

    """Eraser"""

    def eraser(self):
        self.brush(type="eraser")

    """Fill"""

    def start_fill(self):
        self.set_tool("fill", "Fill", None, None, None, "cross")
        self.ui.canvas.bind("<Button-1>", self.fill)

    def fill(self, event):
        x, y = self.canvas_to_pict_xy(event.x, event.y)
        tmp_image = self.image if self.selected_mask_img is None else self.image.copy()

        if self.image.mode == "RGBA":
            fill_color = common.rgb_tuple_to_rgba_tuple(ImageColor.getrgb(self.brush_color), 255)
        else:
            fill_color = ImageColor.getrgb(self.brush_color)

        if self.is_gradient_fill.get():
            self.gradient_fill(x, y)
        else:
            ImageDraw.floodfill(tmp_image, (x, y), fill_color)
            if self.selected_mask_img is not None:
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)

        self.update_canvas()
        self.record_action()

    def gradient_fill(self, x, y):
        def color_distance(c1, c2):
            return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5

        if not (0 <= x < self.image.width and 0 <= y < self.image.height):
            return

        start_color = ImageColor.getrgb(self.brush_color)
        end_color = ImageColor.getrgb(self.second_brush_color)
        threshold = 50
        direction = self.gradient_mode_optionmenu.get()

        temp = self.image.copy()

        fill_color = (255, 0, 255, 255) if self.image.mode == "RGBA" else (255, 0, 255)
        try:
            ImageDraw.floodfill(temp, (x, y), fill_color, thresh=threshold)
        except Exception:
            return

        diff = ImageChops.difference(self.image.convert("RGB"), temp.convert("RGB"))
        mask = diff.convert("L").point(lambda p: 255 if p != 0 else 0)

        bbox = mask.getbbox()
        if not bbox:
            return
        min_x, min_y, max_x, max_y = bbox

        gradient = Image.new(self.image.mode, self.image.size)
        for j in range(min_y, max_y + 1):
            for i in range(min_x, max_x + 1):
                if 0 <= i < mask.width and 0 <= j < mask.height and mask.getpixel((i, j)) == 255:
                    if direction == _("Vertically"):
                        ratio = (j - min_y) / max(1, (max_y - min_y))
                    elif direction == _("Horizontally"):
                        ratio = (i - min_x) / max(1, (max_x - min_x))
                    elif direction == _("Diagonally"):
                        ratio = ((i - min_x) + (j - min_y)) / max(1, (max_x - min_x + max_y - min_y))
                    elif direction == _("Radially"):
                        cx = (min_x + max_x) // 2
                        cy = (min_y + max_y) // 2
                        max_dist = math.hypot(max_x - cx, max_y - cy)
                        ratio = math.hypot(i - cx, j - cy) / max(1, max_dist)
                    elif direction == _("Rings"):
                        cx = (min_x + max_x) // 2
                        cy = (min_y + max_y) // 2
                        ratio = abs(math.sin(math.hypot(i - cx, j - cy) / 10))
                    elif direction == _("Noise"):
                        ratio = random.random()

                    r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                    g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                    b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)

                    if self.image.mode == "RGBA":
                        gradient.putpixel((i, j), (r, g, b, 255))
                    else:
                        gradient.putpixel((i, j), (r, g, b))

        filled = Image.composite(gradient, self.image, mask)

        if self.selected_mask_img is None:
            self.image.paste(filled)
        else:
            self.image.paste(filled, (0, 0), self.selected_mask_img)

    """Recoloring brush"""

    def recoloring_brush(self):
        self.set_tool("r-brush", "R. Brush", self.brush_size, 1, 50, "pencil")

        prev_x = None
        prev_y = None
        point_history = None

        def drawing(event):
            nonlocal prev_x, prev_y, point_history

            if self.is_brush_smoothing is False:
                x, y = self.canvas_to_pict_xy(event.x, event.y)
            else:
                if point_history is None:
                    point_history = BhHistory(limit_length=self.brush_smoothing_factor)
                xf, yf = self.canvas_to_pict_xy_f(event.x, event.y)
                point_history.add_point(BhPoint(x=xf, y=yf, pressure=1.0))
                s_point = point_history.get_smoothing_point(
                    self.brush_smoothing_factor,
                    self.brush_smoothing_quality,
                )
                if s_point is not None:
                    x = int(s_point.x)
                    y = int(s_point.y)
                else:
                    x, y = self.canvas_to_pict_xy(event.x, event.y)

            if prev_x is None:
                prev_x, prev_y = x, y

            draw_recoloring_brush(x, y, prev_x, prev_y)
            prev_x, prev_y = x, y

            self.update_canvas()  # force=False  # Do not delete tools shapes.
            draw_brush_halo(x, y)

        def end(event):
            nonlocal prev_x, prev_y, point_history

            if prev_x is None:
                return

            self.ui.canvas.delete("tools")
            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_brush_halo(x, y)

            point_history = None
            prev_x, prev_y = (None, None)
            self.record_action()

        def move(event):
            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_brush_halo(x, y)

        def draw_recoloring_brush(x1, y1, x2, y2):
            color_to = ImageColor.getrgb(self.brush_color)
            color_from = ImageColor.getrgb(self.second_brush_color)

            # FIXME: In current time it works only for 100% opacity color.
            if self.image.mode == "RGBA":
                color_from = common.rgb_tuple_to_rgba_tuple(color_from, 255)
                color_to = common.rgb_tuple_to_rgba_tuple(color_to, 255)

            if self.selected_mask_img is None:
                bh_draw_recoloring_line(self.image, x1, y1, x2, y2, color_from, color_to, self.tool_size)
            else:
                tmp_image = self.image.copy()
                bh_draw_recoloring_line(tmp_image, x1, y1, x2, y2, color_from, color_to, self.tool_size)
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
                del tmp_image

        def draw_brush_halo(x, y):
            self.ui.canvas.delete("tools")

            d1 = (self.tool_size - 1) // 2
            d2 = self.tool_size // 2

            self.ui.canvas.create_rectangle(
                int((x - d1) * self.zoom - 1),
                int((y - d1) * self.zoom - 1),
                int((x + d2 + 1) * self.zoom),
                int((y + d2 + 1) * self.zoom),
                outline="white",
                width=1,
                tag="tools",
            )
            self.ui.canvas.create_rectangle(
                int((x - d1) * self.zoom),
                int((y - d1) * self.zoom),
                int((x + d2 + 1) * self.zoom - 1),
                int((y + d2 + 1) * self.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
            )

        def leave(event):
            self.ui.canvas.delete("tools")

        self.ui.canvas.bind("<Button-1>", drawing)
        self.ui.canvas.bind("<B1-Motion>", drawing)
        self.ui.canvas.bind("<ButtonRelease-1>", end)
        self.ui.canvas.bind("<Motion>", move)
        self.ui.canvas.bind("<Leave>", leave)

    """Spray"""

    def spray(self):
        def start_spray(event):
            self.prev_x, self.prev_y = self.canvas_to_pict_xy(event.x, event.y)
            self.spraying = True
            do_spray()

        def do_spray():
            if not self.spraying or self.prev_x is None or self.prev_y is None:
                return

            if self.selected_mask_img is None:
                tmp_image = self.image
                tmp_draw = ImageDraw.Draw(tmp_image)
            else:
                tmp_image = self.image.copy()
                tmp_draw = ImageDraw.Draw(tmp_image)

            for i in range(self.tool_size * 2):
                offset_x = random.randint(-self.tool_size, self.tool_size)
                offset_y = random.randint(-self.tool_size, self.tool_size)
                if offset_x**2 + offset_y**2 <= self.tool_size**2:
                    tmp_draw.point((self.prev_x + offset_x, self.prev_y + offset_y), fill=self.brush_color)

            if self.selected_mask_img is None:
                pass
            else:
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)

            del tmp_image

            self.update_canvas()
            self.spray_job = self.ui.after(50, do_spray)

        def move_spray(event):
            self.prev_x, self.prev_y = self.canvas_to_pict_xy(event.x, event.y)

        def stop_spray(event):
            self.spraying = False
            if self.spray_job:
                self.ui.after_cancel(self.spray_job)
                self.spray_job = None
            self.prev_x, self.prev_y = (None, None)
            self.record_action()

        self.set_tool("spray", "Spray", self.spray_size, 5, 30, "spraycan")

        self.spraying = False
        self.spray_job = None
        self.ui.canvas.bind("<Button-1>", start_spray)
        self.ui.canvas.bind("<B1-Motion>", move_spray)
        self.ui.canvas.bind("<ButtonRelease-1>", stop_spray)

    """Text"""

    def text_tool(self):
        def add_text(event):
            self.draw.text((self.text_x, self.text_y), self.tx_entry.get(), fill=self.brush_color, font=self.imagefont)
            self.update_canvas()
            self.record_action()

        def draw_text_halo(event):
            self.ui.canvas.delete("tools")

            x, y = self.canvas_to_pict_xy(event.x, event.y)
            self.imagefont = ImageFont.truetype(self.font_path, self.tool_size)

            bbox = self.draw.textbbox((0, 0), self.tx_entry.get(), font=self.imagefont)

            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            self.text_x = x - text_width // 2 - bbox[0]
            self.text_y = y - text_height // 2 - bbox[1]

            self.ui.canvas.create_rectangle(
                (x - text_width // 2) * self.zoom,
                (y - text_height // 2) * self.zoom,
                (x + text_width // 2) * self.zoom,
                (y + text_height // 2) * self.zoom,
                outline="white",
                width=1,
                tag="tools",
            )

            self.ui.canvas.create_rectangle(
                (x - text_width // 2) * self.zoom,
                (y - text_height // 2) * self.zoom,
                (x + text_width // 2) * self.zoom,
                (y + text_height // 2) * self.zoom,
                outline="black",
                width=1,
                tag="tools",
                dash=(5, 5),
            )

        def leave(event):
            self.ui.canvas.delete("tools")

        self.set_tool("text", "Text", self.font_size, 11, 96, "cross")
        self.ui.canvas.bind("<Button-1>", add_text)
        self.ui.canvas.bind("<Motion>", draw_text_halo)
        self.ui.canvas.bind("<Leave>", leave)
