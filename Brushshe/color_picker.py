# CTk Color Picker for ctk
# Original Author: Akash Bora (Akascape)
# Contributers: Victor Vimbert-Guerlais (helloHackYnow)
# Modifed by Brushshe developers for Brushshe app

import math
import os
import sys

import customtkinter as ctk
from PIL import Image, ImageTk


def resource(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class AskColor(ctk.CTkToplevel):
    def __init__(self, title: str = "Choose Color", initial_color: str = None):
        super().__init__()

        self.title(title)
        self.resizable(width=False, height=False)
        self.transient(self.master)
        self.lift()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.after(10)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.default_hex_color = "#ffffff"
        self.default_rgb = [255, 255, 255]
        self.rgb_color = self.default_rgb[:]

        self.image_dimension = self._apply_window_scaling(250)
        self.target_dimension = self._apply_window_scaling(20)

        self.bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

        """UI"""
        self.frame = ctk.CTkFrame(master=self)
        self.frame.grid(padx=10, pady=10, sticky="nswe")

        self.canvas = ctk.CTkCanvas(
            self.frame,
            height=self.image_dimension,
            width=self.image_dimension,
            highlightthickness=0,
            bg=self.bg_color,
        )
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_mouse_drag)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)

        self.img1 = Image.open(resource("icons/color_wheel.png")).resize(
            (self.image_dimension, self.image_dimension), Image.Resampling.LANCZOS
        )
        self.img2 = Image.open(resource("icons/target.png")).resize(
            (self.target_dimension, self.target_dimension), Image.Resampling.LANCZOS
        )

        self.brightness_slider_value = ctk.IntVar()
        self.brightness_slider_value.set(255)

        self.img_tmp = self.get_real_circuit(self.img1, self.brightness_slider_value.get())

        self.wheel = ImageTk.PhotoImage(self.img_tmp)
        self.target = ImageTk.PhotoImage(self.img2)

        self.wheel_canvas_id = self.canvas.create_image(
            self.image_dimension / 2, self.image_dimension / 2, image=self.wheel
        )

        self.slider = ctk.CTkSlider(
            master=self.frame,
            height=20,
            border_width=1,
            button_length=15,
            progress_color=self.default_hex_color,
            from_=0,
            to=255,
            variable=self.brightness_slider_value,
            number_of_steps=256,
            command=lambda x: self.update_colors(),
        )
        self.slider.pack(fill="both", padx=10, pady=10)

        self.entry = ctk.CTkEntry(master=self.frame, text_color="black", fg_color=self.default_hex_color)
        self.entry.pack(fill="both", padx=10, pady=10)
        self.entry.insert(0, self.default_hex_color)
        self.entry.bind("<Return>", self.entry_return)

        self.button = ctk.CTkButton(master=self.frame, text="OK", command=self._ok_event)
        self.button.pack(fill="both", padx=10, pady=10)

        self.set_initial_color(initial_color)

        self.after(150, lambda: self.entry.focus())
        self.grab_set()

    def entry_return(self, event):
        if self.default_hex_color != self.entry.get():
            self.set_initial_color(self.entry.get())

    def get(self):
        self._color = self.entry._fg_color
        self.master.wait_window(self)
        return self._color

    def _ok_event(self, event=None):
        try:
            self.entry.configure(fg_color=self.entry.get())
            self._color = self.entry.get()
            self.winfo_rgb(self._color)
        except Exception:  # noqa: E722
            self.entry.configure(fg_color="red")
            return
        self.grab_release()
        self.destroy()
        del self.img1
        del self.img2
        del self.img_tmp
        del self.wheel
        del self.target

    def _on_closing(self):
        self._color = None
        self.grab_release()
        self.destroy()
        del self.img1
        del self.img2
        del self.img_tmp
        del self.wheel
        del self.target

    def get_real_circuit(self, img, brightness):
        if brightness > 255:
            brightness = 255
        if brightness < 0:
            brightness = 0
        source = img.split()
        r = source[0].point(lambda i: i * brightness / 255)
        g = source[1].point(lambda i: i * brightness / 255)
        b = source[2].point(lambda i: i * brightness / 255)
        return Image.merge(img.mode, (r, g, b, source[3]))  # rgba

    def update_wheel(self, x, y):
        self.canvas.delete("all")
        self.img_tmp = self.get_real_circuit(self.img1, self.brightness_slider_value.get())
        self.wheel = ImageTk.PhotoImage(self.img_tmp)
        self.wheel_canvas_id = self.canvas.create_image(
            self.image_dimension / 2,
            self.image_dimension / 2,
            image=self.wheel,
        )
        d_from_center = math.sqrt(((self.image_dimension / 2) - x) ** 2 + ((self.image_dimension / 2) - y) ** 2)
        if d_from_center < self.image_dimension / 2:
            self.target_x, self.target_y = x, y
        else:
            self.target_x, self.target_y = self.projection_on_circle(
                x, y, self.image_dimension / 2, self.image_dimension / 2, self.image_dimension / 2 - 1
            )
        self.wheel_target_id = self.canvas.create_image(self.target_x, self.target_y, image=self.target)

    def on_mouse_drag(self, event):
        x = event.x
        y = event.y

        self.update_wheel(x, y)
        self.get_target_color()
        self.update_colors()

    def get_target_color(self):
        try:
            self.rgb_color = self.img1.getpixel((self.target_x, self.target_y))

            r = self.rgb_color[0]
            g = self.rgb_color[1]
            b = self.rgb_color[2]
            self.rgb_color = [r, g, b]

        except AttributeError:
            self.rgb_color = self.default_rgb

    def update_colors(self):
        brightness = self.brightness_slider_value.get()

        self.img_tmp = self.get_real_circuit(self.img1, self.brightness_slider_value.get())
        self.wheel = ImageTk.PhotoImage(self.img_tmp)
        self.canvas.itemconfig(self.wheel_canvas_id, image=self.wheel)

        self.get_target_color()

        r = int(self.rgb_color[0] * (brightness / 255))
        g = int(self.rgb_color[1] * (brightness / 255))
        b = int(self.rgb_color[2] * (brightness / 255))

        self.rgb_color = [r, g, b]

        self.update_slider()

    def update_slider(self):
        self.default_hex_color = "#{:02x}{:02x}{:02x}".format(*self.rgb_color)

        self.slider.configure(progress_color=self.default_hex_color)
        self.entry.configure(fg_color=self.default_hex_color)

        self.entry.delete(0, ctk.END)
        self.entry.insert(0, str(self.default_hex_color))

        if self.brightness_slider_value.get() < 120:
            self.entry.configure(text_color="white")
        else:
            self.entry.configure(text_color="black")

        if str(self.entry._fg_color) == "black":
            self.entry.configure(text_color="white")

    def projection_on_circle(self, point_x, point_y, circle_x, circle_y, radius):
        angle = math.atan2(point_y - circle_y, point_x - circle_x)
        projection_x = circle_x + radius * math.cos(angle)
        projection_y = circle_y + radius * math.sin(angle)

        return projection_x, projection_y

    def set_initial_color(self, initial_color):
        # https://github.com/python/cpython/blob/3.13/Lib/colorsys.py
        def rgb_to_hsv(r, g, b):
            maxc = max(r, g, b)
            minc = min(r, g, b)
            rangec = maxc - minc
            v = maxc
            if minc == maxc:
                return 0.0, 0.0, v
            s = rangec / maxc
            rc = (maxc - r) / rangec
            gc = (maxc - g) / rangec
            bc = (maxc - b) / rangec
            if r == maxc:
                h = bc - gc
            elif g == maxc:
                h = 2.0 + rc - bc
            else:
                h = 4.0 + gc - rc
            h = (h / 6.0) % 1.0
            return h, s, v

        if initial_color:
            try:
                rgb = self.winfo_rgb(initial_color)
                r = math.floor(rgb[0] / 256)
                g = math.floor(rgb[1] / 256)
                b = math.floor(rgb[2] / 256)
            except ValueError:
                return
            except Exception:
                self.entry.configure(fg_color="red")
                return

            self.default_hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)

            h, s, v = rgb_to_hsv(r, g, b)

            radius = self.image_dimension / 2
            cr = s * radius
            # angle = (1 - h) * (2 * math.pi)
            angle = h * (2 * math.pi) - math.pi  # For current image wheel
            mid_x = self.image_dimension / 2
            mid_y = self.image_dimension / 2
            x_offset = math.cos(angle) * cr
            y_offset = math.sin(angle) * cr
            x = mid_x + x_offset
            y = mid_y + y_offset

            self.rgb_color = [r, g, b]
            self.brightness_slider_value.set(v)
            self.update_slider()
            self.update_wheel(x, y)
