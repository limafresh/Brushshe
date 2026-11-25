# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Callable

import customtkinter as ctk
from PIL import Image, ImageTk
from ui import messagebox
from ui.spinbox import IntSpinbox
from utils.translator import _


class ChangeSizeDialog(ctk.CTkToplevel):
    MAX_IMAGE_WIDTH = 2000
    MAX_IMAGE_HEIGHT = 2000

    def __init__(
        self, master, icon: ImageTk.PhotoImage, image: Image, crop_function: Callable, scale_function: Callable
    ):
        super().__init__(master)

        self.title(_("Change size..."))
        self.wm_iconbitmap()
        self.after(300, lambda: self.iconphoto(False, icon))
        self.transient(master)

        self._image = image
        self._crop_function = crop_function
        self._scale_function = scale_function

        segmented_button = ctk.CTkSegmentedButton(
            self, values=[_("Crop"), _("Scale")], command=self._segmented_button_callback
        )
        segmented_button.pack(padx=10, pady=10)
        segmented_button.set(_("Crop"))

        dimensions_frame = ctk.CTkFrame(self)
        dimensions_frame.pack(padx=10, pady=10)

        ctk.CTkLabel(dimensions_frame, text=_("Width")).grid(row=1, column=1, padx=10, pady=10)

        self._width_spinbox = IntSpinbox(dimensions_frame, width=150)
        self._width_spinbox.grid(row=2, column=1, padx=10, pady=10)
        self._width_spinbox.set(self._image.width)

        ctk.CTkLabel(dimensions_frame, text=_("Height")).grid(row=1, column=2, padx=10, pady=10)

        self._height_spinbox = IntSpinbox(dimensions_frame, width=150)
        self._height_spinbox.grid(row=2, column=2, padx=10, pady=10)
        self._height_spinbox.set(self._image.height)

        self._aspect_ratio_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(
            self,
            text=_("Maintain aspect ratio"),
            variable=self._aspect_ratio_var,
        ).pack(padx=10, pady=10)

        self._ok_button = ctk.CTkButton(self, text="OK", command=self._crop)
        self._ok_button.pack(padx=10, pady=10)

    def _segmented_button_callback(self, value):
        if value == _("Crop"):
            self._ok_button.configure(command=self._crop)
        elif value == _("Scale"):
            self._ok_button.configure(command=self._scale)
        else:
            print("Oops")

    def _crop(self):
        try:
            new_width = int(self._width_spinbox.get())
            new_height = self._get_new_height()

            if not self._continue_if_big_size(new_width, new_height):
                return

            self._crop_function(0, 0, new_width, new_height)
        except Exception as e:
            print(e)

    def _scale(self):
        try:
            new_width = int(self._width_spinbox.get())
            new_height = self._get_new_height()

            if not self._continue_if_big_size(new_width, new_height):
                return

            self._scale_function(new_width, new_height)
        except Exception as e:
            print(e)

    def _get_new_height(self) -> int:
        if self._aspect_ratio_var.get():
            new_height = int(self._image.height * self._width_spinbox.get() / self._image.width)
        else:
            new_height = int(self._height_spinbox.get())

        return new_height

    def _continue_if_big_size(self, new_width: int, new_height: int) -> bool:
        if new_width > self.MAX_IMAGE_WIDTH or new_height > self.MAX_IMAGE_HEIGHT:
            msg = messagebox.continue_big_size()
            if msg.get() != _("Yes"):
                return False

        return True
