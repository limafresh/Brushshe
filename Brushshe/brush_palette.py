import os
import sys

import customtkinter as ctk


class BrushPalette(ctk.CTkFrame):
    def __init__(
        self,
        master,
        click_main_btn,
        click_second_btn,
        click_flip_btn,
        height: int = 40,
        width: int = 54,
        corner_radius: int = 0,
        bg_color: str = "transparent",
        **kwargs,
    ):
        self._main_color = "#000000"
        self._second_color = "#FFFFFF"
        self.click_main_btn = click_main_btn
        self.click_second_btn = click_second_btn
        self.click_flip_btn = click_flip_btn

        super().__init__(master, height=height, width=width, corner_radius=corner_radius, bg_color=bg_color, **kwargs)
        super().pack(side=ctk.LEFT)

        ctk.CTkButton(
            self,
            text=None,
            width=12,
            height=12,
            border_width=0,
            corner_radius=0,
            command=self.click_flip_btn,
            fg_color="#707070",
            hover_color="#7f7f7f",
        ).place(x=32, y=0)

        self.second_color_btn = ctk.CTkButton(
            self,
            text=None,
            width=24,
            height=24,
            border_width=2,
            corner_radius=0,
            command=self.click_second_btn,
            fg_color=self._second_color,
            hover_color=self._second_color,
        )
        self.second_color_btn.place(x=22, y=14)

        self.main_color_btn = ctk.CTkButton(
            self,
            text=None,
            width=24,
            height=24,
            border_width=2,
            corner_radius=0,
            command=self.click_main_btn,
            fg_color=self._main_color,
            hover_color=self._main_color,
        )
        self.main_color_btn.place(x=6, y=2)

    def configure(self, **kwargs):
        super().configure(**kwargs)

    def resource(self, relative_path):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    @property
    def main_color(self):
        return self._main_color

    @main_color.setter
    def main_color(self, value):
        self._main_color = value
        self.main_color_btn.configure(fg_color=self._main_color, hover_color=self._main_color)

    @property
    def second_color(self):
        return self._second_color

    @second_color.setter
    def second_color(self, value):
        self._second_color = value
        self.second_color_btn.configure(fg_color=self._second_color, hover_color=self._second_color)
