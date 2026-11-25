# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Callable

import customtkinter as ctk
from constants import Constants
from PIL import Image, ImageTk
from utils.common import resource
from utils.translator import _


class Frames(ctk.CTkToplevel):
    COLUMNS = 2

    def __init__(self, icon: ImageTk.PhotoImage, apply_frame: Callable):
        super().__init__()

        self.title(_("Frames"))
        self.wm_iconbitmap()
        self.after(300, lambda: self.iconphoto(False, icon))

        self._apply_frame = apply_frame

        self._frames = [Image.open(resource(f"assets/frames/{name}.png")) for name in Constants.FRAMES_NAMES]

        frames_thumbnails = [
            ctk.CTkImage(
                Image.open(resource(f"assets/frames_preview/{name}.png")),
                size=(100, 100),
            )
            for name in Constants.FRAMES_NAMES
        ]

        row = 0
        column = 0

        for i, image in enumerate(frames_thumbnails):
            ctk.CTkButton(self, text=None, image=image, command=lambda i=i: self._on_frame_click(i)).grid(
                column=column, row=row, padx=10, pady=10
            )
            column += 1
            if column == self.COLUMNS:
                column = 0
                row += 1

    def _on_frame_click(self, index: int):
        selected_frame = self._frames[index]
        self._apply_frame(selected_frame)
