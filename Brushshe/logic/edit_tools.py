# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math

from PIL import Image, ImageChops, ImageDraw, ImageTk


class EditTools:
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

        x_begin = None
        y_begin = None
        x_end = None
        y_end = None

        def selecting(event):
            nonlocal x_begin, y_begin, x_end, y_end

            x, y = self.canvas_to_pict_xy(event.x, event.y)

            if x_begin is None or y_begin is None:
                x_begin = x
                y_begin = y

            x_end = x
            y_end = y

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            if x_begin < 0:
                x_begin = 0
            if x_begin > x_max:
                x_begin = x_max
            if y_begin < 0:
                y_begin = 0
            if y_begin > y_max:
                y_begin = y_max
            if x_end < 0:
                x_end = 0
            if x_end > x_max:
                x_end = x_max
            if y_end < 0:
                y_end = 0
            if y_end > y_max:
                y_end = y_max

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            draw_tool(x1, y1, x2, y2)

        def select_end(event):
            nonlocal x_begin, y_begin, x_end, y_end

            if x_begin is None or y_begin is None:
                return

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            self.ui.canvas.delete("tools")

            x_begin = None
            y_begin = None
            x_end = None
            y_end = None

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

        def draw_tool(x1, y1, x2, y2):
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

        self.ui.canvas.bind("<Button-1>", selecting)
        self.ui.canvas.bind("<B1-Motion>", selecting)
        self.ui.canvas.bind("<ButtonRelease-1>", select_end)

    """Insert"""

    def start_insert(self):
        if hasattr(self, "buffer_local") is False or self.buffer_local is None:
            return
        self.set_tool("insert", "Insert", 100, 1, 500, "cross")
        self.insert_simple(self.buffer_local)

    def insert_simple(self, insert_image=None):
        image_tmp = insert_image
        current_zoom = None
        image_tmp_view = None
        image_tk = None
        x1, y1 = None, None

        def move(event):
            nonlocal image_tmp, image_tmp_view, image_tk, current_zoom, x1, y1

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
            image_tmp = insert_image.resize((it_width, it_height), resampling)

            x, y = self.canvas_to_pict_xy(event.x, event.y)

            x1 = int(x - (it_width - 1) / 2)
            y1 = int(y - (it_height - 1) / 2)
            x2 = int(x1 + it_width - 1)
            y2 = int(y1 + it_height - 1)

            image_tmp_view = image_tmp.resize((int(it_width * self.zoom), int(it_height * self.zoom)), Image.BOX)
            image_tk = ImageTk.PhotoImage(image_tmp_view)
            current_zoom = self.zoom

            draw_tool(x1, y1, x2, y2)

        def insert_end(event):
            nonlocal image_tmp, x1, y1

            if x1 is None or y1 is None:
                return

            if image_tmp.mode == "RGBA":
                self.image.paste(image_tmp, (x1, y1), image_tmp)
            else:
                self.image.paste(image_tmp, (x1, y1))

            self.update_canvas()
            self.record_action()

        def leave(event):
            self.ui.canvas.delete("tools")

        def draw_tool(x1, y1, x2, y2):
            nonlocal image_tk

            self.ui.canvas.delete("tools")

            self.ui.canvas.create_image(
                int(x1 * self.zoom),
                int(y1 * self.zoom),
                image=image_tk,
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

        self.ui.canvas.bind("<ButtonRelease-1>", insert_end)
        self.ui.canvas.bind("<Motion>", move)
        self.ui.canvas.bind("<Leave>", leave)

    """Crop"""

    def crop_simple(self):
        self.set_tool("crop", "Crop", None, None, None, "cross")

        x_begin = None
        y_begin = None
        x_end = None
        y_end = None

        def cropping(event):
            nonlocal x_begin, y_begin, x_end, y_end

            x, y = self.canvas_to_pict_xy(event.x, event.y)

            if x_begin is None or y_begin is None:
                x_begin = x
                y_begin = y

            x_end = x
            y_end = y
            x_max = self.image.width - 1
            y_max = self.image.height - 1

            if x_begin < 0:
                x_begin = 0
            if x_begin > x_max:
                x_begin = x_max
            if y_begin < 0:
                y_begin = 0
            if y_begin > y_max:
                y_begin = y_max
            if x_end < 0:
                x_end = 0
            if x_end > x_max:
                x_end = x_max
            if y_end < 0:
                y_end = 0
            if y_end > y_max:
                y_end = y_max

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            draw_tool(x1, y1, x2, y2)

        def crop_end(event):
            nonlocal x_begin, y_begin, x_end, y_end

            if x_begin is None or y_begin is None:
                return

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            self.ui.canvas.delete("tools")

            x_begin = None
            y_begin = None
            x_end = None
            y_end = None

            self.crop_picture(math.floor(x1), math.floor(y1), math.ceil(x2) + 1, math.ceil(y2) + 1)

            # Remove mask if exist.
            # TODO: Continue...
            self.selected_mask_img = None

            self.update_canvas()

        def draw_tool(x1, y1, x2, y2):
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

        self.ui.canvas.bind("<Button-1>", cropping)
        self.ui.canvas.bind("<B1-Motion>", cropping)
        self.ui.canvas.bind("<ButtonRelease-1>", crop_end)
