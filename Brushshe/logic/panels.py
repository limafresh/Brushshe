# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import math
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image
from ui import messagebox
from ui.tooltip import Tooltip
from utils.common import generate_inverted_icon, resource
from utils.config_loader import config, write_config
from utils.translator import _


class Panels:
    """Left toolbar"""

    def set_left_toolbar(self, need_choose_file=True):
        if need_choose_file:
            file_path = filedialog.askopenfilename(
                title=_("Import left toolbar config"), filetypes=[("JSON", "*.json")]
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
                self.make_left_toolbar(config_data)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Warning: Left toolbar configuration file is invalid or missing.")
            return

    def make_left_toolbar(self, config_data: dict):
        columns = config_data.get("columns", 4)
        items_list = config_data.get("items", [])

        row = 0
        column = 0

        for item in items_list:
            if not item.get("item"):
                print("No 'item' key in item!")
                continue

            if not self.tools_dict.get(item["item"]) and item["item"] != "separator":
                print(f"Invalid 'item' value: {item['item']}!")
                continue

            if item["item"] == "separator":
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

            if isinstance(self.tools_dict[item["item"]], dict):
                tool_command = self.tools_dict[item["item"]]["command"]
            else:
                tool_command = self.tools_dict[item["item"]]

            if item.get("name"):
                if item["name"].get("translate"):
                    tool_name = _(item["name"]["text"])
                else:
                    tool_name = item["name"]["text"]

                if (
                    isinstance(self.tools_dict[item["item"]], dict)
                    and self.tools_dict[item["item"]].get("hotkey")
                    and not item.get("notShowHotkey")
                ):
                    tooltip_text = f"{tool_name} ({self.tools_dict[item['item']]['hotkey']})"
                else:
                    tooltip_text = tool_name
            else:
                tooltip_text = None

            try:
                icon_path = f"assets/icons/toolbar/{item['item']}.png"

                if config.get("Brushshe", "color_theme") != "brushshe_theme":
                    tool_icon = ctk.CTkImage(
                        light_image=generate_inverted_icon(icon_path),
                        size=(22, 22),
                    )
                else:
                    tool_icon = ctk.CTkImage(
                        light_image=Image.open(resource(icon_path)),
                        dark_image=generate_inverted_icon(icon_path),
                        size=(22, 22),
                    )
            except Exception:
                not_found_path = "assets/icons/toolbar/not_found.png"

                if config.get("Brushshe", "color_theme") != "brushshe_theme":
                    tool_icon = ctk.CTkImage(
                        dark_image=generate_inverted_icon(not_found_path),
                        size=(22, 22),
                    )
                else:
                    tool_icon = ctk.CTkImage(
                        light_image=Image.open(resource(not_found_path)),
                        dark_image=generate_inverted_icon(not_found_path),
                        size=(22, 22),
                    )

            tool_button = ctk.CTkButton(
                self.ui.tools_frame, text=None, width=30, height=30, image=tool_icon, command=tool_command
            )
            tool_button.grid(column=column, row=row, pady=1, padx=1)

            if tooltip_text:
                Tooltip(tool_button, message=tooltip_text)

            column += 1
            if column >= columns:
                column = 0
                row += 1

    """Palette"""

    def import_palette(self, value=None):
        if value is None:
            file_path = filedialog.askopenfilename(title=_("Import palette"), filetypes=[("HEX", "*.hex")])

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
                        print(f"Warning: String `{color}` is not correct color.")
                        continue
                    colors.append(color)
        except FileNotFoundError:
            return
        except Exception:
            print("Incorrect file format?")
            return

        self.palette = colors
        self.make_color_palette(colors)

    def export_palette(self):
        path = filedialog.asksaveasfilename(
            title=_("Export palette"), filetypes=([("HEX", "*.hex")]), defaultextension=".hex"
        )
        if path:
            with open(path, "w") as f:
                f.writelines(color.lstrip("#") + "\n" for color in self.palette)

        messagebox.export_palette()

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
                print(f"Warning: String `{color}` is not correct color.")
                continue

            row = ii // max_columns_in_row
            column = ii % max_columns_in_row

            color_checked = f"#{r:02x}{g:02x}{b:02x}"

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
            tmp_btn.bind("<Button-3>", lambda event, obj=tmp_btn, i=ii: self.color_choice_btn(event, obj, i))
            tmp_btn.bind("<Double-Button-1>", lambda event, obj=tmp_btn, i=ii: self.color_choice_btn(event, obj, i))

            ii += 1
