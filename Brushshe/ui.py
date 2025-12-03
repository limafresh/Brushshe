# Any copyright is dedicated to the Public Domain.
# https://creativecommons.org/publicdomain/zero/1.0/

"""This file contains Brushshe GUI"""

import os
import sys
import webbrowser
from collections import deque
from tkinter import PhotoImage

import customtkinter as ctk
import gallery
import messagebox
from core import data
from core.brush_palette import BrushPalette
from core.config_loader import config, write_config
from core.scroll import scroll
from core.spinbox import IntSpinbox
from core.tooltip import Tooltip
from core.translator import _
from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from logic import BrushsheLogic
from PIL import Image


def resource(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class BrushsheUi(ctk.CTk):
    def __init__(self):
        super().__init__(className="Brushshe")
        self.logic = BrushsheLogic(self)

        """ Main window """
        self.geometry("790x680")
        self.title(_("Unnamed") + " - " + _("Brushshe"))
        if os.name == "nt":
            self.iconbitmap(resource("icons/icon.ico"))
        else:
            self.iconphoto(True, PhotoImage(file=resource("assets/icons/icon.png")))
        self.protocol("WM_DELETE_WINDOW", self.logic.when_closing)

        """ Menu """
        menu = CTkMenuBar(self)

        file_menu = menu.add_cascade(_("File"))
        file_dropdown = CustomDropdownMenu(widget=file_menu)
        file_dropdown.add_option(option=_("New"), command=lambda: self.logic.new_picture("white"))
        file_dropdown.add_option(option=_("New with other color"), command=self.logic.other_bg_color)
        file_dropdown.add_option(
            option=_("New transparent"), command=lambda: self.new_picture(color="#00000000", mode="RGBA")
        )
        file_dropdown.add_separator()
        file_dropdown.add_option(option=_("Open from file"), command=self.logic.open_from_file)
        file_dropdown.add_option(option=_("Open from URL"), command=self.logic.open_from_url)
        file_dropdown.add_option(option=_("Open my gallery"), command=lambda: gallery.show(self.open_image))
        file_dropdown.add_separator()
        file_dropdown.add_option(option=_("Save changes to this picture"), command=self.logic.save_current)
        file_dropdown.add_option(option=_("Save as new picture"), command=self.logic.save_as)
        file_dropdown.add_option(option=_("Save to my gallery"), command=self.logic.save_to_gallery)
        file_dropdown.add_separator()
        file_dropdown.add_option(option=_("Import palette (hex)"), command=self.logic.import_palette)
        file_dropdown.add_separator()
        file_dropdown.add_option(option=_("Exit"), command=self.logic.when_closing)

        image_menu = menu.add_cascade(_("Image"))
        image_dropdown = CustomDropdownMenu(widget=image_menu)
        image_dropdown.add_option(option=_("Rotate right"), command=lambda: self.logic.rotate(-90))
        image_dropdown.add_option(option=_("Rotate left"), command=lambda: self.logic.rotate(90))
        image_dropdown.add_separator()
        image_dropdown.add_option(option=_("Change size"), command=self.change_size)
        image_dropdown.add_separator()
        image_dropdown.add_option(option=_("Create screenshot"), command=self.logic.create_screenshot)
        image_dropdown.add_option(option=_("Paste image from clipboard"), command=self.logic.paste_image_from_clipboard)

        view_menu = menu.add_cascade(_("View"))
        view_dropdown = CustomDropdownMenu(widget=view_menu)
        view_dropdown.add_option(option=_("Zoom In"), command=self.logic.zoom_in)
        view_dropdown.add_option(option=_("Zoom Out"), command=self.logic.zoom_out)
        view_dropdown.add_separator()
        view_dropdown.add_option(option=_("Reset"), command=self.logic.reset_zoom)

        select_menu = menu.add_cascade(_("Select"))
        select_dropdown = CustomDropdownMenu(widget=select_menu)
        select_dropdown.add_option(
            option=_("Rectangle select"),
            command=lambda: self.logic.select_by_shape(shape="rectangle"),
        )
        select_dropdown.add_option(option=_("Polygon select"), command=self.logic.select_by_polygon)
        select_dropdown.add_option(
            option=_("Fuzzy select"), command=lambda: self.logic.select_by_color(fill_limit=True)
        )
        select_dropdown.add_option(option=_("Select by color"), command=lambda: self.logic.select_by_color())
        select_dropdown.add_option(option=_("Invert selected"), command=self.logic.invert_mask)
        select_dropdown.add_option(option=_("Select all"), command=self.logic.select_all_mask)
        select_dropdown.add_option(option=_("Deselect all"), command=self.logic.remove_mask)
        select_dropdown.add_separator()
        select_dropdown.add_option(option=_("Display mask as fill"), command=lambda: self.logic.set_mask_type(0))
        select_dropdown.add_option(
            option=_("Display mask as ants (experimental)"), command=lambda: self.logic.set_mask_type(1)
        )

        tools_menu = menu.add_cascade(_("Tools"))
        tools_dropdown = CustomDropdownMenu(widget=tools_menu)

        draw_tools_submenu = tools_dropdown.add_submenu(_("Draw tools"))
        draw_tools_submenu.add_option(option=_("Brush"), command=self.logic.brush)
        draw_tools_submenu.add_option(option=_("Eraser"), command=self.logic.eraser)
        draw_tools_submenu.add_option(option=_("Fill"), command=self.logic.fill)
        draw_tools_submenu.add_option(option=_("Recoloring Brush"), command=self.logic.recoloring_brush)
        draw_tools_submenu.add_option(option=_("Spray"), command=self.logic.spray)
        draw_tools_submenu.add_option(option=_("Text"), command=self.logic.text_tool)

        shapes_submenu = tools_dropdown.add_submenu(_("Shapes"))
        shape_options = ["Rectangle", "Oval", "Fill rectangle", "Fill oval", "Line"]
        for shape in shape_options:
            shapes_submenu.add_option(option=_(shape), command=lambda shape=shape: self.logic.create_shape(shape))
        shapes_submenu.add_option(option=_("Bezier curve"), command=self.logic.bezier_shape)

        edit_submenu = tools_dropdown.add_submenu(_("Edit tools"))
        edit_submenu.add_option(option=_("Cut"), command=lambda: self.logic.copy_tool(deleted=True))
        edit_submenu.add_option(option=_("Copy"), command=lambda: self.logic.copy_tool())
        edit_submenu.add_option(option=_("Insert"), command=lambda: self.logic.start_insert())
        edit_submenu.add_option(option=_("Crop"), command=lambda: self.logic.crop_simple())

        tools_dropdown.add_option(option=_("Effects"), command=self.logic.effects)

        tools_icon_size = (20, 20)
        tools_dropdown.add_separator()
        smile_icon = ctk.CTkImage(Image.open(resource("assets/icons/smile.png")), size=tools_icon_size)
        tools_dropdown.add_option(option=_("Stickers"), image=smile_icon, command=self.logic.show_stickers_choice)
        frame_icon = ctk.CTkImage(Image.open(resource("assets/icons/frame.png")), size=tools_icon_size)
        tools_dropdown.add_option(option=_("Frames"), image=frame_icon, command=self.logic.show_frame_choice)
        tools_dropdown.add_separator()
        tools_dropdown.add_option(option=_("Remove white background"), command=self.logic.remove_white_background)

        menu.add_cascade(_("My Gallery"), command=lambda: gallery.show(self.logic.open_image))

        other_menu = menu.add_cascade(_("More"))
        other_dropdown = CustomDropdownMenu(widget=other_menu)
        other_dropdown.add_option(option=_("Settings"), command=self.settings)
        other_dropdown.add_option(
            option=_("Reset settings after exiting"), command=self.logic.reset_settings_after_exiting
        )
        # Icon taken from CTkMessagebox by Akascape
        info_icon = ctk.CTkImage(Image.open(resource("assets/icons/info.png")), size=tools_icon_size)
        other_dropdown.add_option(option=_("About program"), image=info_icon, command=messagebox.about_brushshe)

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

    """Change size window"""

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
                    new_height = int(self.logic.image.height * width_spinbox.get() / self.logic.image.width)
                else:
                    new_height = int(height_spinbox.get())

                if int(width_spinbox.get()) > 2000 or new_height > 2000:
                    msg = messagebox.continue_big_size()
                    if msg.get() == _("Yes"):
                        self.logic.crop_picture(0, 0, int(width_spinbox.get()), new_height)
                else:
                    self.logic.crop_picture(0, 0, int(width_spinbox.get()), new_height)
            except Exception as e:
                print(e)

        def scale():
            try:
                if aspect_ratio_var.get() == "on":
                    new_height = int(self.logic.image.height * width_spinbox.get() / self.logic.image.width)
                else:
                    new_height = int(height_spinbox.get())

                if int(width_spinbox.get()) > 2000 or new_height > 2000:
                    msg = messagebox.continue_big_size()
                    if msg.get() == _("Yes"):
                        scaled_image = self.logic.image.resize((int(width_spinbox.get()), new_height), Image.NEAREST)
                        self.logic.image = scaled_image
                        self.logic.picture_postconfigure()
                else:
                    scaled_image = self.logic.image.resize((int(width_spinbox.get()), new_height), Image.NEAREST)
                    self.logic.image = scaled_image
                    self.logic.picture_postconfigure()
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
        width_spinbox.set(self.logic.image.width)

        ctk.CTkLabel(width_height_frame, text=_("Height")).grid(row=1, column=2, padx=10, pady=10)
        height_spinbox = IntSpinbox(width_height_frame, width=150)
        height_spinbox.grid(row=2, column=2, padx=10, pady=10)
        height_spinbox.set(self.logic.image.height)

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

    """Settings window"""

    def settings(self):
        def change_theme(value):
            mode = {_("Light"): "light", _("Dark"): "dark"}.get(value, "system")
            ctk.set_appearance_mode(mode)
            config.set("Brushshe", "theme", mode)
            write_config()

        def change_undo_levels():
            data.undo_stack = deque(data.undo_stack, maxlen=undo_levels_spinbox.get())
            data.redo_stack = deque(data.redo_stack, maxlen=undo_levels_spinbox.get())
            config.set("Brushshe", "undo_levels", str(undo_levels_spinbox.get()))
            write_config()

        def smooth_switch_event():
            data.is_brush_smoothing = smooth_var.get()
            config.set("Brushshe", "smoothing", str(data.is_brush_smoothing))
            write_config()

        def bsq_event(value):
            data.brush_smoothing_quality = int(value)
            config.set("Brushshe", "brush_smoothing_quality", str(data.brush_smoothing_quality))
            write_config()

        def bsf_event(value):
            data.brush_smoothing_factor = int(value)
            config.set("Brushshe", "brush_smoothing_factor", str(data.brush_smoothing_factor))
            write_config()

        def palette_radiobutton_callback():
            self.logic.import_palette(resource(f"assets/palettes/{palette_var.get()}_palette.hex"))
            config.set("Brushshe", "palette", palette_var.get())
            write_config()

        def autosave_switch_event():
            config.set("Brushshe", "autosave", str(data.autosave_var.get()))
            write_config()

        settings_tl = ctk.CTkToplevel(self)
        settings_tl.geometry("400x650")
        settings_tl.title(_("Settings"))
        settings_tl.transient(self)

        settings_frame = ctk.CTkScrollableFrame(settings_tl, fg_color="transparent")
        settings_frame.pack(padx=10, pady=10, fill="both", expand=True)
        scroll(settings_frame)

        theme_frame = ctk.CTkFrame(settings_frame)
        theme_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(theme_frame, text=_("Theme")).pack(padx=10, pady=10)

        theme_btn = ctk.CTkSegmentedButton(
            theme_frame,
            values=[_("System"), _("Light"), _("Dark")],
            command=change_theme,
        )
        theme_btn.set(_(config.get("Brushshe", "theme").capitalize()))
        theme_btn.pack(padx=10, pady=10)

        undo_levels_frame = ctk.CTkFrame(settings_frame)
        undo_levels_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(undo_levels_frame, text=_("Maximum undo/redo levels")).pack(padx=10, pady=10)

        undo_levels_spinbox = IntSpinbox(undo_levels_frame, width=150)
        undo_levels_spinbox.pack(padx=10, pady=10)
        undo_levels_spinbox.set(data.undo_stack.maxlen)

        ctk.CTkButton(undo_levels_frame, text=_("Apply"), command=change_undo_levels).pack(padx=10, pady=10)

        smooth_frame = ctk.CTkFrame(settings_frame)
        smooth_frame.pack(padx=10, pady=10, fill="x")

        smooth_var = ctk.BooleanVar(value=data.is_brush_smoothing)
        ctk.CTkSwitch(
            smooth_frame,
            text=_("Smoothing for brush/eraser"),
            variable=smooth_var,
            onvalue=True,
            offvalue=False,
            command=smooth_switch_event,
        ).pack(padx=10, pady=10)

        ctk.CTkLabel(smooth_frame, text=_("Brush smoothing quality")).pack(padx=10, pady=10)

        bsq_slider = ctk.CTkSlider(smooth_frame, from_=1, to=64, command=bsq_event)
        bsq_slider.set(data.brush_smoothing_quality)
        bsq_slider.pack(padx=10, pady=10)

        ctk.CTkLabel(smooth_frame, text=_("Brush smoothing factor (weight)")).pack(padx=10, pady=1)

        bsf_slider = ctk.CTkSlider(smooth_frame, from_=3, to=64, command=bsf_event)
        bsf_slider.set(data.brush_smoothing_factor)
        bsf_slider.pack(padx=10, pady=10)

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

        autosave_frame = ctk.CTkFrame(settings_frame)
        autosave_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkSwitch(
            autosave_frame,
            text=_("Autosave"),
            variable=data.autosave_var,
            onvalue=True,
            offvalue=False,
            command=autosave_switch_event,
        ).pack(padx=10, pady=10)

        check_new_version_frame = ctk.CTkFrame(settings_frame)
        check_new_version_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkButton(
            check_new_version_frame,
            text=f"{_('Check new versions (yours is')} {data.version_full})",
            command=lambda: webbrowser.open(r"https://github.com/limafresh/Brushshe/releases"),
        ).pack(padx=10, pady=10)


ctk.set_appearance_mode(config.get("Brushshe", "theme"))
ctk.set_default_color_theme(resource("assets/brushshe_theme.json"))
