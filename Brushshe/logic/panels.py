# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
from collections.abc import Callable
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image
from ui import messagebox
from ui.tooltip import Tooltip
from utils.common import generate_inverted_icon, resource
from utils.config_loader import config, save_config
from utils.translator import _


class Panels:
    def __init__(
        self,
        tools_frame: ctk.CTkFrame,
        palette_frame: ctk.CTkFrame,
        tools_dict: dict,
        change_color: Callable,
        change_palette_button_color: Callable,
    ):
        self.tools_frame = tools_frame
        self.palette_frame = palette_frame
        self.tools_dict = tools_dict
        self.change_color = change_color
        self.change_palette_button_color = change_palette_button_color

        self.palette: list[str] = []
        self.hide_left_toolbar = False

    # --- Left toolbar ---

    def set_left_toolbar(self, need_choose_file: bool = True):
        if self.hide_left_toolbar:
            return

        if need_choose_file:
            file_path = filedialog.askopenfilename(
                title=_("Import left toolbar config"), filetypes=[("JSON", "*.json")]
            )
            if file_path:
                json_path = file_path
                save_config("left_toolbar_config", json_path)
            else:
                return
        else:
            config_entry = config.get("Brushshe", "left_toolbar_config")
            if config_entry == "default":
                json_path = resource("assets/left_toolbar.json")
            else:
                json_path = config_entry

        for widget in self.tools_frame.winfo_children():
            widget.destroy()

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                self._make_left_toolbar(config_data)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Warning: Left toolbar configuration file is invalid or missing.")
            return

    def _make_left_toolbar(self, config_data: dict):
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
                ctk.CTkFrame(self.tools_frame, width=30, height=4).grid(column=column, row=row, pady=1, padx=1)
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
                text_color = ctk.ThemeManager.theme["CTkButton"]["text_color"]
                is_white_0 = sum(self.tools_frame.winfo_rgb(text_color[0])) / 3 > 32767
                is_white_1 = sum(self.tools_frame.winfo_rgb(text_color[1])) / 3 > 32767

                tool_icon = ctk.CTkImage(
                    light_image=Image.open(resource(icon_path))
                    if not is_white_0
                    else generate_inverted_icon(icon_path),
                    dark_image=Image.open(resource(icon_path)) if not is_white_1 else generate_inverted_icon(icon_path),
                    size=(22, 22),
                )
            except Exception as e:
                print(f"Icon error: {e}")

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
                self.tools_frame, text=None, width=30, height=30, image=tool_icon, command=tool_command
            )
            tool_button.grid(column=column, row=row, pady=1, padx=1)

            if tooltip_text:
                Tooltip(tool_button, message=tooltip_text)

            column += 1
            if column >= columns:
                column = 0
                row += 1

    # --- Palette ---

    def import_palette(self, palette_path: str | None = None):
        if palette_path is None:
            file_path = filedialog.askopenfilename(title=_("Import palette"), filetypes=[("HEX", "*.hex")])

            if not file_path:
                return

            palette_path = file_path
            save_config("palette", palette_path)

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
                        self.palette_frame.winfo_rgb(color)
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
        self._make_color_palette()

    def export_palette(self):
        path = filedialog.asksaveasfilename(
            title=_("Export palette"), filetypes=([("HEX", "*.hex")]), defaultextension=".hex"
        )
        if path:
            with open(path, "w") as f:
                f.writelines(color.lstrip("#") + "\n" for color in self.palette)

            messagebox.export_palette()

    def _make_color_palette(self):
        max_columns_in_row = 16

        for child in self.palette_frame.winfo_children():
            child.destroy()

        for index, color in enumerate(self.palette):
            row = index // max_columns_in_row
            column = index % max_columns_in_row

            color_button = ctk.CTkButton(
                self.palette_frame,
                fg_color=color,
                hover=False,
                text=None,
                width=24,
                height=24,
                border_width=1,
                corner_radius=1,
                command=lambda c=color: self.change_color(c),
            )
            color_button.grid(row=row, column=column, padx=1, pady=1)

            for event_name in ("<Button-3>", "<Double-Button-1>"):
                color_button.bind(
                    event_name,
                    lambda event, button=color_button, i=index: self.change_palette_button_color(event, button, i),
                )
