# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from io import BytesIO
from tkinter import filedialog
from urllib.request import urlopen

import customtkinter as ctk
import data
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from ui import messagebox
from utils.translator import _

"""Stickers, frames and effects"""


class Decorations:
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
