import math
import os
import random
import sys
import webbrowser
from collections import deque
from io import BytesIO
from tkinter import PhotoImage
from urllib.request import urlopen
from uuid import uuid4

# import time  # Need for debug.
import customtkinter as ctk
import gallery
from brush_palette import BrushPalette
from color_picker import AskColor
from config_loader import config, config_file_path, write_config
from core.bezier import make_bezier
from core.bhbrush import bh_draw_line, bh_draw_recoloring_line
from core.bhcomposer import BhComposer
from core.bhhistory import BhHistory, BhPoint
from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from CTkMessagebox import CTkMessagebox
from file_dialog import FileDialog
from PIL import (
    Image,
    ImageChops,
    ImageColor,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
    ImageGrab,
    ImageOps,
    ImageStat,
    ImageTk,
)
from spinbox import IntSpinbox
from tooltip import Tooltip
from translator import _


def resource(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


key_mods = {
    0x0001: "Shift",
    0x0002: "Caps Lock",
    0x0004: "Control",
    0x0008: "Left-hand Alt",
    0x0010: "Num Lock",
    0x0080: "Right-hand Alt",
    0x0100: "Mouse button 1",
    0x0200: "Mouse button 2",
    0x0400: "Mouse button 3",
}


class Brushshe(ctk.CTk):
    def __init__(self):
        super().__init__(className="Brushshe")

        """ Version """
        self.version_prefix = ""
        self.version_major = "2"
        self.version_minor = "3"
        self.version_patch = "0"
        self.version_suffix = ' "Vientiane"'

        self.version_full = "{0}{1}.{2}.{3}{4}".format(
            self.version_prefix,
            self.version_major,
            self.version_minor,
            self.version_patch,
            self.version_suffix,
        )

        """ Main Window """
        self.geometry("790x680")
        self.title(_("Unnamed") + " - " + _("Brushshe"))
        if os.name == "nt":
            self.iconbitmap(resource("icons/icon.ico"))
        else:
            self.iconphoto(True, PhotoImage(file=resource("icons/icon.png")))
        self.protocol("WM_DELETE_WINDOW", self.when_closing)

        """ Menu """
        menu = CTkMenuBar(self)

        file_menu = menu.add_cascade(_("File"))
        file_dropdown = CustomDropdownMenu(widget=file_menu)

        file_dropdown.add_option(option=_("New"), command=lambda: self.new_picture("white"))
        file_dropdown.add_option(
            option=_("New with other color"), command=self.other_bg_color
        )  # TODO: Use dialog from there.
        file_dropdown.add_option(
            option=_("New transparent"),
            command=lambda: self.new_picture(color="#00000000", mode="RGBA"),
        )

        file_dropdown.add_option(option=_("Open from file"), command=self.open_from_file)
        file_dropdown.add_option(option=_("Open from URL"), command=self.open_from_url)
        file_dropdown.add_option(option=_("Save changes to this picture"), command=self.save_current)
        file_dropdown.add_option(option=_("Save as new picture"), command=self.save_as)
        file_dropdown.add_separator()
        file_dropdown.add_option(option=_("Open my gallery"), command=lambda: gallery.show(self.open_image))
        file_dropdown.add_option(option=_("Save to my gallery"), command=self.save_to_gallery)
        file_dropdown.add_separator()
        file_dropdown.add_option(option=_("Import palette (hex)"), command=self.import_palette)

        image_menu = menu.add_cascade(_("Image"))
        image_dropdown = CustomDropdownMenu(widget=image_menu)
        image_dropdown.add_option(option=_("Rotate right"), command=lambda: self.rotate(-90))
        image_dropdown.add_option(option=_("Rotate left"), command=lambda: self.rotate(90))
        image_dropdown.add_separator()
        image_dropdown.add_option(option=_("Change size"), command=self.change_size)
        image_dropdown.add_separator()
        image_dropdown.add_option(option=_("Create screenshot"), command=self.create_screenshot)
        image_dropdown.add_option(option=_("Paste image from clipboard"), command=self.paste_image_from_clipboard)

        view_menu = menu.add_cascade(_("View"))
        view_dropdown = CustomDropdownMenu(widget=view_menu)
        view_dropdown.add_option(option=_("Zoom In"), command=self.zoom_in)
        view_dropdown.add_option(option=_("Zoom Out"), command=self.zoom_out)
        view_dropdown.add_separator()
        view_dropdown.add_option(option=_("Reset"), command=self.reset_zoom)

        select_menu = menu.add_cascade(_("Select"))
        select_dropdown = CustomDropdownMenu(widget=select_menu)
        select_dropdown.add_option(
            option=_("Rectangle select"),
            command=lambda: self.select_by_shape(shape="rectangle"),
        )
        select_dropdown.add_option(option=_("Polygon select"), command=self.select_by_polygon)
        select_dropdown.add_option(option=_("Fuzzy select"), command=lambda: self.select_by_color(fill_limit=True))
        select_dropdown.add_option(option=_("Select by color"), command=lambda: self.select_by_color())
        select_dropdown.add_option(option=_("Invert selected"), command=self.invert_mask)
        select_dropdown.add_option(option=_("Deselect all"), command=self.remove_mask)

        tools_menu = menu.add_cascade(_("Tools"))
        tools_dropdown = CustomDropdownMenu(widget=tools_menu)

        draw_tools_submenu = tools_dropdown.add_submenu(_("Draw tools"))
        draw_tools_submenu.add_option(option=_("Brush"), command=self.brush)
        draw_tools_submenu.add_option(option=_("Eraser"), command=self.eraser)
        draw_tools_submenu.add_option(option=_("Fill"), command=self.fill)
        draw_tools_submenu.add_option(option=_("Recoloring Brush"), command=self.recoloring_brush)
        draw_tools_submenu.add_option(option=_("Spray"), command=self.spray)

        shapes_submenu = tools_dropdown.add_submenu(_("Shapes"))
        shape_options = ["Rectangle", "Oval", "Fill rectangle", "Fill oval", "Line"]
        for shape in shape_options:
            shapes_submenu.add_option(option=_(shape), command=lambda shape=shape: self.create_shape(shape))
        shapes_submenu.add_option(option=_("Bezier curve"), command=self.bezier_shape)

        edit_submenu = tools_dropdown.add_submenu(_("Edit tools"))
        edit_submenu.add_option(option=_("Cut"), command=lambda: self.copy_tool(deleted=True))
        edit_submenu.add_option(option=_("Copy"), command=lambda: self.copy_tool())
        edit_submenu.add_option(option=_("Insert"), command=lambda: self.start_insert())
        edit_submenu.add_option(option=_("Crop"), command=lambda: self.crop_simple())

        tools_icon_size = (20, 20)
        tools_dropdown.add_separator()
        smile_icon = ctk.CTkImage(Image.open(resource("icons/smile.png")), size=tools_icon_size)
        tools_dropdown.add_option(option=_("Stickers"), image=smile_icon, command=self.show_stickers_choice)
        text_icon = ctk.CTkImage(Image.open(resource("icons/text.png")), size=tools_icon_size)
        tools_dropdown.add_option(option=_("Text"), image=text_icon, command=self.text_tool)
        frame_icon = ctk.CTkImage(Image.open(resource("icons/frame.png")), size=tools_icon_size)
        tools_dropdown.add_option(option=_("Frames"), image=frame_icon, command=self.show_frame_choice)
        effects_icon = ctk.CTkImage(Image.open(resource("icons/effects.png")), size=tools_icon_size)
        tools_dropdown.add_option(option=_("Effects"), image=effects_icon, command=self.effects)
        tools_dropdown.add_separator()
        tools_dropdown.add_option(option=_("Remove white background"), command=self.remove_white_background)

        menu.add_cascade(_("My Gallery"), command=lambda: gallery.show(self.open_image))

        other_menu = menu.add_cascade(_("More"))
        other_dropdown = CustomDropdownMenu(widget=other_menu)
        other_dropdown.add_option(option=_("Settings"), command=self.settings)
        other_dropdown.add_option(option=_("Reset settings after exiting"), command=self.reset_settings_after_exiting)
        other_dropdown.add_option(option=_("About program"), command=self.about_program)

        """Top Bar"""
        tools_frame = ctk.CTkFrame(self, corner_radius=0)
        tools_frame.pack(side=ctk.TOP, fill=ctk.X)

        # Brush size used to paint all the icons in the toolbar: 50
        # Width and height of all icons - 512 px

        # Open, New and Save are already exists in menu bar.

        undo_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/undo_light.png")),
            dark_image=Image.open(resource("icons/undo_dark.png")),
            size=(22, 22),
        )
        undo_button = ctk.CTkButton(
            tools_frame,
            text=None,
            width=30,
            image=undo_icon,
            fg_color=tools_frame.cget("fg_color"),
            hover=False,
            command=self.undo,
        )
        undo_button.pack(side=ctk.LEFT, padx=1)
        Tooltip(undo_button, message=_("Undo") + " (Ctrl+Z)")

        redo_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/redo_light.png")),
            dark_image=Image.open(resource("icons/redo_dark.png")),
            size=(22, 22),
        )

        redo_button = ctk.CTkButton(
            tools_frame,
            text=None,
            width=30,
            image=redo_icon,
            fg_color=tools_frame.cget("fg_color"),
            hover=False,
            command=self.redo,
        )
        redo_button.pack(side=ctk.LEFT, padx=1)
        Tooltip(redo_button, message=_("Redo") + " (Ctrl+Y)")

        self.tool_config_docker = ctk.CTkFrame(tools_frame)
        self.tool_config_docker.pack(side=ctk.LEFT, padx=4)
        self.tool_config_docker.configure(height=30, fg_color="transparent")

        save_to_gallery_btn = ctk.CTkButton(tools_frame, text=_("Save to gallery"), command=self.save_to_gallery)
        save_to_gallery_btn.pack(side=ctk.RIGHT, padx=1, pady=2)
        Tooltip(save_to_gallery_btn, message=_("Save to gallery") + " (Ctrl+S)")

        """Canvas frame"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack_propagate(False)
        self.main_frame.pack(fill=ctk.BOTH, expand=True)

        self.tools_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tools_frame.pack(side=ctk.LEFT, fill=ctk.Y)

        """Tools (Left) Bar"""
        tools_list = [
            {
                "type": "button",
                "name": _("Brush"),
                "helper": _("Brush") + " (Ctrl+B)",
                "action": self.brush,
                "icon_name": "brush",
            },
            {
                "type": "button",
                "name": _("Eraser"),
                "helper": _("Eraser") + " (Ctrl+E)",
                "action": self.eraser,
                "icon_name": "eraser",
            },
            {
                "type": "button",
                "name": _("Fill"),
                "helper": _("Fill"),
                "action": self.start_fill,
                "icon_name": "fill",
            },
            {
                "type": "button",
                "name": _("Recoloring Brush"),
                "helper": _("Recoloring Brush"),
                "action": self.recoloring_brush,
                "icon_name": "recoloring_brush",
            },
            {
                "type": "button",
                "name": _("Spray"),
                "helper": _("Spray"),
                "action": self.spray,
                "icon_name": "spray",
            },
            {"type": "separator"},
            {
                "type": "button",
                "name": _("Rectangle"),
                "helper": _("Rectangle"),
                "action": lambda: self.create_shape("Rectangle"),
                "icon_name": "rectangle",
            },
            {
                "type": "button",
                "name": _("Oval"),
                "helper": _("Oval"),
                "action": lambda: self.create_shape("Oval"),
                "icon_name": "oval",
            },
            {
                "type": "button",
                "name": _("Fill rectangle"),
                "helper": _("Fill rectangle"),
                "action": lambda: self.create_shape("Fill rectangle"),
                "icon_name": "fill_rectangle",
            },
            {
                "type": "button",
                "name": _("Fill oval"),
                "helper": _("Fill oval"),
                "action": lambda: self.create_shape("Fill oval"),
                "icon_name": "fill_oval",
            },
            {
                "type": "button",
                "name": _("Line"),
                "helper": _("Line"),
                "action": lambda: self.create_shape("Line"),
                "icon_name": "line",
            },
            {
                "type": "button",
                "name": _("Bezier"),
                "helper": _("Bezier"),
                "action": self.bezier_shape,
                "icon_name": "bezier",
            },
            {"type": "separator"},
            {
                "type": "button",
                "name": _("Cut"),
                "helper": _("Cut"),  # + " (Ctrl+X)",
                "action": lambda: self.copy_tool(deleted=True),
                "icon_name": "cut",
            },
            {
                "type": "button",
                "name": _("Copy"),
                "helper": _("Copy"),  # + " (Ctrl+C)",
                "action": lambda: self.copy_tool(),
                "icon_name": "copy",
            },
            {
                "type": "button",
                "name": _("Insert"),
                "helper": _("Insert"),  # + " (Ctrl+V)",
                "action": self.start_insert,
                "icon_name": "insert",
            },
            {
                "type": "button",
                "name": _("Crop"),
                "helper": _("Crop"),
                "action": self.crop_simple,
                "icon_name": "crop",
            },
            {"type": "separator"},
            {
                "type": "button",
                "name": _("Rectangle select"),
                "helper": _("Rectangle select"),
                "action": lambda: self.select_by_shape(shape="rectangle"),
                "icon_name": "rectangle_select",
            },
            {
                "type": "button",
                "name": _("Polygon select"),
                "helper": _("Polygon select"),
                "action": self.select_by_polygon,
                "icon_name": "polygon_select",
            },
            {
                "type": "button",
                "name": _("Fuzzy select"),
                "helper": _("Fuzzy select (limited select by color)"),
                "action": lambda: self.select_by_color(fill_limit=True),
                "icon_name": "fuzzy_select",
            },
            {
                "type": "button",
                "name": _("Select by color"),
                "helper": _("Select by color"),
                "action": lambda: self.select_by_color(),
                "icon_name": "select_by_color",
            },
            {
                "type": "button",
                "name": _("Deselect all"),
                "helper": _("Deselect all"),
                "action": self.remove_mask,
                "icon_name": "deselect_all",
            },
            # {"type": "separator"},
            # {
            #     "type": "button",
            #     "name": _("test"),
            #     "helper": _("test"),
            #     "action": None,
            #     "icon_name": "test",
            # },
        ]

        self.set_tools_docker(tools_list, 2)

        """Canvas"""
        self.canvas_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.canvas_frame.pack_propagate(False)
        self.canvas_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

        self.canvas_frame_main = ctk.CTkFrame(self.canvas_frame, fg_color="transparent")
        self.canvas_frame_main.pack_propagate(False)
        self.canvas_frame_main.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

        self.canvas_frame_right = ctk.CTkFrame(self.main_frame, fg_color="transparent", width=16)
        self.canvas_frame_right.pack(side=ctk.RIGHT, fill=ctk.Y)

        self.canvas_frame_rd = ctk.CTkFrame(self.canvas_frame_right, fg_color="transparent", width=16, height=16)
        self.canvas_frame_rd.pack(side=ctk.BOTTOM)

        self.v_scrollbar = ctk.CTkScrollbar(self.canvas_frame_right, orientation="vertical")
        self.v_scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y)

        self.h_scrollbar = ctk.CTkScrollbar(self.canvas_frame_main, orientation="horizontal")
        self.h_scrollbar.pack(side=ctk.BOTTOM, fill=ctk.X)

        # Canvas and canvas_parent must have equivalent top-left coordinate.
        self.canvas = ctk.CTkCanvas(
            self.canvas_frame_main, yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set
        )

        self.canvas.pack(side=ctk.TOP, anchor="center", expand=True)  # As in most drawing programs

        self.v_scrollbar.configure(command=self.v_scrollbar_command)
        self.h_scrollbar.configure(command=self.h_scrollbar_command)

        """Palette"""
        self.bottom_docker = ctk.CTkFrame(self, corner_radius=0)
        self.bottom_docker.pack(side=ctk.BOTTOM, fill=ctk.X)

        self.brush_palette = BrushPalette(
            self.bottom_docker,
            click_main_btn=self.main_color_choice,
            click_second_btn=self.second_color_choice,
            click_flip_btn=self.flip_brush_colors,
        )
        self.brush_palette.pack(side=ctk.LEFT, padx=2)

        self.palette_widget = ctk.CTkFrame(
            self.bottom_docker,
        )
        self.palette_widget.pack(side=ctk.LEFT, fill=ctk.X, padx=2, pady=2)

        self.standard_palettes = ["default", "4bit", "vintage", "seven"]
        if config.get("Brushshe", "palette") in self.standard_palettes:
            self.import_palette(resource(f"assets/palettes/{config.get('Brushshe', 'palette')}_palette.hex"))
        else:
            self.import_palette(resource(config.get("Brushshe", "palette")))

        self.size_button = ctk.CTkButton(self.bottom_docker, text="640x480", command=self.change_size)
        self.size_button.pack(side=ctk.RIGHT, padx=1)

        """ Initialization """
        # Max tail can not be more 4 MB = 1024 (width) x 1024 (height) x 4 (rgba).
        # canvas_tail_size: Max = 1024. Default = 128. Min = 16.
        self.canvas_tail_size = 128

        # If None - no crop, if set - need check out of crop.
        self.canvas_tails_area = None

        self.brush_color = "black"
        self.second_brush_color = "white"
        self.bg_color = "white"
        self.brush_shape = "circle"
        self.undo_stack = deque(maxlen=config.getint("Brushshe", "undo_levels"))
        self.redo_stack = deque(maxlen=config.getint("Brushshe", "undo_levels"))

        self.brush_size = 2
        self.eraser_size = 4
        self.spray_size = 10
        self.shape_size = 2
        self.sticker_size = 100
        self.font_size = 24
        self.zoom = 1
        self.selected_mask_img = None  # Can be gray_image or None

        self.is_brush_smoothing = config.getboolean("Brushshe", "smoothing")
        self.brush_smoothing_factor = config.getint("Brushshe", "brush_smoothing_factor")  # Between: 3..64
        self.brush_smoothing_quality = config.getint("Brushshe", "brush_smoothing_quality")  # Between: 1..64

        self.composer = BhComposer(0, 0)  # Empty init.

        self.new_picture(self.bg_color, first_time=True)
        self.brush()

        self.prev_x, self.prev_y = (None, None)
        self.current_font = "Open Sans"
        self.font_path = resource("assets/fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf")
        self.is_reset_settings_after_exiting = False
        self.current_file = None
        self.is_sticker_use_real_size = ctk.StringVar(value="off")

        self.canvas.bind("<Button-3>", self.eyedropper)

        self.canvas.bind("<Button-2>", self.begin_moving_canvas)
        self.canvas.bind("<B2-Motion>", self.continue_moving_canvas)

        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-y>", lambda e: self.redo())
        self.bind("<Control-s>", lambda e: self.save_to_gallery())

        # I changed the hotkeys because they don't work if the layout is not Latin,
        # and they are also intercepted when entering text
        self.bind("<Control-f>", lambda e: self.flip_brush_colors())
        self.bind("<Control-b>", lambda e: self.brush())
        self.bind("<Control-e>", lambda e: self.eraser())

        # Default zooming keys for mani painting programs.
        self.bind("<Key-equal>", lambda e: self.zoom_in(e))  # Key "=" -> ("+" without Shift)
        self.bind("<Key-minus>", lambda e: self.zoom_out(e))

        self.bind("<Key-bracketleft>", lambda e: self.change_tool_size_bind(e, -1))  # Key "["
        self.bind("<Key-bracketright>", lambda e: self.change_tool_size_bind(e, 1))  # Key "]"
        self.bind("<Key-braceleft>", lambda e: self.change_tool_size_bind(e, -10))  # Key "{"
        self.bind("<Key-braceright>", lambda e: self.change_tool_size_bind(e, 10))  # Key "}"

        self.bind("<Key>", self.key_handler)

        # Scroll on mouse
        # Windows OS
        self.canvas.bind("<MouseWheel>", self.scroll_on_canvasy)
        self.canvas.bind("<Shift-MouseWheel>", self.scroll_on_canvasx)
        # Linux OS
        self.canvas.bind("<Button-4>", self.scroll_on_canvasy)
        self.canvas.bind("<Button-5>", self.scroll_on_canvasy)
        self.canvas.bind("<Shift-Button-4>", self.scroll_on_canvasx)
        self.canvas.bind("<Shift-Button-5>", self.scroll_on_canvasx)

        # Resize window (and canvas)
        self.bind("<Configure>", self.on_window_resize)

        # Width and height of all sticker images - 88 px
        # Width and height of new sticker images - 512 px
        stickers_names = [
            "smile",
            "flower",
            "heart",
            "okay",
            "cheese",
            "face2",
            "cat",
            "alien",
            "like",
            "unicorn",
            "pineapple",
            "grass",
            "rain",
            "strawberry",
            "butterfly",
            "flower2",
        ]
        self.stickers = [Image.open(resource(f"assets/stickers/{name}.png")) for name in stickers_names]

        self.fonts_dict = {
            "Open Sans": "assets/fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf",
            "Monomakh": "assets/fonts/Monomakh/Monomakh-Regular.ttf",
            "Pacifico": "assets/fonts/Pacifico/Pacifico-Regular.ttf",
            "Comforter": "assets/fonts/Comforter/Comforter-Regular.ttf",
            "Rubik Bubbles": "assets/fonts/Rubik_Bubbles/RubikBubbles-Regular.ttf",
            "Press Start 2P": "assets/fonts/Press_Start_2P/PressStart2P-Regular.ttf",
        }
        self.fonts = list(self.fonts_dict.keys())

        self.update()  # Update interface before recalculate canvas.
        self.force_resize_canvas()
        self.update_canvas()

        if len(sys.argv) > 1:
            self.open_image(sys.argv[1])

    """ Functionality """

    # Keybinding without locale.
    def key_handler(self, event):
        if self.current_tool != "text":
            # Do not use with origin .bind() for equivalent key binds. Only or that, or this.

            # Debug
            # print(event.char, event.keycode, event.state)

            shift = True if event.state & 0x0001 else False
            ctrl = True if event.state & 0x0004 else False
            alt_l = True if event.state & 0x0008 else False
            alt_r = True if event.state & 0x0080 else False
            alt = True if (alt_l or alt_r) else False
            # All else modifiers was ignored.

            if shift is False and ctrl is False and alt is False and event.keycode == 53:  # Key-x
                self.flip_brush_colors()

            if shift is False and ctrl is False and alt is False and event.keycode == 56:  # Key-b
                self.brush()

            if shift is False and ctrl is False and alt is False and event.keycode == 26:  # Key-e
                self.eraser()

    def set_tools_docker(self, tools_list, columns=1):
        row = 0
        column = 0

        for tool in tools_list:
            if tool["type"] == "separator":
                column = 0
                row += 1
                s = ctk.CTkFrame(
                    self.tools_frame,
                    width=30,
                    height=4,
                )
                s.grid(column=column, row=row, pady=1, padx=1)
                row += 1
                continue

            tool_helper = tool["helper"]
            tool_command = tool["action"]
            tool_icon_name = tool["icon_name"]

            try:
                tool_icon = ctk.CTkImage(
                    light_image=Image.open(resource(f"icons/{tool_icon_name}_light.png")),
                    dark_image=Image.open(resource(f"icons/{tool_icon_name}_dark.png")),
                    size=(22, 22),
                )
            except Exception:
                # tool_icon = None
                tool_icon = ctk.CTkImage(
                    light_image=Image.open(resource("icons/not_found_light.png")),
                    dark_image=Image.open(resource("icons/not_found_dark.png")),
                    size=(22, 22),
                )

            tool_button = ctk.CTkButton(
                self.tools_frame, text=None, width=30, height=30, image=tool_icon, command=tool_command
            )
            tool_button.grid(column=column, row=row, pady=1, padx=1)
            Tooltip(tool_button, message=tool_helper)

            column += 1
            if column >= columns:
                column = 0
                row += 1

    def change_tool_size_bind(self, event=None, delta=1):
        new_size = self.get_tool_size() + delta
        max_sizes = {
            "brush": 50,
            "r-brush": 50,
            "eraser": 50,
            "shape": 50,
            "spray": 30,
            "sticker": 250,
            "text": 96,
            "insert": 500,
            "real size sticker": 500,
        }
        if new_size < 1:
            new_size = 1
        if new_size > max_sizes[self.current_tool]:
            new_size = max_sizes[self.current_tool]
        self.change_tool_size(new_size)
        self.tool_size_slider.set(int(new_size))

    def make_color_palette(self, colors):
        max_columns_in_row = 16

        if colors is None or len(colors) == 0:
            print("Wrong palette")
            return

        for child in self.palette_widget.winfo_children():
            child.destroy()

        ii = 0
        for color in colors:
            try:
                rgb = self.winfo_rgb(color)
                r = math.floor(rgb[0] / 256)
                g = math.floor(rgb[1] / 256)
                b = math.floor(rgb[2] / 256)
            except Exception:
                print("Warning: String `{}` is not correct color.".format(color))
                continue

            row = ii // max_columns_in_row
            column = ii % max_columns_in_row

            color_checked = "#{:02x}{:02x}{:02x}".format(r, g, b)

            tmp_btn = ctk.CTkButton(
                self.palette_widget,
                fg_color=color_checked,
                hover=False,
                text=None,
                width=24,
                height=24,
                border_width=1,
                corner_radius=1,
                command=lambda c=color_checked: self.change_color(c),
            )
            # tmp_btn.pack(side=ctk.LEFT, padx=1, pady=1)
            tmp_btn.grid(row=row, column=column, padx=1, pady=1)
            tmp_btn.bind("<Button-3>", lambda event, obj=tmp_btn: self.color_choice_bth(event, obj))
            tmp_btn.bind("<Double-Button-1>", lambda event, obj=tmp_btn: self.color_choice_bth(event, obj))

            ii += 1

    def v_scrollbar_command(self, a, b, c=None):
        self.canvas.yview(a, b, c)
        if self.canvas_tails_area is not None and self.get_canvas_tails_area() != self.canvas_tails_area:
            self.update_canvas()

    def h_scrollbar_command(self, a, b, c=None):
        self.canvas.xview(a, b, c)
        if self.canvas_tails_area is not None and self.get_canvas_tails_area() != self.canvas_tails_area:
            self.update_canvas()

    def on_window_resize(self, event):
        # Update canvas after any resize window.
        if self.zoom >= 1 and hasattr(self, "canvas"):
            self.update_canvas()

    def when_closing(self):
        if ImageChops.difference(self.saved_copy, self.image).getbbox() or self.saved_copy.size != self.image.size:
            closing_msg = CTkMessagebox(
                title=_("You are leaving Brushshe"),
                message=_("There are unsaved changes. Exit?"),
                option_1=_("Save"),
                option_2=_("No"),
                option_3=_("Yes"),
                icon=resource("icons/question.png"),
                icon_size=(100, 100),
                sound=True,
            )
            if closing_msg.get() == _("Save"):
                self.save_current()
            elif closing_msg.get() == _("Yes"):
                self.destroy_app()
        else:
            self.destroy_app()

    def destroy_app(self):
        if self.is_reset_settings_after_exiting:
            os.remove(config_file_path)
        self.destroy()

    def scroll_on_canvasy(self, event):
        if event.num == 5 or event.delta < 0:
            count = 1
        if event.num == 4 or event.delta > 0:
            count = -1
        self.canvas.yview_scroll(count, "units")
        if self.canvas_tails_area is not None and self.get_canvas_tails_area() != self.canvas_tails_area:
            self.update_canvas()

    def scroll_on_canvasx(self, event):
        if event.num == 5 or event.delta < 0:
            count = 1
        if event.num == 4 or event.delta > 0:
            count = -1
        self.canvas.xview_scroll(count, "units")
        if self.canvas_tails_area is not None and self.get_canvas_tails_area() != self.canvas_tails_area:
            self.update_canvas()

    def begin_moving_canvas(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def continue_moving_canvas(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        if self.canvas_tails_area is not None and self.get_canvas_tails_area() != self.canvas_tails_area:
            self.update_canvas()

    def zoom_in(self, event=None):
        self.canvas.delete("tools")

        if 1 < self.zoom < 2:  # Need if zoom not integer but more 1 and less 2
            self.zoom = 1
        if 1 <= self.zoom < 12:
            self.zoom += 1
        elif self.zoom < 1:
            self.zoom *= 2

        self.force_resize_canvas_with_correct()
        self.update_canvas()

    def zoom_out(self, event=None):
        self.canvas.delete("tools")

        if 1 < self.zoom:
            self.zoom -= 1
        elif 0.05 < self.zoom <= 1:  # Zooming limited down by 0.05.
            self.zoom /= 2

        self.force_resize_canvas_with_correct()
        self.update_canvas()

    def reset_zoom(self, event=None):
        self.canvas.delete("tools")

        self.zoom = 1

        self.force_resize_canvas_with_correct()
        self.update_canvas()

    def canvas_to_pict_xy(self, x, y):
        return self.canvas.canvasx(x) // self.zoom, self.canvas.canvasy(y) // self.zoom

    def canvas_to_pict_xy_f(self, x, y):
        return self.canvas.canvasx(x) / self.zoom, self.canvas.canvasy(y) / self.zoom

    def get_tool_main_color(self):
        if self.current_tool == "eraser":
            color = self.bg_color
            if self.image.mode == "RGBA":
                color = "#00000000"
        else:
            # For shape, etc.
            color = self.brush_color
            if self.image.mode == "RGBA":
                color = self.rgb_tuple_to_rgba_tuple(self.rgb_color_to_tuple(color), 255)
        return color

    def draw_line(self, x1, y1, x2, y2):
        color = self.get_tool_main_color()

        if self.selected_mask_img is None:
            bh_draw_line(self.draw, x1, y1, x2, y2, color, self.tool_size, self.brush_shape, self.current_tool)
        else:
            tmp_image = self.image.copy()
            tmp_draw = ImageDraw.Draw(tmp_image)
            bh_draw_line(tmp_draw, x1, y1, x2, y2, color, self.tool_size, self.brush_shape, self.current_tool)
            self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
            del tmp_image

    def update_canvas(self):
        # Debug
        # t1 = time.perf_counter(), time.process_time()

        # self._update_canvas()
        self._tailing_update_canvas()

        # Debug
        # t2 = time.perf_counter(), time.process_time()
        # print(f" Real time: {t2[0] - t1[0]:.6f} sec. CPU time: {t2[1] - t1[1]:.6f} sec")

    # def _update_canvas(self):
    #     # Please try not to cram into this function what can be moved to others.
    #     # This function is critical and its speed is important
    #     if self.zoom == 1:
    #         canvas_image = self.image
    #     else:
    #         canvas_image = self.image.resize(
    #             (int(self.image.width * self.zoom), int(self.image.height * self.zoom)), Image.BOX
    #         )
    #     self.img_tk = ImageTk.PhotoImage(canvas_image)
    #     self.canvas.itemconfig(self.canvas_image, image=self.img_tk)

    def _tailing_update_canvas(self):
        if self.zoom < 1:
            # https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-filters
            canvas_image = self.image.resize(
                (math.ceil(self.image.width * self.zoom), math.ceil(self.image.height * self.zoom)), Image.BOX
            )
            if self.selected_mask_img is None:
                mask_image = None
            else:
                mask_image = self.selected_mask_img.resize(
                    (
                        math.ceil(self.selected_mask_img.width * self.zoom),
                        math.ceil(self.selected_mask_img.height * self.zoom),
                    ),
                    Image.NEAREST,
                )

            self.composer.set_l_image(canvas_image)
            self.composer.set_mask_image(mask_image)

            compose_image = self.composer.get_compose_image(0, 0, canvas_image.width - 1, canvas_image.height - 1)

            self.img_tk = ImageTk.PhotoImage(compose_image)
            self.canvas.itemconfig(self.canvas_image, image=self.img_tk)
            self.canvas.moveto(self.canvas_image, 0, 0)
            self.canvas_tails_area = None

            return

        else:  # self.zoom > 1 or self.zoom = 1:
            # It work incorrect at this implementation for zoom < 1.

            cw_full = math.ceil(self.image.width * self.zoom)
            ch_full = math.ceil(self.image.height * self.zoom)

            (x1, y1, x2, y2) = self.get_canvas_tails_area()

            # Check, maybe the image all on canvas.
            if x1 == 0 and y1 == 0 and x2 == cw_full - 1 and y2 == ch_full - 1:
                x1_correct = 0
                y1_correct = 0
                dx = 0
                dy = 0
                tmp_canvas_image = self.image
                tmp_mask_image = self.selected_mask_img
            else:
                tiles_xy_on_image = (
                    math.floor(x1 / self.zoom),
                    math.floor(y1 / self.zoom),
                    math.floor(x2 / self.zoom) + 1,
                    math.floor(y2 / self.zoom) + 1,
                )

                # Subpixel correct.
                x1_correct = tiles_xy_on_image[0] * self.zoom
                y1_correct = tiles_xy_on_image[1] * self.zoom

                dx = math.floor(x1 - x1_correct)
                dy = math.floor(y1 - y1_correct)

                # # Debug
                # print((x1, y1, x2, y2), tiles_xy_on_image, (x1_correct, y1_correct), (dx, dy))

                tmp_canvas_image = self.image.crop(tiles_xy_on_image)
                if self.selected_mask_img is None:
                    tmp_mask_image = None
                else:
                    tmp_mask_image = self.selected_mask_img.crop(tiles_xy_on_image)

            r_w = math.floor(tmp_canvas_image.width * self.zoom)
            r_h = math.floor(tmp_canvas_image.height * self.zoom)
            if r_w < 1:
                r_w = 1
            if r_h < 1:
                r_h = 1

            canvas_image = tmp_canvas_image.resize((r_w, r_h), Image.NEAREST)
            if tmp_mask_image is None:
                mask_image = None
            else:
                mask_image = tmp_mask_image.resize((r_w, r_h), Image.NEAREST)

            self.composer.set_l_image(canvas_image)
            self.composer.set_mask_image(mask_image)

            compose_image = self.composer.get_compose_image(x1, y1, x2 + dx, y2 + dy)

            self.img_tk = ImageTk.PhotoImage(compose_image)
            self.canvas.itemconfig(self.canvas_image, image=self.img_tk)
            self.canvas.moveto(self.canvas_image, x1_correct, y1_correct)
            self.canvas_tails_area = (x1, y1, x2, y2)

            return

    def get_canvas_tails_area(self):
        cw_full = int(self.image.width * self.zoom)
        ch_full = int(self.image.height * self.zoom)

        # Set param canvas with real image size. Not use bbox in this place.
        self.canvas.config(scrollregion=(0, 0, cw_full, ch_full), width=cw_full, height=ch_full)

        iw, ih = self.image.size
        cx_frame_1, cx_frame_2 = self.canvas.xview()
        cy_frame_1, cy_frame_2 = self.canvas.yview()

        # Find the area without subpixel correct.
        x1 = math.floor(cx_frame_1 * cw_full / self.canvas_tail_size) * self.canvas_tail_size
        y1 = math.floor(cy_frame_1 * ch_full / self.canvas_tail_size) * self.canvas_tail_size
        x2 = math.ceil(cx_frame_2 * cw_full / self.canvas_tail_size) * self.canvas_tail_size - 1
        y2 = math.ceil(cy_frame_2 * ch_full / self.canvas_tail_size) * self.canvas_tail_size - 1
        if x2 > cw_full - 1:
            x2 = cw_full - 1
        if y2 > ch_full - 1:
            y2 = ch_full - 1

        return (x1, y1, x2, y2)

    def force_resize_canvas(self):
        cw_full = int(self.image.width * self.zoom)
        ch_full = int(self.image.height * self.zoom)

        # Scrollregion begin from the left part of first pixel and tail on the end part of last pixel.
        self.canvas.config(
            scrollregion=(0, 0, cw_full, ch_full),
            width=cw_full,
            height=ch_full,
        )

        self.size_button.configure(text=f"{self.image.width}x{self.image.height}")

    def force_resize_canvas_with_correct(self):
        wd_x_1 = self.canvas.winfo_x()
        wd_y_1 = self.canvas.winfo_y()

        cx_frame_1, cx_frame_2 = self.canvas.xview()
        cy_frame_1, cy_frame_2 = self.canvas.yview()
        dx_1 = (cx_frame_2 + cx_frame_1) / 2
        dy_1 = (cy_frame_2 + cy_frame_1) / 2

        self.force_resize_canvas()

        cx_frame_1, cx_frame_2 = self.canvas.xview()
        cy_frame_1, cy_frame_2 = self.canvas.yview()
        dx_2 = (cx_frame_2 + cx_frame_1) / 2
        dy_2 = (cy_frame_2 + cy_frame_1) / 2
        cw_full = int(self.image.width * self.zoom)
        ch_full = int(self.image.height * self.zoom)

        self.canvas.scan_mark(int(dx_1 * cw_full - wd_x_1), int(dy_1 * ch_full - wd_y_1))
        self.canvas.scan_dragto(int(dx_2 * cw_full), int(dy_2 * ch_full), gain=1)

    def crop_picture(self, x1, y1, x2, y2, event=None):
        new_width = x2 - x1
        new_height = y2 - y1

        if self.image.mode == "RGBA":
            new_image = Image.new("RGBA", (new_width, new_height), "#00000000")
            new_image.paste(self.image, (-x1, -y1), self.image)
        else:
            new_image = Image.new("RGB", (new_width, new_height), self.bg_color)
            new_image.paste(self.image, (-x1, -y1))
        self.image = new_image
        self.draw = ImageDraw.Draw(self.image)

        self.selected_mask_img = None

        self.force_resize_canvas()
        self.update_canvas()

        self.undo_stack.append(self.image.copy())

    def eyedropper(self, event):
        # Get the coordinates of the click event
        x, y = self.canvas_to_pict_xy(event.x, event.y)

        color = self.image.getpixel((x, y))
        self.obtained_color = "#{:02x}{:02x}{:02x}".format(*color)

        self.brush_color = self.obtained_color
        self.brush_palette.main_color = self.obtained_color

    def start_fill(self):  # beta
        self.set_tool("fill", "Fill", None, None, None, "cross")
        self.canvas.bind("<Button-1>", self.fill)

    def fill(self, event):
        x, y = self.canvas_to_pict_xy(event.x, event.y)

        if self.selected_mask_img is None:
            tmp_image = self.image
        else:
            tmp_image = self.image.copy()

        if self.image.mode == "RGBA":
            ImageDraw.floodfill(
                tmp_image,
                (x, y),
                self.rgb_tuple_to_rgba_tuple(ImageColor.getrgb(self.brush_color), 255),
            )
        else:
            ImageDraw.floodfill(tmp_image, (x, y), ImageColor.getrgb(self.brush_color))

        if self.selected_mask_img is None:
            pass
        else:
            self.image.paste(tmp_image, (0, 0), self.selected_mask_img)

        del tmp_image

        self.update_canvas()
        self.undo_stack.append(self.image.copy())

    def open_from_file(self):
        dialog = FileDialog(self, title=_("Open from file"))
        if dialog.path:
            self.open_image(dialog.path)

    def open_from_url(self):
        dialog = ctk.CTkInputDialog(text=_("Enter URL:"), title=_("Open from URL"))
        image_url = dialog.get_input()
        if image_url is not None:
            try:
                with urlopen(image_url) as response:
                    image_data = BytesIO(response.read())
                    self.open_image(image_data)
            except Exception as e:
                self.open_file_error(e)

    def save_current(self):
        if self.current_file is not None:
            try:
                self.image.save(self.current_file)
                self.saved_copy = self.image.copy()
                CTkMessagebox(
                    title=_("Saved"),
                    message=_("Changes to your existing picture have been saved successfully!"),
                    icon=resource("icons/saved.png"),
                    icon_size=(100, 100),
                    sound=True,
                )
            except Exception as e:
                self.save_file_error(e)
        else:
            self.save_as()

    def save_as(self):
        dialog = FileDialog(self, title=_("Save to device"), save=True)
        if dialog.path:
            try:
                self.image.save(dialog.path)
                self.saved_copy = self.image.copy()
                CTkMessagebox(
                    title=_("Saved"),
                    message=_("The picture has been successfully saved to your device in format")
                    + f" {dialog.extension}!",
                    icon=resource("icons/saved.png"),
                    icon_size=(100, 100),
                    sound=True,
                )
                self.current_file = dialog.path
                self.title(os.path.basename(self.current_file) + " - " + _("Brushshe"))
            except Exception as e:
                self.save_file_error(e)

    def save_file_error(self, e):
        CTkMessagebox(
            title=_("Oh, unfortunately, it happened"),
            message=f"{_('Error - cannot save file:')} {e}",
            icon=resource("icons/cry.png"),
            icon_size=(100, 100),
            sound=True,
        )

    def other_bg_color(self):
        askcolor = AskColor(title=_("Choose a different background color"), initial_color="#ffffff")
        obtained_bg_color = askcolor.get()
        if obtained_bg_color:
            self.new_picture(obtained_bg_color)

    def show_stickers_choice(self):
        def sticker_from_file():
            dialog = FileDialog(sticker_choose, title=_("Sticker from file"))
            if dialog.path:
                try:
                    sticker_image = Image.open(dialog.path)
                    self.set_current_sticker(sticker_image)
                except Exception as e:
                    self.open_file_error(e)

        def sticker_from_url():
            dialog = ctk.CTkInputDialog(text=_("Enter URL:"), title=_("Open from URL"))
            image_url = dialog.get_input()
            if image_url is not None:
                try:
                    with urlopen(image_url) as response:
                        image_data = BytesIO(response.read())
                        sticker_image = Image.open(image_data)
                        self.set_current_sticker(sticker_image)
                except Exception as e:
                    self.open_file_error(e)

        def tabview_callback():
            if tabview.get() == _("From file"):
                sticker_from_file()
            elif tabview.get() == _("From URL"):
                sticker_from_url()
            tabview.set(_("From set"))

        sticker_choose = ctk.CTkToplevel(self)
        sticker_choose.geometry("370x500")
        sticker_choose.title(_("Choose a sticker"))

        tabview = ctk.CTkTabview(sticker_choose, command=tabview_callback)
        tabview.add(_("From set"))
        tabview.add(_("From file"))
        tabview.add(_("From URL"))
        tabview.set(_("From set"))
        tabview.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        stickers_scrollable_frame = ctk.CTkScrollableFrame(tabview.tab(_("From set")))
        stickers_scrollable_frame.pack(fill=ctk.BOTH, expand=True)

        stickers_frame = ctk.CTkFrame(stickers_scrollable_frame)
        stickers_frame.pack()

        row = 0
        column = 0
        for sticker_image in self.stickers:
            sticker_ctkimage = ctk.CTkImage(sticker_image, size=(100, 100))
            ctk.CTkButton(
                stickers_frame,
                text=None,
                image=sticker_ctkimage,
                command=lambda img=sticker_image: self.set_current_sticker(img),
            ).grid(row=row, column=column, padx=10, pady=10)
            column += 1
            if column == 2:
                column = 0
                row += 1

    def set_current_sticker(self, sticker_image=None):  # Choose a sticker
        if sticker_image:
            self.last_sticker_image = sticker_image

        if self.is_sticker_use_real_size.get() == "off":
            self.set_tool("sticker", "Stickers", self.sticker_size, 10, 250, "cross")
            self.insert_simple(self.last_sticker_image)
        else:
            self.set_tool("real size sticker", "Stickers", 100, 1, 500, "cross")
            self.insert_simple(self.last_sticker_image)

    def text_tool(self):
        def add_text(event):
            self.draw.text((self.text_x, self.text_y), self.tx_entry.get(), fill=self.brush_color, font=self.imagefont)
            self.update_canvas()
            self.undo_stack.append(self.image.copy())

        def draw_text_halo(event):
            self.canvas.delete("tools")

            x, y = self.canvas_to_pict_xy(event.x, event.y)
            self.imagefont = ImageFont.truetype(self.font_path, self.tool_size)

            bbox = self.draw.textbbox((0, 0), self.tx_entry.get(), font=self.imagefont)

            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            self.text_x = x - text_width // 2 - bbox[0]
            self.text_y = y - text_height // 2 - bbox[1]

            self.canvas.create_rectangle(
                (x - text_width // 2) * self.zoom,
                (y - text_height // 2) * self.zoom,
                (x + text_width // 2) * self.zoom,
                (y + text_height // 2) * self.zoom,
                outline="white",
                width=1,
                tag="tools",
            )

            self.canvas.create_rectangle(
                (x - text_width // 2) * self.zoom,
                (y - text_height // 2) * self.zoom,
                (x + text_width // 2) * self.zoom,
                (y + text_height // 2) * self.zoom,
                outline="black",
                width=1,
                tag="tools",
                dash=(5, 5),
            )

        def leave(event):
            self.canvas.delete("tools")

        self.set_tool("text", "Text", self.font_size, 11, 96, "cross")
        self.canvas.bind("<Button-1>", add_text)
        self.canvas.bind("<Motion>", draw_text_halo)
        self.canvas.bind("<Leave>", leave)

    def font_optionmenu_callback(self, value):
        self.current_font = value
        self.font_path = resource(self.fonts_dict.get(value))
        self.imagefont = ImageFont.truetype(self.font_path, self.tool_size)

    def show_frame_choice(self):
        def on_frames_click(index):
            selected_frame = frames[index]
            resized_frame = selected_frame.resize((self.image.width, self.image.height))

            self.image.paste(resized_frame, (0, 0), resized_frame)

            self.update_canvas()
            self.undo_stack.append(self.image.copy())

        frames_win = ctk.CTkToplevel(self)
        frames_win.title(_("Frames"))

        frames_names = [
            "frame1",
            "frame2",
            "frame3",
            "frame4",
            "frame5",
            "frame6",
            "frame7",
        ]
        frames_thumbnails = [
            ctk.CTkImage(
                Image.open(resource(f"assets/frames_preview/{name}.png")),
                size=(100, 100),
            )
            for name in frames_names
        ]

        frames = [Image.open(resource(f"assets/frames/{name}.png")) for name in frames_names]

        row = 0
        column = 0

        for i, image in enumerate(frames_thumbnails):
            ctk.CTkButton(frames_win, text=None, image=image, command=lambda i=i: on_frames_click(i)).grid(
                column=column, row=row, padx=10, pady=10
            )
            column += 1
            if column == 2:
                column = 0
                row += 1

    # Shape creation functions
    def create_shape(self, shape):
        x_begin, y_begin = None, None

        def start_shape(event):
            nonlocal x_begin, y_begin

            self.shape_x, self.shape_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            x_begin, y_begin = self.canvas_to_pict_xy(event.x, event.y)
            self.get_contrast_color()

            shape_methods = {
                "Rectangle": self.canvas.create_rectangle,
                "Oval": self.canvas.create_oval,
                "Line": self.canvas.create_line,
                "Fill rectangle": self.canvas.create_rectangle,
                "Fill oval": self.canvas.create_oval,
            }

            create_method = shape_methods.get(shape)
            if create_method:
                param = "fill" if shape == "Line" else "outline"
                self.shape_id = create_method(
                    self.shape_x, self.shape_y, self.shape_x, self.shape_y, **{param: self.contrast_color}
                )

        def draw_shape(event):
            if not hasattr(self, "shape_x"):
                return
            x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self.canvas.coords(self.shape_id, self.shape_x, self.shape_y, x, y)

        def end_shape(event):
            nonlocal x_begin, y_begin

            if not hasattr(self, "shape_x"):
                return

            x_end, y_end = self.canvas_to_pict_xy(event.x, event.y)

            if x_begin < x_end:
                x0, x1 = x_begin, x_end
            else:
                x0, x1 = x_end, x_begin
            if y_begin < y_end:
                y0, y1 = y_begin, y_end
            else:
                y0, y1 = y_end, y_begin

            if self.selected_mask_img is None:
                tmp_draw = ImageDraw.Draw(self.image)
            else:
                tmp_image = self.image.copy()
                tmp_draw = ImageDraw.Draw(tmp_image)

            color = self.get_tool_main_color()

            if shape == "Rectangle":
                tmp_draw.rectangle([x0, y0, x1, y1], outline=self.brush_color, width=self.tool_size)
            elif shape == "Oval":
                tmp_draw.ellipse([x0, y0, x1, y1], outline=self.brush_color, width=self.tool_size)
            elif shape == "Line":
                # self.draw_line(x_begin, y_begin, x_end, y_end)
                bh_draw_line(
                    tmp_draw, x_begin, y_begin, x_end, y_end, color, self.tool_size, self.brush_shape, self.current_tool
                )
            elif shape == "Fill rectangle":
                tmp_draw.rectangle([x0, y0, x1, y1], fill=self.brush_color)
            elif shape == "Fill oval":
                tmp_draw.ellipse([x0, y0, x1, y1], fill=self.brush_color)
            else:
                print("Warning: Incorrect shape.")

            if self.selected_mask_img is None:
                pass
            else:
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
                del tmp_image

            self.update_canvas()
            self.undo_stack.append(self.image.copy())

            # Removing unnecessary variables for normal selection of the next shape in the menu
            #   and disabling other side effects.
            del self.shape_x, self.shape_y
            self.canvas.delete(self.shape_id)

        if shape == "Fill rectangle" or shape == "Fill oval":
            self.set_tool("shape", shape, None, None, None, "cross")
        else:
            self.set_tool("shape", shape, self.shape_size, 1, 50, "cross")

        self.canvas.bind("<ButtonPress-1>", start_shape)
        self.canvas.bind("<B1-Motion>", draw_shape)
        self.canvas.bind("<ButtonRelease-1>", end_shape)

    def bezier_shape(self):
        # Simple 4th point (cubic) Bezier curve.

        canvas_points = []
        image_points = []
        bezier_id = None

        # Clear canvas.
        self.update_canvas()

        def start(event):
            nonlocal canvas_points, image_points, bezier_id

            if len(canvas_points) == 0:
                self.get_contrast_color()

                cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

                canvas_points.append((cx, cy))
                image_points.append(self.canvas_to_pict_xy(event.x, event.y))

                bezier_id = self.canvas.create_line(
                    cx, cy, cx, cy, fill=self.contrast_color, tag="tools"
                )  # smooth="bezier"

        def drawing(event):
            nonlocal canvas_points, bezier_id

            if bezier_id is None or len(canvas_points) == 0:
                return

            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            len_p = len(canvas_points)
            canvas_points_tmp = canvas_points.copy()

            if len_p <= 1:
                canvas_points_tmp.append((cx, cy))
            else:
                canvas_points_tmp.append(canvas_points_tmp[len_p - 1])
                canvas_points_tmp[len_p - 1] = (cx, cy)

            ts = [t / 32.0 for t in range(33)]  # 32 lines for preview.
            b = make_bezier(canvas_points_tmp)
            points = b(ts)

            # Do 2d array flat for canvas.coords
            points_flat = [j for sub in points for j in sub]

            self.canvas.coords(bezier_id, *points_flat)

        def end(event):
            nonlocal canvas_points, image_points, bezier_id

            if bezier_id is None or len(canvas_points) == 0:
                return

            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            px, py = self.canvas_to_pict_xy(event.x, event.y)
            len_p = len(canvas_points)
            stop = False

            if len_p <= 1:
                canvas_points.append((cx, cy))
                image_points.append((px, py))
            else:
                tx, ty = canvas_points[len_p - 2]

                if cx == tx and cy == ty and len_p > 2:
                    stop = True
                else:
                    canvas_points.append(canvas_points[len_p - 1])
                    canvas_points[len_p - 1] = (cx, cy)

                    len_ip = len(image_points)
                    image_points.append(image_points[len_ip - 1])
                    image_points[len_ip - 1] = (px, py)

            # Finish
            if len(canvas_points) >= 4 or stop:
                # Calculate segments count.
                max_segments = 0
                points_len = len(image_points)
                for ii, ip in enumerate(image_points):
                    if ii < points_len - 1:
                        max_segments += max(
                            abs(image_points[ii][0] - image_points[ii + 1][0]),
                            abs(image_points[ii][1] - image_points[ii + 1][1]),
                        )
                max_segments = max_segments // 3
                if max_segments < 32:
                    max_segments = 32

                # Draw on picture.
                ts = [t / max_segments for t in range(int(max_segments + 1))]
                b = make_bezier(image_points)
                points = b(ts)
                points_len = len(points)

                color = self.get_tool_main_color()

                if self.selected_mask_img is None:
                    tmp_image = self.image
                    tmp_draw = ImageDraw.Draw(tmp_image)
                else:
                    tmp_image = self.image.copy()
                    tmp_draw = ImageDraw.Draw(tmp_image)

                for it, tt in enumerate(points):
                    if it < points_len - 1:
                        bh_draw_line(
                            tmp_draw,
                            int(points[it][0]),
                            int(points[it][1]),
                            int(points[it + 1][0]),
                            int(points[it + 1][1]),
                            color,
                            self.tool_size,
                            self.brush_shape,
                            self.current_tool,
                        )

                if self.selected_mask_img is None:
                    pass
                else:
                    self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
                    del tmp_image

                self.canvas.delete(bezier_id)
                self.update_canvas()
                self.undo_stack.append(self.image.copy())

                # Reset nonlocal variables.
                canvas_points = []
                image_points = []
                bezier_id = None

        self.set_tool("shape", "Bezier", self.shape_size, 1, 50, "cross")

        self.canvas.bind("<ButtonPress-1>", start)
        self.canvas.bind("<B1-Motion>", drawing)
        self.canvas.bind("<ButtonRelease-1>", end)
        self.canvas.bind("<Motion>", drawing)

    def recoloring_brush(self):
        self.set_tool("r-brush", "R. Brush", self.brush_size, 1, 50, "pencil")

        prev_x = None
        prev_y = None
        point_history = None

        def drawing(event):
            nonlocal prev_x, prev_y, point_history

            if self.is_brush_smoothing is False:
                x, y = self.canvas_to_pict_xy(event.x, event.y)
            else:
                if point_history is None:
                    point_history = BhHistory(limit_length=self.brush_smoothing_factor)
                xf, yf = self.canvas_to_pict_xy_f(event.x, event.y)
                point_history.add_point(BhPoint(x=xf, y=yf, pressure=1.0))
                s_point = point_history.get_smoothing_point(
                    self.brush_smoothing_factor,
                    self.brush_smoothing_quality,
                )
                if s_point is not None:
                    x = int(s_point.x)
                    y = int(s_point.y)
                else:
                    x, y = self.canvas_to_pict_xy(event.x, event.y)

            if prev_x is None:
                prev_x, prev_y = x, y

            draw_recoloring_brush(x, y, prev_x, prev_y)
            prev_x, prev_y = x, y

            self.update_canvas()  # force=False  # Do not delete tools shapes.
            draw_brush_halo(x, y)

        def end(event):
            nonlocal prev_x, prev_y, point_history

            if prev_x is None:
                return

            self.canvas.delete("tools")
            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_brush_halo(x, y)

            point_history = None
            prev_x, prev_y = (None, None)
            self.undo_stack.append(self.image.copy())

        def move(event):
            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_brush_halo(x, y)

        def draw_recoloring_brush(x1, y1, x2, y2):
            color_to = ImageColor.getrgb(self.brush_color)
            color_from = ImageColor.getrgb(self.second_brush_color)

            # FIXME: In current time it works only for 100% opacity color.
            if self.image.mode == "RGBA":
                color_from = self.rgb_tuple_to_rgba_tuple(color_from, 255)
                color_to = self.rgb_tuple_to_rgba_tuple(color_to, 255)

            if self.selected_mask_img is None:
                bh_draw_recoloring_line(self.image, x1, y1, x2, y2, color_from, color_to, self.tool_size)
            else:
                tmp_image = self.image.copy()
                bh_draw_recoloring_line(tmp_image, x1, y1, x2, y2, color_from, color_to, self.tool_size)
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
                del tmp_image

        def draw_brush_halo(x, y):
            self.canvas.delete("tools")

            d1 = (self.tool_size - 1) // 2
            d2 = self.tool_size // 2

            self.canvas.create_rectangle(
                int((x - d1) * self.zoom - 1),
                int((y - d1) * self.zoom - 1),
                int((x + d2 + 1) * self.zoom),
                int((y + d2 + 1) * self.zoom),
                outline="white",
                width=1,
                tag="tools",
            )
            self.canvas.create_rectangle(
                int((x - d1) * self.zoom),
                int((y - d1) * self.zoom),
                int((x + d2 + 1) * self.zoom - 1),
                int((y + d2 + 1) * self.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
            )

        def leave(event):
            self.canvas.delete("tools")

        self.canvas.bind("<Button-1>", drawing)
        self.canvas.bind("<B1-Motion>", drawing)
        self.canvas.bind("<ButtonRelease-1>", end)
        self.canvas.bind("<Motion>", move)
        self.canvas.bind("<Leave>", leave)

    def copy_tool(self, deleted=False):
        if self.selected_mask_img is None:
            self.copy_simple(deleted)
        else:
            self.copy_selected(deleted)

    def copy_selected(self, deleted=False):
        if self.selected_mask_img is None:
            return

        tmp_bg_color = (0, 0, 0, 0)
        tmp_img_mask = self.selected_mask_img
        tmp_img = Image.new("RGBA", (self.image.width, self.image.height), tmp_bg_color)
        tmp_img.paste(self.image, (0, 0), tmp_img_mask)

        # Trim image.
        bg = Image.new(tmp_img.mode, tmp_img.size, tmp_bg_color)
        diff = ImageChops.difference(tmp_img, bg)
        # diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()

        if bbox:
            self.buffer_local = tmp_img.crop(bbox)
        else:
            self.buffer_local = tmp_img

        del tmp_img

        if deleted:
            bg_color = self.bg_color
            if self.image.mode == "RGBA":
                bg_color = (0, 0, 0, 0)
            tmp_img = Image.new(self.image.mode, (self.image.width, self.image.height), bg_color)
            self.image.paste(tmp_img, (0, 0), tmp_img_mask)
            del tmp_img
            self.undo_stack.append(self.image.copy())

        self.update_canvas()

    def copy_simple(self, deleted=False):
        if deleted is False:
            self.set_tool("copy", "Copy", None, None, None, "cross")
        else:
            self.set_tool("cut", "Cut", None, None, None, "cross")

        x_begin = None
        y_begin = None
        x_end = None
        y_end = None

        def selecting(event):
            nonlocal x_begin, y_begin, x_end, y_end

            x, y = self.canvas_to_pict_xy(event.x, event.y)

            if x_begin is None or y_begin is None:
                x_begin = x
                y_begin = y

            x_end = x
            y_end = y

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            if x_begin < 0:
                x_begin = 0
            if x_begin > x_max:
                x_begin = x_max
            if y_begin < 0:
                y_begin = 0
            if y_begin > y_max:
                y_begin = y_max
            if x_end < 0:
                x_end = 0
            if x_end > x_max:
                x_end = x_max
            if y_end < 0:
                y_end = 0
            if y_end > y_max:
                y_end = y_max

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            draw_tool(x1, y1, x2, y2)

        def select_end(event):
            nonlocal x_begin, y_begin, x_end, y_end

            if x_begin is None or y_begin is None:
                return

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            self.canvas.delete("tools")

            x_begin = None
            y_begin = None
            x_end = None
            y_end = None

            # INFO: Float. From begin first pixel to end last pixel (begin last+1 pixel).
            #       One first pixel look like (0, 0, 1, 1).
            self.buffer_local = self.image.crop((x1, y1, x2 + 1, y2 + 1))

            if deleted is not False:
                if self.image.mode != "RGBA":
                    ImageDraw.Draw(self.image).rectangle(
                        (x1, y1, x2, y2),
                        fill=self.bg_color,
                        outline=self.bg_color,
                    )
                else:
                    ImageDraw.Draw(self.image).rectangle(
                        (x1, y1, x2, y2),
                        fill="#00000000",
                        outline="#00000000",
                    )
                self.undo_stack.append(self.image.copy())  # Need only for cut.

            self.update_canvas()

        def draw_tool(x1, y1, x2, y2):
            self.canvas.delete("tools")

            self.canvas.create_rectangle(
                int(x1 * self.zoom),
                int(y1 * self.zoom),
                int((x2 + 1) * self.zoom - 1),
                int((y2 + 1) * self.zoom - 1),
                outline="white",
                width=1,
                tag="tools",
            )
            self.canvas.create_rectangle(
                int(x1 * self.zoom),
                int(y1 * self.zoom),
                int((x2 + 1) * self.zoom - 1),
                int((y2 + 1) * self.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
                dash=(5, 5),
            )

        self.canvas.bind("<Button-1>", selecting)
        self.canvas.bind("<B1-Motion>", selecting)
        self.canvas.bind("<ButtonRelease-1>", select_end)

    def start_insert(self):
        if hasattr(self, "buffer_local") is False or self.buffer_local is None:
            return
        self.set_tool("insert", "Insert", 100, 1, 500, "cross")
        self.insert_simple(self.buffer_local)

    def insert_simple(self, insert_image=None):
        image_tmp = insert_image
        current_zoom = None
        image_tmp_view = None
        image_tk = None
        x1, y1 = None, None

        def move(event):
            nonlocal image_tmp, image_tmp_view, image_tk, current_zoom, x1, y1

            if self.current_tool == "sticker":
                it_width = self.tool_size
                it_height = int(insert_image.height * self.tool_size / insert_image.width)
                resampling = Image.BICUBIC
            else:
                it_width = int(insert_image.width / 100 * self.tool_size)
                it_height = int(insert_image.height / 100 * self.tool_size)
                if it_width <= 1 or it_height <= 1:
                    it_width, it_height = (1, 1)
                resampling = Image.NEAREST
            image_tmp = insert_image.resize((it_width, it_height), resampling)

            x, y = self.canvas_to_pict_xy(event.x, event.y)

            x1 = int(x - (it_width - 1) / 2)
            y1 = int(y - (it_height - 1) / 2)
            x2 = int(x1 + it_width - 1)
            y2 = int(y1 + it_height - 1)

            image_tmp_view = image_tmp.resize((int(it_width * self.zoom), int(it_height * self.zoom)), Image.BOX)
            image_tk = ImageTk.PhotoImage(image_tmp_view)
            current_zoom = self.zoom

            draw_tool(x1, y1, x2, y2)

        def insert_end(event):
            nonlocal image_tmp, x1, y1

            if x1 is None or y1 is None:
                return

            if image_tmp.mode == "RGBA":
                self.image.paste(image_tmp, (x1, y1), image_tmp)
            else:
                self.image.paste(image_tmp, (x1, y1))

            self.update_canvas()
            self.undo_stack.append(self.image.copy())

        def leave(event):
            self.canvas.delete("tools")

        def draw_tool(x1, y1, x2, y2):
            nonlocal image_tk

            self.canvas.delete("tools")

            self.canvas.create_image(
                int(x1 * self.zoom),
                int(y1 * self.zoom),
                image=image_tk,
                tag="tools",
                anchor="nw",
            )

            self.canvas.create_rectangle(
                int(x1 * self.zoom),
                int(y1 * self.zoom),
                int((x2 + 1) * self.zoom - 1),
                int((y2 + 1) * self.zoom - 1),
                outline="white",
                width=1,
                tag="tools",
            )
            self.canvas.create_rectangle(
                int(x1 * self.zoom),
                int(y1 * self.zoom),
                int((x2 + 1) * self.zoom - 1),
                int((y2 + 1) * self.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
                dash=(5, 5),
            )

        self.canvas.bind("<ButtonRelease-1>", insert_end)
        self.canvas.bind("<Motion>", move)
        self.canvas.bind("<Leave>", leave)

    def crop_simple(self):
        self.set_tool("crop", "Crop", None, None, None, "cross")

        x_begin = None
        y_begin = None
        x_end = None
        y_end = None

        def cropping(event):
            nonlocal x_begin, y_begin, x_end, y_end

            x, y = self.canvas_to_pict_xy(event.x, event.y)

            if x_begin is None or y_begin is None:
                x_begin = x
                y_begin = y

            x_end = x
            y_end = y
            x_max = self.image.width - 1
            y_max = self.image.height - 1

            if x_begin < 0:
                x_begin = 0
            if x_begin > x_max:
                x_begin = x_max
            if y_begin < 0:
                y_begin = 0
            if y_begin > y_max:
                y_begin = y_max
            if x_end < 0:
                x_end = 0
            if x_end > x_max:
                x_end = x_max
            if y_end < 0:
                y_end = 0
            if y_end > y_max:
                y_end = y_max

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            draw_tool(x1, y1, x2, y2)

        def crop_end(event):
            nonlocal x_begin, y_begin, x_end, y_end

            if x_begin is None or y_begin is None:
                return

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            self.canvas.delete("tools")

            x_begin = None
            y_begin = None
            x_end = None
            y_end = None

            self.crop_picture(math.floor(x1), math.floor(y1), math.ceil(x2) + 1, math.ceil(y2) + 1)

            # Remove mask if exist.
            # TODO: Continue...
            self.selected_mask_img = None

            self.update_canvas()

        def draw_tool(x1, y1, x2, y2):
            self.canvas.delete("tools")

            self.canvas.create_rectangle(
                int(x1 * self.zoom),
                int(y1 * self.zoom),
                int((x2 + 1) * self.zoom - 1),
                int((y2 + 1) * self.zoom - 1),
                outline="yellow",
                width=1,
                tag="tools",
            )
            self.canvas.create_rectangle(
                int(x1 * self.zoom),
                int(y1 * self.zoom),
                int((x2 + 1) * self.zoom - 1),
                int((y2 + 1) * self.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
                dash=(2, 2),
            )

        self.canvas.bind("<Button-1>", cropping)
        self.canvas.bind("<B1-Motion>", cropping)
        self.canvas.bind("<ButtonRelease-1>", crop_end)

    def effects(self):
        def set_effects_area_copy():
            nonlocal area_copy
            if effects_area.get() == 1:
                area_copy = image_copy
            else:
                area_copy = buffer_local_copy

        def post_actions(result):
            if effects_area.get() == 1:
                self.image = result
                self.update_canvas()
                self.draw = ImageDraw.Draw(self.image)
                self.undo_stack.append(self.image.copy())
            else:
                self.buffer_local = result

        def blur():
            radius = blur_slider.get()
            result = area_copy.filter(ImageFilter.GaussianBlur(radius=radius))
            post_actions(result)

        def detail():
            factor = detail_slider.get()
            enhancer = ImageEnhance.Sharpness(area_copy)
            result = enhancer.enhance(factor)
            post_actions(result)

        def contour():
            result = area_copy.filter(ImageFilter.CONTOUR)
            post_actions(result)

        def grayscale():
            result = ImageOps.grayscale(area_copy)
            post_actions(result)

        def mirror():
            result = ImageOps.mirror(area_copy)
            post_actions(result)

        def metal():
            result = area_copy.filter(ImageFilter.EMBOSS)
            post_actions(result)

        def inversion():
            result = ImageOps.invert(area_copy)
            post_actions(result)

        effects_win = ctk.CTkToplevel(self)
        effects_win.title(_("Effects"))
        effects_win.geometry("250x500")

        effects_area = ctk.IntVar(value=1)
        whole_image_radiobutton = ctk.CTkRadioButton(
            effects_win, text=_("Whole image"), command=set_effects_area_copy, variable=effects_area, value=1
        )
        whole_image_radiobutton.pack(padx=10, pady=10)
        copied_area_radiobutton = ctk.CTkRadioButton(
            effects_win, text=_("Copied area"), command=set_effects_area_copy, variable=effects_area, value=2
        )
        copied_area_radiobutton.pack(padx=10, pady=10)

        if hasattr(self, "buffer_local") is False or self.buffer_local is None:
            copied_area_radiobutton.configure(state="disabled")

        effects_frame = ctk.CTkScrollableFrame(effects_win)
        effects_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkButton(
            effects_win,
            text=_("Remove all effects"),
            command=lambda: post_actions(area_copy),
            fg_color="red",
            text_color="white",
        ).pack(padx=10, pady=10)

        # Blur
        blur_frame = ctk.CTkFrame(effects_frame)
        blur_frame.pack(padx=10, pady=10)

        ctk.CTkLabel(blur_frame, text=_("Blur")).pack(padx=10, pady=10)

        blur_slider = ctk.CTkSlider(blur_frame, from_=0, to=20)
        blur_slider.pack(padx=10, pady=10)

        ctk.CTkButton(blur_frame, text=_("Apply"), command=blur).pack(padx=10, pady=10)

        # Detail
        detail_frame = ctk.CTkFrame(effects_frame)
        detail_frame.pack(padx=10, pady=10)

        ctk.CTkLabel(detail_frame, text=_("Detail")).pack(padx=10, pady=10)

        detail_slider = ctk.CTkSlider(detail_frame, from_=1, to=20)
        detail_slider.pack(padx=10, pady=10)

        ctk.CTkButton(detail_frame, text=_("Apply"), command=detail).pack(padx=10, pady=10)

        effects_dict = {  # dictionary for effects which without slider
            "Contour": contour,
            "Grayscale": grayscale,
            "Mirror": mirror,
            "Metal": metal,
            "Inversion": inversion,
        }

        for effect_name, effect_command in effects_dict.items():
            effect_frame = ctk.CTkFrame(effects_frame)
            effect_frame.pack(padx=10, pady=10)

            ctk.CTkLabel(effect_frame, text=_(effect_name)).pack(padx=10, pady=10)

            ctk.CTkButton(effect_frame, text=_("Apply"), command=effect_command).pack(padx=10, pady=10)

        image_copy = self.image.copy()

        if hasattr(self, "buffer_local") and self.buffer_local is not None:
            buffer_local_copy = self.buffer_local.copy()

        area_copy = None
        set_effects_area_copy()

        effects_win.grab_set()  # Disable main window

    def about_program(self):
        about_text = _(
            "Brushshe is a painting program where you can create whatever you like.\n\n"
            "An eagle named Brucklin is its mascot.\n\n"
        )
        about_msg = CTkMessagebox(
            title=_("About program"),
            message=about_text + self.version_full,
            icon=resource("icons/brucklin.png"),
            icon_size=(150, 191),
            option_1="OK",
            option_2="GitHub",
            height=400,
        )
        if about_msg.get() == "GitHub":
            webbrowser.open(r"https://github.com/limafresh/Brushshe")

    def new_picture(self, color="#FFFFFF", mode="RGB", first_time=False):
        self.canvas.delete("tools")
        self.bg_color = color

        self.image = Image.new(mode, (640, 480), color)
        self.saved_copy = self.image.copy()
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        if first_time:
            self.img_tk = ImageTk.PhotoImage(self.image)
            self.canvas_image = self.canvas.create_image(0, 0, anchor=ctk.NW, image=self.img_tk)
        else:
            pass

        self.selected_mask_img = None

        self.force_resize_canvas()
        self.update_canvas()

        self.undo_stack.append(self.image.copy())
        self.title(_("Unnamed") + " - " + _("Brushshe"))
        self.current_file = None

    def change_tool_size(self, value):
        self.tool_size = int(value)
        if self.current_tool == "brush" or self.current_tool == "r-brush":
            self.brush_size = int(value)
        elif self.current_tool == "eraser":
            self.eraser_size = int(value)
        elif self.current_tool == "spray":
            self.spray_size = int(value)
        elif self.current_tool == "shape":
            self.shape_size = int(value)
        elif self.current_tool == "sticker":
            self.sticker_size = int(value)
        elif self.current_tool == "text":
            self.font_size = int(value)
        if self.current_tool in ["insert", "real size sticker"]:
            self.tool_size_label.configure(text=f"{self.tool_size} %")
        else:
            self.tool_size_label.configure(text=self.tool_size)
        self.tool_size_tooltip.configure(message=self.tool_size)

    def get_tool_size(self):
        res = self.tool_size
        if self.current_tool == "brush" or self.current_tool == "r-brush":
            res = self.brush_size
        elif self.current_tool == "eraser":
            res = self.eraser_size
        elif self.current_tool == "spray":
            res = self.spray_size
        elif self.current_tool == "shape":
            res = self.shape_size
        elif self.current_tool == "sticker":
            res = self.sticker_size
        elif self.current_tool == "text":
            res = self.font_size
        return res

    def brush(self, type="brush"):
        prev_x = None
        prev_y = None
        point_history = None

        if type == "brush":
            self.set_tool("brush", "Brush", self.brush_size, 1, 50, "pencil")
        elif type == "eraser":
            self.set_tool("eraser", "Eraser", self.eraser_size, 1, 50, "target")
        else:
            print("Warning: Incorrect brush type. Set default as.")
            self.set_tool("brush", "Brush", self.brush_size, 1, 50, "pencil")

        def paint(event):
            nonlocal prev_x, prev_y, point_history

            if self.is_brush_smoothing is False:
                x, y = self.canvas_to_pict_xy(event.x, event.y)
            else:
                if point_history is None:
                    point_history = BhHistory(limit_length=self.brush_smoothing_factor)
                xf, yf = self.canvas_to_pict_xy_f(event.x, event.y)
                point_history.add_point(BhPoint(x=xf, y=yf, pressure=1.0))
                s_point = point_history.get_smoothing_point(
                    self.brush_smoothing_factor,
                    self.brush_smoothing_quality,
                )
                if s_point is not None:
                    x = int(s_point.x)
                    y = int(s_point.y)
                else:
                    x, y = self.canvas_to_pict_xy(event.x, event.y)

            if prev_x is not None and prev_y is not None:
                self.draw_line(prev_x, prev_y, x, y)
            else:
                self.draw_line(x, y, x, y)

            prev_x, prev_y = x, y

            self.update_canvas()
            draw_brush_halo(x, y)

        def stop_paint(event):
            nonlocal prev_x, prev_y, point_history

            if prev_x is None:
                return

            self.canvas.delete("tools")
            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_brush_halo(x, y)

            point_history = None
            prev_x, prev_y = (None, None)
            self.undo_stack.append(self.image.copy())

        def move(event):
            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_brush_halo(x, y)

        def draw_brush_halo(x, y):
            self.canvas.delete("tools")

            d1 = (self.tool_size - 1) // 2
            d2 = self.tool_size // 2

            # TODO: Need use the pixel perfect halo for zoom >= 2 if it doesn't too slow.

            if self.brush_shape == "circle":
                canvas_create_shape = self.canvas.create_oval
            elif self.brush_shape == "square":
                canvas_create_shape = self.canvas.create_rectangle

            canvas_create_shape(
                int((x - d1) * self.zoom - 1),
                int((y - d1) * self.zoom - 1),
                int((x + d2 + 1) * self.zoom),
                int((y + d2 + 1) * self.zoom),
                outline="white",
                width=1,
                tag="tools",
            )
            canvas_create_shape(
                int((x - d1) * self.zoom),
                int((y - d1) * self.zoom),
                int((x + d2 + 1) * self.zoom - 1),
                int((y + d2 + 1) * self.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
            )

        def leave(event):
            self.canvas.delete("tools")

        self.canvas.bind("<Button-1>", paint)
        self.canvas.bind("<B1-Motion>", paint)
        self.canvas.bind("<ButtonRelease-1>", stop_paint)
        self.canvas.bind("<Motion>", move)
        self.canvas.bind("<Leave>", leave)

    def eraser(self):
        self.brush(type="eraser")

    def spray(self):
        def start_spray(event):
            self.prev_x, self.prev_y = self.canvas_to_pict_xy(event.x, event.y)
            self.spraying = True
            do_spray()

        def do_spray():
            if not self.spraying or self.prev_x is None or self.prev_y is None:
                return

            if self.selected_mask_img is None:
                tmp_image = self.image
                tmp_draw = ImageDraw.Draw(tmp_image)
            else:
                tmp_image = self.image.copy()
                tmp_draw = ImageDraw.Draw(tmp_image)

            for i in range(self.tool_size * 2):
                offset_x = random.randint(-self.tool_size, self.tool_size)
                offset_y = random.randint(-self.tool_size, self.tool_size)
                if offset_x**2 + offset_y**2 <= self.tool_size**2:
                    tmp_draw.point((self.prev_x + offset_x, self.prev_y + offset_y), fill=self.brush_color)

            if self.selected_mask_img is None:
                pass
            else:
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)

            del tmp_image

            self.update_canvas()
            self.spray_job = self.after(50, do_spray)

        def move_spray(event):
            self.prev_x, self.prev_y = self.canvas_to_pict_xy(event.x, event.y)

        def stop_spray(event):
            self.spraying = False
            if self.spray_job:
                self.after_cancel(self.spray_job)
                self.spray_job = None
            self.prev_x, self.prev_y = (None, None)
            self.undo_stack.append(self.image.copy())

        self.set_tool("spray", "Spray", self.spray_size, 5, 30, "spraycan")

        self.spraying = False
        self.spray_job = None
        self.canvas.bind("<Button-1>", start_spray)
        self.canvas.bind("<B1-Motion>", move_spray)
        self.canvas.bind("<ButtonRelease-1>", stop_spray)

    # TODO: Add selected_mask_img on history with type `mask`.
    # FIXME: Need add length synchronization undo_stack and redo_stack (actually it must be one stack).
    def undo(self):
        if len(self.undo_stack) > 1:
            tmp_image = self.undo_stack.pop()
            is_resize = False
            if self.image.width != tmp_image.width or self.image.height != tmp_image.height:
                is_resize = True
            self.redo_stack.append(tmp_image)
            self.image = self.undo_stack[-1].copy()
            self.draw = ImageDraw.Draw(self.image)
            if is_resize:
                self.selected_mask_img = None
                self.force_resize_canvas()
            self.update_canvas()

    def redo(self):
        if len(self.redo_stack) > 0:
            tmp_image = self.redo_stack.pop().copy()
            is_resize = False
            if self.image.width != tmp_image.width or self.image.height != tmp_image.height:
                is_resize = True
            self.image = tmp_image
            self.undo_stack.append(self.image.copy())
            self.draw = ImageDraw.Draw(self.image)
            if is_resize:
                self.selected_mask_img = None
                self.force_resize_canvas()
            self.update_canvas()

    def save_to_gallery(self):
        file_path = gallery.gallery_folder / f"{uuid4()}.png"
        while file_path.exists():
            file_path = gallery.gallery_folder / f"{uuid4()}.png"
        self.image.save(file_path)
        self.saved_copy = self.image.copy()

        self.current_file = str(file_path)
        self.title(os.path.basename(self.current_file) + " - " + _("Brushshe"))

        CTkMessagebox(
            title=_("Saved"),
            message=_('The picture has been successfully saved to the gallery ("My Gallery" in the menu at the top)!'),
            icon=resource("icons/saved.png"),
            icon_size=(100, 100),
            sound=True,
        )

    def change_color(self, new_color):
        self.brush_color = new_color
        self.brush_palette.main_color = self.brush_color

    def main_color_choice(self):
        askcolor = AskColor(title=_("Color select"), initial_color=self.brush_color)
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            self.brush_color = self.obtained_color
            self.brush_palette.main_color = self.obtained_color

    def second_color_choice(self):
        askcolor = AskColor(title=_("Color select"), initial_color=self.second_brush_color)
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            self.second_brush_color = self.obtained_color
            self.brush_palette.second_color = self.obtained_color

    def color_choice_bth(self, event, btn):
        askcolor = AskColor(title=_("Color select"), initial_color=btn.cget("fg_color"))
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            btn.configure(
                fg_color=self.obtained_color,
                hover_color=self.obtained_color,
                command=lambda c=self.obtained_color: self.change_color(c),
            )
            self.brush_color = self.obtained_color
            self.brush_palette.main_color = self.obtained_color

    def flip_brush_colors(self):
        self.brush_color = self.brush_palette.second_color
        self.second_brush_color = self.brush_palette.main_color

        self.brush_palette.main_color = self.brush_color
        self.brush_palette.second_color = self.second_brush_color

    def open_image(self, openimage):
        try:
            self.bg_color = "white"
            self.image = Image.open(openimage)
            self.saved_copy = self.image.copy()
            self.picture_postconfigure()

            self.selected_mask_img = None

            if not isinstance(openimage, BytesIO):
                self.current_file = openimage
                self.title(os.path.basename(self.current_file) + " - " + _("Brushshe"))
            else:
                self.title(_("Unnamed") + " - " + _("Brushshe"))
                self.current_file = None
        except Exception as e:
            self.open_file_error(e)

    def open_file_error(self, e):
        CTkMessagebox(
            title=_("Oh, unfortunately, it happened"),
            message=f"{_('Error - cannot open file:')} {e}",
            icon=resource("icons/cry.png"),
            icon_size=(100, 100),
            sound=True,
        )

    def get_contrast_color(self):
        stat = ImageStat.Stat(self.image)
        r, g, b = stat.mean[:3]
        self.contrast_color = "#232323" if (r + g + b) / 3 > 127 else "#e8e8e8"

    def rotate(self, degree):
        rotated_image = self.image.rotate(degree, expand=True)
        self.image = rotated_image
        self.picture_postconfigure()

    def create_screenshot(self):
        self.withdraw()
        self.iconify()
        self.after(200)
        self.image = ImageGrab.grab()
        self.deiconify()
        self.picture_postconfigure()

    def remove_white_background(self):
        transparent_bg_img = self.image.convert("RGBA")
        datas = transparent_bg_img.getdata()

        new_data = []
        for item in datas:
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                new_data.append((0, 0, 0, 0))  # Lines with zeroes compressed better.
            else:
                new_data.append(item)

        transparent_bg_img.putdata(new_data)
        self.image = transparent_bg_img
        self.picture_postconfigure()

    def picture_postconfigure(self):
        self.canvas.delete("tools")

        self.draw = ImageDraw.Draw(self.image)

        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        self.force_resize_canvas()
        self.update_canvas()

        self.undo_stack.append(self.image.copy())

    def set_tool(self, tool, tool_name, tool_size, from_, to, cursor):
        self.current_tool = tool

        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<Shift-Button-1>")
        self.canvas.unbind("<Control-Button-1>")
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<Leave>")
        self.canvas.unbind("<BackSpace>")
        self.canvas.unbind("<Return>")

        for child in self.tool_config_docker.winfo_children():
            child.destroy()

        self.tool_label = ctk.CTkLabel(self.tool_config_docker, text=None)
        self.tool_label.pack(side=ctk.LEFT, padx=1)

        self.tool_size_slider = ctk.CTkSlider(self.tool_config_docker, command=self.change_tool_size)
        self.tool_size_slider.pack(side=ctk.LEFT, padx=1)
        self.tool_size_tooltip = Tooltip(self.tool_size_slider)
        self.tool_size_label = ctk.CTkLabel(self.tool_config_docker, text=None)
        self.tool_size_label.pack(side=ctk.LEFT, padx=5)

        if tool_size is None and from_ is None and to is None:
            self.tool_label.configure(text=_(tool_name))
            self.tool_size_slider.pack_forget()
            self.tool_size_label.pack_forget()
        else:
            self.tool_label.configure(text=_(tool_name) + ":")
            self.tool_size = tool_size
            self.tool_size_slider.configure(from_=from_, to=to)
            self.tool_size_slider.set(self.tool_size)
            self.tool_size_slider.pack(side=ctk.LEFT, padx=1)
            if self.current_tool in ["insert", "real size sticker"]:
                self.tool_size_label.configure(text=f"{self.tool_size} %")
            else:
                self.tool_size_label.configure(text=self.tool_size)
            self.tool_size_label.pack(side=ctk.LEFT, padx=5)
            self.tool_size_tooltip.configure(message=self.tool_size)

        if self.current_tool in ["brush", "eraser"]:
            brush_shape_btn = ctk.CTkSegmentedButton(
                self.tool_config_docker, values=["●", "■"], command=self.brush_shape_btn_callback
            )
            if self.brush_shape == "circle":
                brush_shape_btn.set("●")
            elif self.brush_shape == "square":
                brush_shape_btn.set("■")
            brush_shape_btn.pack(side=ctk.LEFT, padx=5)
        elif self.current_tool == "text":
            self.tx_entry = ctk.CTkEntry(self.tool_config_docker, placeholder_text=_("Enter text..."))
            self.tx_entry.pack(side=ctk.LEFT, padx=5)

            font_optionmenu = ctk.CTkOptionMenu(
                self.tool_config_docker,
                values=self.fonts,
                dynamic_resizing=False,
                command=self.font_optionmenu_callback,
            )
            font_optionmenu.set(self.current_font)
            font_optionmenu.pack(side=ctk.LEFT, padx=1)
        elif self.current_tool == "sticker" or self.current_tool == "real size sticker":
            ctk.CTkCheckBox(
                self.tool_config_docker,
                text=_("Use real size"),
                variable=self.is_sticker_use_real_size,
                onvalue="on",
                offvalue="off",
                command=self.set_current_sticker,
            ).pack(side=ctk.LEFT, padx=5)

        self.canvas.configure(cursor=cursor)
        self.canvas.delete("tools")

    def change_size(self):
        def size_sb_callback(value):
            if value == _("Crop"):
                ready_size_button.configure(command=crop)
            elif value == _("Scale"):
                ready_size_button.configure(command=scale)
            else:
                print("Oops")

        def crop():
            try:
                if aspect_ratio_var.get() == "on":
                    new_height = int(self.image.height * width_spinbox.get() / self.image.width)
                else:
                    new_height = int(height_spinbox.get())

                if int(width_spinbox.get()) > 2000 or new_height > 2000:
                    continue_size_msg = CTkMessagebox(
                        title=_("The new size will be too big"),
                        message=_("Drawing will be slow") + " " + _("Continue?"),
                        icon=resource("icons/question.png"),
                        icon_size=(100, 100),
                        option_1=_("No"),
                        option_2=_("Yes"),
                        sound=True,
                    )
                    if continue_size_msg.get() == _("Yes"):
                        self.crop_picture(0, 0, int(width_spinbox.get()), new_height)
                else:
                    self.crop_picture(0, 0, int(width_spinbox.get()), new_height)
            except Exception as e:
                print(e)

        def scale():
            try:
                if aspect_ratio_var.get() == "on":
                    new_height = int(self.image.height * width_spinbox.get() / self.image.width)
                else:
                    new_height = int(height_spinbox.get())

                if int(width_spinbox.get()) > 2000 or new_height > 2000:
                    continue_size_msg = CTkMessagebox(
                        title=_("The new size will be too big"),
                        message=_("Drawing will be slow") + " " + _("Continue?"),
                        icon=resource("icons/question.png"),
                        icon_size=(100, 100),
                        option_1=_("No"),
                        option_2=_("Yes"),
                        sound=True,
                    )
                    if continue_size_msg.get() == _("Yes"):
                        scaled_image = self.image.resize((int(width_spinbox.get()), new_height), Image.NEAREST)
                        self.image = scaled_image
                        self.picture_postconfigure()
                else:
                    scaled_image = self.image.resize((int(width_spinbox.get()), new_height), Image.NEAREST)
                    self.image = scaled_image
                    self.picture_postconfigure()
            except Exception as e:
                print(e)

        change_size_toplevel = ctk.CTkToplevel(self)
        change_size_toplevel.title(_("Change size..."))
        change_size_toplevel.transient(self)

        size_sb = ctk.CTkSegmentedButton(change_size_toplevel, values=[_("Crop"), _("Scale")], command=size_sb_callback)
        size_sb.pack(padx=10, pady=10)
        size_sb.set(_("Crop"))

        width_height_frame = ctk.CTkFrame(change_size_toplevel)
        width_height_frame.pack(padx=10, pady=10)

        ctk.CTkLabel(width_height_frame, text=_("Width")).grid(row=1, column=1, padx=10, pady=10)
        width_spinbox = IntSpinbox(width_height_frame, width=150)
        width_spinbox.grid(row=2, column=1, padx=10, pady=10)
        width_spinbox.set(self.image.width)

        ctk.CTkLabel(width_height_frame, text=_("Height")).grid(row=1, column=2, padx=10, pady=10)
        height_spinbox = IntSpinbox(width_height_frame, width=150)
        height_spinbox.grid(row=2, column=2, padx=10, pady=10)
        height_spinbox.set(self.image.height)

        aspect_ratio_var = ctk.StringVar(value="on")
        ctk.CTkCheckBox(
            change_size_toplevel,
            text=_("Maintain aspect ratio"),
            variable=aspect_ratio_var,
            onvalue="on",
            offvalue="off",
        ).pack(padx=10, pady=10)

        ready_size_button = ctk.CTkButton(change_size_toplevel, text="OK", command=crop)
        ready_size_button.pack(padx=10, pady=10)

    def settings(self):
        def change_theme():
            ctk.set_appearance_mode(theme_var.get())
            config.set("Brushshe", "theme", theme_var.get())
            write_config()

        def change_undo_levels():
            self.undo_stack = deque(self.undo_stack, maxlen=undo_levels_spinbox.get())
            self.redo_stack = deque(self.redo_stack, maxlen=undo_levels_spinbox.get())
            config.set("Brushshe", "undo_levels", str(undo_levels_spinbox.get()))
            write_config()

        def smooth_switch_event():
            self.is_brush_smoothing = smooth_var.get()
            config.set("Brushshe", "smoothing", str(self.is_brush_smoothing))
            write_config()

        def brush_smoothing_factor_event(event):
            self.brush_smoothing_factor = brush_smoothing_factor_var.get()
            config.set("Brushshe", "brush_smoothing_factor", str(self.brush_smoothing_factor))
            write_config()

        def brush_smoothing_quality_event(event):
            self.brush_smoothing_quality = brush_smoothing_quality_var.get()
            config.set("Brushshe", "brush_smoothing_quality", str(self.brush_smoothing_quality))
            write_config()

        def palette_radiobutton_callback():
            self.import_palette(resource(f"assets/palettes/{palette_var.get()}_palette.hex"))
            config.set("Brushshe", "palette", palette_var.get())
            write_config()

        settings_tl = ctk.CTkToplevel(self)
        settings_tl.geometry("400x650")
        settings_tl.title(_("Settings"))
        settings_tl.transient(self)

        settings_frame = ctk.CTkScrollableFrame(settings_tl, fg_color="transparent")
        settings_frame.pack(padx=10, pady=10, fill="both", expand=True)

        theme_frame = ctk.CTkFrame(settings_frame)
        theme_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(theme_frame, text=_("Theme")).pack(padx=10, pady=10)

        theme_var = ctk.StringVar(value=config.get("Brushshe", "theme"))
        for theme_name in ["System", "Light", "Dark"]:
            ctk.CTkRadioButton(
                theme_frame,
                text=_(theme_name),
                variable=theme_var,
                value=theme_name,
                command=change_theme,
            ).pack(padx=10, pady=10)

        undo_levels_frame = ctk.CTkFrame(settings_frame)
        undo_levels_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(undo_levels_frame, text=_("Maximum undo/redo levels")).pack(padx=10, pady=10)

        undo_levels_spinbox = IntSpinbox(undo_levels_frame, width=150)
        undo_levels_spinbox.pack(padx=10, pady=10)
        undo_levels_spinbox.set(self.undo_stack.maxlen)

        ctk.CTkButton(undo_levels_frame, text=_("Apply"), command=change_undo_levels).pack(padx=10, pady=10)

        smooth_frame = ctk.CTkFrame(settings_frame)
        smooth_frame.pack(padx=10, pady=10, fill="x")

        smooth_var = ctk.BooleanVar(value=self.is_brush_smoothing)
        ctk.CTkSwitch(
            smooth_frame,
            text=_("Smoothing for brush/eraser"),
            variable=smooth_var,
            onvalue=True,
            offvalue=False,
            command=smooth_switch_event,
        ).pack(padx=10, pady=10)

        ctk.CTkLabel(smooth_frame, text=_("Brush smoothing quality")).pack(padx=10, pady=10)
        brush_smoothing_quality_var = ctk.IntVar(value=self.brush_smoothing_quality)
        ctk.CTkSlider(
            smooth_frame,
            variable=brush_smoothing_quality_var,
            command=brush_smoothing_quality_event,
            from_=1,
            to=64,
        ).pack(padx=10, pady=10)

        ctk.CTkLabel(smooth_frame, text=_("Brush smoothing factor (weight)")).pack(padx=10, pady=1)
        brush_smoothing_factor_var = ctk.IntVar(value=self.brush_smoothing_factor)
        ctk.CTkSlider(
            smooth_frame,
            variable=brush_smoothing_factor_var,
            command=brush_smoothing_factor_event,
            from_=3,
            to=64,
        ).pack(padx=10, pady=10)

        palette_frame = ctk.CTkFrame(settings_frame)
        palette_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(palette_frame, text=_("Palette")).pack(padx=10, pady=10)

        palette_var = ctk.StringVar(value=config.get("Brushshe", "palette"))
        for palette_name in self.standard_palettes:
            ctk.CTkRadioButton(
                palette_frame,
                text=_(palette_name.capitalize()),
                variable=palette_var,
                value=palette_name,
                command=palette_radiobutton_callback,
            ).pack(padx=10, pady=10)

        check_new_version_frame = ctk.CTkFrame(settings_frame)
        check_new_version_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkButton(
            check_new_version_frame,
            text=f"{_('Check new versions (yours is')} {self.version_full})",
            command=lambda: webbrowser.open(r"https://github.com/limafresh/Brushshe/releases"),
        ).pack(padx=10, pady=10)

    def import_palette(self, value=None):
        if value is None:
            dialog = FileDialog(
                self,
                title=_("Import palette from .hex file"),
            )

            if dialog.path is None or dialog.path == "":
                return

            palette_path = dialog.path
            config.set("Brushshe", "palette", palette_path)
            write_config()
        else:
            palette_path = value

        colors = []

        try:
            with open(palette_path) as f:
                lines = f.readlines()
                for line in lines:
                    if len(line) == 0:
                        continue

                    color = line.strip()
                    if line[0] != "#":
                        color = "#" + color
                    try:
                        self.winfo_rgb(color)
                    except Exception:
                        print("Warning: String `{}` is not correct color.".format(color))
                        continue
                    colors.append(color)
        except FileNotFoundError:
            return
        except Exception:
            print("Incorrect file format?")
            return

        self.make_color_palette(colors)

    def reset_settings_after_exiting(self):
        self.is_reset_settings_after_exiting = True

    def brush_shape_btn_callback(self, value):
        if value == "●":
            self.brush_shape = "circle"
        elif value == "■":
            self.brush_shape = "square"

    def paste_image_from_clipboard(self):
        try:
            pasted_img = ImageGrab.grabclipboard()
            self.bg_color = "white"
            self.image = pasted_img
            self.picture_postconfigure()
        except Exception as e:
            CTkMessagebox(
                title=_("Oh, unfortunately, it happened"),
                message=f"{_('Error - cannot paste image:')} {e}",
                icon=resource("icons/cry.png"),
                icon_size=(100, 100),
                sound=True,
            )

    def rgb_color_to_tuple(self, color):
        try:
            rgb = self.winfo_rgb(color)
            r = math.floor(rgb[0] / 256)
            g = math.floor(rgb[1] / 256)
            b = math.floor(rgb[2] / 256)
        except Exception:
            return (0, 0, 0)
        return (r, g, b)

    def rgb_tuple_to_rgba_tuple(self, color, alpha: int):
        try:
            res = (color[0], color[1], color[2], alpha)
        except Exception:
            print("Error: Wrong color.")
            res = (0, 0, 0, 0)
        return res

    def select_init_mask(self):
        if self.composer is None:
            return

        if self.selected_mask_img is None:
            self.selected_mask_img = Image.new("L", (self.image.width, self.image.height), "white")

        if self.selected_mask_img.width != self.image.width or self.selected_mask_img.height != self.image.height:
            self.selected_mask_img = Image.new("L", (self.image.width, self.image.height), "white")

    def remove_mask(self):
        self.selected_mask_img = None
        self.composer.mask_img = None
        self.update_canvas()

    def invert_mask(self):
        self.select_init_mask()

        tmp_mask_img = ImageOps.invert(self.selected_mask_img)
        self.selected_mask_img = tmp_mask_img
        del tmp_mask_img

        self.update_canvas()

    def select_by_shape(self, shape="rectangle"):
        self.set_tool("select", "Select", None, None, None, "cross")

        x_begin = None
        y_begin = None
        x_end = None
        y_end = None
        _mode = "replace"

        def selecting(event, mode):
            nonlocal x_begin, y_begin, x_end, y_end, _mode

            if mode is not None:
                _mode = mode
            self.select_init_mask()

            x, y = self.canvas_to_pict_xy(event.x, event.y)

            if x_begin is None or y_begin is None:
                x_begin = x
                y_begin = y

            x_end = x
            y_end = y

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            if x_begin < 0:
                x_begin = 0
            if x_begin > x_max:
                x_begin = x_max
            if y_begin < 0:
                y_begin = 0
            if y_begin > y_max:
                y_begin = y_max
            if x_end < 0:
                x_end = 0
            if x_end > x_max:
                x_end = x_max
            if y_end < 0:
                y_end = 0
            if y_end > y_max:
                y_end = y_max

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            draw_tool(x1, y1, x2, y2)

        def select_end(event):
            nonlocal x_begin, y_begin, x_end, y_end, _mode

            if x_begin is None or y_begin is None:
                return

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            self.canvas.delete("tools")

            x_begin = None
            y_begin = None
            x_end = None
            y_end = None

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            draw = ImageDraw.Draw(self.selected_mask_img)

            if _mode == "replace":
                draw.rectangle([0, 0, x_max, y_max], fill="black")

            if _mode == "subtract":
                draw.rectangle([x1, y1, x2, y2], fill="black")
            else:  # add or replace
                draw.rectangle([x1, y1, x2, y2], fill="white")

            self.update_canvas()

        def draw_tool(x1, y1, x2, y2):
            self.canvas.delete("tools")

            self.canvas.create_rectangle(
                int(x1 * self.zoom),
                int(y1 * self.zoom),
                int((x2 + 1) * self.zoom - 1),
                int((y2 + 1) * self.zoom - 1),
                outline="white",
                width=1,
                tag="tools",
            )
            self.canvas.create_rectangle(
                int(x1 * self.zoom),
                int(y1 * self.zoom),
                int((x2 + 1) * self.zoom - 1),
                int((y2 + 1) * self.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
                dash=(5, 5),
            )

        self.canvas.bind("<Button-1>", lambda e: selecting(e, "replace"))
        self.canvas.bind("<Shift-Button-1>", lambda e: selecting(e, "add"))
        self.canvas.bind("<Control-Button-1>", lambda e: selecting(e, "subtract"))
        self.canvas.bind("<B1-Motion>", lambda e: selecting(e, None))
        self.canvas.bind("<ButtonRelease-1>", select_end)

    def select_by_polygon(self):
        self.set_tool("select", "Select", None, None, None, "cross")

        xy_list = None
        _mode = "replace"
        delta = 5

        def selecting(event, mode, type="click"):
            nonlocal xy_list, _mode

            self.canvas.focus_set()  # For the key binding.

            if mode is not None:
                _mode = mode
            if type == "click":
                self.select_init_mask()

            x, y = self.canvas_to_pict_xy(event.x, event.y)
            x = int(x)
            y = int(y)

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            if x < 0:
                x = 0
            if x > x_max:
                x = x_max
            if y < 0:
                y = 0
            if y > y_max:
                y = y_max

            if type == "unclick":
                if xy_list is None:
                    xy_list = []

                xy_len = len(xy_list)
                if (
                    xy_len >= 4
                    and xy_list[0] - delta < x < xy_list[0] + delta
                    and xy_list[1] - delta < y < xy_list[1] + delta
                ):
                    xy_list.append(xy_list[0])
                    xy_list.append(xy_list[1])
                    select_end(event)
                    return

                xy_list.append(x)
                xy_list.append(y)

            draw_tool(x, y)

        def select_end(event):
            nonlocal xy_list, _mode

            if xy_list is None:
                return

            self.canvas.delete("tools")

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            draw = ImageDraw.Draw(self.selected_mask_img)

            if _mode == "replace":
                draw.rectangle([0, 0, x_max, y_max], fill="black")

            if _mode == "subtract":
                draw.polygon(xy_list, fill="black")
            else:  # add or replace
                draw.polygon(xy_list, fill="white")

            xy_list = None

            self.update_canvas()

        def key_backspace(event):
            nonlocal xy_list

            if xy_list is None:
                return

            xy_len = len(xy_list)
            if xy_len >= 4:
                del xy_list[-1]
                del xy_list[-1]

                xy_len = len(xy_list)
                draw_tool(xy_list[xy_len - 2], xy_list[xy_len - 1])

        def key_enter(event):
            nonlocal xy_list

            if xy_list is None:
                return

            if len(xy_list) >= 4:
                select_end(event)

        def draw_tool(x, y):
            nonlocal xy_list, _mode

            self.canvas.delete("tools")

            if xy_list is None or 0 == len(xy_list):
                x_begin = x
                y_begin = y
            else:
                xy_len = len(xy_list)
                x_begin = xy_list[0]
                y_begin = xy_list[1]
                self.canvas.create_line(
                    int(xy_list[xy_len - 2] * self.zoom),
                    int(xy_list[xy_len - 1] * self.zoom),
                    int(x * self.zoom),
                    int(y * self.zoom),
                    fill="black",
                    width=1,
                    tag="tools",
                )
                self.canvas.create_line(
                    int(xy_list[xy_len - 2] * self.zoom),
                    int(xy_list[xy_len - 1] * self.zoom),
                    int(x * self.zoom),
                    int(y * self.zoom),
                    fill="white",
                    width=1,
                    tag="tools",
                    dash=(5, 5),
                )
                if xy_len >= 4:
                    tmp_xy_list = [int(x * self.zoom) for x in xy_list]
                    self.canvas.create_line(tmp_xy_list, fill="black", width=1, tag="tools")
                    self.canvas.create_line(tmp_xy_list, fill="white", width=1, tag="tools", dash=(5, 5))

            self.canvas.create_rectangle(
                int(x_begin * self.zoom + delta),
                int(y_begin * self.zoom + delta),
                int(x_begin * self.zoom - delta),
                int(y_begin * self.zoom - delta),
                outline="black",
                fill="white",
                width=1,
                tag="tools",
            )

        self.canvas.bind("<Button-1>", lambda e: selecting(e, "replace"))
        self.canvas.bind("<Shift-Button-1>", lambda e: selecting(e, "add"))
        self.canvas.bind("<Control-Button-1>", lambda e: selecting(e, "subtract"))
        self.canvas.bind("<B1-Motion>", lambda e: selecting(e, None, "moving"))
        self.canvas.bind("<Motion>", lambda e: selecting(e, None, "moving"))
        self.canvas.bind("<ButtonRelease-1>", lambda e: selecting(e, None, "unclick"))
        self.canvas.bind("<BackSpace>", key_backspace)
        self.canvas.bind("<Return>", key_enter)

    def _color_diff(self, color1: float | tuple[int, ...], color2: float | tuple[int, ...]) -> float:
        first = color1 if isinstance(color1, tuple) else (color1,)
        second = color2 if isinstance(color2, tuple) else (color2,)
        return sum(abs(first[i] - second[i]) for i in range(len(second)))

    def select_by_color(self, fill_limit=False):
        self.set_tool("select_by_color", "Select by color", None, None, None, "dotbox")

        _mode = "replace"
        thresh = 1

        def selecting(event, mode):
            nonlocal _mode

            self.canvas.focus_set()

            if mode is not None:
                _mode = mode

            self.select_init_mask()

            x, y = self.canvas_to_pict_xy(event.x, event.y)
            x = int(x)
            y = int(y)

            x_max = self.image.width - 1
            y_max = self.image.height - 1

            if x < 0:
                x = 0
            if x > x_max:
                x = x_max
            if y < 0:
                y = 0
            if y > y_max:
                y = y_max

            draw = ImageDraw.Draw(self.selected_mask_img)

            if _mode == "replace":
                draw.rectangle([0, 0, x_max, y_max], fill=0)

            if _mode == "subtract":
                fill_color = 0
            else:  # add or replace
                fill_color = 255

            if not fill_limit:
                pixels_mask = self.selected_mask_img.load()
                pixels_image = self.image.load()

                assert pixels_image is not None

                try:
                    background = pixels_image[x, y]
                except (ValueError, IndexError):
                    return

                for ii in range(x_max + 1):
                    for jj in range(y_max + 1):
                        try:
                            p = pixels_image[ii, jj]
                            if self._color_diff(p, background) <= thresh:
                                pixels_mask[ii, jj] = fill_color
                        except (ValueError, IndexError):
                            pass
            else:
                self._floodfill_mask(self.image, self.selected_mask_img, (x, y), fill_color)

            self.update_canvas()

        self.canvas.bind("<Button-1>", lambda e: selecting(e, "replace"))
        self.canvas.bind("<Shift-Button-1>", lambda e: selecting(e, "add"))
        self.canvas.bind("<Control-Button-1>", lambda e: selecting(e, "subtract"))

    def _floodfill_mask(
        self,
        image: Image.Image,
        mask: Image.Image,
        xy: tuple[int, int],
        value: float | tuple[int, ...],
        border: float | tuple[int, ...] | None = None,
        thresh: float = 0,
    ) -> None:
        pixel = image.copy().load()
        pixel_m = mask.load()
        assert pixel is not None
        assert pixel_m is not None
        x, y = xy
        try:
            background = pixel[x, y]
            # if self._color_diff(value, background) <= thresh:
            #     return  # seed point already has fill color
            pixel[x, y] = value
            pixel_m[x, y] = value
        except (ValueError, IndexError):
            return  # seed point outside image
        edge = {(x, y)}

        # Default floodfill algorithm.
        full_edge = set()
        while edge:
            new_edge = set()
            for x, y in edge:
                for s, t in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    # If already processed, or if a coordinate is negative, skip
                    if (s, t) in full_edge or s < 0 or t < 0:
                        continue
                    try:
                        p = pixel[s, t]
                    except (ValueError, IndexError):
                        pass
                    else:
                        full_edge.add((s, t))
                        if border is None:
                            fill = self._color_diff(p, background) <= thresh
                        else:
                            fill = p not in (value, border)
                        if fill:
                            pixel[s, t] = value
                            pixel_m[s, t] = value
                            new_edge.add((s, t))
            full_edge = edge
            edge = new_edge


ctk.set_appearance_mode(config.get("Brushshe", "theme"))
ctk.set_default_color_theme(resource("brushshe_theme.json"))
app = Brushshe()
app.mainloop()
