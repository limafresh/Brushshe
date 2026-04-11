# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import math
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image
from ui.tooltip import Tooltip
from utils.common import resource
from utils.config_loader import config, write_config
from utils.translator import _


class Panels:
    """Left toolbar"""

    def set_left_toolbar(self, need_choose_file=True):
        if need_choose_file:
            file_path = filedialog.askopenfilename(
                title=_("Import left toolbar config from file"), filetypes=[("JSON", "*.json")]
            )
            if file_path:
                json_path = file_path
                config.set("Brushshe", "left_toolbar_config", json_path)
                write_config()
            else:
                return
        else:
            config_entry = config.get("Brushshe", "left_toolbar_config")
            if config_entry == "default":
                json_path = resource("assets/configs/left_toolbar.json")
            else:
                json_path = config_entry

        for widget in self.ui.tools_frame.winfo_children():
            widget.destroy()

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Warning: Left toolbar configuration file is invalid or missing.")
            return

        columns = config_data.get("columns", 4)
        tools_list = config_data.get("tools", [])

        row = 0
        column = 0

        for tool in tools_list:
            if tool["type"] == "separator":
                column = 0
                row += 1
                s = ctk.CTkFrame(
                    self.ui.tools_frame,
                    width=30,
                    height=4,
                )
                s.grid(column=column, row=row, pady=1, padx=1)
                row += 1
                continue

            tool_command = eval(tool["action"], {"self": self})
            tool_icon_name = tool["icon_name"]

            if tool.get("helper"):
                tooltip_text = _(tool["helper"])
            elif tool.get("hotkey"):
                tooltip_text = f"{_(tool['name'])} {tool['hotkey']}"
            else:
                tooltip_text = _(tool["name"])

            try:
                if config.get("Brushshe", "color_theme") != "brushshe_theme":
                    tool_icon = ctk.CTkImage(
                        light_image=Image.open(resource(f"assets/icons/toolbar/{tool_icon_name}_dark.png")),
                        size=(22, 22),
                    )
                else:
                    tool_icon = ctk.CTkImage(
                        light_image=Image.open(resource(f"assets/icons/toolbar/{tool_icon_name}_light.png")),
                        dark_image=Image.open(resource(f"assets/icons/toolbar/{tool_icon_name}_dark.png")),
                        size=(22, 22),
                    )
            except Exception:
                if config.get("Brushshe", "color_theme") != "brushshe_theme":
                    tool_icon = ctk.CTkImage(
                        dark_image=Image.open(resource("assets/icons/toolbar/not_found_dark.png")),
                        size=(22, 22),
                    )
                else:
                    tool_icon = ctk.CTkImage(
                        light_image=Image.open(resource("assets/icons/toolbar/not_found_light.png")),
                        dark_image=Image.open(resource("assets/icons/toolbar/not_found_dark.png")),
                        size=(22, 22),
                    )

            tool_button = ctk.CTkButton(
                self.ui.tools_frame, text=None, width=30, height=30, image=tool_icon, command=tool_command
            )
            tool_button.grid(column=column, row=row, pady=1, padx=1)
            Tooltip(tool_button, message=tooltip_text)

            column += 1
            if column >= columns:
                column = 0
                row += 1

    """Palette"""

    def import_palette(self, value=None):
        if value is None:
            file_path = filedialog.askopenfilename(title=_("Import palette from file"), filetypes=[("HEX", "*.hex")])

            if not file_path:
                return

            palette_path = file_path
            config.set("Brushshe", "palette", palette_path)
            write_config()
        else:
            palette_path = value

        colors = []

        try:
            with open(palette_path) as f:
                lines = f.readlines()
                for line in lines:
                    color = line.strip()
                    if not color:
                        continue

                    if not color.startswith("#"):
                        color = "#" + color
                    try:
                        self.ui.winfo_rgb(color)
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

    def make_color_palette(self, colors):
        max_columns_in_row = 16

        if colors is None or len(colors) == 0:
            print("Wrong palette")
            return

        for child in self.ui.palette_widget.winfo_children():
            child.destroy()

        ii = 0
        for color in colors:
            try:
                rgb = self.ui.winfo_rgb(color)
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
                self.ui.palette_widget,
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
