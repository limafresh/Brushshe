# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
from ui.CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from ui.scroll import scroll
from utils.translator import _


class Gallery:
    def show_gallery(self):
        my_gallery = ctk.CTkToplevel()
        my_gallery.title(_("Brushshe Gallery"))
        my_gallery.geometry("650x580")

        menu = CTkMenuBar(my_gallery)
        gallery_menu = menu.add_cascade(_("My Gallery"))
        g_dropdown = CustomDropdownMenu(widget=gallery_menu)
        g_dropdown.add_option(option=_("Refresh"), command=self.logic.load_gallery_buttons)
        g_dropdown.add_option(option=_("Clear cache"), command=self.logic.clear_gallery_thumbs_cache)

        self.gallery_progressbar = ctk.CTkProgressBar(my_gallery, mode="intermediate")
        self.gallery_progressbar.pack(padx=10, pady=10, fill="x")

        self.gallery_scrollable_frame = ctk.CTkScrollableFrame(my_gallery)
        self.gallery_scrollable_frame.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        scroll(self.gallery_scrollable_frame)

        self.gallery_frame = ctk.CTkFrame(self.gallery_scrollable_frame)
        self.gallery_frame.pack(padx=10, pady=10)

        # Threads work bad with Tkinter event_loop.
        # Cache must be enough for normal work after first open gallery.
        # Thread(target=load_buttons, daemon=True).start()

        self.logic.load_gallery_buttons()
