# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import importlib.util
from tkinter import filedialog
from types import SimpleNamespace

import data
from ui import messagebox
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
