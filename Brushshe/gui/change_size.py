# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
from PIL import Image
from ui import messagebox
from ui.spinbox import IntSpinbox
from utils.translator import _


class ChangeSize:
    def open_change_size_toplevel(self):
        toplevel = ctk.CTkToplevel(self)
        toplevel.title(_("Change size..."))
        toplevel.wm_iconbitmap()
        toplevel.after(300, lambda: toplevel.iconphoto(False, self.iconpath))
        toplevel.transient(self)

        size_sb = ctk.CTkSegmentedButton(toplevel, values=[_("Crop"), _("Scale")], command=self.size_sb_callback)
        size_sb.pack(padx=10, pady=10)
        size_sb.set(_("Crop"))

        width_height_frame = ctk.CTkFrame(toplevel)
        width_height_frame.pack(padx=10, pady=10)

        ctk.CTkLabel(width_height_frame, text=_("Width")).grid(row=1, column=1, padx=10, pady=10)
        self.width_spinbox = IntSpinbox(width_height_frame, width=150)
        self.width_spinbox.grid(row=2, column=1, padx=10, pady=10)
        self.width_spinbox.set(self.logic.image.width)

        ctk.CTkLabel(width_height_frame, text=_("Height")).grid(row=1, column=2, padx=10, pady=10)
        self.height_spinbox = IntSpinbox(width_height_frame, width=150)
        self.height_spinbox.grid(row=2, column=2, padx=10, pady=10)
        self.height_spinbox.set(self.logic.image.height)

        self.aspect_ratio_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            toplevel,
            text=_("Maintain aspect ratio"),
            variable=self.aspect_ratio_var,
        ).pack(padx=10, pady=10)

        self.ready_size_button = ctk.CTkButton(toplevel, text="OK", command=self.crop)
        self.ready_size_button.pack(padx=10, pady=10)

    def size_sb_callback(self, value):
        if value == _("Crop"):
            self.ready_size_button.configure(command=self.crop)
        elif value == _("Scale"):
            self.ready_size_button.configure(command=self.scale)
        else:
            print("Oops")

    def crop(self):
        try:
            new_width = int(self.width_spinbox.get())
            new_height = self.get_new_height()

            if not self.continue_if_big_size(new_width, new_height):
                return

            self.logic.crop_picture(0, 0, new_width, new_height)
        except Exception as e:
            print(e)

    def scale(self):
        try:
            new_width = int(self.width_spinbox.get())
            new_height = self.get_new_height()

            if not self.continue_if_big_size(new_width, new_height):
                return

            scaled_image = self.logic.image.resize((new_width, new_height), Image.NEAREST)
            self.logic.image = scaled_image
            self.logic.picture_postconfigure()
        except Exception as e:
            print(e)

    def get_new_height(self) -> int:
        if self.aspect_ratio_var.get():
            new_height = int(self.logic.image.height * self.width_spinbox.get() / self.logic.image.width)
        else:
            new_height = int(self.height_spinbox.get())

        return new_height

    def continue_if_big_size(self, new_width: int, new_height: int) -> bool:
        if new_width > 2000 or new_height > 2000:
            msg = messagebox.continue_big_size()
            if msg.get() != _("Yes"):
                return False

        return True
