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
    def show_stickers_choice(self):
        self.sticker_choose = ctk.CTkToplevel(self)
        self.sticker_choose.geometry("370x500")
        self.sticker_choose.title(_("Choose a sticker"))
        self.sticker_choose.wm_iconbitmap()
        self.sticker_choose.after(300, lambda: self.sticker_choose.iconphoto(False, self.iconpath))

        self.stickers_tabview = ctk.CTkTabview(self.sticker_choose, command=self.stickers_tabview_callback)
        self.stickers_tabview.add(_("From set"))
        self.stickers_tabview.add(_("From file"))
        self.stickers_tabview.add(_("From URL"))
        self.stickers_tabview.set(_("From set"))
        self.stickers_tabview.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        stickers_scrollable_frame = ctk.CTkScrollableFrame(self.stickers_tabview.tab(_("From set")))
        stickers_scrollable_frame.pack(fill=ctk.BOTH, expand=True)
        scroll(stickers_scrollable_frame)

        stickers_frame = ctk.CTkFrame(stickers_scrollable_frame)
        stickers_frame.pack()

        stickers = [Image.open(resource(f"assets/stickers/{name}.png")) for name in Constants.STICKERS_NAMES]
        row = 0
        column = 0
        for sticker_image in stickers:
            sticker_ctkimage = ctk.CTkImage(sticker_image, size=(100, 100))
            ctk.CTkButton(
                stickers_frame,
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
            self.logic.sticker_from_file(self.sticker_choose)
        elif self.stickers_tabview.get() == _("From URL"):
            self.logic.sticker_from_url()
        self.stickers_tabview.set(_("From set"))
