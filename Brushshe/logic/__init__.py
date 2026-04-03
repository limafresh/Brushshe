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
from .paint_tools import PaintTools
from .panels import Panels
from .screenshot import Screenshot
from .selection import Selection
from .shapes import Shapes
from .tool_operations import ToolOperations


class BrushsheLogic(
    Common,
    CanvasOperations,
    PaintTools,
    Shapes,
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
        self.is_brush_smoothing = config.getboolean("Brushshe", "smoothing")
        self.brush_smoothing_factor = config.getint("Brushshe", "brush_smoothing_factor")  # Between: 3..64
        self.brush_smoothing_quality = config.getint("Brushshe", "brush_smoothing_quality")  # Between: 1..64
        self.autosave_var = ctk.BooleanVar(value=config.getboolean("Brushshe", "autosave"))

        self.is_gradient_fill = ctk.StringVar(value="off")
        self.is_sticker_use_real_size = ctk.StringVar(value="off")
        self.is_insert_smoothing = ctk.StringVar(value="off")

        # Max tail can not be more 4 MB = 1024 (width) x 1024 (height) x 4 (rgba).
        # canvas_tail_size: Max = 1024. Default = 128. Min = 16.
        self.canvas_tail_size = 128
        # If None - no crop, if set - need check out of crop.
        self.canvas_tails_area = None

        self.brush_color = "black"
        self.second_brush_color = "white"
        self.bg_color = "white"
        self.brush_shape = "circle"

        self.brush_size = 2
        self.eraser_size = 4
        self.spray_size = 10
        self.shape_size = 2
        self.sticker_size = 100
        self.font_size = 24

        self.tool_size_dict = {
            "brush": self.brush_size,
            "r-brush": self.brush_size,
            "eraser": self.eraser_size,
            "spray": self.spray_size,
            "shape": self.shape_size,
            "sticker": self.sticker_size,
            "text": self.font_size,
        }

        self.composer = BhComposer(0, 0)  # Empty init.
        self.composer.mask_type = 0  # Type: 0 - fill, 1 - ants

        self.zoom = 1
        self.selected_mask_img = None  # Can be gray_image or None
        self.current_file = None
        self.prev_x, self.prev_y = None, None
        self.current_font = "Open Sans"
        self.font_path = resource("assets/fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf")
        self.is_reset_settings_after_exiting = False

        self.timer_mask_time_for_update = 200  # ms
        self.timer_mask_last_update = 0
        self.timer_mask_update = self.ui.after(self.timer_mask_time_for_update, self.mask_update)

        """Color themes"""
        themes_folder = Path(resource("assets/themes"))
        self.color_themes = [
            str(path.relative_to(themes_folder).with_suffix("")) for path in themes_folder.rglob("*.json")
        ] + ["blue", "green", "dark-blue"]

        for folder in [Constants.GALLERY_FOLDER, Constants.ADDONS_FOLDER]:
            if not folder.exists():
                folder.mkdir(parents=True)
