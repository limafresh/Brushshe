# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os

import customtkinter as ctk
import data


class AddonManager:
    def load_installed_addons(self):
        files = os.listdir(data.addons_folder)

        for f in files:
            btn = ctk.CTkButton(self.ui.installed_addons_tab, text=f)
            btn.pack(padx=10, pady=10, fill="x")

    def load_addon_store(self):
        pass

    def install_addon(self):
        pass
