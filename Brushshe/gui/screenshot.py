# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Callable

import customtkinter as ctk
from PIL import Image, ImageGrab, ImageTk
from utils.translator import _


class Screenshot(ctk.CTkToplevel):
    def __init__(self, master, replace_picture: Callable):
        self.master = master

        self.master.withdraw()
        self.master.iconify()
        self.master.after(200)
        self.screenshot = ImageGrab.grab()

        super().__init__()

        self.attributes("-fullscreen", True)
        self.state("zoomed")

        self.replace_picture = replace_picture

        self.canvas = ctk.CTkCanvas(self)
        self.canvas.pack(fill="both", expand=True)

        screenthot_tk = ImageTk.PhotoImage(self.screenshot)
        self.canvas.create_image(0, 0, anchor="nw", image=screenthot_tk)
        self.canvas.image = screenthot_tk

        button_frame = ctk.CTkFrame(self)
        button_frame.place(x=10, y=10)

        ctk.CTkButton(
            button_frame,
            text=_("Cancel"),
            command=lambda: (self.destroy(), self.master.deiconify()),
        ).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(button_frame, text="OK", command=lambda: self._ready_screenshot(self.finished_screenshot)).pack(
            side="left", padx=10, pady=10
        )
        ctk.CTkButton(
            button_frame,
            text=_("Capture the entire screen"),
            command=lambda: self._ready_screenshot(self.screenshot),
        ).pack(side="left", padx=10, pady=10)

        self._crop()

    def _crop(self):
        self.x_begin = None
        self.y_begin = None
        self.x_end = None
        self.y_end = None

        self.canvas.bind("<Button-1>", self._selecting)
        self.canvas.bind("<B1-Motion>", self._selecting)
        self.canvas.bind("<ButtonRelease-1>", self._crop_end)

    def _selecting(self, event):
        if self.x_begin is None or self.y_begin is None:
            self.x_begin = event.x
            self.y_begin = event.y

        self.x_end = event.x
        self.y_end = event.y

        x_max = self.screenshot.width - 1
        y_max = self.screenshot.height - 1

        self.x_begin = max(self.x_begin, 0)
        self.x_begin = min(self.x_begin, x_max)
        self.y_begin = max(self.y_begin, 0)
        self.y_begin = min(self.y_begin, y_max)
        self.x_end = max(self.x_end, 0)
        self.x_end = min(self.x_end, x_max)
        self.y_end = max(self.y_end, 0)
        self.y_end = min(self.y_end, y_max)

        x1 = min(self.x_begin, self.x_end)
        x2 = max(self.x_begin, self.x_end)
        y1 = min(self.y_begin, self.y_end)
        y2 = max(self.y_begin, self.y_end)

        self._draw_tool(x1, y1, x2, y2)

    def _crop_end(self, event):
        if self.x_begin is None or self.y_begin is None:
            return

        x1 = min(self.x_begin, self.x_end)
        x2 = max(self.x_begin, self.x_end)
        y1 = min(self.y_begin, self.y_end)
        y2 = max(self.y_begin, self.y_end)

        self.x_begin = None
        self.y_begin = None
        self.x_end = None
        self.y_end = None

        new_width = x2 - x1
        new_height = y2 - y1

        self.finished_screenshot = Image.new("RGB", (new_width, new_height), "white")
        self.finished_screenshot.paste(self.screenshot, (-x1, -y1))

    def _draw_tool(self, x1: float, y1: float, x2: float, y2: float):
        self.canvas.delete("tool")

        self.canvas.create_rectangle(
            int(x1),
            int(y1),
            int(x2 + 1),
            int(y2 + 1),
            outline="white",
            width=1,
            tag="tool",
        )

        self.canvas.create_rectangle(
            int(x1),
            int(y1),
            int(x2 + 1),
            int(y2 + 1),
            outline="black",
            width=1,
            tag="tool",
            dash=(5, 5),
        )

    def _ready_screenshot(self, screenshot_img: Image.Image):
        self.replace_picture(screenshot_img.copy())
        self.destroy()
        self.master.deiconify()
