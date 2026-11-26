# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections import deque
from pathlib import Path

import customtkinter as ctk
from constants import Constants
from core.bhcomposer import BhComposer
from utils.common import resource
from utils.config_loader import config

from .addons import Addons
from .canvas import CanvasOperations
from .common import Common
from .edit_tools import EditTools
from .panels import Panels
from .screenshot import Screenshot
from .selection import Selection
from .tool_operations import ToolOperations


class BrushsheLogic(
    Common,
    CanvasOperations,
    EditTools,
    Selection,
    Screenshot,
    Panels,
    ToolOperations,
    Addons,
):
    def __init__(self, ui):
        self.ui = ui

        """From config"""
        self.undo_stack = deque(maxlen=config.getint("Brushshe", "undo_levels"))
        self.redo_stack = deque(maxlen=config.getint("Brushshe", "undo_levels"))
        self.grid_step = config.getint("Brushshe", "grid_step")
        self.autosave_var = ctk.BooleanVar(value=config.getboolean("Brushshe", "autosave"))
        self.use_title_menu = ctk.BooleanVar(value=config.getboolean("Brushshe", "use_title_menu"))
        self.hide_left_toolbar = ctk.BooleanVar(value=config.getboolean("Brushshe", "hide_left_toolbar"))

        self.is_gradient_fill = ctk.BooleanVar(value=False)
        self.is_sticker_use_real_size = ctk.BooleanVar(value=False)
        self.is_insert_smoothing = ctk.BooleanVar(value=False)
        self.is_reset_settings_after_exiting = ctk.BooleanVar(value=False)

        # Max tail can not be more 4 MB = 1024 (width) x 1024 (height) x 4 (rgba).
        # canvas_tail_size: Max = 1024. Default = 128. Min = 16.
        self.canvas_tail_size = 128
        # If None - no crop, if set - need check out of crop.
        self.canvas_tails_area = None

        self.bg_color = "white"

        self.tool_size_dict = {
            "brush": Constants().BRUSH_SIZE,
            "r-brush": Constants().BRUSH_SIZE,
            "eraser": Constants().ERASER_SIZE,
            "spray": Constants().SPRAY_SIZE,
            "shape": Constants().SHAPE_SIZE,
            "sticker": Constants().STICKER_SIZE,
            "text": Constants().FONT_SIZE,
        }

        self.composer = BhComposer(0, 0)  # Empty init.
        self.composer.mask_type = 0  # Type: 0 - fill, 1 - ants

        self.current_file = None
        self.prev_x, self.prev_y = None, None
        self.current_font = "Open Sans"
        self.is_grid_visible = False

        self.timer_mask_time_for_update = 200  # ms
        self.timer_mask_last_update = 0
        self.timer_mask_update = self.ui.after(self.timer_mask_time_for_update, self.mask_update)

        """Color themes"""
        themes_folder = Path(resource("assets/themes"))
        self.color_themes = [
            str(path.relative_to(themes_folder).with_suffix("")) for path in themes_folder.rglob("*.json")
        ] + ctk.ThemeManager._built_in_themes

        for folder in [Constants.GALLERY_FOLDER, Constants.ADDONS_FOLDER]:
            if not folder.exists():
                folder.mkdir(parents=True)

        self.tools_dict = {
            "brush": {"command": self.brush, "hotkey": "Ctrl+B"},
            "eraser": {"command": self.eraser, "hotkey": "Ctrl+E"},
            "fill": self.start_fill,
            "recoloring_brush": self.recoloring_brush,
            "spray": self.spray,
            "text": self.text_tool,
            "rectangle": lambda: self.create_shape("Rectangle"),
            "oval": lambda: self.create_shape("Oval"),
            "fill_rectangle": lambda: self.create_shape("Fill rectangle"),
            "fill_oval": lambda: self.create_shape("Fill oval"),
            "line": lambda: self.create_shape("Line"),
            "bezier": self.bezier_shape,
            "cut": {"command": lambda: self.copy_tool(deleted=True), "hotkey": "Ctrl+X"},
            "copy": {"command": self.copy_tool, "hotkey": "Ctrl+C"},
            "insert": {"command": self.start_insert, "hotkey": "Ctrl+V"},
            "crop": self.crop_simple,
            "rectangle_select": lambda: self.select_by_shape(shape="rectangle"),
            "polygon_select": self.select_by_polygon,
            "fuzzy_select": lambda: self.select_by_color(fill_limit=True),
            "select_by_color": self.select_by_color,
            "deselect_all": self.remove_mask,
            "effects": self.effects,
        }
