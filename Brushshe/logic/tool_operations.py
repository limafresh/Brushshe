# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
from constants import Constants
from core.gradient_fill import directions
from ui.tooltip import Tooltip
from utils.common import resource
from utils.translator import _

from . import state


class ToolOperations:
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
        new_size = max(new_size, 1)
        new_size = min(new_size, max_sizes[state.current_tool])
        self.change_tool_size(new_size)
        self.ui.tool_size_slider.set(int(new_size))

    def change_tool_size(self, value):
        state.tool_size = int(value)
        self.ui.tool_size_tooltip.configure(message=state.tool_size)

        if self.tool_size_dict.get(state.current_tool):
            self.tool_size_dict[state.current_tool] = int(value)

        if state.current_tool in ["insert", "real size sticker"]:
            self.ui.tool_size_label.configure(text=f"{state.tool_size} %")
        else:
            self.ui.tool_size_label.configure(text=state.tool_size)

    def get_tool_size(self):
        return self.tool_size_dict.get(state.current_tool) or state.tool_size

    def set_tool(self, tool, tool_name, tool_size, from_, to, cursor):
        state.current_tool = tool

        self.ui.canvas.unbind("<Button-1>")
        self.ui.canvas.unbind("<Shift-Button-1>")
        self.ui.canvas.unbind("<Control-Button-1>")
        self.ui.canvas.unbind("<ButtonPress-1>")
        self.ui.canvas.unbind("<ButtonRelease-1>")
        self.ui.canvas.unbind("<B1-Motion>")
        self.ui.canvas.unbind("<Motion>")
        self.ui.canvas.unbind("<Leave>")
        self.ui.canvas.unbind("<BackSpace>")
        self.ui.canvas.unbind("<Return>")

        for child in self.ui.tool_config_docker.winfo_children():
            child.destroy()

        self.ui.tool_label = ctk.CTkLabel(self.ui.tool_config_docker, text=None)
        self.ui.tool_label.pack(side=ctk.LEFT, padx=1)

        self.ui.tool_size_slider = ctk.CTkSlider(self.ui.tool_config_docker, command=self.change_tool_size)
        self.ui.tool_size_slider.pack(side=ctk.LEFT, padx=1)
        self.ui.tool_size_tooltip = Tooltip(self.ui.tool_size_slider)
        self.ui.tool_size_label = ctk.CTkLabel(self.ui.tool_config_docker, text=None)
        self.ui.tool_size_label.pack(side=ctk.LEFT, padx=5)

        if tool_size is None and from_ is None and to is None:
            self.ui.tool_label.configure(text=tool_name)
            self.ui.tool_size_slider.pack_forget()
            self.ui.tool_size_label.pack_forget()
        else:
            self.ui.tool_label.configure(text=tool_name + ":")
            state.tool_size = tool_size
            self.ui.tool_size_slider.configure(from_=from_, to=to)
            self.ui.tool_size_slider.set(state.tool_size)
            self.ui.tool_size_slider.pack(side=ctk.LEFT, padx=1)
            if state.current_tool in ["insert", "real size sticker"]:
                self.ui.tool_size_label.configure(text=f"{state.tool_size} %")
            else:
                self.ui.tool_size_label.configure(text=state.tool_size)
            self.ui.tool_size_label.pack(side=ctk.LEFT, padx=5)
            self.ui.tool_size_tooltip.configure(message=state.tool_size)

        if state.current_tool in ["brush", "eraser"]:
            brush_shape_btn = ctk.CTkSegmentedButton(
                self.ui.tool_config_docker, values=["●", "■"], command=self.brush_shape_btn_callback
            )
            brush_shape_btn.set({"circle": "●", "square": "■"}[state.brush_shape])
            brush_shape_btn.pack(side=ctk.LEFT, padx=5)
        elif state.current_tool == "fill":
            ctk.CTkCheckBox(
                self.ui.tool_config_docker,
                text=_("Gradient"),
                variable=self.is_gradient_fill,
                command=self.gradient_fill_checkbox_event,
            ).pack(side=ctk.LEFT, padx=5)
            self.direction_by_label = {_(direction): direction for direction in directions}
            self.gradient_mode_optionmenu = ctk.CTkOptionMenu(
                self.ui.tool_config_docker,
                values=list(self.direction_by_label.keys()),
                command=self.gradient_optionmenu_callback,
            )
            self.gradient_mode_optionmenu.set(_("Vertically"))
            self.gradient_mode_optionmenu.pack(side=ctk.LEFT, padx=1)
        elif state.current_tool == "text":
            self.tx_entry = ctk.CTkEntry(self.ui.tool_config_docker, placeholder_text=_("Enter text..."))
            self.tx_entry.pack(side=ctk.LEFT, padx=5)
            self.tx_entry.bind("<KeyRelease>", self.update_text_content)

            font_optionmenu = ctk.CTkOptionMenu(
                self.ui.tool_config_docker,
                values=Constants.FONTS,
                dynamic_resizing=False,
                command=self.font_optionmenu_callback,
            )
            font_optionmenu.set(self.current_font)
            font_optionmenu.pack(side=ctk.LEFT, padx=1)
        elif state.current_tool == "sticker" or state.current_tool == "real size sticker":
            ctk.CTkCheckBox(
                self.ui.tool_config_docker,
                text=_("Use real size"),
                variable=self.is_sticker_use_real_size,
                command=self.set_current_sticker,
            ).pack(side=ctk.LEFT, padx=5)
        elif state.current_tool == "effects":
            self.effects_optionmenu = ctk.CTkOptionMenu(
                self.ui.tool_config_docker, values=[_(value) for value in Constants.EFFECTS_VALUES]
            )
            self.effects_optionmenu.pack(side=ctk.LEFT, padx=5)
            ctk.CTkButton(self.ui.tool_config_docker, text="OK", width=35, command=self.apply_effect).pack(
                side=ctk.LEFT, padx=1
            )
        elif state.current_tool == "insert":
            ctk.CTkCheckBox(
                self.ui.tool_config_docker,
                text=_("Smoothing"),
                variable=self.is_insert_smoothing,
                command=self.insert_smoothing_event,
            ).pack(side=ctk.LEFT, padx=5)

        self.ui.focus_set()

        self.ui.canvas.configure(cursor=cursor)
        self.ui.canvas.delete("tools")

    def brush_shape_btn_callback(self, value):
        state.brush_shape = {"●": "circle", "■": "square"}[value]

    def gradient_fill_checkbox_event(self):
        self.paint_tools.is_gradient_fill = self.is_gradient_fill.get()

    def gradient_optionmenu_callback(self, choice):
        self.paint_tools.gradient_fill_direction = self.direction_by_label[choice]

    def update_text_content(self, event):
        self.paint_tools.text_content = self.tx_entry.get()

    def font_optionmenu_callback(self, value):
        self.current_font = value
        self.paint_tools.font_path = resource(Constants.FONTS_DICT.get(value))

    def insert_smoothing_event(self, choice):
        self.edit_tools_is_insert_smoothing = choice
