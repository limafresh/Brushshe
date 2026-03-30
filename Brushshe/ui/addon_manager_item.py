# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
from ui.tooltip import Tooltip
from utils.translator import _


class AddonManagerItem(ctk.CTkFrame):
    def __init__(self, master, title: str, delete_button_command=None, run_button_command=None, **kwargs):
        super().__init__(master, **kwargs)
        super().pack(padx=10, pady=10, fill="x", expand=True)

        self._text_frame = ctk.CTkFrame(self)
        self._text_frame.pack(side="left")

        self._label = ctk.CTkLabel(self._text_frame, text=title)
        self._label.pack(padx=10, pady=10)

        self._delete_button = ctk.CTkButton(
            self, text="X", width=30, fg_color="red", hover_color="#cc0000", command=delete_button_command
        )
        self._delete_button.pack(padx=10, pady=10, side="right")
        Tooltip(self._delete_button, _("Uninstall add-on"))

        self._run_button = ctk.CTkButton(self, text=_("Run"), command=run_button_command)
        self._run_button.pack(padx=10, pady=10, side="right")
