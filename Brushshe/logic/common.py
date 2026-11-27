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
from constants import Constants
from core.bhbrush import bh_draw_line
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageGrab, ImageOps, ImageStat, ImageTk
from ui import messagebox
from ui.color_picker import AskColor
from utils import common
from utils.config_loader import config_file_path
from utils.translator import _

from logic.edit_tools import EditTools
from logic.paint_tools import PaintTools
from logic.selection import Selection
from logic.shapes import Shapes

from . import state


class Common:
    def init_tools(self):
        self.paint_tools = PaintTools(
            self.ui.canvas,
            self.set_tool,
            self.canvas_to_pict_xy,
            self.draw_line,
            self.update_canvas,
            self.record_action,
        )
        self.shapes = Shapes(
            self.ui.canvas,
            self.set_tool,
            self.canvas_to_pict_xy,
            self.get_contrast_color,
            self.get_tool_main_color,
            self.update_canvas,
            self.record_action,
        )
        self.edit_tools = EditTools(
            self.ui.canvas,
            self.set_tool,
            self.canvas_to_pict_xy,
            self.update_canvas,
            self.record_action,
            self.crop_picture,
        )
        self.selection = Selection(
            self.ui.canvas, self.set_tool, self.canvas_to_pict_xy, self.update_canvas, self.composer
        )

    def brush(self):
        self.paint_tools.brush()

    def eraser(self):
        self.paint_tools.brush(type="eraser")

    def start_fill(self):
        self.paint_tools.fill()

    def recoloring_brush(self):
        self.paint_tools.recoloring_brush()

    def spray(self):
        self.paint_tools.spray()

    def text_tool(self):
        self.paint_tools.text()

    def create_shape(self, shape):
        self.shapes.create_shape(shape)

    def bezier_shape(self):
        self.shapes.bezier()

    def copy_tool(self, deleted=False):
        self.edit_tools.copy(deleted)

    def start_insert(self):
        self.edit_tools.insert()

    def insert_simple(self, insert_image=None):
        self.edit_tools.insert_simple(insert_image)

    def crop_simple(self):
        self.edit_tools.crop_simple()

    def select_by_shape(self, shape):
        self.selection.select_by_shape(shape)

    def select_by_polygon(self):
        self.selection.select_by_polygon()

    def select_by_color(self, fill_limit):
        self.selection.select_by_color(fill_limit)

    def select_all_mask(self):
        self.selection.select_all()

    def remove_mask(self):
        self.selection.deselect_all()

    def set_left_toolbar(self, need_choose_file):
        self.panels.set_left_toolbar(need_choose_file)

    def import_palette(self, palette_path):
        self.panels.import_palette(palette_path)

    def export_palette(self):
        self.panels.export_palette()

    # Keybinding without locale.
    def key_handler(self, event):
        if state.current_tool != "text":
            # Do not use with origin .bind() for equivalent key binds. Only or that, or this.

            # Debug
            # print(event.char, event.keycode, event.state)

            shift = bool(event.state & 1)
            ctrl = bool(event.state & 4)
            alt_l = bool(event.state & 8)
            alt_r = bool(event.state & 128)
            alt = bool(alt_l or alt_r)
            # All else modifiers was ignored.

            if shift is False and ctrl is False and alt is False and event.keycode == 53:  # Key-x
                self.flip_brush_colors()

            if shift is False and ctrl is False and alt is False and event.keycode == 56:  # Key-b
                self.brush()

            if shift is False and ctrl is False and alt is False and event.keycode == 26:  # Key-e
                self.eraser()

    def when_closing(self):
        if (
            self.saved_copy.mode != state.image.mode
            or self.saved_copy.size != state.image.size
            or ImageChops.difference(self.saved_copy, state.image).getbbox()
        ):
            msg = messagebox.leave_brushshe(self.ui)
            if msg.get() == _("Save"):
                self.save_current()
            elif msg.get() == _("Yes"):
                self.destroy_app()
        else:
            self.destroy_app()

    def destroy_app(self):
        if self.is_reset_settings_after_exiting.get():
            os.remove(config_file_path)
        self.ui.destroy()

    def get_tool_main_color(self):
        if state.current_tool == "eraser":
            color = state.bg_color
            if state.image.mode == "RGBA":
                color = "#00000000"
        else:
            # For shape, etc.
            color = state.brush_color
            if state.image.mode == "RGBA":
                color = common.rgb_tuple_to_rgba_tuple(self.rgb_color_to_tuple(color), 255)
        return color

    def record_action(self):
        self.undo_stack.append(state.image.copy())
        if self.autosave_var.get() and self.current_file is not None:
            self.save_current(autosave=True)

    def draw_line(self, x1, y1, x2, y2):
        color = self.get_tool_main_color()

        if state.selected_mask_img is None:
            bh_draw_line(state.draw, x1, y1, x2, y2, color, state.tool_size, state.brush_shape, state.current_tool)
        else:
            tmp_image = state.image.copy()
            tmp_draw = ImageDraw.Draw(tmp_image)
            bh_draw_line(tmp_draw, x1, y1, x2, y2, color, state.tool_size, state.brush_shape, state.current_tool)
            state.image.paste(tmp_image, (0, 0), state.selected_mask_img)
            del tmp_image

    def crop_picture(self, x1, y1, x2, y2, event=None):
        new_width = x2 - x1
        new_height = y2 - y1

        if state.image.mode == "RGBA":
            new_image = Image.new("RGBA", (new_width, new_height), "#00000000")
            new_image.paste(state.image, (-x1, -y1), state.image)
        else:
            new_image = Image.new("RGB", (new_width, new_height), state.bg_color)
            new_image.paste(state.image, (-x1, -y1))
        state.image = new_image
        state.draw = ImageDraw.Draw(state.image)

        state.selected_mask_img = None

        self.force_resize_canvas()
        self.update_canvas()

        self.record_action()

    def scale_picture(self, new_width, new_height):
        scaled_image = state.image.resize((new_width, new_height), Image.NEAREST)
        state.image = scaled_image
        self.picture_postconfigure()

    def eyedropper(self, event):
        # Get the coordinates of the click event
        x, y = self.canvas_to_pict_xy(event.x, event.y)

        color = state.image.getpixel((x, y))
        if isinstance(color, tuple):
            color = color[:3]
        self.obtained_color = "#{:02x}{:02x}{:02x}".format(*color)

        state.brush_color = self.obtained_color
        self.ui.brush_palette.main_color = self.obtained_color

    def open_from_file(self):
        file_path = filedialog.askopenfilename(title=_("Open from file"), filetypes=Constants.OPEN_IMG_FILETYPES)
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
        if self.current_file is not None:
            try:
                state.image.save(self.current_file)
                self.saved_copy = state.image.copy()
                if not autosave:
                    messagebox.save_current()
            except Exception as e:
                messagebox.save_file_error(e)
        else:
            self.save_as()

    def save_as(self):
        file_path = filedialog.asksaveasfilename(
            title=_("Save to device"), filetypes=Constants.SAVE_IMG_FILETYPES, defaultextension=".png"
        )
        if file_path:
            try:
                state.image.save(file_path)
                self.saved_copy = state.image.copy()
                messagebox.save_as(Path(file_path).suffix)
                self.current_file = file_path
                self.ui.title(os.path.basename(self.current_file) + " - " + _("Brushshe"))
            except Exception as e:
                messagebox.save_file_error(e)

    def other_bg_color(self):
        askcolor = AskColor(title=_("Choose a different background color"), initial_color="#ffffff")
        obtained_bg_color = askcolor.get()
        if obtained_bg_color:
            self.new_picture(obtained_bg_color)

    def new_picture(self, color="#FFFFFF", mode="RGB", first_time=False):
        self.ui.canvas.delete("tools")
        state.bg_color = color

        state.image = Image.new(mode, (640, 480), color)
        self.saved_copy = state.image.copy()
        state.draw = ImageDraw.Draw(state.image)
        self.ui.canvas.xview_moveto(0)
        self.ui.canvas.yview_moveto(0)

        if first_time:
            self.img_tk = ImageTk.PhotoImage(state.image)
            self.canvas_image = self.ui.canvas.create_image(0, 0, anchor=ctk.NW, image=self.img_tk)
        else:
            pass

        state.selected_mask_img = None

        self.force_resize_canvas()
        self.update_canvas()

        self.record_action()
        self.ui.title(_("Unnamed") + " - " + _("Brushshe"))
        self.current_file = None

    # TODO: Add selected_mask_img on history with type `mask`.
    # FIXME: Need add length synchronization undo_stack and redo_stack (actually it must be one stack).
    def undo(self):
        if len(self.undo_stack) > 1:
            tmp_image = self.undo_stack.pop()
            self.redo_stack.append(tmp_image)
            state.image = self.undo_stack[-1].copy()
            state.draw = ImageDraw.Draw(state.image)
            if state.image.width != tmp_image.width or state.image.height != tmp_image.height:
                state.selected_mask_img = None
                self.force_resize_canvas()
            self.update_canvas()

    def redo(self):
        if len(self.redo_stack) > 0:
            tmp_image = self.redo_stack.pop().copy()
            is_resize = False
            if state.image.width != tmp_image.width or state.image.height != tmp_image.height:
                is_resize = True
            state.image = tmp_image
            self.record_action()
            state.draw = ImageDraw.Draw(state.image)
            if is_resize:
                state.selected_mask_img = None
                self.force_resize_canvas()
            self.update_canvas()

    def save_to_gallery(self):
        file_path = Constants.GALLERY_FOLDER / f"{uuid4()}.png"
        while file_path.exists():
            file_path = Constants.GALLERY_FOLDER / f"{uuid4()}.png"
        state.image.save(file_path)
        self.saved_copy = state.image.copy()

        self.current_file = str(file_path)
        self.ui.title(os.path.basename(self.current_file) + " - " + _("Brushshe"))

        messagebox.save_to_gallery()

    def change_color(self, new_color):
        state.brush_color = new_color
        self.ui.brush_palette.main_color = state.brush_color

    def main_color_choice(self):
        askcolor = AskColor(title=_("Color select"), initial_color=state.brush_color)
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            self.change_color(self.obtained_color)

    def second_color_choice(self):
        askcolor = AskColor(title=_("Color select"), initial_color=state.second_brush_color)
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            state.second_brush_color = self.obtained_color
            self.ui.brush_palette.second_color = self.obtained_color

    def color_choice_btn(self, event, btn, index):
        askcolor = AskColor(title=_("Color select"), initial_color=btn.cget("fg_color"))
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            btn.configure(
                fg_color=self.obtained_color,
                hover_color=self.obtained_color,
                command=lambda c=self.obtained_color: self.change_color(c),
            )
            self.change_color(self.obtained_color)
            self.palette[index] = self.obtained_color

    def flip_brush_colors(self):
        state.brush_color = self.ui.brush_palette.second_color
        state.second_brush_color = self.ui.brush_palette.main_color

        self.ui.brush_palette.main_color = state.brush_color
        self.ui.brush_palette.second_color = state.second_brush_color

    def open_image(self, openimage):
        try:
            state.bg_color = "white"
            state.image = Image.open(openimage)
            self.saved_copy = state.image.copy()
            self.picture_postconfigure()

            state.selected_mask_img = None

            if not isinstance(openimage, BytesIO):
                self.current_file = openimage
                self.ui.title(os.path.basename(self.current_file) + " - " + _("Brushshe"))
            else:
                self.ui.title(_("Unnamed") + " - " + _("Brushshe"))
                self.current_file = None
        except Exception as e:
            messagebox.open_file_error(e)

    def rotate(self, degree):
        rotated_image = state.image.rotate(degree, expand=True)
        state.image = rotated_image
        self.picture_postconfigure()

    def remove_white_background(self):
        transparent_bg_img = state.image.convert("RGBA")
        datas = transparent_bg_img.getdata()

        new_data = []
        for item in datas:
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                new_data.append((0, 0, 0, 0))  # Lines with zeroes compressed better.
            else:
                new_data.append(item)

        transparent_bg_img.putdata(new_data)
        state.image = transparent_bg_img
        self.picture_postconfigure()

    def replace_picture(self, image):
        state.image = image
        self.picture_postconfigure()

    def picture_postconfigure(self):
        self.ui.canvas.delete("tools")

        state.draw = ImageDraw.Draw(state.image)

        self.ui.canvas.xview_moveto(0)
        self.ui.canvas.yview_moveto(0)

        self.force_resize_canvas()
        self.update_canvas()

        self.record_action()

    def brush_shape_btn_callback(self, value):
        if value == "●":
            state.brush_shape = "circle"
        elif value == "■":
            state.brush_shape = "square"

    def paste_image_from_clipboard(self):
        try:
            pasted_img = ImageGrab.grabclipboard()
            state.bg_color = "white"
            state.image = pasted_img
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

    def get_contrast_color(self) -> str:
        stat = ImageStat.Stat(state.image)
        r, g, b = stat.mean[:3]
        contrast_color = "#232323" if (r + g + b) / 3 > 127 else "#e8e8e8"

        return contrast_color

    def set_current_sticker(self, sticker_image=None):  # Choose a sticker
        if sticker_image:
            self.last_sticker_image = sticker_image

        if not self.is_sticker_use_real_size.get():
            self.set_tool("sticker", _("Stickers"), Constants().STICKER_SIZE, 10, 250, "cross")
            self.insert_simple(self.last_sticker_image)
        else:
            self.set_tool("real size sticker", _("Stickers"), 100, 1, 500, "cross")
            self.insert_simple(self.last_sticker_image)

    def apply_frame(self, frame):
        resized_frame = frame.resize((state.image.width, state.image.height))
        state.image.paste(resized_frame, (0, 0), resized_frame)
        self.update_canvas()
        self.record_action()

    def effects(self):
        self.set_tool("effects", _("Effects"), 10, 1, 20, "circle")

    def apply_effect(self):
        effect_value = self.effects_optionmenu.get()

        if effect_value == _("Blur"):
            result = state.image.copy().filter(ImageFilter.GaussianBlur(radius=state.tool_size))
        elif effect_value == _("Detail"):
            result = ImageEnhance.Sharpness(state.image.copy()).enhance(state.tool_size)
        elif effect_value == _("Contour"):
            result = state.image.copy().filter(ImageFilter.CONTOUR)
        elif effect_value == _("Grayscale"):
            result = ImageOps.grayscale(state.image.copy())
        elif effect_value == _("Mirror"):
            result = ImageOps.mirror(state.image.copy())
        elif effect_value == _("Metal"):
            result = state.image.copy().filter(ImageFilter.EMBOSS)
        elif effect_value == _("Inversion"):
            result = ImageOps.invert(state.image.copy())
        elif effect_value == _("Brightness"):
            result = ImageEnhance.Brightness(state.image.copy()).enhance(state.tool_size / 10)
        elif effect_value == _("Contrast"):
            result = ImageEnhance.Contrast(state.image.copy()).enhance(state.tool_size / 10)

        self.effects_post_actions(result)

    def effects_post_actions(self, result):
        if state.selected_mask_img is None:
            state.image = result
            state.draw = ImageDraw.Draw(state.image)
        else:
            state.image.paste(result, (0, 0), state.selected_mask_img)

        self.update_canvas()
        self.record_action()
