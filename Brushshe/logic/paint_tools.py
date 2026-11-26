# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import random
from collections.abc import Callable

from constants import Constants
from core.bhbrush import bh_draw_recoloring_line
from core.bhhistory import BhHistory, BhPoint
from core.gradient_fill import gradient_fill
from customtkinter import CTkCanvas
from PIL import Image, ImageColor, ImageDraw, ImageFont
from utils import common
from utils.config_loader import config
from utils.translator import _

from . import state


class PaintTools:
    def __init__(
        self,
        canvas: CTkCanvas,
        set_tool: Callable,
        canvas_to_pict_xy: Callable,
        draw_line: Callable,
        update_canvas: Callable,
        record_action: Callable,
        image: Image.Image,
        draw: ImageDraw.Draw,
    ):
        self.canvas = canvas
        self.set_tool = set_tool
        self.canvas_to_pict_xy = canvas_to_pict_xy
        self.draw_line = draw_line
        self.update_canvas = update_canvas
        self.record_action = record_action
        state.image = image
        state.draw = draw

        self.is_brush_smoothing = config.getboolean("Brushshe", "smoothing")
        self.brush_smoothing_factor = config.getint("Brushshe", "brush_smoothing_factor")  # Between: 3..64
        self.brush_smoothing_quality = config.getint("Brushshe", "brush_smoothing_quality")  # Between: 1..64

        self.is_gradient_fill = False
        self.gradient_fill_direction = "Vertically"

        self.font_path = common.resource("assets/fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf")
        self.text_content = ""

    def brush(self, type: str = "brush"):
        self.prev_x = None
        self.prev_y = None
        self.point_history = None

        if type == "brush":
            self.set_tool("brush", _("Brush"), Constants().BRUSH_SIZE, 1, 50, "pencil")
        elif type == "eraser":
            self.set_tool("eraser", _("Eraser"), Constants().ERASER_SIZE, 1, 50, "target")
        else:
            print("Warning: Incorrect brush type. Set default as.")
            self.set_tool("brush", _("Brush"), Constants().BRUSH_SIZE, 1, 50, "pencil")

        self.canvas.bind("<Button-1>", self._paint)
        self.canvas.bind("<B1-Motion>", self._paint)
        self.canvas.bind("<ButtonRelease-1>", self._stop_paint)
        self.canvas.bind("<Motion>", self._move_paint)
        self.canvas.bind("<Leave>", lambda e: self.canvas.delete("tools"))

    def _paint(self, event, recoloring: bool = False):
        if self.is_brush_smoothing is False:
            x, y = self.canvas_to_pict_xy(event.x, event.y)
        else:
            if self.point_history is None:
                self.point_history = BhHistory(limit_length=self.brush_smoothing_factor)

            xf, yf = self.canvas_to_pict_xy(event.x, event.y, f=True)
            self.point_history.add_point(BhPoint(x=xf, y=yf, pressure=1.0))
            s_point = self.point_history.get_smoothing_point(
                self.brush_smoothing_factor,
                self.brush_smoothing_quality,
            )

            if s_point is not None:
                x = int(s_point.x)
                y = int(s_point.y)
            else:
                x, y = self.canvas_to_pict_xy(event.x, event.y)

        if self.prev_x is None or self.prev_y is None:
            self.prev_x, self.prev_y = x, y

        if recoloring:
            draw_func = self._draw_recoloring_brush
        else:
            draw_func = self.draw_line

        draw_func(x, y, self.prev_x, self.prev_y)

        self.prev_x, self.prev_y = x, y
        self.update_canvas()
        self._draw_brush_halo(x, y, recoloring)

    def _stop_paint(self, event, recoloring: bool = False):
        if self.prev_x is None:
            return

        self.canvas.delete("tools")
        x, y = self.canvas_to_pict_xy(event.x, event.y)
        self._draw_brush_halo(x, y, recoloring)

        self.point_history = None
        self.prev_x, self.prev_y = (None, None)
        self.record_action()

    def _move_paint(self, event, recoloring: bool = False):
        x, y = self.canvas_to_pict_xy(event.x, event.y)
        self._draw_brush_halo(x, y, recoloring)

    def _draw_brush_halo(self, x, y, recoloring):
        self.canvas.delete("tools")

        d1 = (state.tool_size - 1) // 2
        d2 = state.tool_size // 2

        if state.brush_shape == "square" or recoloring:
            canvas_create_shape = self.canvas.create_rectangle
        elif state.brush_shape == "circle":
            canvas_create_shape = self.canvas.create_oval

        canvas_create_shape(
            int((x - d1) * state.zoom - 1),
            int((y - d1) * state.zoom - 1),
            int((x + d2 + 1) * state.zoom),
            int((y + d2 + 1) * state.zoom),
            outline="white",
            width=1,
            tag="tools",
        )
        canvas_create_shape(
            int((x - d1) * state.zoom),
            int((y - d1) * state.zoom),
            int((x + d2 + 1) * state.zoom - 1),
            int((y + d2 + 1) * state.zoom - 1),
            outline="black",
            width=1,
            tag="tools",
        )

    def fill(self):
        self.set_tool("fill", _("Fill"), None, None, None, "cross")
        self.canvas.bind("<Button-1>", self._fill)

    def _fill(self, event):
        x, y = self.canvas_to_pict_xy(event.x, event.y)
        tmp_image = state.image if state.selected_mask_img is None else state.image.copy()

        if state.image.mode == "RGBA":
            fill_color = common.rgb_tuple_to_rgba_tuple(ImageColor.getrgb(state.brush_color), 255)
        else:
            fill_color = ImageColor.getrgb(state.brush_color)

        if self.is_gradient_fill:
            filled = gradient_fill(
                x, y, state.image, state.brush_color, state.second_brush_color, self.gradient_fill_direction
            )
            if filled is not None and state.selected_mask_img is None:
                state.image.paste(filled)
            else:
                state.image.paste(filled, (0, 0), state.selected_mask_img)
        else:
            ImageDraw.floodfill(tmp_image, (x, y), fill_color)
            if state.selected_mask_img is not None:
                state.image.paste(tmp_image, (0, 0), state.selected_mask_img)

        self.update_canvas()
        self.record_action()

    def recoloring_brush(self):
        self.set_tool("r-brush", _("R. Brush"), Constants().BRUSH_SIZE, 1, 50, "pencil")

        self.prev_x = None
        self.prev_y = None
        self.point_history = None

        self.canvas.bind("<Button-1>", lambda e: self._paint(e, True))
        self.canvas.bind("<B1-Motion>", lambda e: self._paint(e, True))
        self.canvas.bind("<ButtonRelease-1>", lambda e: self._stop_paint(e, True))
        self.canvas.bind("<Motion>", lambda e: self._move_paint(e, True))
        self.canvas.bind("<Leave>", lambda e: self.canvas.delete("tools"))

    def _draw_recoloring_brush(self, x1: float, y1: float, x2: float, y2: float):
        color_to = ImageColor.getrgb(state.brush_color)
        color_from = ImageColor.getrgb(state.second_brush_color)

        if state.image.mode == "RGBA":
            color_from = common.rgb_tuple_to_rgba_tuple(color_from, 255)
            color_to = common.rgb_tuple_to_rgba_tuple(color_to, 255)

        if state.selected_mask_img is None:
            bh_draw_recoloring_line(state.image, x1, y1, x2, y2, color_from, color_to, state.tool_size)
        else:
            tmp_image = state.image.copy()
            bh_draw_recoloring_line(tmp_image, x1, y1, x2, y2, color_from, color_to, state.tool_size)
            state.image.paste(tmp_image, (0, 0), state.selected_mask_img)
            del tmp_image

    def spray(self):
        self.set_tool("spray", _("Spray"), Constants().SPRAY_SIZE, 5, 30, "spraycan")

        self.spraying = False
        self.spray_job = None
        self.canvas.bind("<Button-1>", self._start_spray)
        self.canvas.bind("<B1-Motion>", self._move_spray)
        self.canvas.bind("<ButtonRelease-1>", self._stop_spray)

    def _start_spray(self, event):
        self.prev_x, self.prev_y = self.canvas_to_pict_xy(event.x, event.y)
        self.spraying = True
        self._do_spray()

    def _do_spray(self):
        if not self.spraying or self.prev_x is None or self.prev_y is None:
            return

        if state.selected_mask_img is None:
            tmp_image = state.image
            tmp_draw = ImageDraw.Draw(tmp_image)
        else:
            tmp_image = state.image.copy()
            tmp_draw = ImageDraw.Draw(tmp_image)

        for i in range(state.tool_size * 2):
            offset_x = random.randint(-state.tool_size, state.tool_size)
            offset_y = random.randint(-state.tool_size, state.tool_size)
            if offset_x**2 + offset_y**2 <= state.tool_size**2:
                tmp_draw.point((self.prev_x + offset_x, self.prev_y + offset_y), fill=state.brush_color)

        if state.selected_mask_img is None:
            pass
        else:
            state.image.paste(tmp_image, (0, 0), state.selected_mask_img)

        del tmp_image

        self.update_canvas()
        self.spray_job = self.canvas.after(50, self._do_spray)

    def _move_spray(self, event):
        self.prev_x, self.prev_y = self.canvas_to_pict_xy(event.x, event.y)

    def _stop_spray(self, event):
        self.spraying = False
        if self.spray_job:
            self.canvas.after_cancel(self.spray_job)
            self.spray_job = None
        self.prev_x, self.prev_y = (None, None)
        self.record_action()

    def text(self):
        self.set_tool("text", _("Text"), Constants().FONT_SIZE, 11, 96, "cross")
        self.canvas.bind("<Button-1>", self._add_text)
        self.canvas.bind("<Motion>", self._draw_text_halo)
        self.canvas.bind("<Leave>", lambda e: self.canvas.delete("tools"))

    def _add_text(self, event):
        state.draw.text((self.text_x, self.text_y), self.text_content, fill=state.brush_color, font=self.imagefont)
        self.update_canvas()
        self.record_action()

    def _draw_text_halo(self, event):
        self.canvas.delete("tools")

        x, y = self.canvas_to_pict_xy(event.x, event.y)
        self.imagefont = ImageFont.truetype(self.font_path, state.tool_size)

        bbox = state.draw.textbbox((0, 0), self.text_content, font=self.imagefont)

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        self.text_x = x - text_width // 2 - bbox[0]
        self.text_y = y - text_height // 2 - bbox[1]

        self.canvas.create_rectangle(
            (x - text_width // 2) * state.zoom,
            (y - text_height // 2) * state.zoom,
            (x + text_width // 2) * state.zoom,
            (y + text_height // 2) * state.zoom,
            outline="white",
            width=1,
            tag="tools",
        )

        self.canvas.create_rectangle(
            (x - text_width // 2) * state.zoom,
            (y - text_height // 2) * state.zoom,
            (x + text_width // 2) * state.zoom,
            (y + text_height // 2) * state.zoom,
            outline="black",
            width=1,
            tag="tools",
            dash=(5, 5),
        )
