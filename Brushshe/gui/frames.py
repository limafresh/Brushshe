# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import customtkinter as ctk
from constants import Constants
from PIL import Image
from utils.common import resource
from utils.translator import _


class Frames:
    def open_frames_toplevel(self):
        toplevel = ctk.CTkToplevel(self)
        toplevel.title(_("Frames"))
        toplevel.wm_iconbitmap()
        toplevel.after(300, lambda: toplevel.iconphoto(False, self.iconpath))

        self.frames = [Image.open(resource(f"assets/frames/{name}.png")) for name in Constants.FRAMES_NAMES]
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
            ctk.CTkButton(toplevel, text=None, image=image, command=lambda i=i: self.on_frames_click(i)).grid(
                column=column, row=row, padx=10, pady=10
            )
            column += 1
            if column == 2:
                column = 0
                row += 1

    def on_frames_click(self, index):
        selected_frame = self.frames[index]
        resized_frame = selected_frame.resize((self.logic.image.width, self.logic.image.height))

        self.logic.image.paste(resized_frame, (0, 0), resized_frame)

        self.logic.update_canvas()
        self.logic.record_action()
