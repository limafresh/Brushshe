# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math
import os
from io import BytesIO
from pathlib import Path
from tkinter import filedialog
from urllib.request import urlopen
from uuid import uuid4

import customtkinter as ctk
import data
from core.bhbrush import bh_draw_line
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageGrab, ImageOps, ImageStat, ImageTk
from ui import messagebox
from ui.color_picker import AskColor
from utils import colors
from utils.config_loader import config_file_path
from utils.translator import _


class Common:
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

    def get_tool_main_color(self):
        if self.current_tool == "eraser":
            color = data.bg_color
            if self.image.mode == "RGBA":
                color = "#00000000"
        else:
            # For shape, etc.
            color = data.brush_color
            if self.image.mode == "RGBA":
                color = colors.rgb_tuple_to_rgba_tuple(self.rgb_color_to_tuple(color), 255)
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

    def open_from_file(self):
        file_path = filedialog.askopenfilename(title=_("Open from file"), filetypes=data.open_img_filetypes)
        if file_path:
            self.open_image(file_path)

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
        file_path = filedialog.asksaveasfilename(title=_("Save to device"), filetypes=data.save_img_filetypes)
        if file_path:
            try:
                self.image.save(file_path)
                self.saved_copy = self.image.copy()
                messagebox.save_as(Path(file_path).suffix)
                data.current_file = file_path
                self.ui.title(os.path.basename(data.current_file) + " - " + _("Brushshe"))
            except Exception as e:
                messagebox.save_file_error(e)

    def other_bg_color(self):
        askcolor = AskColor(title=_("Choose a different background color"), initial_color="#ffffff")
        obtained_bg_color = askcolor.get()
        if obtained_bg_color:
            self.new_picture(obtained_bg_color)

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
        file_path = data.gallery_folder / f"{uuid4()}.png"
        while file_path.exists():
            file_path = data.gallery_folder / f"{uuid4()}.png"
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
            self.change_color(self.obtained_color)

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
            self.change_color(self.obtained_color)

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

    def rotate(self, degree):
        rotated_image = self.image.rotate(degree, expand=True)
        self.image = rotated_image
        self.picture_postconfigure()

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
            rgb = self.ui.winfo_rgb(color)
            r = math.floor(rgb[0] / 256)
            g = math.floor(rgb[1] / 256)
            b = math.floor(rgb[2] / 256)
        except Exception:
            return (0, 0, 0)
        return (r, g, b)

    def get_contrast_color(self):
        stat = ImageStat.Stat(self.image)
        r, g, b = stat.mean[:3]
        self.contrast_color = "#232323" if (r + g + b) / 3 > 127 else "#e8e8e8"

    def sticker_from_file(self, parent):
        file_path = filedialog.askopenfilename(title=_("Sticker from file"), filetypes=data.open_img_filetypes)
        if file_path:
            try:
                sticker_image = Image.open(file_path)
                self.set_current_sticker(sticker_image)
            except Exception as e:
                messagebox.open_file_error(e)

    def sticker_from_url(self):
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

    def set_current_sticker(self, sticker_image=None):  # Choose a sticker
        if sticker_image:
            self.last_sticker_image = sticker_image

        if data.is_sticker_use_real_size.get() == "off":
            self.set_tool("sticker", "Stickers", data.sticker_size, 10, 250, "cross")
            self.insert_simple(self.last_sticker_image)
        else:
            self.set_tool("real size sticker", "Stickers", 100, 1, 500, "cross")
            self.insert_simple(self.last_sticker_image)

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
