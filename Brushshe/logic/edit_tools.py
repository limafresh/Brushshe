# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math
from collections.abc import Callable

from customtkinter import CTkCanvas
from PIL import Image, ImageChops, ImageDraw, ImageTk
from utils.translator import _

from . import state
from .rect_selector import RectSelector


class EditTools:
    def __init__(
        self,
        canvas: CTkCanvas,
        set_tool: Callable,
        canvas_to_pict_xy: Callable,
        update_canvas: Callable,
        record_action: Callable,
        crop_picture: Callable,
    ):
        self.canvas = canvas
        self.set_tool = set_tool
        self.canvas_to_pict_xy = canvas_to_pict_xy
        self.update_canvas = update_canvas
        self.record_action = record_action
        self.crop_picture = crop_picture

        self.is_insert_smoothing = False

        self.selector = RectSelector(self.canvas, self.canvas_to_pict_xy, "tools")

    """Copy/cut"""

    def copy(self, deleted: bool = False):
        if state.selected_mask_img is None:
            self._copy_simple(deleted)
        else:
            self._copy_selected(deleted)

    def _copy_selected(self, deleted: bool = False):
        if state.selected_mask_img is None:
            return

        tmp_bg_color = (0, 0, 0, 0)
        tmp_img_mask = state.selected_mask_img
        tmp_img = Image.new("RGBA", (state.image.width, state.image.height), tmp_bg_color)
        tmp_img.paste(state.image, (0, 0), tmp_img_mask)

        # Trim image.
        bg = Image.new(tmp_img.mode, tmp_img.size, tmp_bg_color)
        diff = ImageChops.difference(tmp_img, bg)
        # diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()

        if bbox:
            self.buffer_local = tmp_img.crop(bbox)
        else:
            self.buffer_local = tmp_img

        del tmp_img

        if deleted:
            bg_color = state.bg_color
            if state.image.mode == "RGBA":
                bg_color = (0, 0, 0, 0)
            tmp_img = Image.new(state.image.mode, (state.image.width, state.image.height), bg_color)
            state.image.paste(tmp_img, (0, 0), tmp_img_mask)
            del tmp_img
            self.record_action()

        self.update_canvas()

    def _copy_simple(self, deleted: bool = False):
        if deleted is False:
            self.set_tool("copy", _("Copy"), None, None, None, "cross")
        else:
            self.set_tool("cut", _("Cut"), None, None, None, "cross")

        self.selector.reset_positions()

        self.canvas.bind("<Button-1>", self.selector.update)
        self.canvas.bind("<B1-Motion>", self.selector.update)
        self.canvas.bind("<ButtonRelease-1>", lambda event: self._copy_select_end(deleted))

    def _copy_select_end(self, deleted: bool):
        result = self.selector.finish()
        if result is None:
            return
        x1, y1, x2, y2 = result

        # INFO: Float. From begin first pixel to end last pixel (begin last+1 pixel).
        #       One first pixel look like (0, 0, 1, 1).
        self.buffer_local = state.image.crop((x1, y1, x2 + 1, y2 + 1))

        if deleted:
            if state.image.mode != "RGBA":
                ImageDraw.Draw(state.image).rectangle(
                    (x1, y1, x2, y2),
                    fill=state.bg_color,
                    outline=state.bg_color,
                )
            else:
                ImageDraw.Draw(state.image).rectangle(
                    (x1, y1, x2, y2),
                    fill="#00000000",
                    outline="#00000000",
                )
            self.record_action()

        self.update_canvas()

    """Insert"""

    def insert(self):
        if hasattr(self, "buffer_local") is False or self.buffer_local is None:
            return

        self.set_tool("insert", _("Insert"), 100, 1, 500, "cross")
        self.insert_simple(self.buffer_local)

    def insert_simple(self, insert_image: Image.Image | None = None):
        self.image_tmp = insert_image
        self.current_zoom = None
        self.image_tmp_view = None
        self.image_tk = None
        self.x1, self.y1 = None, None

        self.canvas.bind("<ButtonRelease-1>", self._insert_end)
        self.canvas.bind("<Motion>", lambda e: self._insert_move(e, insert_image))
        self.canvas.bind("<Leave>", lambda e: self.canvas.delete("tools"))

    def _insert_move(self, event, insert_image: Image.Image):
        if state.current_tool == "sticker":
            it_width = state.tool_size
            it_height = int(insert_image.height * state.tool_size / insert_image.width)
            resampling = Image.BICUBIC
        else:
            it_width = int(insert_image.width / 100 * state.tool_size)
            it_height = int(insert_image.height / 100 * state.tool_size)
            if it_width <= 1 or it_height <= 1:
                it_width, it_height = (1, 1)
            if self.is_insert_smoothing:
                resampling = Image.NEAREST
            else:
                resampling = Image.BICUBIC

        self.image_tmp = insert_image.resize((it_width, it_height), resampling)
        x, y = self.canvas_to_pict_xy(event.x, event.y)

        self.x1 = int(x - (it_width - 1) / 2)
        self.y1 = int(y - (it_height - 1) / 2)
        x2 = int(self.x1 + it_width - 1)
        y2 = int(self.y1 + it_height - 1)

        self.image_tmp_view = self.image_tmp.resize(
            (int(it_width * state.zoom), int(it_height * state.zoom)), Image.BOX
        )
        self.image_tk = ImageTk.PhotoImage(self.image_tmp_view)
        self.current_zoom = state.zoom

        self._insert_draw_tool(self.x1, self.y1, x2, y2)

    def _insert_end(self, event):
        if self.x1 is None or self.y1 is None:
            return

        if self.image_tmp.mode == "RGBA":
            state.image.paste(self.image_tmp, (self.x1, self.y1), self.image_tmp)
        else:
            state.image.paste(self.image_tmp, (self.x1, self.y1))

        self.update_canvas()
        self.record_action()

    def _insert_draw_tool(self, x1: float, y1: float, x2: float, y2: float):
        self.canvas.delete("tools")

        self.canvas.create_image(
            int(x1 * state.zoom),
            int(y1 * state.zoom),
            image=self.image_tk,
            tag="tools",
            anchor="nw",
        )

        self.selector.draw_dashed_rect(x1, y1, x2, y2)

    """Crop"""

    def crop_simple(self):
        self.set_tool("crop", _("Crop"), None, None, None, "cross")

        self.selector.reset_positions()

        self.canvas.bind("<Button-1>", self.selector.update)
        self.canvas.bind("<B1-Motion>", self.selector.update)
        self.canvas.bind("<ButtonRelease-1>", self._crop_end)

    def _crop_end(self, event):
        result = self.selector.finish()
        if result is None:
            return
        x1, y1, x2, y2 = result

        self.crop_picture(math.floor(x1), math.floor(y1), math.ceil(x2) + 1, math.ceil(y2) + 1)

        # Remove mask if exist.
        # TODO: Continue...
        state.selected_mask_img = None

        self.update_canvas()
