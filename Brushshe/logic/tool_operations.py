# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
from constants import Constants
from PIL import ImageFont
from ui.tooltip import Tooltip
from utils.common import resource
from utils.translator import _


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
        if new_size < 1:
            new_size = 1
        if new_size > max_sizes[self.current_tool]:
            new_size = max_sizes[self.current_tool]
        self.change_tool_size(new_size)
        self.ui.tool_size_slider.set(int(new_size))

    def change_tool_size(self, value):
        self.tool_size = int(value)
        self.ui.tool_size_tooltip.configure(message=self.tool_size)

        if self.tool_size_dict.get(self.current_tool):
            self.tool_size_dict[self.current_tool] = int(value)

        if self.current_tool in ["insert", "real size sticker"]:
            self.ui.tool_size_label.configure(text=f"{self.tool_size} %")
        else:
            self.ui.tool_size_label.configure(text=self.tool_size)

    def get_tool_size(self):
        return self.tool_size_dict.get(self.current_tool) or self.tool_size

    def set_tool(self, tool, tool_name, tool_size, from_, to, cursor):
        self.current_tool = tool

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
            self.ui.tool_label.configure(text=_(tool_name))
            self.ui.tool_size_slider.pack_forget()
            self.ui.tool_size_label.pack_forget()
        else:
            self.ui.tool_label.configure(text=_(tool_name) + ":")
            self.tool_size = tool_size
            self.ui.tool_size_slider.configure(from_=from_, to=to)
            self.ui.tool_size_slider.set(self.tool_size)
            self.ui.tool_size_slider.pack(side=ctk.LEFT, padx=1)
            if self.current_tool in ["insert", "real size sticker"]:
                self.ui.tool_size_label.configure(text=f"{self.tool_size} %")
            else:
                self.ui.tool_size_label.configure(text=self.tool_size)
            self.ui.tool_size_label.pack(side=ctk.LEFT, padx=5)
            self.ui.tool_size_tooltip.configure(message=self.tool_size)

        def brush_shape_btn_callback(value):
            self.brush_shape = {"●": "circle", "■": "square"}[value]

        def font_optionmenu_callback(value):
            self.current_font = value
            self.font_path = resource(Constants.FONTS_DICT.get(value))
            self.imagefont = ImageFont.truetype(self.font_path, self.tool_size)

        if self.current_tool in ["brush", "eraser"]:
            brush_shape_btn = ctk.CTkSegmentedButton(
                self.ui.tool_config_docker, values=["●", "■"], command=brush_shape_btn_callback
            )
            brush_shape_btn.set({"circle": "●", "square": "■"}[self.brush_shape])
            brush_shape_btn.pack(side=ctk.LEFT, padx=5)
        elif self.current_tool == "fill":
            ctk.CTkCheckBox(
                self.ui.tool_config_docker,
                text=_("Gradient"),
                variable=self.is_gradient_fill,
                onvalue="on",
                offvalue="off",
            ).pack(side=ctk.LEFT, padx=5)
            self.gradient_mode_optionmenu = ctk.CTkOptionMenu(
                self.ui.tool_config_docker,
                values=[_("Vertically"), _("Horizontally"), _("Diagonally"), _("Radially"), _("Rings"), _("Noise")],
            )
            self.gradient_mode_optionmenu.set(_("Vertically"))
            self.gradient_mode_optionmenu.pack(side=ctk.LEFT, padx=1)
        elif self.current_tool == "text":
            self.tx_entry = ctk.CTkEntry(self.ui.tool_config_docker, placeholder_text=_("Enter text..."))
            self.tx_entry.pack(side=ctk.LEFT, padx=5)

            font_optionmenu = ctk.CTkOptionMenu(
                self.ui.tool_config_docker,
                values=Constants.FONTS,
                dynamic_resizing=False,
                command=font_optionmenu_callback,
            )
            font_optionmenu.set(self.current_font)
            font_optionmenu.pack(side=ctk.LEFT, padx=1)
        elif self.current_tool == "sticker" or self.current_tool == "real size sticker":
            ctk.CTkCheckBox(
                self.ui.tool_config_docker,
                text=_("Use real size"),
                variable=self.is_sticker_use_real_size,
                onvalue="on",
                offvalue="off",
                command=self.set_current_sticker,
            ).pack(side=ctk.LEFT, padx=5)
        elif self.current_tool == "effects":
            self.effects_optionmenu = ctk.CTkOptionMenu(
                self.ui.tool_config_docker, values=[_(value) for value in Constants.EFFECTS_VALUES]
            )
            self.effects_optionmenu.pack(side=ctk.LEFT, padx=5)
            ctk.CTkButton(self.ui.tool_config_docker, text="OK", width=35, command=self.apply_effect).pack(
                side=ctk.LEFT, padx=1
            )
        elif self.current_tool == "insert":
            ctk.CTkCheckBox(
                self.ui.tool_config_docker,
                text=_("Smoothing"),
                variable=self.is_insert_smoothing,
                onvalue="on",
                offvalue="off",
            ).pack(side=ctk.LEFT, padx=5)

        self.ui.focus_set()

        self.ui.canvas.configure(cursor=cursor)
        self.ui.canvas.delete("tools")
