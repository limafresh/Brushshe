# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
import data
from PIL import Image, ImageGrab, ImageTk
from utils.translator import _


class Screenshot:
    def screenshot_crop(self, screenshot_canvas, screenshot):
        x_begin = None
        y_begin = None
        x_end = None
        y_end = None

        def cropping(event):
            nonlocal x_begin, y_begin, x_end, y_end

            x, y = event.x, event.y

            if x_begin is None or y_begin is None:
                x_begin = x
                y_begin = y

            x_end = x
            y_end = y
            x_max = screenshot.width - 1
            y_max = screenshot.height - 1

            if x_begin < 0:
                x_begin = 0
            if x_begin > x_max:
                x_begin = x_max
            if y_begin < 0:
                y_begin = 0
            if y_begin > y_max:
                y_begin = y_max
            if x_end < 0:
                x_end = 0
            if x_end > x_max:
                x_end = x_max
            if y_end < 0:
                y_end = 0
            if y_end > y_max:
                y_end = y_max

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            draw_tool(x1, y1, x2, y2)

        def crop_end(event):
            nonlocal x_begin, y_begin, x_end, y_end

            if x_begin is None or y_begin is None:
                return

            x1 = min(x_begin, x_end)
            x2 = max(x_begin, x_end)
            y1 = min(y_begin, y_end)
            y2 = max(y_begin, y_end)

            x_begin = None
            y_begin = None
            x_end = None
            y_end = None

            new_width = x2 - x1
            new_height = y2 - y1

            self.finished_screenshot = Image.new("RGB", (new_width, new_height), data.bg_color)
            self.finished_screenshot.paste(screenshot, (-x1, -y1))

        def draw_tool(x1, y1, x2, y2):
            screenshot_canvas.delete("screenshot_tool")

            screenshot_canvas.create_rectangle(
                int(x1),
                int(y1),
                int(x2 + 1),
                int(y2 + 1),
                outline="white",
                width=1,
                tag="screenshot_tool",
            )
            screenshot_canvas.create_rectangle(
                int(x1),
                int(y1),
                int(x2 + 1),
                int(y2 + 1),
                outline="black",
                width=1,
                tag="screenshot_tool",
                dash=(5, 5),
            )

        screenshot_canvas.bind("<Button-1>", cropping)
        screenshot_canvas.bind("<B1-Motion>", cropping)
        screenshot_canvas.bind("<ButtonRelease-1>", crop_end)

    def create_screenshot(self):
        def ready_screenshot(screenshot_img):
            self.image = screenshot_img.copy()
            self.picture_postconfigure()
            screenshot_window.destroy()

        self.ui.withdraw()
        self.ui.iconify()
        self.ui.after(200)
        screenshot = ImageGrab.grab()
        self.ui.deiconify()

        screenshot_window = ctk.CTkToplevel(self.ui)
        screenshot_window.attributes("-fullscreen", True)

        screenshot_canvas = ctk.CTkCanvas(screenshot_window)
        screenshot_canvas.pack(fill="both", expand=True)

        screenthot_tk = ImageTk.PhotoImage(screenshot)
        screenshot_canvas.create_image(0, 0, anchor="nw", image=screenthot_tk)
        screenshot_canvas.image = screenthot_tk

        screenshot_button_frame = ctk.CTkFrame(screenshot_window)
        screenshot_button_frame.place(x=10, y=10)

        ctk.CTkButton(screenshot_button_frame, text=_("Cancel"), command=lambda: screenshot_window.destroy()).pack(
            side="left", padx=10, pady=10
        )
        ctk.CTkButton(
            screenshot_button_frame, text="OK", command=lambda: ready_screenshot(self.finished_screenshot)
        ).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(
            screenshot_button_frame, text=_("Capture the entire screen"), command=lambda: ready_screenshot(screenshot)
        ).pack(side="left", padx=10, pady=10)

        self.screenshot_crop(screenshot_canvas, screenshot)
