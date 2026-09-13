# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import customtkinter as ctk
from constants import Constants
from PIL import Image
from ui.scroll import scroll
from utils.common import resource
from utils.translator import _


class Stickers:
    def open_stickers_toplevel(self):
        self.stickers_toplevel = ctk.CTkToplevel(self)
        self.stickers_toplevel.geometry("370x500")
        self.stickers_toplevel.title(_("Choose a sticker"))
        self.stickers_toplevel.wm_iconbitmap()
        self.stickers_toplevel.after(300, lambda: self.stickers_toplevel.iconphoto(False, self.iconpath))

        self.stickers_tabview = ctk.CTkTabview(self.stickers_toplevel, command=self.stickers_tabview_callback)
        self.stickers_tabview.add(_("From set"))
        self.stickers_tabview.add(_("From file"))
        self.stickers_tabview.add(_("From URL"))
        self.stickers_tabview.set(_("From set"))
        self.stickers_tabview.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        scrollable_frame = ctk.CTkScrollableFrame(self.stickers_tabview.tab(_("From set")))
        scrollable_frame.pack(fill=ctk.BOTH, expand=True)
        scroll(scrollable_frame)

        frame = ctk.CTkFrame(scrollable_frame)
        frame.pack()

        stickers = [Image.open(resource(f"assets/stickers/{name}.png")) for name in Constants.STICKERS_NAMES]
        row = 0
        column = 0
        for sticker_image in stickers:
            sticker_ctkimage = ctk.CTkImage(sticker_image, size=(100, 100))
            ctk.CTkButton(
                frame,
                text=None,
                image=sticker_ctkimage,
                command=lambda img=sticker_image: self.logic.set_current_sticker(img),
            ).grid(row=row, column=column, padx=10, pady=10)
            column += 1
            if column == 2:
                column = 0
                row += 1

    def stickers_tabview_callback(self):
        if self.stickers_tabview.get() == _("From file"):
            self.logic.sticker_from_file(self.stickers_toplevel)
        elif self.stickers_tabview.get() == _("From URL"):
            self.logic.sticker_from_url()
        self.stickers_tabview.set(_("From set"))
