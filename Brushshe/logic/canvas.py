# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math
import time

from PIL import Image, ImageTk


class CanvasOperations:
    def v_scrollbar_command(self, a, b, c=None):
        self.ui.canvas.yview(a, b, c)
        if self.canvas_tails_area is not None and self.get_canvas_tails_area() != self.canvas_tails_area:
            self.update_canvas()

    def h_scrollbar_command(self, a, b, c=None):
        self.ui.canvas.xview(a, b, c)
        if self.canvas_tails_area is not None and self.get_canvas_tails_area() != self.canvas_tails_area:
            self.update_canvas()

    def on_window_resize(self, event):
        # Update canvas after any resize window.
        if self.zoom >= 1 and hasattr(self.ui, "canvas"):
            self.update_canvas()

    def scroll_on_canvasy(self, event):
        if event.num == 5 or event.delta < 0:
            count = 1
        if event.num == 4 or event.delta > 0:
            count = -1
        self.ui.canvas.yview_scroll(count, "units")
        if self.canvas_tails_area is not None and self.get_canvas_tails_area() != self.canvas_tails_area:
            self.update_canvas()

    def scroll_on_canvasx(self, event):
        if event.num == 5 or event.delta < 0:
            count = 1
        if event.num == 4 or event.delta > 0:
            count = -1
        self.ui.canvas.xview_scroll(count, "units")
        if self.canvas_tails_area is not None and self.get_canvas_tails_area() != self.canvas_tails_area:
            self.update_canvas()

    def begin_moving_canvas(self, event):
        self.ui.canvas.scan_mark(event.x, event.y)

    def continue_moving_canvas(self, event):
        self.ui.canvas.scan_dragto(event.x, event.y, gain=1)
        if self.canvas_tails_area is not None and self.get_canvas_tails_area() != self.canvas_tails_area:
            self.update_canvas()

    def zoom_in(self, event=None):
        self.ui.canvas.delete("tools")

        if 1 < self.zoom < 2:  # Need if zoom not integer but more 1 and less 2
            self.zoom = 1
        if 1 <= self.zoom < 12:
            self.zoom += 1
        elif self.zoom < 1:
            self.zoom *= 2

        self.force_resize_canvas_with_correct()
        self.update_canvas()

    def zoom_out(self, event=None):
        self.ui.canvas.delete("tools")

        if 1 < self.zoom:
            self.zoom -= 1
        elif 0.05 < self.zoom <= 1:  # Zooming limited down by 0.05.
            self.zoom /= 2

        self.force_resize_canvas_with_correct()
        self.update_canvas()

    def reset_zoom(self, event=None):
        self.ui.canvas.delete("tools")

        self.zoom = 1

        self.force_resize_canvas_with_correct()
        self.update_canvas()

    def canvas_to_pict_xy(self, x, y):
        return self.ui.canvas.canvasx(x) // self.zoom, self.ui.canvas.canvasy(y) // self.zoom

    def canvas_to_pict_xy_f(self, x, y):
        return self.ui.canvas.canvasx(x) / self.zoom, self.ui.canvas.canvasy(y) / self.zoom

    def update_canvas(self):
        # Debug
        # t1 = time.perf_counter(), time.process_time()

        # self._update_canvas()
        self._tailing_update_canvas()

        # Debug
        # t2 = time.perf_counter(), time.process_time()
        # print(f" Real time: {t2[0] - t1[0]:.6f} sec. CPU time: {t2[1] - t1[1]:.6f} sec")

        self.timer_mask_last_update = int(time.time() * 1000)  # Set current time in ms

    def _tailing_update_canvas(self):
        if self.zoom < 1:
            # https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-filters
            canvas_image = self.image.resize(
                (math.ceil(self.image.width * self.zoom), math.ceil(self.image.height * self.zoom)), Image.BOX
            )
            if self.selected_mask_img is None:
                mask_image = None
            else:
                mask_image = self.selected_mask_img.resize(
                    (
                        math.ceil(self.selected_mask_img.width * self.zoom),
                        math.ceil(self.selected_mask_img.height * self.zoom),
                    ),
                    Image.NEAREST,
                )

            tails_area = None

            self.composer.set_l_image(canvas_image)
            self.composer.set_mask_image(mask_image, tails_area)

            compose_image = self.composer.get_compose_image(0, 0, canvas_image.width - 1, canvas_image.height - 1)

            self.img_tk = ImageTk.PhotoImage(compose_image)
            self.ui.canvas.itemconfig(self.canvas_image, image=self.img_tk)
            self.ui.canvas.moveto(self.canvas_image, 0, 0)
            self.canvas_tails_area = tails_area

            return

        else:  # data.zoom > 1 or data.zoom = 1:
            # It work incorrect at this implementation for zoom < 1.

            cw_full = math.ceil(self.image.width * self.zoom)
            ch_full = math.ceil(self.image.height * self.zoom)

            (x1, y1, x2, y2) = self.get_canvas_tails_area()

            # Check, maybe the image all on canvas.
            if x1 == 0 and y1 == 0 and x2 == cw_full - 1 and y2 == ch_full - 1:
                x1_correct = 0
                y1_correct = 0
                dx = 0
                dy = 0
                tmp_canvas_image = self.image
                tmp_mask_image = self.selected_mask_img
            else:
                tiles_xy_on_image = (
                    math.floor(x1 / self.zoom),
                    math.floor(y1 / self.zoom),
                    math.floor(x2 / self.zoom) + 1,
                    math.floor(y2 / self.zoom) + 1,
                )

                # Subpixel correct.
                x1_correct = tiles_xy_on_image[0] * self.zoom
                y1_correct = tiles_xy_on_image[1] * self.zoom

                dx = math.floor(x1 - x1_correct)
                dy = math.floor(y1 - y1_correct)

                # # Debug
                # print((x1, y1, x2, y2), tiles_xy_on_image, (x1_correct, y1_correct), (dx, dy))

                tmp_canvas_image = self.image.crop(tiles_xy_on_image)
                if self.selected_mask_img is None:
                    tmp_mask_image = None
                else:
                    tmp_mask_image = self.selected_mask_img.crop(tiles_xy_on_image)

            r_w = math.floor(tmp_canvas_image.width * self.zoom)
            r_h = math.floor(tmp_canvas_image.height * self.zoom)
            if r_w < 1:
                r_w = 1
            if r_h < 1:
                r_h = 1

            canvas_image = tmp_canvas_image.resize((r_w, r_h), Image.NEAREST)
            if tmp_mask_image is None:
                mask_image = None
            else:
                mask_image = tmp_mask_image.resize((r_w, r_h), Image.NEAREST)

            tails_area = (x1, y1, x2, y2)

            self.composer.set_l_image(canvas_image)
            self.composer.set_mask_image(mask_image, tails_area)

            compose_image = self.composer.get_compose_image(x1, y1, x2 + dx, y2 + dy)

            self.img_tk = ImageTk.PhotoImage(compose_image)
            self.ui.canvas.itemconfig(self.canvas_image, image=self.img_tk)
            self.ui.canvas.moveto(self.canvas_image, x1_correct, y1_correct)
            self.canvas_tails_area = tails_area

            return

    def get_canvas_tails_area(self):
        cw_full = int(self.image.width * self.zoom)
        ch_full = int(self.image.height * self.zoom)

        # Set param canvas with real image size. Not use bbox in this place.
        self.ui.canvas.config(scrollregion=(0, 0, cw_full, ch_full), width=cw_full, height=ch_full)

        iw, ih = self.image.size
        cx_frame_1, cx_frame_2 = self.ui.canvas.xview()
        cy_frame_1, cy_frame_2 = self.ui.canvas.yview()

        # Find the area without subpixel correct.
        x1 = math.floor(cx_frame_1 * cw_full / self.canvas_tail_size) * self.canvas_tail_size
        y1 = math.floor(cy_frame_1 * ch_full / self.canvas_tail_size) * self.canvas_tail_size
        x2 = math.ceil(cx_frame_2 * cw_full / self.canvas_tail_size) * self.canvas_tail_size - 1
        y2 = math.ceil(cy_frame_2 * ch_full / self.canvas_tail_size) * self.canvas_tail_size - 1
        if x2 > cw_full - 1:
            x2 = cw_full - 1
        if y2 > ch_full - 1:
            y2 = ch_full - 1

        return (x1, y1, x2, y2)

    def force_resize_canvas(self):
        cw_full = int(self.image.width * self.zoom)
        ch_full = int(self.image.height * self.zoom)

        # Scrollregion begin from the left part of first pixel and tail on the end part of last pixel.
        self.ui.canvas.config(
            scrollregion=(0, 0, cw_full, ch_full),
            width=cw_full,
            height=ch_full,
        )

        self.ui.size_button.configure(text=f"{self.image.width}x{self.image.height}")

    def force_resize_canvas_with_correct(self):
        wd_x_1 = self.ui.canvas.winfo_x()
        wd_y_1 = self.ui.canvas.winfo_y()

        cx_frame_1, cx_frame_2 = self.ui.canvas.xview()
        cy_frame_1, cy_frame_2 = self.ui.canvas.yview()
        dx_1 = (cx_frame_2 + cx_frame_1) / 2
        dy_1 = (cy_frame_2 + cy_frame_1) / 2

        self.force_resize_canvas()

        cx_frame_1, cx_frame_2 = self.ui.canvas.xview()
        cy_frame_1, cy_frame_2 = self.ui.canvas.yview()
        dx_2 = (cx_frame_2 + cx_frame_1) / 2
        dy_2 = (cy_frame_2 + cy_frame_1) / 2
        cw_full = int(self.image.width * self.zoom)
        ch_full = int(self.image.height * self.zoom)

        self.ui.canvas.scan_mark(int(dx_1 * cw_full - wd_x_1), int(dy_1 * ch_full - wd_y_1))
        self.ui.canvas.scan_dragto(int(dx_2 * cw_full), int(dy_2 * ch_full), gain=1)
