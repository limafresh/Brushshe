# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math

from PIL import Image, ImageChops, ImageDraw, ImageTk


class EditTools:
    """Common"""

    def edit_selecting(self, event, screenshot=False):
        if screenshot:
            image = self.screenshot
            draw_tool = self.screenshot_draw_tool
        else:
            image = self.image
            draw_tool = self.edit_draw_tool

        x, y = self.canvas_to_pict_xy(event.x, event.y)

        if self.x_begin is None or self.y_begin is None:
            self.x_begin = x
            self.y_begin = y

        self.x_end = x
        self.y_end = y

        x_max = image.width - 1
        y_max = image.height - 1

        if self.x_begin < 0:
            self.x_begin = 0
        if self.x_begin > x_max:
            self.x_begin = x_max
        if self.y_begin < 0:
            self.y_begin = 0
        if self.y_begin > y_max:
            self.y_begin = y_max
        if self.x_end < 0:
            self.x_end = 0
        if self.x_end > x_max:
            self.x_end = x_max
        if self.y_end < 0:
            self.y_end = 0
        if self.y_end > y_max:
            self.y_end = y_max

        x1 = min(self.x_begin, self.x_end)
        x2 = max(self.x_begin, self.x_end)
        y1 = min(self.y_begin, self.y_end)
        y2 = max(self.y_begin, self.y_end)

        draw_tool(x1, y1, x2, y2)

    def edit_draw_tool(self, x1, y1, x2, y2):
        self.ui.canvas.delete("tools")

        self.ui.canvas.create_rectangle(
            int(x1 * self.zoom),
            int(y1 * self.zoom),
            int((x2 + 1) * self.zoom - 1),
            int((y2 + 1) * self.zoom - 1),
            outline="white",
            width=1,
            tag="tools",
        )
        self.ui.canvas.create_rectangle(
            int(x1 * self.zoom),
            int(y1 * self.zoom),
            int((x2 + 1) * self.zoom - 1),
            int((y2 + 1) * self.zoom - 1),
            outline="black",
            width=1,
            tag="tools",
            dash=(5, 5),
        )

    def edit_end(self, screenshot=False):
        if self.x_begin is None or self.y_begin is None:
            return

        x1 = min(self.x_begin, self.x_end)
        x2 = max(self.x_begin, self.x_end)
        y1 = min(self.y_begin, self.y_end)
        y2 = max(self.y_begin, self.y_end)

        if not screenshot:
            self.ui.canvas.delete("tools")

        self.x_begin = None
        self.y_begin = None
        self.x_end = None
        self.y_end = None

        return x1, y1, x2, y2

    """Copy and cut"""

    def copy_tool(self, deleted=False):
        if self.selected_mask_img is None:
            self.copy_simple(deleted)
        else:
            self.copy_selected(deleted)

    def copy_selected(self, deleted=False):
        if self.selected_mask_img is None:
            return

        tmp_bg_color = (0, 0, 0, 0)
        tmp_img_mask = self.selected_mask_img
        tmp_img = Image.new("RGBA", (self.image.width, self.image.height), tmp_bg_color)
        tmp_img.paste(self.image, (0, 0), tmp_img_mask)

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
            bg_color = self.bg_color
            if self.image.mode == "RGBA":
                bg_color = (0, 0, 0, 0)
            tmp_img = Image.new(self.image.mode, (self.image.width, self.image.height), bg_color)
            self.image.paste(tmp_img, (0, 0), tmp_img_mask)
            del tmp_img
            self.record_action()

        self.update_canvas()

    def copy_simple(self, deleted=False):
        if deleted is False:
            self.set_tool("copy", "Copy", None, None, None, "cross")
        else:
            self.set_tool("cut", "Cut", None, None, None, "cross")

        self.x_begin = None
        self.y_begin = None
        self.x_end = None
        self.y_end = None

        self.ui.canvas.bind("<Button-1>", self.edit_selecting)
        self.ui.canvas.bind("<B1-Motion>", self.edit_selecting)
        self.ui.canvas.bind("<ButtonRelease-1>", lambda event: self.copy_select_end(deleted))

    def copy_select_end(self, deleted):
        result = self.edit_end()
        if result is None:
            return
        x1, y1, x2, y2 = result

        # INFO: Float. From begin first pixel to end last pixel (begin last+1 pixel).
        #       One first pixel look like (0, 0, 1, 1).
        self.buffer_local = self.image.crop((x1, y1, x2 + 1, y2 + 1))

        if deleted is not False:
            if self.image.mode != "RGBA":
                ImageDraw.Draw(self.image).rectangle(
                    (x1, y1, x2, y2),
                    fill=self.bg_color,
                    outline=self.bg_color,
                )
            else:
                ImageDraw.Draw(self.image).rectangle(
                    (x1, y1, x2, y2),
                    fill="#00000000",
                    outline="#00000000",
                )
            self.record_action()  # Need only for cut.

        self.update_canvas()

    """Insert"""

    def start_insert(self):
        if hasattr(self, "buffer_local") is False or self.buffer_local is None:
            return
        self.set_tool("insert", "Insert", 100, 1, 500, "cross")
        self.insert_simple(self.buffer_local)

    def insert_simple(self, insert_image=None):
        self.image_tmp = insert_image
        self.current_zoom = None
        self.image_tmp_view = None
        self.image_tk = None
        self.x1, self.y1 = None, None

        self.ui.canvas.bind("<ButtonRelease-1>", self.insert_end)
        self.ui.canvas.bind("<Motion>", lambda e: self.insert_move(e, insert_image))
        self.ui.canvas.bind("<Leave>", lambda e: self.ui.canvas.delete("tools"))

    def insert_move(self, event, insert_image):
        if self.current_tool == "sticker":
            it_width = self.tool_size
            it_height = int(insert_image.height * self.tool_size / insert_image.width)
            resampling = Image.BICUBIC
        else:
            it_width = int(insert_image.width / 100 * self.tool_size)
            it_height = int(insert_image.height / 100 * self.tool_size)
            if it_width <= 1 or it_height <= 1:
                it_width, it_height = (1, 1)
            if self.is_insert_smoothing.get():
                resampling = Image.NEAREST
            else:
                resampling = Image.BICUBIC
        self.image_tmp = insert_image.resize((it_width, it_height), resampling)

        x, y = self.canvas_to_pict_xy(event.x, event.y)

        self.x1 = int(x - (it_width - 1) / 2)
        self.y1 = int(y - (it_height - 1) / 2)
        x2 = int(self.x1 + it_width - 1)
        y2 = int(self.y1 + it_height - 1)

        self.image_tmp_view = self.image_tmp.resize((int(it_width * self.zoom), int(it_height * self.zoom)), Image.BOX)
        self.image_tk = ImageTk.PhotoImage(self.image_tmp_view)
        self.current_zoom = self.zoom

        self.insert_draw_tool(self.x1, self.y1, x2, y2)

    def insert_end(self, event):
        if self.x1 is None or self.y1 is None:
            return

        if self.image_tmp.mode == "RGBA":
            self.image.paste(self.image_tmp, (self.x1, self.y1), self.image_tmp)
        else:
            self.image.paste(self.image_tmp, (self.x1, self.y1))

        self.update_canvas()
        self.record_action()

    def insert_draw_tool(self, x1, y1, x2, y2):
        self.ui.canvas.delete("tools")

        self.ui.canvas.create_image(
            int(x1 * self.zoom),
            int(y1 * self.zoom),
            image=self.image_tk,
            tag="tools",
            anchor="nw",
        )

        self.ui.canvas.create_rectangle(
            int(x1 * self.zoom),
            int(y1 * self.zoom),
            int((x2 + 1) * self.zoom - 1),
            int((y2 + 1) * self.zoom - 1),
            outline="white",
            width=1,
            tag="tools",
        )
        self.ui.canvas.create_rectangle(
            int(x1 * self.zoom),
            int(y1 * self.zoom),
            int((x2 + 1) * self.zoom - 1),
            int((y2 + 1) * self.zoom - 1),
            outline="black",
            width=1,
            tag="tools",
            dash=(5, 5),
        )

    """Crop"""

    def crop_simple(self):
        self.set_tool("crop", "Crop", None, None, None, "cross")

        self.x_begin = None
        self.y_begin = None
        self.x_end = None
        self.y_end = None

        self.ui.canvas.bind("<Button-1>", self.edit_selecting)
        self.ui.canvas.bind("<B1-Motion>", self.edit_selecting)
        self.ui.canvas.bind("<ButtonRelease-1>", self.crop_end)

    def crop_end(self, event):
        result = self.edit_end()
        if result is None:
            return
        x1, y1, x2, y2 = result

        self.crop_picture(math.floor(x1), math.floor(y1), math.ceil(x2) + 1, math.ceil(y2) + 1)

        # Remove mask if exist.
        # TODO: Continue...
        self.selected_mask_img = None

        self.update_canvas()
