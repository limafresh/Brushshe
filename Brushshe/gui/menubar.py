# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
from PIL import Image
from ui import messagebox
from ui.CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from utils.resource import resource
from utils.translator import _


class MenuBar:
    def create_menubar(self):
        menu = CTkMenuBar(self)

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
        file_dropdown.add_option(option=_("Open my gallery"), command=self.show_gallery)
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
        tools_dropdown.add_option(option=_("Stickers"), image=smile_icon, command=self.show_stickers_choice)
        frame_icon = ctk.CTkImage(Image.open(resource("assets/icons/frame.png")), size=tools_icon_size)
        tools_dropdown.add_option(option=_("Frames"), image=frame_icon, command=self.show_frame_choice)
        tools_dropdown.add_separator()
        tools_dropdown.add_option(option=_("Remove white background"), command=self.logic.remove_white_background)

        menu.add_cascade(_("My Gallery"), command=self.show_gallery)

        other_menu = menu.add_cascade(_("More"))
        other_dropdown = CustomDropdownMenu(widget=other_menu)
        other_dropdown.add_option(option=_("Run add-on"), command=self.logic.open_addon)
        other_dropdown.add_option(option=_("Settings"), command=self.settings)
        other_dropdown.add_option(
            option=_("Reset settings after exiting"), command=self.logic.reset_settings_after_exiting
        )
        # Icon taken from CTkMessagebox by Akascape
        info_icon = ctk.CTkImage(Image.open(resource("assets/icons/info.png")), size=tools_icon_size)
        other_dropdown.add_option(option=_("About program"), image=info_icon, command=messagebox.about_brushshe)
