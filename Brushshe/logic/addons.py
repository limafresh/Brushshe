# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import importlib.util
import os
import shutil
from tkinter import filedialog
from types import SimpleNamespace

import customtkinter as ctk
import data
from ui import messagebox
from ui.addon_manager_item import AddonManagerItem
from utils.translator import _


class Addons:
    def open_addon(self):
        addon_path = filedialog.askopenfilename(title=_("Open add-on"), filetypes=([("PY", "*.py")]))
        if addon_path:
            self.run_addon(addon_path)

    def run_addon(self, path: str):
        data.tool_size = 2
        self.set_tool("addon", "Add-on", None, None, None, "arrow")

        api = SimpleNamespace(
            # Functions
            draw_line=self.draw_line,
            undo=self.undo,
            redo=self.redo,
            new_picture=lambda color, mode: self.new_picture(color, mode),
            rotate=self.rotate,
            other_bg_color=self.other_bg_color,
            change_color=self.change_color,
            crop_picture=self.crop_picture,
            open_from_file=self.open_from_file,
            flip_brush_colors=self.flip_brush_colors,
            remove_white_background=self.remove_white_background,
            set_addon_tool_size=self.set_addon_tool_size,
            # Variables
            tool_config_docker=self.ui.tool_config_docker,
            canvas=self.ui.canvas,
        )
        spec = importlib.util.spec_from_file_location("addon", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "register"):
            try:
                module.register(api)
            except Exception as e:
                messagebox.addon_error(e)
            self.record_action()
        else:
            messagebox.addon_not_have_register_function()

    def set_addon_tool_size(self, size: int):
        data.tool_size = size

    def load_installed_addons(self):
        for widget in self.ui.installed_addons_frame.winfo_children():
            widget.destroy()

        files = os.listdir(data.addons_folder)
        is_empty = True

        for f in files:
            if f.endswith(".py"):
                is_empty = False
                full_path = os.path.join(data.addons_folder, f)
                AddonManagerItem(
                    self.ui.installed_addons_frame,
                    title=f,
                    delete_button_command=lambda fp=full_path: self.uninstall_addon(fp),
                    run_button_command=lambda fp=full_path: self.run_addon(fp),
                )

        if is_empty:
            ctk.CTkLabel(self.ui.installed_addons_frame, text=_("Empty")).pack(pady=50)

    def load_addon_store(self):
        pass

    def install_addon(self):
        addon_path = filedialog.askopenfilename(title=_("Open add-on"), filetypes=([("PY", "*.py")]))
        if addon_path:
            shutil.copy(addon_path, data.addons_folder)

        self.load_installed_addons()

    def uninstall_addon(self, path: str):
        os.remove(path)
        self.load_installed_addons()
