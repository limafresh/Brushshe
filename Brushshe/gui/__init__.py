# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import sys

import customtkinter as ctk
import data
from logic import BrushsheLogic
from PIL import Image, ImageTk
from ui.brush_palette import BrushPalette
from ui.tooltip import Tooltip
from utils.config_loader import config
from utils.resource import resource
from utils.translator import _

from .change_size import ChangeSize
from .frames import Frames
from .gallery import Gallery
from .menubar import MenuBar
from .settings import Settings
from .stickers import Stickers


class BrushsheGui(ctk.CTk, MenuBar, ChangeSize, Settings, Stickers, Frames, Gallery):
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

        """Tools (left) bar"""
        tools_list = [
            {
                "type": "button",
                "name": _("Brush"),
                "helper": _("Brush") + " (Ctrl+B)",
                "action": self.logic.brush,
                "icon_name": "brush",
            },
            {
                "type": "button",
                "name": _("Eraser"),
                "helper": _("Eraser") + " (Ctrl+E)",
                "action": self.logic.eraser,
                "icon_name": "eraser",
            },
            {
                "type": "button",
                "name": _("Fill"),
                "helper": _("Fill"),
                "action": self.logic.start_fill,
                "icon_name": "fill",
            },
            {
                "type": "button",
                "name": _("Recoloring Brush"),
                "helper": _("Recoloring Brush"),
                "action": self.logic.recoloring_brush,
                "icon_name": "recoloring_brush",
            },
            {
                "type": "button",
                "name": _("Spray"),
                "helper": _("Spray"),
                "action": self.logic.spray,
                "icon_name": "spray",
            },
            {
                "type": "button",
                "name": _("Text"),
                "helper": _("Text"),
                "action": self.logic.text_tool,
                "icon_name": "text",
            },
            {"type": "separator"},
            {
                "type": "button",
                "name": _("Rectangle"),
                "helper": _("Rectangle"),
                "action": lambda: self.logic.create_shape("Rectangle"),
                "icon_name": "rectangle",
            },
            {
                "type": "button",
                "name": _("Oval"),
                "helper": _("Oval"),
                "action": lambda: self.logic.create_shape("Oval"),
                "icon_name": "oval",
            },
            {
                "type": "button",
                "name": _("Fill rectangle"),
                "helper": _("Fill rectangle"),
                "action": lambda: self.logic.create_shape("Fill rectangle"),
                "icon_name": "fill_rectangle",
            },
            {
                "type": "button",
                "name": _("Fill oval"),
                "helper": _("Fill oval"),
                "action": lambda: self.logic.create_shape("Fill oval"),
                "icon_name": "fill_oval",
            },
            {
                "type": "button",
                "name": _("Line"),
                "helper": _("Line"),
                "action": lambda: self.logic.create_shape("Line"),
                "icon_name": "line",
            },
            {
                "type": "button",
                "name": _("Bezier"),
                "helper": _("Bezier"),
                "action": self.logic.bezier_shape,
                "icon_name": "bezier",
            },
            {"type": "separator"},
            {
                "type": "button",
                "name": _("Cut"),
                "helper": _("Cut") + " (Ctrl+X)",
                "action": lambda: self.logic.copy_tool(deleted=True),
                "icon_name": "cut",
            },
            {
                "type": "button",
                "name": _("Copy"),
                "helper": _("Copy") + " (Ctrl+C)",
                "action": lambda: self.logic.copy_tool(),
                "icon_name": "copy",
            },
            {
                "type": "button",
                "name": _("Insert"),
                "helper": _("Insert") + " (Ctrl+V)",
                "action": self.logic.start_insert,
                "icon_name": "insert",
            },
            {
                "type": "button",
                "name": _("Crop"),
                "helper": _("Crop"),
                "action": self.logic.crop_simple,
                "icon_name": "crop",
            },
            {"type": "separator"},
            {
                "type": "button",
                "name": _("Rectangle select"),
                "helper": _("Rectangle select"),
                "action": lambda: self.logic.select_by_shape(shape="rectangle"),
                "icon_name": "rectangle_select",
            },
            {
                "type": "button",
                "name": _("Polygon select"),
                "helper": _("Polygon select"),
                "action": self.logic.select_by_polygon,
                "icon_name": "polygon_select",
            },
            {
                "type": "button",
                "name": _("Fuzzy select"),
                "helper": _("Fuzzy select (limited select by color)"),
                "action": lambda: self.logic.select_by_color(fill_limit=True),
                "icon_name": "fuzzy_select",
            },
            {
                "type": "button",
                "name": _("Select by color"),
                "helper": _("Select by color"),
                "action": lambda: self.logic.select_by_color(),
                "icon_name": "select_by_color",
            },
            {
                "type": "button",
                "name": _("Deselect all"),
                "helper": _("Deselect all"),
                "action": self.logic.remove_mask,
                "icon_name": "deselect_all",
            },
            {"type": "separator"},
            {
                "type": "button",
                "name": _("Effects"),
                "helper": _("Effects"),
                "action": self.logic.effects,
                "icon_name": "effects",
            },
        ]

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

        self.standard_palettes = ["default", "4bit", "vintage", "seven"]
        if config.get("Brushshe", "palette") in self.standard_palettes:
            self.logic.import_palette(resource(f"assets/palettes/{config.get('Brushshe', 'palette')}_palette.hex"))
        else:
            self.logic.import_palette(resource(config.get("Brushshe", "palette")))

        self.size_button = ctk.CTkButton(self.bottom_docker, text="640x480", command=self.change_size)
        self.size_button.pack(side="right", padx=1)

        """Initialization"""
        self.logic.set_tools_docker(tools_list, 2)
        self.logic.new_picture(data.bg_color, first_time=True)
        self.logic.brush()
        self.update()  # Update interface before recalculate canvas.
        self.logic.force_resize_canvas()
        self.logic.update_canvas()

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
