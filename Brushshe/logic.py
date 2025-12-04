# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math
import os
import random
import time
from io import BytesIO
from urllib.request import urlopen
from uuid import uuid4

import customtkinter as ctk
import data
import gallery
import messagebox
from color_picker import AskColor
from core.bezier import make_bezier
from core.bhbrush import bh_draw_line, bh_draw_recoloring_line
from core.bhhistory import BhHistory, BhPoint
from core.config_loader import config, config_file_path, write_config
from core.scroll import scroll
from core.tooltip import Tooltip
from data import resource
from file_dialog import FileDialog
from PIL import (
    Image,
    ImageChops,
    ImageColor,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
    ImageGrab,
    ImageOps,
    ImageStat,
    ImageTk,
)
from translator import _


class BrushsheLogic:
    def __init__(self, ui):
        self.ui = ui

        self.timer_mask_time_for_update = 200  # ms
        self.timer_mask_last_update = 0
        self.timer_mask_update = self.ui.after(self.timer_mask_time_for_update, self.mask_update)

        data.init()

    # Keybinding without locale.
    def key_handler(self, event):
        if self.current_tool != "text":
            # Do not use with origin .bind() for equivalent key binds. Only or that, or this.

            # Debug
            # print(event.char, event.keycode, event.state)

            shift = True if event.state & 0x0001 else False
            ctrl = True if event.state & 0x0004 else False
            alt_l = True if event.state & 0x0008 else False
            alt_r = True if event.state & 0x0080 else False
            alt = True if (alt_l or alt_r) else False
            # All else modifiers was ignored.

            if shift is False and ctrl is False and alt is False and event.keycode == 53:  # Key-x
                self.flip_brush_colors()

            if shift is False and ctrl is False and alt is False and event.keycode == 56:  # Key-b
                self.brush()

            if shift is False and ctrl is False and alt is False and event.keycode == 26:  # Key-e
                self.eraser()

    def set_tools_docker(self, tools_list, columns=1):
        row = 0
        column = 0

        for tool in tools_list:
            if tool["type"] == "separator":
                column = 0
                row += 1
                s = ctk.CTkFrame(
                    self.ui.tools_frame,
                    width=30,
                    height=4,
                )
                s.grid(column=column, row=row, pady=1, padx=1)
                row += 1
                continue

            tool_helper = tool["helper"]
            tool_command = tool["action"]
            tool_icon_name = tool["icon_name"]

            try:
                tool_icon = ctk.CTkImage(
                    light_image=Image.open(resource(f"assets/icons/toolbar/{tool_icon_name}_light.png")),
                    dark_image=Image.open(resource(f"assets/icons/toolbar/{tool_icon_name}_dark.png")),
                    size=(22, 22),
                )
            except Exception:
                # tool_icon = None
                tool_icon = ctk.CTkImage(
                    light_image=Image.open(resource("assets/icons/toolbar/not_found_light.png")),
                    dark_image=Image.open(resource("assets/icons/toolbar/not_found_dark.png")),
                    size=(22, 22),
                )

            tool_button = ctk.CTkButton(
                self.ui.tools_frame, text=None, width=30, height=30, image=tool_icon, command=tool_command
            )
            tool_button.grid(column=column, row=row, pady=1, padx=1)
            Tooltip(tool_button, message=tool_helper)

            column += 1
            if column >= columns:
                column = 0
                row += 1

    def change_tool_size_bind(self, event=None, delta=1):
        new_size = self.get_tool_size() + delta
        max_sizes = {
            "brush": 50,
            "r-brush": 50,
            "eraser": 50,
            "shape": 50,
            "spray": 30,
            "sticker": 250,
            "text": 96,
            "insert": 500,
            "real size sticker": 500,
        }
        if new_size < 1:
            new_size = 1
        if new_size > max_sizes[self.current_tool]:
            new_size = max_sizes[self.current_tool]
        self.change_tool_size(new_size)
        self.ui.tool_size_slider.set(int(new_size))

    def make_color_palette(self, colors):
        max_columns_in_row = 16

        if colors is None or len(colors) == 0:
            print("Wrong palette")
            return

        for child in self.ui.palette_widget.winfo_children():
            child.destroy()

        ii = 0
        for color in colors:
            try:
                rgb = self.ui.winfo_rgb(color)
                r = math.floor(rgb[0] / 256)
                g = math.floor(rgb[1] / 256)
                b = math.floor(rgb[2] / 256)
            except Exception:
                print("Warning: String `{}` is not correct color.".format(color))
                continue

            row = ii // max_columns_in_row
            column = ii % max_columns_in_row

            color_checked = "#{:02x}{:02x}{:02x}".format(r, g, b)

            tmp_btn = ctk.CTkButton(
                self.ui.palette_widget,
                fg_color=color_checked,
                hover=False,
                text=None,
                width=24,
                height=24,
                border_width=1,
                corner_radius=1,
                command=lambda c=color_checked: self.change_color(c),
            )
            # tmp_btn.pack(side=ctk.LEFT, padx=1, pady=1)
            tmp_btn.grid(row=row, column=column, padx=1, pady=1)
            tmp_btn.bind("<Button-3>", lambda event, obj=tmp_btn: self.color_choice_bth(event, obj))
            tmp_btn.bind("<Double-Button-1>", lambda event, obj=tmp_btn: self.color_choice_bth(event, obj))

            ii += 1

    def v_scrollbar_command(self, a, b, c=None):
        self.ui.canvas.yview(a, b, c)
        if data.canvas_tails_area is not None and self.get_canvas_tails_area() != data.canvas_tails_area:
            self.update_canvas()

    def h_scrollbar_command(self, a, b, c=None):
        self.ui.canvas.xview(a, b, c)
        if data.canvas_tails_area is not None and self.get_canvas_tails_area() != data.canvas_tails_area:
            self.logic.update_canvas()

    def on_window_resize(self, event):
        # Update canvas after any resize window.
        if data.zoom >= 1 and hasattr(self.ui, "canvas"):
            self.update_canvas()

    def when_closing(self):
        if ImageChops.difference(self.saved_copy, self.image).getbbox() or self.saved_copy.size != self.image.size:
            msg = messagebox.leave_brushshe()
            if msg.get() == _("Save"):
                self.save_current()
            elif msg.get() == _("Yes"):
                self.destroy_app()
        else:
            self.destroy_app()

    def destroy_app(self):
        if data.is_reset_settings_after_exiting:
            os.remove(config_file_path)
        self.ui.destroy()

    def scroll_on_canvasy(self, event):
        if event.num == 5 or event.delta < 0:
            count = 1
        if event.num == 4 or event.delta > 0:
            count = -1
        self.ui.canvas.yview_scroll(count, "units")
        if data.canvas_tails_area is not None and self.get_canvas_tails_area() != data.canvas_tails_area:
            self.update_canvas()

    def scroll_on_canvasx(self, event):
        if event.num == 5 or event.delta < 0:
            count = 1
        if event.num == 4 or event.delta > 0:
            count = -1
        self.ui.canvas.xview_scroll(count, "units")
        if data.canvas_tails_area is not None and self.get_canvas_tails_area() != data.canvas_tails_area:
            self.update_canvas()

    def begin_moving_canvas(self, event):
        self.ui.canvas.scan_mark(event.x, event.y)

    def continue_moving_canvas(self, event):
        self.ui.canvas.scan_dragto(event.x, event.y, gain=1)
        if data.canvas_tails_area is not None and self.get_canvas_tails_area() != data.canvas_tails_area:
            self.update_canvas()

    def zoom_in(self, event=None):
        self.ui.canvas.delete("tools")

        if 1 < data.zoom < 2:  # Need if zoom not integer but more 1 and less 2
            data.zoom = 1
        if 1 <= data.zoom < 12:
            data.zoom += 1
        elif data.zoom < 1:
            data.zoom *= 2

        self.force_resize_canvas_with_correct()
        self.update_canvas()

    def zoom_out(self, event=None):
        self.ui.canvas.delete("tools")

        if 1 < data.zoom:
            data.zoom -= 1
        elif 0.05 < data.zoom <= 1:  # Zooming limited down by 0.05.
            data.zoom /= 2

        self.force_resize_canvas_with_correct()
        self.update_canvas()

    def reset_zoom(self, event=None):
        self.ui.canvas.delete("tools")

        data.zoom = 1

        self.force_resize_canvas_with_correct()
        self.update_canvas()

    def canvas_to_pict_xy(self, x, y):
        return self.ui.canvas.canvasx(x) // data.zoom, self.ui.canvas.canvasy(y) // data.zoom

    def canvas_to_pict_xy_f(self, x, y):
        return self.ui.canvas.canvasx(x) / data.zoom, self.ui.canvas.canvasy(y) / data.zoom

    def get_tool_main_color(self):
        if self.current_tool == "eraser":
            color = data.bg_color
            if self.image.mode == "RGBA":
                color = "#00000000"
        else:
            # For shape, etc.
            color = data.brush_color
            if self.image.mode == "RGBA":
                color = self.rgb_tuple_to_rgba_tuple(self.rgb_color_to_tuple(color), 255)
        return color

    def record_action(self):
        data.undo_stack.append(self.image.copy())
        if data.autosave_var.get() and data.current_file is not None:
            self.save_current(autosave=True)

    def draw_line(self, x1, y1, x2, y2):
        color = self.get_tool_main_color()

        if self.selected_mask_img is None:
            bh_draw_line(self.draw, x1, y1, x2, y2, color, data.tool_size, data.brush_shape, self.current_tool)
        else:
            tmp_image = self.image.copy()
            tmp_draw = ImageDraw.Draw(tmp_image)
            bh_draw_line(tmp_draw, x1, y1, x2, y2, color, data.tool_size, data.brush_shape, self.current_tool)
            self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
            del tmp_image

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
        if data.zoom < 1:
            # https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-filters
            canvas_image = self.image.resize(
                (math.ceil(self.image.width * data.zoom), math.ceil(self.image.height * data.zoom)), Image.BOX
            )
            if self.selected_mask_img is None:
                mask_image = None
            else:
                mask_image = self.selected_mask_img.resize(
                    (
                        math.ceil(self.selected_mask_img.width * data.zoom),
                        math.ceil(self.selected_mask_img.height * data.zoom),
                    ),
                    Image.NEAREST,
                )

            tails_area = None

            data.composer.set_l_image(canvas_image)
            data.composer.set_mask_image(mask_image, tails_area)

            compose_image = data.composer.get_compose_image(0, 0, canvas_image.width - 1, canvas_image.height - 1)

            self.img_tk = ImageTk.PhotoImage(compose_image)
            self.ui.canvas.itemconfig(self.canvas_image, image=self.img_tk)
            self.ui.canvas.moveto(self.canvas_image, 0, 0)
            data.canvas_tails_area = tails_area

            return

        else:  # data.zoom > 1 or data.zoom = 1:
            # It work incorrect at this implementation for zoom < 1.

            cw_full = math.ceil(self.image.width * data.zoom)
            ch_full = math.ceil(self.image.height * data.zoom)

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
                    math.floor(x1 / data.zoom),
                    math.floor(y1 / data.zoom),
                    math.floor(x2 / data.zoom) + 1,
                    math.floor(y2 / data.zoom) + 1,
                )

                # Subpixel correct.
                x1_correct = tiles_xy_on_image[0] * data.zoom
                y1_correct = tiles_xy_on_image[1] * data.zoom

                dx = math.floor(x1 - x1_correct)
                dy = math.floor(y1 - y1_correct)

                # # Debug
                # print((x1, y1, x2, y2), tiles_xy_on_image, (x1_correct, y1_correct), (dx, dy))

                tmp_canvas_image = self.image.crop(tiles_xy_on_image)
                if self.selected_mask_img is None:
                    tmp_mask_image = None
                else:
                    tmp_mask_image = self.selected_mask_img.crop(tiles_xy_on_image)

            r_w = math.floor(tmp_canvas_image.width * data.zoom)
            r_h = math.floor(tmp_canvas_image.height * data.zoom)
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

            data.composer.set_l_image(canvas_image)
            data.composer.set_mask_image(mask_image, tails_area)

            compose_image = data.composer.get_compose_image(x1, y1, x2 + dx, y2 + dy)

            self.img_tk = ImageTk.PhotoImage(compose_image)
            self.ui.canvas.itemconfig(self.canvas_image, image=self.img_tk)
            self.ui.canvas.moveto(self.canvas_image, x1_correct, y1_correct)
            data.canvas_tails_area = tails_area

            return

    def get_canvas_tails_area(self):
        cw_full = int(self.image.width * data.zoom)
        ch_full = int(self.image.height * data.zoom)

        # Set param canvas with real image size. Not use bbox in this place.
        self.ui.canvas.config(scrollregion=(0, 0, cw_full, ch_full), width=cw_full, height=ch_full)

        iw, ih = self.image.size
        cx_frame_1, cx_frame_2 = self.ui.canvas.xview()
        cy_frame_1, cy_frame_2 = self.ui.canvas.yview()

        # Find the area without subpixel correct.
        x1 = math.floor(cx_frame_1 * cw_full / data.canvas_tail_size) * data.canvas_tail_size
        y1 = math.floor(cy_frame_1 * ch_full / data.canvas_tail_size) * data.canvas_tail_size
        x2 = math.ceil(cx_frame_2 * cw_full / data.canvas_tail_size) * data.canvas_tail_size - 1
        y2 = math.ceil(cy_frame_2 * ch_full / data.canvas_tail_size) * data.canvas_tail_size - 1
        if x2 > cw_full - 1:
            x2 = cw_full - 1
        if y2 > ch_full - 1:
            y2 = ch_full - 1

        return (x1, y1, x2, y2)

    def force_resize_canvas(self):
        cw_full = int(self.image.width * data.zoom)
        ch_full = int(self.image.height * data.zoom)

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
        cw_full = int(self.image.width * data.zoom)
        ch_full = int(self.image.height * data.zoom)

        self.ui.canvas.scan_mark(int(dx_1 * cw_full - wd_x_1), int(dy_1 * ch_full - wd_y_1))
        self.ui.canvas.scan_dragto(int(dx_2 * cw_full), int(dy_2 * ch_full), gain=1)

    def crop_picture(self, x1, y1, x2, y2, event=None):
        new_width = x2 - x1
        new_height = y2 - y1

        if self.image.mode == "RGBA":
            new_image = Image.new("RGBA", (new_width, new_height), "#00000000")
            new_image.paste(self.image, (-x1, -y1), self.image)
        else:
            new_image = Image.new("RGB", (new_width, new_height), data.bg_color)
            new_image.paste(self.image, (-x1, -y1))
        self.image = new_image
        self.draw = ImageDraw.Draw(self.image)

        self.selected_mask_img = None

        self.force_resize_canvas()
        self.update_canvas()

        self.record_action()

    def eyedropper(self, event):
        # Get the coordinates of the click event
        x, y = self.canvas_to_pict_xy(event.x, event.y)

        color = self.image.getpixel((x, y))
        self.obtained_color = "#{:02x}{:02x}{:02x}".format(*color)

        data.brush_color = self.obtained_color
        self.ui.brush_palette.main_color = self.obtained_color

    def start_fill(self):
        self.set_tool("fill", "Fill", None, None, None, "cross")
        self.ui.canvas.bind("<Button-1>", self.fill)

    def fill(self, event):
        x, y = self.canvas_to_pict_xy(event.x, event.y)
        tmp_image = self.image if self.selected_mask_img is None else self.image.copy()

        if self.image.mode == "RGBA":
            fill_color = self.rgb_tuple_to_rgba_tuple(ImageColor.getrgb(data.brush_color), 255)
        else:
            fill_color = ImageColor.getrgb(data.brush_color)

        if data.is_gradient_fill.get() == "on":
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

        start_color = ImageColor.getrgb(data.brush_color)
        end_color = ImageColor.getrgb(data.second_brush_color)
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

    def open_from_file(self):
        dialog = FileDialog(self.ui, title=_("Open from file"))
        if dialog.path:
            self.open_image(dialog.path)

    def open_from_url(self):
        dialog = ctk.CTkInputDialog(text=_("Enter URL:"), title=_("Open from URL"))
        image_url = dialog.get_input()
        if image_url is not None:
            try:
                with urlopen(image_url) as response:
                    image_data = BytesIO(response.read())
                    self.open_image(image_data)
            except Exception as e:
                messagebox.open_file_error(e)

    def save_current(self, autosave=False):
        if data.current_file is not None:
            try:
                self.image.save(data.current_file)
                self.saved_copy = self.image.copy()
                if not autosave:
                    messagebox.save_current()
            except Exception as e:
                messagebox.save_file_error(e)
        else:
            self.save_as()

    def save_as(self):
        dialog = FileDialog(self.ui, title=_("Save to device"), save=True)
        if dialog.path:
            try:
                self.image.save(dialog.path)
                self.saved_copy = self.image.copy()
                messagebox.save_as(dialog.extension)
                data.current_file = dialog.path
                self.ui.title(os.path.basename(data.current_file) + " - " + _("Brushshe"))
            except Exception as e:
                messagebox.save_file_error(e)

    def other_bg_color(self):
        askcolor = AskColor(title=_("Choose a different background color"), initial_color="#ffffff")
        obtained_bg_color = askcolor.get()
        if obtained_bg_color:
            self.new_picture(obtained_bg_color)

    def show_stickers_choice(self):
        def sticker_from_file():
            dialog = FileDialog(sticker_choose, title=_("Sticker from file"))
            if dialog.path:
                try:
                    sticker_image = Image.open(dialog.path)
                    self.set_current_sticker(sticker_image)
                except Exception as e:
                    messagebox.open_file_error(e)

        def sticker_from_url():
            dialog = ctk.CTkInputDialog(text=_("Enter URL:"), title=_("Open from URL"))
            image_url = dialog.get_input()
            if image_url is not None:
                try:
                    with urlopen(image_url) as response:
                        image_data = BytesIO(response.read())
                        sticker_image = Image.open(image_data)
                        self.set_current_sticker(sticker_image)
                except Exception as e:
                    messagebox.open_file_error(e)

        def tabview_callback():
            if tabview.get() == _("From file"):
                sticker_from_file()
            elif tabview.get() == _("From URL"):
                sticker_from_url()
            tabview.set(_("From set"))

        sticker_choose = ctk.CTkToplevel(self.ui)
        sticker_choose.geometry("370x500")
        sticker_choose.title(_("Choose a sticker"))

        tabview = ctk.CTkTabview(sticker_choose, command=tabview_callback)
        tabview.add(_("From set"))
        tabview.add(_("From file"))
        tabview.add(_("From URL"))
        tabview.set(_("From set"))
        tabview.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        stickers_scrollable_frame = ctk.CTkScrollableFrame(tabview.tab(_("From set")))
        stickers_scrollable_frame.pack(fill=ctk.BOTH, expand=True)
        scroll(stickers_scrollable_frame)

        stickers_frame = ctk.CTkFrame(stickers_scrollable_frame)
        stickers_frame.pack()

        row = 0
        column = 0
        for sticker_image in data.stickers:
            sticker_ctkimage = ctk.CTkImage(sticker_image, size=(100, 100))
            ctk.CTkButton(
                stickers_frame,
                text=None,
                image=sticker_ctkimage,
                command=lambda img=sticker_image: self.set_current_sticker(img),
            ).grid(row=row, column=column, padx=10, pady=10)
            column += 1
            if column == 2:
                column = 0
                row += 1

    def set_current_sticker(self, sticker_image=None):  # Choose a sticker
        if sticker_image:
            self.last_sticker_image = sticker_image

        if data.is_sticker_use_real_size.get() == "off":
            self.set_tool("sticker", "Stickers", data.sticker_size, 10, 250, "cross")
            self.insert_simple(self.last_sticker_image)
        else:
            self.set_tool("real size sticker", "Stickers", 100, 1, 500, "cross")
            self.insert_simple(self.last_sticker_image)

    def text_tool(self):
        def add_text(event):
            self.draw.text((self.text_x, self.text_y), self.tx_entry.get(), fill=data.brush_color, font=self.imagefont)
            self.update_canvas()
            self.record_action()

        def draw_text_halo(event):
            self.ui.canvas.delete("tools")

            x, y = self.canvas_to_pict_xy(event.x, event.y)
            self.imagefont = ImageFont.truetype(data.font_path, data.tool_size)

            bbox = self.draw.textbbox((0, 0), self.tx_entry.get(), font=self.imagefont)

            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            self.text_x = x - text_width // 2 - bbox[0]
            self.text_y = y - text_height // 2 - bbox[1]

            self.ui.canvas.create_rectangle(
                (x - text_width // 2) * data.zoom,
                (y - text_height // 2) * data.zoom,
                (x + text_width // 2) * data.zoom,
                (y + text_height // 2) * data.zoom,
                outline="white",
                width=1,
                tag="tools",
            )

            self.ui.canvas.create_rectangle(
                (x - text_width // 2) * data.zoom,
                (y - text_height // 2) * data.zoom,
                (x + text_width // 2) * data.zoom,
                (y + text_height // 2) * data.zoom,
                outline="black",
                width=1,
                tag="tools",
                dash=(5, 5),
            )

        def leave(event):
            self.ui.canvas.delete("tools")

        self.set_tool("text", "Text", data.font_size, 11, 96, "cross")
        self.ui.canvas.bind("<Button-1>", add_text)
        self.ui.canvas.bind("<Motion>", draw_text_halo)
        self.ui.canvas.bind("<Leave>", leave)

    def font_optionmenu_callback(self, value):
        data.current_font = value
        data.font_path = resource(data.fonts_dict.get(value))
        self.imagefont = ImageFont.truetype(data.font_path, data.tool_size)

    def show_frame_choice(self):
        def on_frames_click(index):
            selected_frame = data.frames[index]
            resized_frame = selected_frame.resize((self.image.width, self.image.height))

            self.image.paste(resized_frame, (0, 0), resized_frame)

            self.update_canvas()
            self.record_action()

        frames_win = ctk.CTkToplevel(self.ui)
        frames_win.title(_("Frames"))

        row = 0
        column = 0

        for i, image in enumerate(data.frames_thumbnails):
            ctk.CTkButton(frames_win, text=None, image=image, command=lambda i=i: on_frames_click(i)).grid(
                column=column, row=row, padx=10, pady=10
            )
            column += 1
            if column == 2:
                column = 0
                row += 1

    # Shape creation functions
    def create_shape(self, shape):
        x_begin, y_begin = None, None

        def start_shape(event):
            nonlocal x_begin, y_begin

            self.shape_x, self.shape_y = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
            x_begin, y_begin = self.canvas_to_pict_xy(event.x, event.y)
            self.get_contrast_color()

            shape_methods = {
                "Rectangle": self.ui.canvas.create_rectangle,
                "Oval": self.ui.canvas.create_oval,
                "Line": self.ui.canvas.create_line,
                "Fill rectangle": self.ui.canvas.create_rectangle,
                "Fill oval": self.ui.canvas.create_oval,
            }

            create_method = shape_methods.get(shape)
            if create_method:
                param = "fill" if shape == "Line" else "outline"
                self.shape_id = create_method(
                    self.shape_x, self.shape_y, self.shape_x, self.shape_y, **{param: self.contrast_color}
                )

        def draw_shape(event):
            if not hasattr(self, "shape_x"):
                return
            x, y = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
            self.ui.canvas.coords(self.shape_id, self.shape_x, self.shape_y, x, y)

        def end_shape(event):
            nonlocal x_begin, y_begin

            if not hasattr(self, "shape_x"):
                return

            x_end, y_end = self.canvas_to_pict_xy(event.x, event.y)

            if x_begin < x_end:
                x0, x1 = x_begin, x_end
            else:
                x0, x1 = x_end, x_begin
            if y_begin < y_end:
                y0, y1 = y_begin, y_end
            else:
                y0, y1 = y_end, y_begin

            if self.selected_mask_img is None:
                tmp_draw = ImageDraw.Draw(self.image)
            else:
                tmp_image = self.image.copy()
                tmp_draw = ImageDraw.Draw(tmp_image)

            color = self.get_tool_main_color()

            if shape == "Rectangle":
                tmp_draw.rectangle([x0, y0, x1, y1], outline=data.brush_color, width=data.tool_size)
            elif shape == "Oval":
                tmp_draw.ellipse([x0, y0, x1, y1], outline=data.brush_color, width=data.tool_size)
            elif shape == "Line":
                # self.draw_line(x_begin, y_begin, x_end, y_end)
                bh_draw_line(
                    tmp_draw, x_begin, y_begin, x_end, y_end, color, data.tool_size, data.brush_shape, self.current_tool
                )
            elif shape == "Fill rectangle":
                tmp_draw.rectangle([x0, y0, x1, y1], fill=data.brush_color)
            elif shape == "Fill oval":
                tmp_draw.ellipse([x0, y0, x1, y1], fill=data.brush_color)
            else:
                print("Warning: Incorrect shape.")

            if self.selected_mask_img is None:
                pass
            else:
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
                del tmp_image

            self.update_canvas()
            self.record_action()

            # Removing unnecessary variables for normal selection of the next shape in the menu
            #   and disabling other side effects.
            del self.shape_x, self.shape_y
            self.ui.canvas.delete(self.shape_id)

        if shape == "Fill rectangle" or shape == "Fill oval":
            self.set_tool("shape", shape, None, None, None, "cross")
        else:
            self.set_tool("shape", shape, data.shape_size, 1, 50, "cross")

        self.ui.canvas.bind("<ButtonPress-1>", start_shape)
        self.ui.canvas.bind("<B1-Motion>", draw_shape)
        self.ui.canvas.bind("<ButtonRelease-1>", end_shape)

    def bezier_shape(self):
        # Simple 4th point (cubic) Bezier curve.

        canvas_points = []
        image_points = []
        bezier_id = None

        # Clear canvas.
        self.update_canvas()

        def start(event):
            nonlocal canvas_points, image_points, bezier_id

            if len(canvas_points) == 0:
                self.get_contrast_color()

                cx, cy = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)

                canvas_points.append((cx, cy))
                image_points.append(self.canvas_to_pict_xy(event.x, event.y))

                bezier_id = self.ui.canvas.create_line(
                    cx, cy, cx, cy, fill=self.contrast_color, tag="tools"
                )  # smooth="bezier"

        def drawing(event):
            nonlocal canvas_points, bezier_id

            if bezier_id is None or len(canvas_points) == 0:
                return

            cx, cy = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
            len_p = len(canvas_points)
            canvas_points_tmp = canvas_points.copy()

            if len_p <= 1:
                canvas_points_tmp.append((cx, cy))
            else:
                canvas_points_tmp.append(canvas_points_tmp[len_p - 1])
                canvas_points_tmp[len_p - 1] = (cx, cy)

            ts = [t / 32.0 for t in range(33)]  # 32 lines for preview.
            b = make_bezier(canvas_points_tmp)
            points = b(ts)

            # Do 2d array flat for canvas.coords
            points_flat = [j for sub in points for j in sub]

            self.ui.canvas.coords(bezier_id, *points_flat)

        def end(event):
            nonlocal canvas_points, image_points, bezier_id

            if bezier_id is None or len(canvas_points) == 0:
                return

            cx, cy = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
            px, py = self.canvas_to_pict_xy(event.x, event.y)
            len_p = len(canvas_points)
            stop = False

            if len_p <= 1:
                canvas_points.append((cx, cy))
                image_points.append((px, py))
            else:
                tx, ty = canvas_points[len_p - 2]

                if cx == tx and cy == ty and len_p > 2:
                    stop = True
                else:
                    canvas_points.append(canvas_points[len_p - 1])
                    canvas_points[len_p - 1] = (cx, cy)

                    len_ip = len(image_points)
                    image_points.append(image_points[len_ip - 1])
                    image_points[len_ip - 1] = (px, py)

            # Finish
            if len(canvas_points) >= 4 or stop:
                # Calculate segments count.
                max_segments = 0
                points_len = len(image_points)
                for ii, ip in enumerate(image_points):
                    if ii < points_len - 1:
                        max_segments += max(
                            abs(image_points[ii][0] - image_points[ii + 1][0]),
                            abs(image_points[ii][1] - image_points[ii + 1][1]),
                        )
                max_segments = max_segments // 3
                if max_segments < 32:
                    max_segments = 32

                # Draw on picture.
                ts = [t / max_segments for t in range(int(max_segments + 1))]
                b = make_bezier(image_points)
                points = b(ts)
                points_len = len(points)

                color = self.get_tool_main_color()

                if self.selected_mask_img is None:
                    tmp_image = self.image
                    tmp_draw = ImageDraw.Draw(tmp_image)
                else:
                    tmp_image = self.image.copy()
                    tmp_draw = ImageDraw.Draw(tmp_image)

                for it, tt in enumerate(points):
                    if it < points_len - 1:
                        bh_draw_line(
                            tmp_draw,
                            int(points[it][0]),
                            int(points[it][1]),
                            int(points[it + 1][0]),
                            int(points[it + 1][1]),
                            color,
                            data.tool_size,
                            data.brush_shape,
                            self.current_tool,
                        )

                if self.selected_mask_img is None:
                    pass
                else:
                    self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
                    del tmp_image

                self.ui.canvas.delete(bezier_id)
                self.update_canvas()
                self.record_action()

                # Reset nonlocal variables.
                canvas_points = []
                image_points = []
                bezier_id = None

        self.set_tool("shape", "Bezier", data.shape_size, 1, 50, "cross")

        self.ui.canvas.bind("<ButtonPress-1>", start)
        self.ui.canvas.bind("<B1-Motion>", drawing)
        self.ui.canvas.bind("<ButtonRelease-1>", end)
        self.ui.canvas.bind("<Motion>", drawing)

    def recoloring_brush(self):
        self.set_tool("r-brush", "R. Brush", data.brush_size, 1, 50, "pencil")

        prev_x = None
        prev_y = None
        point_history = None

        def drawing(event):
            nonlocal prev_x, prev_y, point_history

            if data.is_brush_smoothing is False:
                x, y = self.canvas_to_pict_xy(event.x, event.y)
            else:
                if point_history is None:
                    point_history = BhHistory(limit_length=data.brush_smoothing_factor)
                xf, yf = self.canvas_to_pict_xy_f(event.x, event.y)
                point_history.add_point(BhPoint(x=xf, y=yf, pressure=1.0))
                s_point = point_history.get_smoothing_point(
                    data.brush_smoothing_factor,
                    data.brush_smoothing_quality,
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
            color_to = ImageColor.getrgb(data.brush_color)
            color_from = ImageColor.getrgb(data.second_brush_color)

            # FIXME: In current time it works only for 100% opacity color.
            if self.image.mode == "RGBA":
                color_from = self.rgb_tuple_to_rgba_tuple(color_from, 255)
                color_to = self.rgb_tuple_to_rgba_tuple(color_to, 255)

            if self.selected_mask_img is None:
                bh_draw_recoloring_line(self.image, x1, y1, x2, y2, color_from, color_to, data.tool_size)
            else:
                tmp_image = self.image.copy()
                bh_draw_recoloring_line(tmp_image, x1, y1, x2, y2, color_from, color_to, data.tool_size)
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
                del tmp_image

        def draw_brush_halo(x, y):
            self.ui.canvas.delete("tools")

            d1 = (data.tool_size - 1) // 2
            d2 = data.tool_size // 2

            self.ui.canvas.create_rectangle(
                int((x - d1) * data.zoom - 1),
                int((y - d1) * data.zoom - 1),
                int((x + d2 + 1) * data.zoom),
                int((y + d2 + 1) * data.zoom),
                outline="white",
                width=1,
                tag="tools",
            )
            self.ui.canvas.create_rectangle(
                int((x - d1) * data.zoom),
                int((y - d1) * data.zoom),
                int((x + d2 + 1) * data.zoom - 1),
                int((y + d2 + 1) * data.zoom - 1),
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
            bg_color = data.bg_color
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
                        fill=data.bg_color,
                        outline=data.bg_color,
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
                int(x1 * data.zoom),
                int(y1 * data.zoom),
                int((x2 + 1) * data.zoom - 1),
                int((y2 + 1) * data.zoom - 1),
                outline="white",
                width=1,
                tag="tools",
            )
            self.ui.canvas.create_rectangle(
                int(x1 * data.zoom),
                int(y1 * data.zoom),
                int((x2 + 1) * data.zoom - 1),
                int((y2 + 1) * data.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
                dash=(5, 5),
            )

        self.ui.canvas.bind("<Button-1>", selecting)
        self.ui.canvas.bind("<B1-Motion>", selecting)
        self.ui.canvas.bind("<ButtonRelease-1>", select_end)

    def delete_selected(self):
        if self.selected_mask_img is None:
            return

        bg_color = data.bg_color
        if self.image.mode == "RGBA":
            bg_color = (0, 0, 0, 0)
        tmp_img = Image.new(self.image.mode, (self.image.width, self.image.height), bg_color)
        self.image.paste(tmp_img, (0, 0), self.selected_mask_img)
        del tmp_img
        self.record_action()
        self.update_canvas()

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
                it_width = data.tool_size
                it_height = int(insert_image.height * data.tool_size / insert_image.width)
                resampling = Image.BICUBIC
            else:
                it_width = int(insert_image.width / 100 * data.tool_size)
                it_height = int(insert_image.height / 100 * data.tool_size)
                if it_width <= 1 or it_height <= 1:
                    it_width, it_height = (1, 1)
                if data.is_insert_smoothing.get() == "off":
                    resampling = Image.NEAREST
                else:
                    resampling = Image.BICUBIC
            image_tmp = insert_image.resize((it_width, it_height), resampling)

            x, y = self.canvas_to_pict_xy(event.x, event.y)

            x1 = int(x - (it_width - 1) / 2)
            y1 = int(y - (it_height - 1) / 2)
            x2 = int(x1 + it_width - 1)
            y2 = int(y1 + it_height - 1)

            image_tmp_view = image_tmp.resize((int(it_width * data.zoom), int(it_height * data.zoom)), Image.BOX)
            image_tk = ImageTk.PhotoImage(image_tmp_view)
            current_zoom = data.zoom

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
                int(x1 * data.zoom),
                int(y1 * data.zoom),
                image=image_tk,
                tag="tools",
                anchor="nw",
            )

            self.ui.canvas.create_rectangle(
                int(x1 * data.zoom),
                int(y1 * data.zoom),
                int((x2 + 1) * data.zoom - 1),
                int((y2 + 1) * data.zoom - 1),
                outline="white",
                width=1,
                tag="tools",
            )
            self.ui.canvas.create_rectangle(
                int(x1 * data.zoom),
                int(y1 * data.zoom),
                int((x2 + 1) * data.zoom - 1),
                int((y2 + 1) * data.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
                dash=(5, 5),
            )

        self.ui.canvas.bind("<ButtonRelease-1>", insert_end)
        self.ui.canvas.bind("<Motion>", move)
        self.ui.canvas.bind("<Leave>", leave)

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
                int(x1 * data.zoom),
                int(y1 * data.zoom),
                int((x2 + 1) * data.zoom - 1),
                int((y2 + 1) * data.zoom - 1),
                outline="white",
                width=1,
                tag="tools",
            )
            self.ui.canvas.create_rectangle(
                int(x1 * data.zoom),
                int(y1 * data.zoom),
                int((x2 + 1) * data.zoom - 1),
                int((y2 + 1) * data.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
                dash=(5, 5),
            )

        self.ui.canvas.bind("<Button-1>", cropping)
        self.ui.canvas.bind("<B1-Motion>", cropping)
        self.ui.canvas.bind("<ButtonRelease-1>", crop_end)

    def effects(self):
        self.set_tool("effects", "Effects", 10, 1, 20, "circle")

    def apply_effect(self):
        def post_actions():
            if self.selected_mask_img is None:
                self.image = result
                self.draw = ImageDraw.Draw(self.image)
            else:
                self.image.paste(result, (0, 0), self.selected_mask_img)
            self.update_canvas()
            self.record_action()

        effect_value = self.effects_optionmenu.get()

        if effect_value == _("Blur"):
            result = self.image.copy().filter(ImageFilter.GaussianBlur(radius=data.tool_size))
        elif effect_value == _("Detail"):
            result = ImageEnhance.Sharpness(self.image.copy()).enhance(data.tool_size)
        elif effect_value == _("Contour"):
            result = self.image.copy().filter(ImageFilter.CONTOUR)
        elif effect_value == _("Grayscale"):
            result = ImageOps.grayscale(self.image.copy())
        elif effect_value == _("Mirror"):
            result = ImageOps.mirror(self.image.copy())
        elif effect_value == _("Metal"):
            result = self.image.copy().filter(ImageFilter.EMBOSS)
        elif effect_value == _("Inversion"):
            result = ImageOps.invert(self.image.copy())
        elif effect_value == _("Brightness"):
            result = ImageEnhance.Brightness(self.image.copy()).enhance(data.tool_size / 10)
        elif effect_value == _("Contrast"):
            result = ImageEnhance.Contrast(self.image.copy()).enhance(data.tool_size / 10)
        post_actions()

    def new_picture(self, color="#FFFFFF", mode="RGB", first_time=False):
        self.ui.canvas.delete("tools")
        data.bg_color = color

        self.image = Image.new(mode, (640, 480), color)
        self.saved_copy = self.image.copy()
        self.draw = ImageDraw.Draw(self.image)
        self.ui.canvas.xview_moveto(0)
        self.ui.canvas.yview_moveto(0)

        if first_time:
            self.img_tk = ImageTk.PhotoImage(self.image)
            self.canvas_image = self.ui.canvas.create_image(0, 0, anchor=ctk.NW, image=self.img_tk)
        else:
            pass

        self.selected_mask_img = None

        self.force_resize_canvas()
        self.update_canvas()

        self.record_action()
        self.ui.title(_("Unnamed") + " - " + _("Brushshe"))
        data.current_file = None

    def change_tool_size(self, value):
        data.tool_size = int(value)
        if self.current_tool == "brush" or self.current_tool == "r-brush":
            data.brush_size = int(value)
        elif self.current_tool == "eraser":
            data.eraser_size = int(value)
        elif self.current_tool == "spray":
            data.spray_size = int(value)
        elif self.current_tool == "shape":
            data.shape_size = int(value)
        elif self.current_tool == "sticker":
            data.sticker_size = int(value)
        elif self.current_tool == "text":
            data.font_size = int(value)
        if self.current_tool in ["insert", "real size sticker"]:
            self.ui.tool_size_label.configure(text=f"{data.tool_size} %")
        else:
            self.ui.tool_size_label.configure(text=data.tool_size)
        self.ui.tool_size_tooltip.configure(message=data.tool_size)

    def get_tool_size(self):
        res = data.tool_size
        if self.current_tool == "brush" or self.current_tool == "r-brush":
            res = data.brush_size
        elif self.current_tool == "eraser":
            res = data.eraser_size
        elif self.current_tool == "spray":
            res = data.spray_size
        elif self.current_tool == "shape":
            res = data.shape_size
        elif self.current_tool == "sticker":
            res = data.sticker_size
        elif self.current_tool == "text":
            res = data.font_size
        return res

    def brush(self, type="brush"):
        prev_x = None
        prev_y = None
        point_history = None

        if type == "brush":
            self.set_tool("brush", "Brush", data.brush_size, 1, 50, "pencil")
        elif type == "eraser":
            self.set_tool("eraser", "Eraser", data.eraser_size, 1, 50, "target")
        else:
            print("Warning: Incorrect brush type. Set default as.")
            self.set_tool("brush", "Brush", data.brush_size, 1, 50, "pencil")

        def paint(event):
            nonlocal prev_x, prev_y, point_history

            if data.is_brush_smoothing is False:
                x, y = self.canvas_to_pict_xy(event.x, event.y)
            else:
                if point_history is None:
                    point_history = BhHistory(limit_length=data.brush_smoothing_factor)
                xf, yf = self.canvas_to_pict_xy_f(event.x, event.y)
                point_history.add_point(BhPoint(x=xf, y=yf, pressure=1.0))
                s_point = point_history.get_smoothing_point(
                    data.brush_smoothing_factor,
                    data.brush_smoothing_quality,
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

            d1 = (data.tool_size - 1) // 2
            d2 = data.tool_size // 2

            # TODO: Need use the pixel perfect halo for zoom >= 2 if it doesn't too slow.

            if data.brush_shape == "circle":
                canvas_create_shape = self.ui.canvas.create_oval
            elif data.brush_shape == "square":
                canvas_create_shape = self.ui.canvas.create_rectangle

            canvas_create_shape(
                int((x - d1) * data.zoom - 1),
                int((y - d1) * data.zoom - 1),
                int((x + d2 + 1) * data.zoom),
                int((y + d2 + 1) * data.zoom),
                outline="white",
                width=1,
                tag="tools",
            )
            canvas_create_shape(
                int((x - d1) * data.zoom),
                int((y - d1) * data.zoom),
                int((x + d2 + 1) * data.zoom - 1),
                int((y + d2 + 1) * data.zoom - 1),
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

    def eraser(self):
        self.brush(type="eraser")

    def spray(self):
        def start_spray(event):
            data.prev_x, data.prev_y = self.canvas_to_pict_xy(event.x, event.y)
            self.spraying = True
            do_spray()

        def do_spray():
            if not self.spraying or data.prev_x is None or data.prev_y is None:
                return

            if self.selected_mask_img is None:
                tmp_image = self.image
                tmp_draw = ImageDraw.Draw(tmp_image)
            else:
                tmp_image = self.image.copy()
                tmp_draw = ImageDraw.Draw(tmp_image)

            for i in range(data.tool_size * 2):
                offset_x = random.randint(-data.tool_size, data.tool_size)
                offset_y = random.randint(-data.tool_size, data.tool_size)
                if offset_x**2 + offset_y**2 <= data.tool_size**2:
                    tmp_draw.point((data.prev_x + offset_x, data.prev_y + offset_y), fill=data.brush_color)

            if self.selected_mask_img is None:
                pass
            else:
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)

            del tmp_image

            self.update_canvas()
            self.spray_job = self.ui.after(50, do_spray)

        def move_spray(event):
            data.prev_x, data.prev_y = self.canvas_to_pict_xy(event.x, event.y)

        def stop_spray(event):
            self.spraying = False
            if self.spray_job:
                self.ui.after_cancel(self.spray_job)
                self.spray_job = None
            data.prev_x, data.prev_y = (None, None)
            self.record_action()

        self.set_tool("spray", "Spray", data.spray_size, 5, 30, "spraycan")

        self.spraying = False
        self.spray_job = None
        self.ui.canvas.bind("<Button-1>", start_spray)
        self.ui.canvas.bind("<B1-Motion>", move_spray)
        self.ui.canvas.bind("<ButtonRelease-1>", stop_spray)

    # TODO: Add selected_mask_img on history with type `mask`.
    # FIXME: Need add length synchronization undo_stack and redo_stack (actually it must be one stack).
    def undo(self):
        if len(data.undo_stack) > 1:
            tmp_image = data.undo_stack.pop()
            is_resize = False
            if self.image.width != tmp_image.width or self.image.height != tmp_image.height:
                is_resize = True
            data.redo_stack.append(tmp_image)
            self.image = data.undo_stack[-1].copy()
            self.draw = ImageDraw.Draw(self.image)
            if is_resize:
                self.selected_mask_img = None
                self.force_resize_canvas()
            self.update_canvas()

    def redo(self):
        if len(data.redo_stack) > 0:
            tmp_image = data.redo_stack.pop().copy()
            is_resize = False
            if self.image.width != tmp_image.width or self.image.height != tmp_image.height:
                is_resize = True
            self.image = tmp_image
            self.record_action()
            self.draw = ImageDraw.Draw(self.image)
            if is_resize:
                self.selected_mask_img = None
                self.force_resize_canvas()
            self.update_canvas()

    def save_to_gallery(self):
        file_path = gallery.gallery_folder / f"{uuid4()}.png"
        while file_path.exists():
            file_path = gallery.gallery_folder / f"{uuid4()}.png"
        self.image.save(file_path)
        self.saved_copy = self.image.copy()

        data.current_file = str(file_path)
        self.ui.title(os.path.basename(data.current_file) + " - " + _("Brushshe"))

        messagebox.save_to_gallery()

    def change_color(self, new_color):
        data.brush_color = new_color
        self.ui.brush_palette.main_color = data.brush_color

    def main_color_choice(self):
        askcolor = AskColor(title=_("Color select"), initial_color=data.brush_color)
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            data.brush_color = self.obtained_color
            self.ui.brush_palette.main_color = self.obtained_color

    def second_color_choice(self):
        askcolor = AskColor(title=_("Color select"), initial_color=data.second_brush_color)
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            data.second_brush_color = self.obtained_color
            self.ui.brush_palette.second_color = self.obtained_color

    def color_choice_bth(self, event, btn):
        askcolor = AskColor(title=_("Color select"), initial_color=btn.cget("fg_color"))
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            btn.configure(
                fg_color=self.obtained_color,
                hover_color=self.obtained_color,
                command=lambda c=self.obtained_color: self.change_color(c),
            )
            data.brush_color = self.obtained_color
            self.ui.brush_palette.main_color = self.obtained_color

    def flip_brush_colors(self):
        data.brush_color = self.ui.brush_palette.second_color
        data.second_brush_color = self.ui.brush_palette.main_color

        self.ui.brush_palette.main_color = data.brush_color
        self.ui.brush_palette.second_color = data.second_brush_color

    def open_image(self, openimage):
        try:
            data.bg_color = "white"
            self.image = Image.open(openimage)
            self.saved_copy = self.image.copy()
            self.picture_postconfigure()

            self.selected_mask_img = None

            if not isinstance(openimage, BytesIO):
                data.current_file = openimage
                self.ui.title(os.path.basename(data.current_file) + " - " + _("Brushshe"))
            else:
                self.ui.title(_("Unnamed") + " - " + _("Brushshe"))
                data.current_file = None
        except Exception as e:
            messagebox.open_file_error(e)

    def get_contrast_color(self):
        stat = ImageStat.Stat(self.image)
        r, g, b = stat.mean[:3]
        self.contrast_color = "#232323" if (r + g + b) / 3 > 127 else "#e8e8e8"

    def rotate(self, degree):
        rotated_image = self.image.rotate(degree, expand=True)
        self.image = rotated_image
        self.picture_postconfigure()

    def screenshot_crop(self, screenshot_canvas, screenshot):
        x_begin = None
        y_begin = None
        x_end = None
        y_end = None

        def cropping(event):
            nonlocal x_begin, y_begin, x_end, y_end

            x, y = event.x, event.y

            if x_begin is None or y_begin is None:
                x_begin = x
                y_begin = y

            x_end = x
            y_end = y
            x_max = screenshot.width - 1
            y_max = screenshot.height - 1

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

            x_begin = None
            y_begin = None
            x_end = None
            y_end = None

            new_width = x2 - x1
            new_height = y2 - y1

            self.finished_screenshot = Image.new("RGB", (new_width, new_height), data.bg_color)
            self.finished_screenshot.paste(screenshot, (-x1, -y1))

        def draw_tool(x1, y1, x2, y2):
            screenshot_canvas.delete("screenshot_tool")

            screenshot_canvas.create_rectangle(
                int(x1),
                int(y1),
                int(x2 + 1),
                int(y2 + 1),
                outline="white",
                width=1,
                tag="screenshot_tool",
            )
            screenshot_canvas.create_rectangle(
                int(x1),
                int(y1),
                int(x2 + 1),
                int(y2 + 1),
                outline="black",
                width=1,
                tag="screenshot_tool",
                dash=(5, 5),
            )

        screenshot_canvas.bind("<Button-1>", cropping)
        screenshot_canvas.bind("<B1-Motion>", cropping)
        screenshot_canvas.bind("<ButtonRelease-1>", crop_end)

    def create_screenshot(self):
        def ready_screenshot(screenshot_img):
            self.image = screenshot_img.copy()
            self.picture_postconfigure()
            screenshot_window.destroy()

        self.withdraw()
        self.iconify()
        self.after(200)
        screenshot = ImageGrab.grab()
        self.deiconify()

        screenshot_window = ctk.CTkToplevel()
        screenshot_window.attributes("-fullscreen", True)

        screenshot_canvas = ctk.CTkCanvas(screenshot_window)
        screenshot_canvas.pack(fill="both", expand=True)

        screenthot_tk = ImageTk.PhotoImage(screenshot)
        screenshot_canvas.create_image(0, 0, anchor="nw", image=screenthot_tk)
        screenshot_canvas.image = screenthot_tk

        screenshot_button_frame = ctk.CTkFrame(screenshot_window)
        screenshot_button_frame.place(x=10, y=10)

        ctk.CTkButton(screenshot_button_frame, text=_("Cancel"), command=lambda: screenshot_window.destroy()).pack(
            side="left", padx=10, pady=10
        )
        ctk.CTkButton(
            screenshot_button_frame, text="OK", command=lambda: ready_screenshot(self.finished_screenshot)
        ).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(
            screenshot_button_frame, text=_("Capture the entire screen"), command=lambda: ready_screenshot(screenshot)
        ).pack(side="left", padx=10, pady=10)

        self.screenshot_crop(screenshot_canvas, screenshot)

    def remove_white_background(self):
        transparent_bg_img = self.image.convert("RGBA")
        datas = transparent_bg_img.getdata()

        new_data = []
        for item in datas:
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                new_data.append((0, 0, 0, 0))  # Lines with zeroes compressed better.
            else:
                new_data.append(item)

        transparent_bg_img.putdata(new_data)
        self.image = transparent_bg_img
        self.picture_postconfigure()

    def picture_postconfigure(self):
        self.ui.canvas.delete("tools")

        self.draw = ImageDraw.Draw(self.image)

        self.ui.canvas.xview_moveto(0)
        self.ui.canvas.yview_moveto(0)

        self.force_resize_canvas()
        self.update_canvas()

        self.record_action()

    def set_tool(self, tool, tool_name, tool_size, from_, to, cursor):
        self.current_tool = tool

        self.ui.canvas.unbind("<Button-1>")
        self.ui.canvas.unbind("<Shift-Button-1>")
        self.ui.canvas.unbind("<Control-Button-1>")
        self.ui.canvas.unbind("<ButtonPress-1>")
        self.ui.canvas.unbind("<ButtonRelease-1>")
        self.ui.canvas.unbind("<B1-Motion>")
        self.ui.canvas.unbind("<Motion>")
        self.ui.canvas.unbind("<Leave>")
        self.ui.canvas.unbind("<BackSpace>")
        self.ui.canvas.unbind("<Return>")

        for child in self.ui.tool_config_docker.winfo_children():
            child.destroy()

        self.ui.tool_label = ctk.CTkLabel(self.ui.tool_config_docker, text=None)
        self.ui.tool_label.pack(side=ctk.LEFT, padx=1)

        self.ui.tool_size_slider = ctk.CTkSlider(self.ui.tool_config_docker, command=self.change_tool_size)
        self.ui.tool_size_slider.pack(side=ctk.LEFT, padx=1)
        self.ui.tool_size_tooltip = Tooltip(self.ui.tool_size_slider)
        self.ui.tool_size_label = ctk.CTkLabel(self.ui.tool_config_docker, text=None)
        self.ui.tool_size_label.pack(side=ctk.LEFT, padx=5)

        if tool_size is None and from_ is None and to is None:
            self.ui.tool_label.configure(text=_(tool_name))
            self.ui.tool_size_slider.pack_forget()
            self.ui.tool_size_label.pack_forget()
        else:
            self.ui.tool_label.configure(text=_(tool_name) + ":")
            data.tool_size = tool_size
            self.ui.tool_size_slider.configure(from_=from_, to=to)
            self.ui.tool_size_slider.set(data.tool_size)
            self.ui.tool_size_slider.pack(side=ctk.LEFT, padx=1)
            if self.current_tool in ["insert", "real size sticker"]:
                self.ui.tool_size_label.configure(text=f"{data.tool_size} %")
            else:
                self.ui.tool_size_label.configure(text=data.tool_size)
            self.ui.tool_size_label.pack(side=ctk.LEFT, padx=5)
            self.ui.tool_size_tooltip.configure(message=data.tool_size)

        if self.current_tool in ["brush", "eraser"]:
            brush_shape_btn = ctk.CTkSegmentedButton(
                self.ui.tool_config_docker, values=["●", "■"], command=self.brush_shape_btn_callback
            )
            if data.brush_shape == "circle":
                brush_shape_btn.set("●")
            elif data.brush_shape == "square":
                brush_shape_btn.set("■")
            brush_shape_btn.pack(side=ctk.LEFT, padx=5)
        elif self.current_tool == "fill":
            ctk.CTkCheckBox(
                self.ui.tool_config_docker,
                text=_("Gradient"),
                variable=data.is_gradient_fill,
                onvalue="on",
                offvalue="off",
            ).pack(side=ctk.LEFT, padx=5)
            self.gradient_mode_optionmenu = ctk.CTkOptionMenu(
                self.ui.tool_config_docker,
                values=[_("Vertically"), _("Horizontally"), _("Diagonally"), _("Radially"), _("Rings"), _("Noise")],
            )
            self.gradient_mode_optionmenu.set(_("Vertically"))
            self.gradient_mode_optionmenu.pack(side=ctk.LEFT, padx=1)
        elif self.current_tool == "text":
            self.tx_entry = ctk.CTkEntry(self.ui.tool_config_docker, placeholder_text=_("Enter text..."))
            self.tx_entry.pack(side=ctk.LEFT, padx=5)

            font_optionmenu = ctk.CTkOptionMenu(
                self.ui.tool_config_docker,
                values=data.fonts,
                dynamic_resizing=False,
                command=self.font_optionmenu_callback,
            )
            font_optionmenu.set(data.current_font)
            font_optionmenu.pack(side=ctk.LEFT, padx=1)
        elif self.current_tool == "sticker" or self.current_tool == "real size sticker":
            ctk.CTkCheckBox(
                self.ui.tool_config_docker,
                text=_("Use real size"),
                variable=data.is_sticker_use_real_size,
                onvalue="on",
                offvalue="off",
                command=self.set_current_sticker,
            ).pack(side=ctk.LEFT, padx=5)
        elif self.current_tool == "effects":
            self.effects_optionmenu = ctk.CTkOptionMenu(
                self.ui.tool_config_docker, values=[_(value) for value in data.effect_values]
            )
            self.effects_optionmenu.pack(side=ctk.LEFT, padx=5)
            ctk.CTkButton(self.ui.tool_config_docker, text="OK", width=35, command=self.apply_effect).pack(
                side=ctk.LEFT, padx=1
            )
        elif self.current_tool == "insert":
            ctk.CTkCheckBox(
                self.ui.tool_config_docker,
                text=_("Smoothing"),
                variable=data.is_insert_smoothing,
                onvalue="on",
                offvalue="off",
            ).pack(side=ctk.LEFT, padx=5)

        self.ui.canvas.configure(cursor=cursor)
        self.ui.canvas.delete("tools")

    def import_palette(self, value=None):
        if value is None:
            dialog = FileDialog(
                self,
                title=_("Import palette from .hex file"),
            )

            if dialog.path is None or dialog.path == "":
                return

            palette_path = dialog.path
            config.set("Brushshe", "palette", palette_path)
            write_config()
        else:
            palette_path = value

        colors = []

        try:
            with open(palette_path) as f:
                lines = f.readlines()
                for line in lines:
                    if len(line) == 0:
                        continue

                    color = line.strip()
                    if line[0] != "#":
                        color = "#" + color
                    try:
                        self.ui.winfo_rgb(color)
                    except Exception:
                        print("Warning: String `{}` is not correct color.".format(color))
                        continue
                    colors.append(color)
        except FileNotFoundError:
            return
        except Exception:
            print("Incorrect file format?")
            return

        self.make_color_palette(colors)

    def reset_settings_after_exiting(self):
        data.is_reset_settings_after_exiting = True

    def brush_shape_btn_callback(self, value):
        if value == "●":
            data.brush_shape = "circle"
        elif value == "■":
            data.brush_shape = "square"

    def paste_image_from_clipboard(self):
        try:
            pasted_img = ImageGrab.grabclipboard()
            data.bg_color = "white"
            self.image = pasted_img
            self.picture_postconfigure()
        except Exception as e:
            messagebox.paste_error(e)

    def rgb_color_to_tuple(self, color):
        try:
            rgb = self.winfo_rgb(color)
            r = math.floor(rgb[0] / 256)
            g = math.floor(rgb[1] / 256)
            b = math.floor(rgb[2] / 256)
        except Exception:
            return (0, 0, 0)
        return (r, g, b)

    def rgb_tuple_to_rgba_tuple(self, color, alpha: int):
        try:
            res = (color[0], color[1], color[2], alpha)
        except Exception:
            print("Error: Wrong color.")
            res = (0, 0, 0, 0)
        return res

    def select_init_mask(self):
        if data.composer is None:
            return

        if self.selected_mask_img is None:
            self.selected_mask_img = Image.new("L", (self.image.width, self.image.height), "white")
        if self.selected_mask_img.width != self.image.width or self.selected_mask_img.height != self.image.height:
            self.selected_mask_img = Image.new("L", (self.image.width, self.image.height), "white")

    def remove_mask(self):
        self.selected_mask_img = None
        data.composer.mask_img = None

        data.composer.set_force_update_mask()
        self.update_canvas()

    def invert_mask(self):
        self.select_init_mask()

        tmp_mask_img = ImageOps.invert(self.selected_mask_img)
        self.selected_mask_img = tmp_mask_img
        del tmp_mask_img

        data.composer.set_force_update_mask()
        self.update_canvas()

    def select_all_mask(self):
        self.select_init_mask()

        x_max = self.image.width - 1
        y_max = self.image.height - 1
        draw = ImageDraw.Draw(self.selected_mask_img)
        draw.rectangle([0, 0, x_max, y_max], fill=255)

        data.composer.set_force_update_mask()
        self.update_canvas()

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

            data.composer.set_force_update_mask()
            self.update_canvas()

        def draw_tool(x1, y1, x2, y2):
            self.ui.canvas.delete("tools")

            self.ui.canvas.create_rectangle(
                int(x1 * data.zoom),
                int(y1 * data.zoom),
                int((x2 + 1) * data.zoom - 1),
                int((y2 + 1) * data.zoom - 1),
                outline="white",
                width=1,
                tag="tools",
            )
            self.ui.canvas.create_rectangle(
                int(x1 * data.zoom),
                int(y1 * data.zoom),
                int((x2 + 1) * data.zoom - 1),
                int((y2 + 1) * data.zoom - 1),
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

            data.composer.set_force_update_mask()
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
                    int(xy_list[xy_len - 2] * data.zoom),
                    int(xy_list[xy_len - 1] * data.zoom),
                    int(x * data.zoom),
                    int(y * data.zoom),
                    fill="black",
                    width=1,
                    tag="tools",
                )
                self.ui.canvas.create_line(
                    int(xy_list[xy_len - 2] * data.zoom),
                    int(xy_list[xy_len - 1] * data.zoom),
                    int(x * data.zoom),
                    int(y * data.zoom),
                    fill="white",
                    width=1,
                    tag="tools",
                    dash=(5, 5),
                )
                if xy_len >= 4:
                    tmp_xy_list = [int(x * data.zoom) for x in xy_list]
                    self.ui.canvas.create_line(tmp_xy_list, fill="black", width=1, tag="tools")
                    self.ui.canvas.create_line(tmp_xy_list, fill="white", width=1, tag="tools", dash=(5, 5))

            self.ui.canvas.create_rectangle(
                int(x_begin * data.zoom + delta),
                int(y_begin * data.zoom + delta),
                int(x_begin * data.zoom - delta),
                int(y_begin * data.zoom - delta),
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
                            if self._color_diff(p, background) <= thresh:
                                pixels_mask[ii, jj] = fill_color
                        except (ValueError, IndexError):
                            pass
            else:
                self._floodfill_mask(self.image, self.selected_mask_img, (x, y), fill_color)

            data.composer.set_force_update_mask()
            self.update_canvas()

        self.ui.canvas.bind("<Button-1>", lambda e: selecting(e, "replace"))
        self.ui.canvas.bind("<Shift-Button-1>", lambda e: selecting(e, "add"))
        self.ui.canvas.bind("<Control-Button-1>", lambda e: selecting(e, "subtract"))

    def _color_diff(self, color1: float | tuple[int, ...], color2: float | tuple[int, ...]) -> float:
        first = color1 if isinstance(color1, tuple) else (color1,)
        second = color2 if isinstance(color2, tuple) else (color2,)
        return sum(abs(first[i] - second[i]) for i in range(len(second)))

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
            # if self._color_diff(value, background) <= thresh:
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
                            fill = self._color_diff(p, background) <= thresh
                        else:
                            fill = p not in (value, border)
                        if fill:
                            pixel[s, t] = value
                            pixel_m[s, t] = value
                            new_edge.add((s, t))
            full_edge = edge
            edge = new_edge

    # Timer for musk
    def mask_update(self):
        mm_time = int(time.time() * 1000)

        if (
            data.composer.mask_type != 0
            and self.selected_mask_img is not None
            and self.timer_mask_last_update + 500 < mm_time
        ):
            # self.timer_mask_last_update = mm_time

            data.composer.inc_ants_position()
            self.update_canvas()
            # print("DEBUG: ants update: {}".format(mm_time))

        # Repeat timer
        self.timer_mask_update = self.ui.after(self.timer_mask_time_for_update, self.mask_update)

    def set_mask_type(self, type: int = 0):
        data.composer.mask_type = type
        # self.timer_mask_last_update = int(time.time() * 1000)

        data.composer.set_force_update_mask()
        self.update_canvas()
