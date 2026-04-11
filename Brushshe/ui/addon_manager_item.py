# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
from ui.tooltip import Tooltip
from utils.translator import _


class AddonManagerItem(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        author=None,
        version=None,
        description=None,
        delete_button_command=None,
        run_button_command=None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        super().pack(padx=10, pady=10, fill="x", expand=True)

        self._text_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._text_frame.pack(padx=10, pady=10, side="left")

        self._title_label = ctk.CTkLabel(self._text_frame, text=title, font=(None, 14, "bold"))
        self._title_label.pack(padx=5, side="left")

        if version:
            self._version_label = ctk.CTkLabel(self._text_frame, text=version)
            self._version_label.pack(padx=5, side="left")
        if author:
            self._author_label = ctk.CTkLabel(self._text_frame, text=f"{_('by')} {author}", font=(None, 14, "italic"))
            self._author_label.pack(padx=5, side="left")
        if description:
            self._title_label.configure(cursor="hand2")
            Tooltip(self._title_label, description)

        self._delete_button = ctk.CTkButton(
            self,
            text="X",
            width=30,
            fg_color="red",
            hover_color="#cc0000",
            text_color="white",
            command=delete_button_command,
        )
        self._delete_button.pack(padx=10, pady=10, side="right")
        Tooltip(self._delete_button, _("Uninstall add-on"))

        self._run_button = ctk.CTkButton(self, text=_("Run"), command=run_button_command)
        self._run_button.pack(padx=10, pady=10, side="right")
