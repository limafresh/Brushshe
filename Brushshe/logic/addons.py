# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import importlib.util
from tkinter import filedialog

from ui import messagebox
from utils.translator import _


class AddonAPI:
    def __init__(self, app):
        # Functions
        self.draw_line = app.draw_line
        self.undo = app.undo
        self.redo = app.redo
        self.new_picture = app.new_picture
        self.rotate = app.rotate
        self.other_bg_color = app.other_bg_color
        self.change_color = app.change_color
        self.crop_picture = app.crop_picture
        self.open_from_file = app.open_from_file
        self.flip_brush_colors = app.flip_brush_colors
        self.remove_white_background = app.remove_white_background
        self.set_addon_tool_size = lambda size: setattr(app, "tool_size", size)
        self.update_canvas = app.update_canvas
        self.record_action = app.record_action
        self.get_contrast_color = app.get_contrast_color
        self.canvas_to_pict_xy = app.canvas_to_pict_xy

        # Variables
        self.tool_config_docker = app.ui.tool_config_docker
        self.canvas = app.ui.canvas


class Addons:
    def open_addon(self):
        addon_path = filedialog.askopenfilename(title=_("Open add-on"), filetypes=([("PY", "*.py")]))
        if addon_path:
            self.run_addon(addon_path)

    def run_addon(self, path: str):
        spec = importlib.util.spec_from_file_location("addon", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "register"):
            try:
                if hasattr(module, "metadata") and module.metadata.get("tool"):
                    tool_args = module.metadata["tool"]
                else:
                    tool_args = ["Add-on", None, None, None, "arrow"]
                self.set_tool("addon", *tool_args)

                module.register(AddonAPI(self))
            except Exception as e:
                messagebox.addon_error(e)
        else:
            messagebox.addon_not_have_register_function()
