# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import sys

import customtkinter as ctk
from constants import Constants
from logic import BrushsheLogic
from PIL import Image, ImageTk
from ui.brush_palette import BrushPalette
from ui.tooltip import Tooltip
from utils.common import resource
from utils.config_loader import config
from utils.translator import _

from .addon_manager import AddonManager
from .change_size import ChangeSize
from .frames import Frames
from .gallery import Gallery
from .menubar import MenuBar
from .settings import Settings
from .stickers import Stickers


class BrushsheGui(ctk.CTk, MenuBar, ChangeSize, Settings, Stickers, Frames, Gallery, AddonManager):
    def __init__(self):
        super().__init__(className="Brushshe")
        self.logic = BrushsheLogic(self)

        """ Main window """
        self.geometry("790x680")
        self.title(_("Unnamed") + " - " + _("Brushshe"))

        self.iconpath = ImageTk.PhotoImage(file=resource("assets/icons/icon.png"))
        self.wm_iconbitmap()
        self.iconphoto(False, self.iconpath)

        self.protocol("WM_DELETE_WINDOW", self.logic.when_closing)

        self.create_menubar()

        """Top bar"""
        tools_frame = ctk.CTkFrame(self, corner_radius=0)
        tools_frame.pack(side="top", fill="x")

        # Brush size used to paint all the icons in the toolbar: 50
        # Width and height of all icons - 512 px

        undo_icon = ctk.CTkImage(
            light_image=Image.open(resource("assets/icons/undo_light.png")),
            dark_image=Image.open(resource("assets/icons/undo_dark.png")),
            size=(22, 22),
        )
        undo_button = ctk.CTkButton(
            tools_frame,
            text=None,
            width=30,
            image=undo_icon,
            fg_color="transparent",
            hover=False,
            command=self.logic.undo,
        )
        undo_button.pack(side="left", padx=1)
        Tooltip(undo_button, message=_("Undo") + " (Ctrl+Z)")

        redo_icon = ctk.CTkImage(
            light_image=Image.open(resource("assets/icons/redo_light.png")),
            dark_image=Image.open(resource("assets/icons/redo_dark.png")),
            size=(22, 22),
        )

        redo_button = ctk.CTkButton(
            tools_frame,
            text=None,
            width=30,
            image=redo_icon,
            fg_color="transparent",
            hover=False,
            command=self.logic.redo,
        )
        redo_button.pack(side="left", padx=1)
        Tooltip(redo_button, message=_("Redo") + " (Ctrl+Y)")

        self.tool_config_docker = ctk.CTkFrame(tools_frame)
        self.tool_config_docker.pack(side="left", padx=4)
        self.tool_config_docker.configure(height=30, fg_color="transparent")

        save_to_gallery_btn = ctk.CTkButton(tools_frame, text=_("Save to gallery"), command=self.logic.save_to_gallery)
        save_to_gallery_btn.pack(side="right", padx=1, pady=2)
        Tooltip(save_to_gallery_btn, message=_("Save to gallery") + " (Ctrl+S)")

        """Canvas frame"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack_propagate(False)
        self.main_frame.pack(fill="both", expand=True)

        self.tools_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tools_frame.pack(side="left", fill="y")

        """Canvas"""
        self.canvas_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.canvas_frame.pack_propagate(False)
        self.canvas_frame.pack(side="left", fill="both", expand=True)

        self.canvas_frame_main = ctk.CTkFrame(self.canvas_frame, fg_color="transparent")
        self.canvas_frame_main.pack_propagate(False)
        self.canvas_frame_main.pack(side="left", fill="both", expand=True)

        self.canvas_frame_right = ctk.CTkFrame(self.main_frame, fg_color="transparent", width=16)
        self.canvas_frame_right.pack(side="right", fill="y")

        self.canvas_frame_rd = ctk.CTkFrame(self.canvas_frame_right, fg_color="transparent", width=16, height=16)
        self.canvas_frame_rd.pack(side="bottom")

        self.v_scrollbar = ctk.CTkScrollbar(
            self.canvas_frame_right, orientation="vertical", command=self.logic.v_scrollbar_command
        )
        self.v_scrollbar.pack(side="right", fill="y")

        self.h_scrollbar = ctk.CTkScrollbar(
            self.canvas_frame_main, orientation="horizontal", command=self.logic.h_scrollbar_command
        )
        self.h_scrollbar.pack(side="bottom", fill="x")

        self.canvas = ctk.CTkCanvas(
            self.canvas_frame_main, yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set
        )
        self.canvas.pack(side="top", anchor="center", expand=True)

        """Bottom bar"""
        self.bottom_docker = ctk.CTkFrame(self, corner_radius=0)
        self.bottom_docker.pack(side="bottom", fill="x")

        self.brush_palette = BrushPalette(
            self.bottom_docker,
            click_main_btn=self.logic.main_color_choice,
            click_second_btn=self.logic.second_color_choice,
            click_flip_btn=self.logic.flip_brush_colors,
        )
        self.brush_palette.pack(side="left", padx=2)

        self.palette_widget = ctk.CTkFrame(
            self.bottom_docker,
        )
        self.palette_widget.pack(side="left", fill="x", padx=2, pady=2)

        if config.get("Brushshe", "palette") in Constants.STANDART_PALETTES:
            self.logic.import_palette(resource(f"assets/palettes/{config.get('Brushshe', 'palette')}_palette.hex"))
        else:
            self.logic.import_palette(resource(config.get("Brushshe", "palette")))

        self.size_button = ctk.CTkButton(self.bottom_docker, text="640x480", command=self.change_size)
        self.size_button.pack(side="right", padx=1)

        """Initialization"""
        self.logic.set_left_toolbar(False)
        self.logic.new_picture(self.logic.bg_color, first_time=True)
        self.logic.brush()
        self.update()  # Update interface before recalculate canvas.
        self.logic.force_resize_canvas()
        self.logic.update_canvas()
        self.logic.set_mask_type(config.getint("Brushshe", "mask"))

        if len(sys.argv) > 1:
            self.logic.open_image(sys.argv[1])

        """Bindings"""
        self.canvas.bind("<Button-3>", self.logic.eyedropper)

        self.canvas.bind("<Button-2>", self.logic.begin_moving_canvas)
        self.canvas.bind("<B2-Motion>", self.logic.continue_moving_canvas)

        self.bind("<Control-z>", lambda e: self.logic.undo())
        self.bind("<Control-y>", lambda e: self.logic.redo())
        self.bind("<Control-s>", lambda e: self.logic.save_to_gallery())

        self.bind("<Control-x>", lambda e: self.logic.copy_tool(deleted=True))
        self.bind("<Control-c>", lambda e: self.logic.copy_tool())
        self.bind("<Control-v>", lambda e: self.logic.start_insert())
        self.bind("<Delete>", lambda e: self.logic.delete_selected())

        self.bind("<Control-f>", lambda e: self.logic.flip_brush_colors())
        self.bind("<Control-b>", lambda e: self.logic.brush())
        self.bind("<Control-e>", lambda e: self.logic.eraser())

        self.bind("<Key-equal>", lambda e: self.logic.zoom_in(e))
        self.bind("<Key-minus>", lambda e: self.logic.zoom_out(e))

        self.bind("<Key-bracketleft>", lambda e: self.logic.change_tool_size_bind(e, -1))
        self.bind("<Key-bracketright>", lambda e: self.logic.change_tool_size_bind(e, 1))
        self.bind("<Key-braceleft>", lambda e: self.logic.change_tool_size_bind(e, -10))
        self.bind("<Key-braceright>", lambda e: self.logic.change_tool_size_bind(e, 10))

        self.bind("<Key>", self.logic.key_handler)

        # Scroll on mouse
        # Windows
        self.canvas.bind("<MouseWheel>", self.logic.scroll_on_canvasy)
        self.canvas.bind("<Shift-MouseWheel>", self.logic.scroll_on_canvasx)
        # Linux
        self.canvas.bind("<Button-4>", self.logic.scroll_on_canvasy)
        self.canvas.bind("<Button-5>", self.logic.scroll_on_canvasy)
        self.canvas.bind("<Shift-Button-4>", self.logic.scroll_on_canvasx)
        self.canvas.bind("<Shift-Button-5>", self.logic.scroll_on_canvasx)

        # Resize window (and canvas)
        self.bind("<Configure>", self.logic.on_window_resize)
