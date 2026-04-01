# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import customtkinter as ctk
import data
from utils.translator import _


class Frames:
    def show_frame_choice(self):
        def on_frames_click(index):
            selected_frame = data.frames[index]
            resized_frame = selected_frame.resize((self.logic.image.width, self.logic.image.height))

            self.logic.image.paste(resized_frame, (0, 0), resized_frame)

            self.logic.update_canvas()
            self.logic.record_action()

        frames_win = ctk.CTkToplevel(self)
        frames_win.title(_("Frames"))
        frames_win.wm_iconbitmap()
        frames_win.after(300, lambda: frames_win.iconphoto(False, self.iconpath))

        row = 0
        column = 0

        for i, image in enumerate(data.frames_thumbnails):
            ctk.CTkButton(frames_win, text=None, image=image, command=lambda i=i: on_frames_click(i)).grid(
                column=column, row=row, padx=10, pady=10
            )
            column += 1
            if column == 2:
                column = 0
                row += 1
