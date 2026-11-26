# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
from PIL import Image, ImageGrab, ImageTk
from utils.translator import _

from . import state


class Screenshot:
    def screenshot_crop(self, screenshot_canvas, screenshot):
        self.x_begin = None
        self.y_begin = None
        self.x_end = None
        self.y_end = None

        screenshot_canvas.bind("<Button-1>", self.screenshot_selecting)
        screenshot_canvas.bind("<B1-Motion>", self.screenshot_selecting)
        screenshot_canvas.bind("<ButtonRelease-1>", lambda e: self.screenshot_crop_end(screenshot))

    def screenshot_selecting(self, event):
        x, y = self.canvas_to_pict_xy(event.x, event.y)

        if self.x_begin is None or self.y_begin is None:
            self.x_begin = x
            self.y_begin = y

        self.x_end = x
        self.y_end = y

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

        self.screenshot_draw_tool(x1, y1, x2, y2)

    def screenshot_end(self):
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

        return x1, y1, x2, y2

    def screenshot_draw_tool(self, x1, y1, x2, y2):
        self.screenshot_canvas.delete("screenshot_tool")

        self.screenshot_canvas.create_rectangle(
            int(x1),
            int(y1),
            int(x2 + 1),
            int(y2 + 1),
            outline="white",
            width=1,
            tag="screenshot_tool",
        )
        self.screenshot_canvas.create_rectangle(
            int(x1),
            int(y1),
            int(x2 + 1),
            int(y2 + 1),
            outline="black",
            width=1,
            tag="screenshot_tool",
            dash=(5, 5),
        )

    def screenshot_crop_end(self, screenshot):
        result = self.screenshot_end(True)
        if result is None:
            return
        x1, y1, x2, y2 = map(int, result)

        new_width = x2 - x1
        new_height = y2 - y1

        self.finished_screenshot = Image.new("RGB", (new_width, new_height), state.bg_color)
        self.finished_screenshot.paste(screenshot, (-x1, -y1))

    def create_screenshot(self):
        self.ui.withdraw()
        self.ui.iconify()
        self.ui.after(200)
        self.screenshot = ImageGrab.grab()

        self.screenshot_window = ctk.CTkToplevel(self.ui)
        self.screenshot_window.attributes("-fullscreen", True)
        self.screenshot_window.state("zoomed")

        self.screenshot_canvas = ctk.CTkCanvas(self.screenshot_window)
        self.screenshot_canvas.pack(fill="both", expand=True)

        screenthot_tk = ImageTk.PhotoImage(self.screenshot)
        self.screenshot_canvas.create_image(0, 0, anchor="nw", image=screenthot_tk)
        self.screenshot_canvas.image = screenthot_tk

        screenshot_button_frame = ctk.CTkFrame(self.screenshot_window)
        screenshot_button_frame.place(x=10, y=10)

        ctk.CTkButton(
            screenshot_button_frame,
            text=_("Cancel"),
            command=lambda: (self.screenshot_window.destroy(), self.ui.deiconify()),
        ).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(
            screenshot_button_frame, text="OK", command=lambda: self.ready_screenshot(self.finished_screenshot)
        ).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(
            screenshot_button_frame,
            text=_("Capture the entire screen"),
            command=lambda: self.ready_screenshot(self.screenshot),
        ).pack(side="left", padx=10, pady=10)

        self.screenshot_crop(self.screenshot_canvas, self.screenshot)

    def ready_screenshot(self, screenshot_img):
        state.image = screenshot_img.copy()
        self.picture_postconfigure()
        self.screenshot_window.destroy()
        self.ui.deiconify()
