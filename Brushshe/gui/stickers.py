# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import customtkinter as ctk
from constants import Constants
from PIL import Image
from ui.scroll import scroll
from utils.resource import resource
from utils.translator import _


class Stickers:
    def show_stickers_choice(self):
        def tabview_callback():
            if tabview.get() == _("From file"):
                self.logic.sticker_from_file(sticker_choose)
            elif tabview.get() == _("From URL"):
                self.logic.sticker_from_url()
            tabview.set(_("From set"))

        sticker_choose = ctk.CTkToplevel(self)
        sticker_choose.geometry("370x500")
        sticker_choose.title(_("Choose a sticker"))
        sticker_choose.wm_iconbitmap()
        sticker_choose.after(300, lambda: sticker_choose.iconphoto(False, self.iconpath))

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
