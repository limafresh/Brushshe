# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import time

from PIL import Image, ImageDraw, ImageOps
from utils import common


class Selection:
    def select_by_shape(self, shape="rectangle"):
        self.set_tool("select", "Select", None, None, None, "cross")

        x_begin = None
        y_begin = None
        x_end = None
        y_end = None
        _mode = "replace"

        def selecting(event, mode):
            nonlocal x_begin, y_begin, x_end, y_end, _mode

            if mode is not None:
                _mode = mode
            self.select_init_mask()

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
            nonlocal x_begin, y_begin, x_end, y_end, _mode

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

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            draw = ImageDraw.Draw(self.selected_mask_img)

            if _mode == "replace":
                draw.rectangle([0, 0, x_max, y_max], fill="black")

            if _mode == "subtract":
                draw.rectangle([x1, y1, x2, y2], fill="black")
            else:  # add or replace
                draw.rectangle([x1, y1, x2, y2], fill="white")

            self.composer.set_force_update_mask()
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

        self.ui.canvas.bind("<Button-1>", lambda e: selecting(e, "replace"))
        self.ui.canvas.bind("<Shift-Button-1>", lambda e: selecting(e, "add"))
        self.ui.canvas.bind("<Control-Button-1>", lambda e: selecting(e, "subtract"))
        self.ui.canvas.bind("<B1-Motion>", lambda e: selecting(e, None))
        self.ui.canvas.bind("<ButtonRelease-1>", select_end)

    def select_by_polygon(self):
        self.set_tool("select", "Select", None, None, None, "cross")

        xy_list = None
        _mode = "replace"
        delta = 5

        def selecting(event, mode, type="click"):
            nonlocal xy_list, _mode

            self.ui.canvas.focus_set()  # For the key binding.

            if mode is not None:
                _mode = mode
            if type == "click":
                self.select_init_mask()

            x, y = self.canvas_to_pict_xy(event.x, event.y)
            x = int(x)
            y = int(y)

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            if x < 0:
                x = 0
            if x > x_max:
                x = x_max
            if y < 0:
                y = 0
            if y > y_max:
                y = y_max

            if type == "unclick":
                if xy_list is None:
                    xy_list = []

                xy_len = len(xy_list)
                if (
                    xy_len >= 4
                    and xy_list[0] - delta < x < xy_list[0] + delta
                    and xy_list[1] - delta < y < xy_list[1] + delta
                ):
                    xy_list.append(xy_list[0])
                    xy_list.append(xy_list[1])
                    select_end(event)
                    return

                xy_list.append(x)
                xy_list.append(y)

            draw_tool(x, y)

        def select_end(event):
            nonlocal xy_list, _mode

            if xy_list is None:
                return

            self.ui.canvas.delete("tools")

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            draw = ImageDraw.Draw(self.selected_mask_img)

            if _mode == "replace":
                draw.rectangle([0, 0, x_max, y_max], fill="black")

            if _mode == "subtract":
                draw.polygon(xy_list, fill="black")
            else:  # add or replace
                draw.polygon(xy_list, fill="white")

            xy_list = None

            self.composer.set_force_update_mask()
            self.update_canvas()

        def key_backspace(event):
            nonlocal xy_list

            if xy_list is None:
                return

            xy_len = len(xy_list)
            if xy_len >= 4:
                del xy_list[-1]
                del xy_list[-1]

                xy_len = len(xy_list)
                draw_tool(xy_list[xy_len - 2], xy_list[xy_len - 1])

        def key_enter(event):
            nonlocal xy_list

            if xy_list is None:
                return

            if len(xy_list) >= 4:
                select_end(event)

        def draw_tool(x, y):
            nonlocal xy_list, _mode

            self.ui.canvas.delete("tools")

            if xy_list is None or 0 == len(xy_list):
                x_begin = x
                y_begin = y
            else:
                xy_len = len(xy_list)
                x_begin = xy_list[0]
                y_begin = xy_list[1]
                self.ui.canvas.create_line(
                    int(xy_list[xy_len - 2] * self.zoom),
                    int(xy_list[xy_len - 1] * self.zoom),
                    int(x * self.zoom),
                    int(y * self.zoom),
                    fill="black",
                    width=1,
                    tag="tools",
                )
                self.ui.canvas.create_line(
                    int(xy_list[xy_len - 2] * self.zoom),
                    int(xy_list[xy_len - 1] * self.zoom),
                    int(x * self.zoom),
                    int(y * self.zoom),
                    fill="white",
                    width=1,
                    tag="tools",
                    dash=(5, 5),
                )
                if xy_len >= 4:
                    tmp_xy_list = [int(x * self.zoom) for x in xy_list]
                    self.ui.canvas.create_line(tmp_xy_list, fill="black", width=1, tag="tools")
                    self.ui.canvas.create_line(tmp_xy_list, fill="white", width=1, tag="tools", dash=(5, 5))

            self.ui.canvas.create_rectangle(
                int(x_begin * self.zoom + delta),
                int(y_begin * self.zoom + delta),
                int(x_begin * self.zoom - delta),
                int(y_begin * self.zoom - delta),
                outline="black",
                fill="white",
                width=1,
                tag="tools",
            )

        self.ui.canvas.bind("<Button-1>", lambda e: selecting(e, "replace"))
        self.ui.canvas.bind("<Shift-Button-1>", lambda e: selecting(e, "add"))
        self.ui.canvas.bind("<Control-Button-1>", lambda e: selecting(e, "subtract"))
        self.ui.canvas.bind("<B1-Motion>", lambda e: selecting(e, None, "moving"))
        self.ui.canvas.bind("<Motion>", lambda e: selecting(e, None, "moving"))
        self.ui.canvas.bind("<ButtonRelease-1>", lambda e: selecting(e, None, "unclick"))
        self.ui.canvas.bind("<BackSpace>", key_backspace)
        self.ui.canvas.bind("<Return>", key_enter)

    def select_by_color(self, fill_limit=False):
        self.set_tool("select_by_color", "Select by color", None, None, None, "dotbox")

        _mode = "replace"
        thresh = 1

        def selecting(event, mode):
            nonlocal _mode

            self.ui.canvas.focus_set()

            if mode is not None:
                _mode = mode

            self.select_init_mask()

            x, y = self.canvas_to_pict_xy(event.x, event.y)
            x = int(x)
            y = int(y)

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            if x < 0:
                x = 0
            if x > x_max:
                x = x_max
            if y < 0:
                y = 0
            if y > y_max:
                y = y_max

            draw = ImageDraw.Draw(self.selected_mask_img)

            if _mode == "replace":
                draw.rectangle([0, 0, x_max, y_max], fill=0)

            if _mode == "subtract":
                fill_color = 0
            else:  # add or replace
                fill_color = 255

            if not fill_limit:
                pixels_mask = self.selected_mask_img.load()
                pixels_image = self.image.load()

                assert pixels_image is not None

                try:
                    background = pixels_image[x, y]
                except (ValueError, IndexError):
                    return

                for ii in range(x_max + 1):
                    for jj in range(y_max + 1):
                        try:
                            p = pixels_image[ii, jj]
                            if common.color_diff(p, background) <= thresh:
                                pixels_mask[ii, jj] = fill_color
                        except (ValueError, IndexError):
                            pass
            else:
                self._floodfill_mask(self.image, self.selected_mask_img, (x, y), fill_color)

            self.composer.set_force_update_mask()
            self.update_canvas()

        self.ui.canvas.bind("<Button-1>", lambda e: selecting(e, "replace"))
        self.ui.canvas.bind("<Shift-Button-1>", lambda e: selecting(e, "add"))
        self.ui.canvas.bind("<Control-Button-1>", lambda e: selecting(e, "subtract"))

    def invert_mask(self):
        self.select_init_mask()

        tmp_mask_img = ImageOps.invert(self.selected_mask_img)
        self.selected_mask_img = tmp_mask_img
        del tmp_mask_img

        self.composer.set_force_update_mask()
        self.update_canvas()

    def select_all_mask(self):
        self.select_init_mask()

        x_max = self.image.width - 1
        y_max = self.image.height - 1
        draw = ImageDraw.Draw(self.selected_mask_img)
        draw.rectangle([0, 0, x_max, y_max], fill=255)

        self.composer.set_force_update_mask()
        self.update_canvas()

    def select_init_mask(self):
        if self.composer is None:
            return

        if self.selected_mask_img is None:
            self.selected_mask_img = Image.new("L", (self.image.width, self.image.height), "white")
        if self.selected_mask_img.width != self.image.width or self.selected_mask_img.height != self.image.height:
            self.selected_mask_img = Image.new("L", (self.image.width, self.image.height), "white")

    def remove_mask(self):
        self.selected_mask_img = None
        self.composer.mask_img = None

        self.composer.set_force_update_mask()
        self.update_canvas()

    # Timer for musk
    def mask_update(self):
        mm_time = int(time.time() * 1000)

        if (
            self.composer.mask_type != 0
            and self.selected_mask_img is not None
            and self.timer_mask_last_update + 500 < mm_time
        ):
            # self.timer_mask_last_update = mm_time

            self.composer.inc_ants_position()
            self.update_canvas()
            # print("DEBUG: ants update: {}".format(mm_time))

        # Repeat timer
        self.timer_mask_update = self.ui.after(self.timer_mask_time_for_update, self.mask_update)

    def set_mask_type(self, type: int = 0):
        self.composer.mask_type = type
        # self.timer_mask_last_update = int(time.time() * 1000)

        self.composer.set_force_update_mask()
        self.update_canvas()

    def delete_selected(self):
        if self.selected_mask_img is None:
            return

        bg_color = self.bg_color
        if self.image.mode == "RGBA":
            bg_color = (0, 0, 0, 0)
        tmp_img = Image.new(self.image.mode, (self.image.width, self.image.height), bg_color)
        self.image.paste(tmp_img, (0, 0), self.selected_mask_img)
        del tmp_img
        self.record_action()
        self.update_canvas()

    def _floodfill_mask(
        self,
        image: Image.Image,
        mask: Image.Image,
        xy: tuple[int, int],
        value: float | tuple[int, ...],
        border: float | tuple[int, ...] | None = None,
        thresh: float = 0,
    ) -> None:
        pixel = image.copy().load()
        pixel_m = mask.load()
        assert pixel is not None
        assert pixel_m is not None
        x, y = xy
        try:
            background = pixel[x, y]
            # if colors.color_diff(value, background) <= thresh:
            #     return  # seed point already has fill color
            pixel[x, y] = value
            pixel_m[x, y] = value
        except (ValueError, IndexError):
            return  # seed point outside image
        edge = {(x, y)}

        # Default floodfill algorithm.
        full_edge = set()
        while edge:
            new_edge = set()
            for x, y in edge:
                for s, t in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    # If already processed, or if a coordinate is negative, skip
                    if (s, t) in full_edge or s < 0 or t < 0:
                        continue
                    try:
                        p = pixel[s, t]
                    except (ValueError, IndexError):
                        pass
                    else:
                        full_edge.add((s, t))
                        if border is None:
                            fill = common.color_diff(p, background) <= thresh
                        else:
                            fill = p not in (value, border)
                        if fill:
                            pixel[s, t] = value
                            pixel_m[s, t] = value
                            new_edge.add((s, t))
            full_edge = edge
            edge = new_edge
