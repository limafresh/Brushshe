# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import ast
import os
import shutil
from collections.abc import Callable
from tkinter import filedialog

import customtkinter as ctk
from constants import Constants
from ui.addon_manager_item import AddonManagerItem
from utils.common import resource
from utils.translator import _


class AddonManager(ctk.CTkToplevel):
    def __init__(self, icon, run_addon: Callable):
        super().__init__()
        self.title(_("Add-on Manager"))
        self.geometry("600x400")
        self.wm_iconbitmap()
        self.after(300, lambda: self.iconphoto(False, icon))

        self.run_addon = run_addon

        ctk.CTkButton(self, text=_("Install add-on from file"), command=self.install_addon).pack(
            padx=10, pady=10, fill="x"
        )

        self.installed_addons_frame = ctk.CTkScrollableFrame(self)
        self.installed_addons_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.load_installed_addons()

    def load_installed_addons(self):
        for widget in self.installed_addons_frame.winfo_children():
            widget.destroy()

        addons_number = self.load_addons_from_folder(resource("addons")) + self.load_addons_from_folder(
            Constants.ADDONS_FOLDER
        )

        self.installed_addons_frame.configure(label_text=f"{_('Installed add-ons')} ({addons_number})")

    def load_addons_from_folder(self, folder) -> int:
        files = os.listdir(folder)
        addons_number = 0

        for f in files:
            if f.endswith(".py"):
                addons_number += 1
                full_path = os.path.join(folder, f)
                metadata = self.get_addon_metadata(full_path)
                AddonManagerItem(
                    self.installed_addons_frame,
                    title=metadata.get("name", f),
                    author=metadata.get("author"),
                    version=metadata.get("version"),
                    description=metadata.get("description"),
                    run_button_command=lambda fp=full_path: self.run_addon(fp),
                )

        return addons_number

    def get_addon_metadata(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id == "metadata"
                            and isinstance(node.value, ast.Dict)
                        ):
                            metadata = {}
                            for key, value in zip(node.value.keys, node.value.values):
                                if isinstance(key, ast.Constant):
                                    k = key.value
                                    if isinstance(value, ast.Constant):
                                        v = value.value
                                        metadata[k] = v
                            return metadata
        except Exception as e:
            print(e)
        return {}

    def install_addon(self):
        addon_path = filedialog.askopenfilename(title=_("Open add-on"), filetypes=([("PY", "*.py")]))
        if addon_path:
            shutil.copy(addon_path, Constants.ADDONS_FOLDER)

        self.load_installed_addons()

    def uninstall_addon(self, path: str):
        os.remove(path)
        self.load_installed_addons()
