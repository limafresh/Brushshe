# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import importlib.util
from types import SimpleNamespace

import data
from ui.file_dialog import FileDialog
from utils.translator import _


class Addons:
    def open_addon(self):
        dialog = FileDialog(self.ui, title=_("Open add-on"))
        if dialog.path:
            self.run_addon(dialog.path)

    def run_addon(self, path: str):
        data.tool_size = 2
        self.set_tool("addon", "Add-on", None, None, None, "arrow")

        api = SimpleNamespace(
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
        )
        spec = importlib.util.spec_from_file_location("addon", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "register"):
            module.register(api)

    def set_addon_tool_size(self, size):
        data.tool_size = size
