# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import customtkinter as ctk
from PIL import Image
from ui import messagebox
from ui.spinbox import IntSpinbox
from utils.translator import _


class ChangeSize:
    def change_size(self):
        def size_sb_callback(value):
            if value == _("Crop"):
                ready_size_button.configure(command=crop)
            elif value == _("Scale"):
                ready_size_button.configure(command=scale)
            else:
                print("Oops")

        def crop():
            try:
                if aspect_ratio_var.get() == "on":
                    new_height = int(self.logic.image.height * width_spinbox.get() / self.logic.image.width)
                else:
                    new_height = int(height_spinbox.get())

                if int(width_spinbox.get()) > 2000 or new_height > 2000:
                    msg = messagebox.continue_big_size()
                    if msg.get() == _("Yes"):
                        self.logic.crop_picture(0, 0, int(width_spinbox.get()), new_height)
                else:
                    self.logic.crop_picture(0, 0, int(width_spinbox.get()), new_height)
            except Exception as e:
                print(e)

        def scale():
            try:
                if aspect_ratio_var.get() == "on":
                    new_height = int(self.logic.image.height * width_spinbox.get() / self.logic.image.width)
                else:
                    new_height = int(height_spinbox.get())

                if int(width_spinbox.get()) > 2000 or new_height > 2000:
                    msg = messagebox.continue_big_size()
                    if msg.get() == _("Yes"):
                        scaled_image = self.logic.image.resize((int(width_spinbox.get()), new_height), Image.NEAREST)
                        self.logic.image = scaled_image
                        self.logic.picture_postconfigure()
                else:
                    scaled_image = self.logic.image.resize((int(width_spinbox.get()), new_height), Image.NEAREST)
                    self.logic.image = scaled_image
                    self.logic.picture_postconfigure()
            except Exception as e:
                print(e)

        change_size_toplevel = ctk.CTkToplevel(self)
        change_size_toplevel.title(_("Change size..."))
        change_size_toplevel.wm_iconbitmap()
        change_size_toplevel.after(300, lambda: change_size_toplevel.iconphoto(False, self.iconpath))
        change_size_toplevel.transient(self)

        size_sb = ctk.CTkSegmentedButton(change_size_toplevel, values=[_("Crop"), _("Scale")], command=size_sb_callback)
        size_sb.pack(padx=10, pady=10)
        size_sb.set(_("Crop"))

        width_height_frame = ctk.CTkFrame(change_size_toplevel)
        width_height_frame.pack(padx=10, pady=10)

        ctk.CTkLabel(width_height_frame, text=_("Width")).grid(row=1, column=1, padx=10, pady=10)
        width_spinbox = IntSpinbox(width_height_frame, width=150)
        width_spinbox.grid(row=2, column=1, padx=10, pady=10)
        width_spinbox.set(self.logic.image.width)

        ctk.CTkLabel(width_height_frame, text=_("Height")).grid(row=1, column=2, padx=10, pady=10)
        height_spinbox = IntSpinbox(width_height_frame, width=150)
        height_spinbox.grid(row=2, column=2, padx=10, pady=10)
        height_spinbox.set(self.logic.image.height)

        aspect_ratio_var = ctk.StringVar(value="on")
        ctk.CTkCheckBox(
            change_size_toplevel,
            text=_("Maintain aspect ratio"),
            variable=aspect_ratio_var,
            onvalue="on",
            offvalue="off",
        ).pack(padx=10, pady=10)

        ready_size_button = ctk.CTkButton(change_size_toplevel, text="OK", command=crop)
        ready_size_button.pack(padx=10, pady=10)
