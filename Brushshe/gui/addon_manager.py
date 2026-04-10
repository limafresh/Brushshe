# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import shutil
import ast
from tkinter import filedialog

import customtkinter as ctk
from constants import Constants
from ui.addon_manager_item import AddonManagerItem
from utils.translator import _


class AddonManager:
    def open_addon_manager(self):
        addon_manager = ctk.CTkToplevel(self)
        addon_manager.title(_("Add-on Manager"))
        addon_manager.geometry("600x400")
        addon_manager.wm_iconbitmap()
        addon_manager.after(300, lambda: addon_manager.iconphoto(False, self.iconpath))

        ctk.CTkButton(addon_manager, text=_("Install add-on from file"), command=self.install_addon).pack(
            padx=10, pady=10, fill="x"
        )

        self.installed_addons_frame = ctk.CTkScrollableFrame(addon_manager)
        self.installed_addons_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.load_installed_addons()

    def load_installed_addons(self):
        for widget in self.installed_addons_frame.winfo_children():
            widget.destroy()

        files = os.listdir(Constants.ADDONS_FOLDER)
        addons_number = 0

        for f in files:
            if f.endswith(".py"):
                addons_number += 1
                full_path = os.path.join(Constants.ADDONS_FOLDER, f)
                metadata = self.get_addon_metadata(full_path)
                AddonManagerItem(
                    self.installed_addons_frame,
                    title=metadata.get("name", f),
                    author=metadata.get("author"),
                    version=metadata.get("version"),
                    description=metadata.get("description"),
                    delete_button_command=lambda fp=full_path: self.uninstall_addon(fp),
                    run_button_command=lambda fp=full_path: self.run_addon(fp),
                )

        self.installed_addons_frame.configure(label_text=f"{_('Installed add-ons')} ({addons_number})")

    def get_addon_metadata(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "metadata":
                            if isinstance(node.value, ast.Dict):
                                metadata = {}
                                for key, value in zip(node.value.keys, node.value.values):
                                    if isinstance(key, (ast.Constant, ast.Str)):
                                        k = key.value if isinstance(key, ast.Constant) else key.s
                                        if isinstance(value, (ast.Constant, ast.Str, ast.Num)):
                                            v = value.value if isinstance(value, ast.Constant) else (value.s if isinstance(value, ast.Str) else value.n)
                                            metadata[k] = v
                                return metadata
        except Exception:
            pass
        return {}

    def install_addon(self):
        addon_path = filedialog.askopenfilename(title=_("Open add-on"), filetypes=([("PY", "*.py")]))
        if addon_path:
            shutil.copy(addon_path, Constants.ADDONS_FOLDER)

        self.load_installed_addons()

    def uninstall_addon(self, path: str):
        os.remove(path)
        self.load_installed_addons()
