# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
from utils.translator import _


class AddonManager:
    def open_addon_manager(self):
        addon_manager = ctk.CTkToplevel(self)
        addon_manager.title(_("Add-on Manager"))
        addon_manager.geometry("600x400")
        addon_manager.wm_iconbitmap()
        addon_manager.after(300, lambda: addon_manager.iconphoto(False, self.iconpath))

        tabview = ctk.CTkTabview(addon_manager)
        installed_addons_tab = tabview.add(_("Installed add-ons"))
        tabview.add(_("Add-on Store"))
        tabview.pack(padx=10, pady=10, fill="both", expand=True)

        ctk.CTkButton(installed_addons_tab, text=_("Install add-on from file"), command=self.logic.install_addon).pack(
            padx=10, pady=10, fill="x"
        )

        self.installed_addons_frame = ctk.CTkScrollableFrame(installed_addons_tab)
        self.installed_addons_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.logic.load_installed_addons()
        self.logic.load_addon_store()
