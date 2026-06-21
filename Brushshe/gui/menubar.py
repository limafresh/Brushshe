# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import webbrowser

import customtkinter as ctk
from PIL import Image
from ui import messagebox
from ui.CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from utils.common import resource
from utils.translator import _


class MenuBar:
    def create_menubar(self):
        menu = CTkMenuBar(self)

        """File menu"""
        file_menu = menu.add_cascade(_("File"))
        file_dropdown = CustomDropdownMenu(widget=file_menu)
        file_dropdown.add_option(option=_("New"), command=lambda: self.logic.new_picture("white"))
        file_dropdown.add_option(option=_("New with other color"), command=self.logic.other_bg_color)
        file_dropdown.add_option(
            option=_("New transparent"), command=lambda: self.logic.new_picture(color="#00000000", mode="RGBA")
        )
        file_dropdown.add_separator()
        file_dropdown.add_option(option=_("Open from file"), command=self.logic.open_from_file)
        file_dropdown.add_option(option=_("Open from URL"), command=self.logic.open_from_url)
        file_dropdown.add_separator()
        file_dropdown.add_option(option=_("Save changes to this picture"), command=self.logic.save_current)
        file_dropdown.add_option(option=_("Save as new picture"), command=self.logic.save_as)
        file_dropdown.add_separator()
        file_dropdown.add_option(option=_("Import left toolbar config from file"), command=self.logic.set_left_toolbar)
        file_dropdown.add_option(option=_("Import palette from file"), command=self.logic.import_palette)
        file_dropdown.add_separator()
        file_dropdown.add_option(option=_("Exit"), command=self.logic.when_closing)

        """Image menu"""
        image_menu = menu.add_cascade(_("Image"))
        image_dropdown = CustomDropdownMenu(widget=image_menu)
        image_dropdown.add_option(option=_("Rotate right"), command=lambda: self.logic.rotate(-90))
        image_dropdown.add_option(option=_("Rotate left"), command=lambda: self.logic.rotate(90))
        image_dropdown.add_separator()
        image_dropdown.add_option(option=_("Change size"), command=self.change_size)
        image_dropdown.add_separator()
        image_dropdown.add_option(option=_("Create screenshot"), command=self.logic.create_screenshot)
        image_dropdown.add_option(option=_("Paste image from clipboard"), command=self.logic.paste_image_from_clipboard)

        """View menu"""
        view_menu = menu.add_cascade(_("View"))
        view_dropdown = CustomDropdownMenu(widget=view_menu)
        view_dropdown.add_option(option=_("Zoom In"), command=self.logic.zoom_in)
        view_dropdown.add_option(option=_("Zoom Out"), command=self.logic.zoom_out)
        view_dropdown.add_separator()
        view_dropdown.add_option(option=_("Reset"), command=self.logic.reset_zoom)

        """Tools menu"""
        tools_menu = menu.add_cascade(_("Tools"))
        tools_dropdown = CustomDropdownMenu(widget=tools_menu)

        draw_submenu = tools_dropdown.add_submenu(_("Draw tools"))
        draw_submenu.add_option(option=_("Brush"), command=self.logic.brush)
        draw_submenu.add_option(option=_("Eraser"), command=self.logic.eraser)
        draw_submenu.add_option(option=_("Fill"), command=self.logic.start_fill)
        draw_submenu.add_option(option=_("Recoloring Brush"), command=self.logic.recoloring_brush)
        draw_submenu.add_option(option=_("Spray"), command=self.logic.spray)
        draw_submenu.add_option(option=_("Text"), command=self.logic.text_tool)

        shapes_submenu = tools_dropdown.add_submenu(_("Shapes"))
        shapes_submenu.add_option(option=_("Rectangle"), command=lambda: self.logic.create_shape("Rectangle"))
        shapes_submenu.add_option(option=_("Oval"), command=lambda: self.logic.create_shape("Oval"))
        shapes_submenu.add_option(option=_("Fill rectangle"), command=lambda: self.logic.create_shape("Fill rectangle"))
        shapes_submenu.add_option(option=_("Fill oval"), command=lambda: self.logic.create_shape("Fill oval"))
        shapes_submenu.add_option(option=_("Line"), command=lambda: self.logic.create_shape("Line"))
        shapes_submenu.add_option(option=_("Bezier"), command=self.logic.bezier_shape)

        edit_submenu = tools_dropdown.add_submenu(_("Edit tools"))
        edit_submenu.add_option(option=_("Cut"), command=lambda: self.logic.copy_tool(deleted=True))
        edit_submenu.add_option(option=_("Copy"), command=self.logic.copy_tool)
        edit_submenu.add_option(option=_("Insert"), command=self.logic.start_insert)
        edit_submenu.add_option(option=_("Crop"), command=self.logic.crop_simple)

        select_submenu = tools_dropdown.add_submenu(_("Select"))
        select_submenu.add_option(
            option=_("Rectangle select"), command=lambda: self.logic.select_by_shape(shape="rectangle")
        )
        select_submenu.add_option(option=_("Polygon select"), command=self.logic.select_by_polygon)
        select_submenu.add_option(option=_("Fuzzy select"), command=lambda: self.logic.select_by_color(fill_limit=True))
        select_submenu.add_option(option=_("Select by color"), command=self.logic.select_by_color)
        select_submenu.add_separator()
        select_submenu.add_option(option=_("Deselect all"), command=self.logic.remove_mask)
        select_submenu.add_option(option=_("Select all"), command=self.logic.select_all_mask)

        tools_dropdown.add_option(option=_("Effects"), command=self.logic.effects)
        tools_dropdown.add_separator()
        tools_icon_size = (20, 20)
        smile_icon = ctk.CTkImage(Image.open(resource("assets/icons/smile.png")), size=tools_icon_size)
        tools_dropdown.add_option(option=_("Stickers"), image=smile_icon, command=self.show_stickers_choice)
        frame_icon = ctk.CTkImage(Image.open(resource("assets/icons/frame.png")), size=tools_icon_size)
        tools_dropdown.add_option(option=_("Frames"), image=frame_icon, command=self.show_frame_choice)
        tools_dropdown.add_separator()
        tools_dropdown.add_option(option=_("Remove white background"), command=self.logic.remove_white_background)

        """My gallery menu"""
        menu.add_cascade(_("My Gallery"), command=self.show_gallery)

        """Add-ons menu"""
        addons_menu = menu.add_cascade(_("Add-ons"))
        addons_dropdown = CustomDropdownMenu(widget=addons_menu)
        addons_dropdown.add_option(option=_("Open and run add-on from file"), command=self.logic.open_addon)
        addons_dropdown.add_option(option=_("Add-on Manager"), command=self.open_addon_manager)

        """More menu"""
        more_menu = menu.add_cascade(_("More"))
        more_dropdown = CustomDropdownMenu(widget=more_menu)
        more_dropdown.add_option(option=_("Settings"), command=self.settings)
        more_dropdown.add_option(
            option=_("Wiki"), command=lambda: webbrowser.open(r"https://github.com/limafresh/Brushshe/wiki")
        )
        # Icon taken from CTkMessagebox by Akascape
        info_icon = ctk.CTkImage(Image.open(resource("assets/icons/info.png")), size=tools_icon_size)
        more_dropdown.add_option(option=_("About program"), image=info_icon, command=messagebox.about_brushshe)
