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
from PIL import ImageTk
from ui.tooltip import Tooltip
from utils.common import resource
from utils.translator import _


class AddonManagerItem(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        author: str | None = None,
        version: str | None = None,
        description: str | None = None,
        delete_button_command: Callable | None = None,
        run_button_command: Callable | None = None,
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

        if delete_button_command:
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


class AddonManager(ctk.CTkToplevel):
    def __init__(self, icon: ImageTk.PhotoImage, run_addon: Callable):
        super().__init__()

        self.title(_("Add-on Manager"))
        self.geometry("600x400")
        self.wm_iconbitmap()
        self.after(300, lambda: self.iconphoto(False, icon))

        self._run_addon = run_addon

        ctk.CTkButton(self, text=_("Install add-on from file"), command=self._install_addon).pack(
            padx=10, pady=10, fill="x"
        )

        self._addons_frame = ctk.CTkScrollableFrame(self)
        self._addons_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self._load_addons()

    def _load_addons(self):
        for widget in self._addons_frame.winfo_children():
            widget.destroy()

        addons_number = self._load_addons_from_folder(resource("addons")) + self._load_addons_from_folder(
            Constants.ADDONS_FOLDER
        )

        self._addons_frame.configure(label_text=f"{_('Installed add-ons')} ({addons_number})")

    def _load_addons_from_folder(self, folder: str) -> int:
        files = os.listdir(folder)
        addons_number = 0

        for f in files:
            if f.endswith(".py"):
                addons_number += 1
                full_path = os.path.join(folder, f)
                metadata = self._get_addon_metadata(full_path)
                AddonManagerItem(
                    self._addons_frame,
                    title=metadata.get("name", f),
                    author=metadata.get("author"),
                    version=metadata.get("version"),
                    description=metadata.get("description"),
                    delete_button_command=(lambda fp=full_path: self._uninstall_addon(fp))
                    if folder == Constants.ADDONS_FOLDER
                    else None,
                    run_button_command=lambda fp=full_path: self._run_addon(fp),
                )

        return addons_number

    def _get_addon_metadata(self, path: str) -> dict:
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

    def _install_addon(self):
        addon_path = filedialog.askopenfilename(title=_("Open add-on"), filetypes=([("PY", "*.py")]))
        if addon_path:
            shutil.copy(addon_path, Constants.ADDONS_FOLDER)

        self._load_addons()

    def _uninstall_addon(self, path: str):
        os.remove(path)
        self._load_addons()
