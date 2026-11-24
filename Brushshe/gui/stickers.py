# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Callable
from io import BytesIO
from tkinter import filedialog
from urllib.request import urlopen

import customtkinter as ctk
from constants import Constants
from PIL import Image, ImageTk
from ui import messagebox
from ui.scroll import scroll
from utils.common import resource
from utils.translator import _


class Stickers(ctk.CTkToplevel):
    def __init__(self, icon: ImageTk.PhotoImage, set_current_sticker: Callable):
        super().__init__()

        self.geometry("370x500")
        self.title(_("Choose a sticker"))
        self.wm_iconbitmap()
        self.after(300, lambda: self.iconphoto(False, icon))

        self._set_current_sticker = set_current_sticker

        self._tabview = ctk.CTkTabview(self, command=self._tabview_callback)
        self._tabview.add(_("From set"))
        self._tabview.add(_("From file"))
        self._tabview.add(_("From URL"))
        self._tabview.set(_("From set"))
        self._tabview.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        scrollable_frame = ctk.CTkScrollableFrame(self._tabview.tab(_("From set")))
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
                command=lambda img=sticker_image: self._set_current_sticker(img),
            ).grid(row=row, column=column, padx=10, pady=10)
            column += 1
            if column == 2:
                column = 0
                row += 1

    def _tabview_callback(self):
        if self._tabview.get() == _("From file"):
            self._sticker_from_file()
        elif self._tabview.get() == _("From URL"):
            self._sticker_from_url()
        self._tabview.set(_("From set"))

    def _sticker_from_file(self):
        file_path = filedialog.askopenfilename(title=_("Sticker from file"), filetypes=Constants.OPEN_IMG_FILETYPES)
        if file_path:
            try:
                sticker_image = Image.open(file_path)
                self._set_current_sticker(sticker_image)
            except Exception as e:
                messagebox.open_file_error(e)

    def _sticker_from_url(self):
        dialog = ctk.CTkInputDialog(text=_("Enter URL:"), title=_("Open from URL"))
        image_url = dialog.get_input()

        if image_url is not None:
            try:
                with urlopen(image_url) as response:
                    image_data = BytesIO(response.read())
                    sticker_image = Image.open(image_data)
                    self._set_current_sticker(sticker_image)
            except Exception as e:
                messagebox.open_file_error(e)
