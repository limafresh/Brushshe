import json
import sys
import webbrowser
from collections import deque
from locale import getlocale
from os import environ, listdir, name, path, remove
from pathlib import Path
from tkinter import PhotoImage
from uuid import uuid4

import customtkinter as ctk
from brushshe_color_picker import AskColor
from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from CTkMessagebox import CTkMessagebox
from CTkToolTip import CTkToolTip
from PIL import (
    Image,
    ImageColor,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
    ImageGrab,
    ImageOps,
    ImageStat,
    ImageTk,
)


def resource(relative_path):
    base_path = getattr(sys, "_MEIPASS", path.dirname(path.abspath(__file__)))
    return path.join(base_path, relative_path)


class Brushshe(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("680x600")
        if name == "nt":
            self.iconbitmap(resource("icons/icon.ico"))
        else:
            self.iconphoto(True, PhotoImage(file=resource("icons/icon.png")))
        ctk.set_default_color_theme(resource("brushshe_theme.json"))
        ctk.set_appearance_mode("system")
        self.protocol("WM_DELETE_WINDOW", self.when_closing)

        # Get system locale
        locale = getlocale()

        if isinstance(locale, tuple) and all(isinstance(item, str) for item in locale):
            language_code = locale[0][:2].lower()
        elif isinstance(locale, str):
            language_code = locale[:2].lower()
        else:
            language_code = None

        self.translations = {}
        self.load_language(language_code)
        self.initialization()

        self.title(self._("Brushshe"))

    """Translate app"""

    def load_language(self, language_code):
        if language_code == "en":
            pass
        else:
            try:
                with open(
                    resource(f"locales/{language_code}.json"),
                    "r",
                    encoding="utf-8",
                ) as f:
                    self.translations = json.load(f)
            except FileNotFoundError:
                print(f"File for language '{language_code}' not found.")
            except json.JSONDecodeError:
                CTkMessagebox(
                    title="Oh, unfortunately, it happened",
                    message="Localization file is corrupted. Brushshe will be in English.",
                    icon=resource("icons/cry.png"),
                    icon_size=(100, 100),
                    sound=True,
                )

    def _(self, key):
        return self.translations.get(key, key)

    def initialization(self):
        self.colors = [
            "white",
            "black",
            "red",
            "#2eff00",
            "blue",
            "yellow",
            "purple",
            "cyan",
            "pink",
            "orange",
            "brown",
            "gray",
        ]

        """ Menu """
        menu = CTkMenuBar(self)

        file_menu = menu.add_cascade(self._("File"))
        file_dropdown = CustomDropdownMenu(widget=file_menu)
        file_dropdown.add_option(option=self._("Open from file"), command=self.open_from_file)
        save_submenu = file_dropdown.add_submenu(self._("Save to device"))
        formats = ["PNG", "JPG", "GIF", "BMP", "TIFF", "WEBP", "ICO", "PPM", "PGM", "PBM"]
        for fmt in formats:
            save_submenu.add_option(option=fmt, command=lambda fmt=fmt: self.save_to_device(f".{fmt.lower()}"))
        file_dropdown.add_separator()
        file_dropdown.add_option(option=self._("Rotate right"), command=lambda: self.rotate(-90))
        file_dropdown.add_option(option=self._("Rotate left"), command=lambda: self.rotate(90))

        new_menu = menu.add_cascade(self._("New"))
        new_dropdown = CustomDropdownMenu(widget=new_menu)

        for color in self.colors:
            new_dropdown.add_option(option=None, bg_color=color, command=lambda c=color: self.new_picture(c))
        new_dropdown.add_separator()
        new_dropdown.add_option(option=self._("Other color"), command=self.other_bg_color)
        new_dropdown.add_option(option=self._("Create screenshot"), command=self.create_screenshot)

        add_menu = menu.add_cascade(self._("Add"))
        add_dropdown = CustomDropdownMenu(widget=add_menu)
        smile_icon = ctk.CTkImage(light_image=Image.open(resource("icons/smile.png")), size=(50, 50))
        add_dropdown.add_option(
            option=self._("Stickers"),
            image=smile_icon,
            command=self.show_stickers_choice,
        )
        text_icon = ctk.CTkImage(light_image=Image.open(resource("icons/text.png")), size=(50, 50))
        add_dropdown.add_option(self._("Text"), image=text_icon, command=self.show_text_window)
        frame_icon = ctk.CTkImage(light_image=Image.open(resource("icons/frame.png")), size=(50, 50))
        add_dropdown.add_option(option=self._("Frames"), image=frame_icon, command=self.show_frame_choice)
        effects_icon = ctk.CTkImage(light_image=Image.open(resource("icons/effects.png")), size=(50, 50))
        add_dropdown.add_option(option=self._("Effects"), image=effects_icon, command=self.effects)

        shapes_menu = menu.add_cascade(self._("Shapes"))
        shapes_dropdown = CustomDropdownMenu(widget=shapes_menu)
        shape_options = [
            "Rectangle",
            "Oval",
            "Line",
            "Fill rectangle",
            "Fill oval",
        ]
        for shape in shape_options:
            shapes_dropdown.add_option(option=self._(shape), command=lambda shape=shape: self.create_shape(shape))

        menu.add_cascade(self._("My Gallery"), command=self.show_gallery)

        other_menu = menu.add_cascade(self._("More"))
        other_dropdown = CustomDropdownMenu(widget=other_menu)
        theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_checkbox = ctk.CTkCheckBox(
            other_dropdown,
            text=self._("Dark theme"),
            variable=theme_var,
            onvalue="Dark",
            offvalue="Light",
            command=lambda: ctk.set_appearance_mode(theme_var.get()),
        )
        theme_checkbox.pack(padx=10, pady=10)
        other_dropdown.add_option(option=self._("About program"), command=self.about_program)

        """Toolbar"""
        tools_frame = ctk.CTkFrame(self)
        tools_frame.pack(side=ctk.TOP, fill=ctk.X)

        brush_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/brush_light.png")),
            dark_image=Image.open(resource("icons/brush_dark.png")),
            size=(20, 20),
        )
        brush_button = ctk.CTkButton(tools_frame, text=None, width=30, image=brush_icon, command=self.brush)
        brush_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(brush_button, message=self._("Brush"), text_color="gray14")

        eraser_icon = ctk.CTkImage(light_image=Image.open(resource("icons/eraser.png")), size=(20, 20))
        eraser_button = ctk.CTkButton(tools_frame, text=None, width=30, image=eraser_icon, command=self.eraser)
        eraser_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(eraser_button, message=self._("Eraser"), text_color="gray14")

        fill_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/fill_light.png")),
            dark_image=Image.open(resource("icons/fill_dark.png")),
            size=(20, 20),
        )
        fill_button = ctk.CTkButton(tools_frame, text=None, width=30, image=fill_icon, command=self.start_fill)
        fill_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(fill_button, message=self._("Fill"), text_color="gray14")

        undo_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/undo_light.png")),
            dark_image=Image.open(resource("icons/undo_dark.png")),
            size=(20, 20),
        )
        undo_button = ctk.CTkButton(tools_frame, text=None, width=30, image=undo_icon, command=self.undo)
        undo_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(undo_button, message=self._("Undo") + " (Ctrl+Z)", text_color="gray14")

        redo_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/redo_light.png")),
            dark_image=Image.open(resource("icons/redo_dark.png")),
            size=(20, 20),
        )
        redo_button = ctk.CTkButton(tools_frame, text=None, width=30, image=redo_icon, command=self.redo)
        redo_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(redo_button, message=self._("Redo") + " (Ctrl+Y)", text_color="gray14")

        self.tool_label = ctk.CTkLabel(tools_frame, text=None)
        self.tool_label.pack(side=ctk.LEFT, padx=1)

        self.tool_size_slider = ctk.CTkSlider(tools_frame, command=self.change_tool_size)
        self.tool_size_slider.pack(side=ctk.LEFT, padx=1)
        self.tool_size_tooltip = CTkToolTip(self.tool_size_slider, text_color="gray14")

        self.tool_size_label = ctk.CTkLabel(tools_frame, text=None)
        self.tool_size_label.pack(side=ctk.LEFT, padx=1)

        save_to_gallery_btn = ctk.CTkButton(tools_frame, text=self._("Save to gallery"), command=self.save_to_gallery)
        save_to_gallery_btn.pack(side=ctk.RIGHT, padx=1)
        CTkToolTip(save_to_gallery_btn, message=self._("Save to gallery") + " (Ctrl+S)", text_color="gray14")

        """Canvas"""
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.pack_propagate(False)
        self.canvas_frame.pack(fill=ctk.BOTH, expand=True)

        self.width_slider = ctk.CTkSlider(
            self.canvas_frame,
            from_=100,
            to=2000,
            orientation="horizontal",
            command=lambda val: self.canvas.configure(width=int(val)),
        )
        self.width_slider.pack(side=ctk.BOTTOM, fill=ctk.X)
        self.width_slider.bind("<ButtonRelease-1>", self.crop_picture)

        self.height_slider = ctk.CTkSlider(
            self.canvas_frame,
            from_=100,
            to=2000,
            orientation="vertical",
            command=lambda val: self.canvas.configure(height=int(val)),
        )
        self.height_slider.pack(side=ctk.LEFT, fill=ctk.Y)
        self.height_slider.bind("<ButtonRelease-1>", self.crop_picture)

        self.v_scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical")
        self.v_scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y)

        self.h_scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="horizontal")
        self.h_scrollbar.pack(side=ctk.BOTTOM, fill=ctk.X)

        self.canvas = ctk.CTkCanvas(
            self.canvas_frame, yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set
        )
        self.canvas.pack()

        self.v_scrollbar.configure(command=self.canvas.yview)
        self.h_scrollbar.configure(command=self.canvas.xview)

        """Palette"""
        self.palette = ctk.CTkFrame(self)
        self.palette.pack(side=ctk.BOTTOM, fill=ctk.X)

        for color in self.colors:
            color_btn = ctk.CTkButton(
                self.palette,
                fg_color=color,
                text=None,
                width=30,
                border_width=2,
                command=lambda c=color: self.change_color(c),
            )
            color_btn.pack(side=ctk.LEFT, padx=1)

        choice_other_color = ctk.CTkButton(
            self.palette,
            text=self._("Other"),
            command=self.other_color_choice,
        )
        choice_other_color.pack(side=ctk.RIGHT, padx=1)

        self.other_color_btn = ctk.CTkButton(
            self.palette,
            text=None,
            width=30,
            border_width=2,
            command=self.select_other_color_btn,
        )
        self.other_color_tooltip = CTkToolTip(self.other_color_btn, message=None, text_color="gray14")

        """ Initialization """
        self.brush_color = "black"
        self.bg_color = "white"
        self.undo_stack = deque(maxlen=10)
        self.redo_stack = deque(maxlen=10)

        self.brush_size = 2
        self.eraser_size = 4
        self.shape_size = 2
        self.sticker_size = 100
        self.font_size = 24

        self.update()  # update interface before calculate picture size
        self.brush()
        self.new_picture(self.bg_color)

        self.prev_x, self.prev_y = (None, None)
        self.font_path = resource("fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf")
        self.canvas.bind("<Button-3>", self.eyedropper)

        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-y>", lambda e: self.redo())
        self.bind("<Control-s>", lambda e: self.save_to_gallery())

        """Defining the Gallery Folder Path"""
        if name == "nt":  # For Windows
            images_folder = Path(environ["USERPROFILE"]) / "Pictures"
        else:  # For macOS and Linux
            images_folder = Path(environ.get("XDG_PICTURES_DIR", str(Path.home())))

        self.gallery_folder = images_folder / "Brushshe Images"

        if not self.gallery_folder.exists():
            self.gallery_folder.mkdir(parents=True)

        # Width and height of all sticker images - 88 px
        stickers_names = [
            "smile",
            "flower",
            "heart",
            "okay",
            "cheese",
            "face2",
            "cat",
            "alien",
            "like",
            "unicorn",
            "pineapple",
            "grass",
            "rain",
            "brucklin",
            "brushshe",
            "strawberry",
            "butterfly",
            "flower2",
        ]
        self.stickers = [Image.open(resource(f"stickers/{name}.png")) for name in stickers_names]

    """ Functionality """

    def when_closing(self):
        closing_msg = CTkMessagebox(
            title=self._("You are leaving Brushshe"),
            message=self._("Continue?"),
            option_1=self._("Yes"),
            option_2=self._("No"),
            icon=resource("icons/question.png"),
            icon_size=(100, 100),
            sound=True,
        )
        if closing_msg.get() == self._("Yes"):
            app.destroy()

    def paint(self, event):
        x, y = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        if self.prev_x is not None and self.prev_y is not None:
            self.draw_line(self.prev_x, self.prev_y, x, y)
        else:
            self.draw_line(x, y, x, y)
        self.update_canvas()
        self.prev_x, self.prev_y = x, y

    def stop_paint(self, event):
        self.prev_x, self.prev_y = (None, None)
        self.undo_stack.append(self.image.copy())

    def draw_line(self, x1, y1, x2, y2):
        if self.current_tool == "brush":
            color = self.brush_color
        elif self.current_tool == "eraser":
            color = self.bg_color

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            # Better variant for pixel compatible.
            if self.tool_size <= 1:
                self.draw.point([x1, y1], fill=color)
            else:
                self.draw.ellipse(
                    [
                        x1 - (self.tool_size - 1) // 2,
                        y1 - (self.tool_size - 1) // 2,
                        x1 + self.tool_size // 2,
                        y1 + self.tool_size // 2,
                    ],
                    fill=color,
                    outline=color,
                )

            if abs(x1 - x2) < 1 and abs(y1 - y2) < 1:
                break

            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def update_canvas(self):
        self.canvas.delete("all")

        self.img_tk = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=ctk.NW, image=self.img_tk)

    def crop_picture(self, event):
        new_image = Image.new("RGB", (int(self.width_slider.get()), int(self.height_slider.get())), self.bg_color)
        new_image.paste(self.image, (0, 0))
        self.image = new_image
        self.draw = ImageDraw.Draw(self.image)
        self.update_canvas()
        self.undo_stack.append(self.image.copy())
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def eyedropper(self, event):
        # Get the coordinates of the click event
        x, y = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

        color = self.image.getpixel((x, y))
        self.obtained_color = "#{:02x}{:02x}{:02x}".format(*color)

        self.brush_color = self.obtained_color
        self.other_color_btn.pack(side=ctk.RIGHT, padx=1)
        self.other_color_btn.configure(fg_color=self.obtained_color)
        self.other_color_tooltip.configure(message=self.obtained_color)

    def start_fill(self):  # beta
        self.set_tool("fill", "Fill", None, None, None, "spraycan")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.bind("<Button-1>", self.fill)

    def fill(self, event):
        x, y = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        ImageDraw.floodfill(self.image, (x, y), ImageColor.getrgb(self.brush_color))
        self.update_canvas()
        self.undo_stack.append(self.image.copy())

    def open_from_file(self):
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[
                (self._("Images"), "*png* *jpg* *jpeg* *gif* *ico* *bmp* *webp* *tiff* *ppm* *pgm* *pbm*"),
                (self._("All files"), "*.*"),
            ]
        )
        if file_path:
            try:
                self.open_image(file_path)
            except Exception as e:
                self.open_file_error(e)

    def save_to_device(self, extension):
        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[(self._("All files"), "*.*")],
        )
        if file_path:
            self.image.save(file_path)
            CTkMessagebox(
                title=self._("Saved"),
                message=self._("The picture has been successfully saved to your device in format") + f" {extension}!",
                icon=resource("icons/saved.png"),
                icon_size=(100, 100),
            )

    def other_bg_color(self):
        askcolor = AskColor(title=self._("Choose a different background color"))
        obtained_bg_color = askcolor.get()
        if obtained_bg_color:
            self.new_picture(obtained_bg_color)

    def show_stickers_choice(self):
        def sticker_from_file():
            file_path = ctk.filedialog.askopenfilename(
                filetypes=[
                    (self._("Images"), "*png* *jpg* *jpeg* *gif* *ico* *bmp* *webp* *tiff* *ppm* *pgm* *pbm*"),
                    (self._("All files"), "*.*"),
                ]
            )
            if file_path:
                try:
                    sticker_image = Image.open(file_path)
                    self.set_current_sticker(sticker_image)
                except Exception as e:
                    self.open_file_error(e)

        sticker_choose = ctk.CTkToplevel(app)
        sticker_choose.geometry("350x420")
        sticker_choose.title(self._("Choose a sticker"))

        tabview = ctk.CTkTabview(sticker_choose)
        tabview.add(self._("Choose a sticker"))
        tabview.add(self._("Sticker from file"))
        tabview.set(self._("Choose a sticker"))
        tabview.pack(fill=ctk.BOTH, expand=True)

        stickers_scrollable_frame = ctk.CTkScrollableFrame(tabview.tab(self._("Choose a sticker")))
        stickers_scrollable_frame.pack(fill=ctk.BOTH, expand=True)

        stickers_frame = ctk.CTkFrame(stickers_scrollable_frame)
        stickers_frame.pack()

        row = 0
        column = 0
        for sticker_image in self.stickers:
            sticker_ctkimage = ctk.CTkImage(light_image=sticker_image, size=(100, 100))
            sticker_btn = ctk.CTkButton(
                stickers_frame,
                text=None,
                image=sticker_ctkimage,
                command=lambda img=sticker_image: self.set_current_sticker(img),
            )
            sticker_btn.grid(row=row, column=column, padx=10, pady=10)
            column += 1
            if column == 2:
                column = 0
                row += 1

        self.sticker_from_file_btn = ctk.CTkButton(
            tabview.tab(self._("Sticker from file")),
            text=self._("Choose sticker from file\nthen click where you want\nit on the picture"),
            command=sticker_from_file,
        )
        self.sticker_from_file_btn.pack(padx=10, pady=10)

    def set_current_sticker(self, sticker_image):  # Choose a sticker
        self.set_tool("sticker", "Stickers", self.sticker_size, 10, 175, "cross")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")

        self.canvas.bind("<Button-1>", lambda event: self.add_sticker(event, sticker_image))

    def add_sticker(self, event, sticker_image):  # Add a sticker
        sticker_image = sticker_image.resize((self.tool_size, self.tool_size))
        x, y = (int(self.canvas.canvasx(event.x)), int(self.canvas.canvasy(event.y)))
        if sticker_image.mode == "RGBA":
            self.image.paste(
                sticker_image, (x - sticker_image.width // 2, y - sticker_image.height // 2), sticker_image
            )
        else:
            self.image.paste(sticker_image, (x - sticker_image.width // 2, y - sticker_image.height // 2))

        self.update_canvas()
        self.undo_stack.append(self.image.copy())

    def add_text(self, event, text):  # Add text
        x, y = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        imagefont = ImageFont.truetype(self.font_path, self.tool_size)

        bbox = self.draw.textbbox((x, y), text, font=imagefont)

        # Text size
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        self.draw.text((x - text_width // 2, y - text_height // 2), text, fill=self.brush_color, font=imagefont)

        self.update_canvas()
        self.undo_stack.append(self.image.copy())
        if self.tx_message_label.winfo_exists():
            self.tx_message_label.configure(text="\n")

    def show_text_window(self):
        def optionmenu_callback(value):
            self.font_path = resource(fonts_dict.get(value))
            self.imagefont = ImageFont.truetype(self.font_path, self.tool_size)

        def add_text_ready():
            self.tx_message_label.configure(text=self._("Now click where you\nwant it on the picture"))
            text = tx_entry.get()
            self.set_tool("text", "Text", self.font_size, 11, 96, "cross")

            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<ButtonRelease-1>")

            self.canvas.bind("<Button-1>", lambda event, t=text: self.add_text(event, text))

        text_win = ctk.CTkToplevel(app)
        text_win.title(self._("Add text to a picture"))

        tx_entry = ctk.CTkEntry(text_win, placeholder_text=self._("Enter text..."))
        tx_entry.pack(padx=10, pady=10)

        fonts_label = ctk.CTkLabel(text_win, text=self._("Fonts:"))
        fonts_label.pack(padx=10, pady=10)

        fonts_dict = {
            "Open Sans": "fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf",
            "Sigmar": "fonts/Sigmar/Sigmar-Regular.ttf",
            "Playwrite IT Moderna": "fonts/Playwrite_IT_Moderna/PlaywriteITModerna-VariableFont_wght.ttf",
            "Monomakh": "fonts/Monomakh/Monomakh-Regular.ttf",
        }
        fonts = list(fonts_dict.keys())

        fonts_optionmenu = ctk.CTkOptionMenu(text_win, values=fonts, command=optionmenu_callback)
        fonts_optionmenu.pack(padx=10, pady=10)

        tx_ok_btn = ctk.CTkButton(text_win, text="OK", command=add_text_ready)
        tx_ok_btn.pack(padx=10, pady=10)

        self.tx_message_label = ctk.CTkLabel(text_win, text="\n")
        self.tx_message_label.pack(padx=10, pady=10)

    def show_frame_choice(self):
        def on_frames_click(index):
            selected_frame = frames[index]
            resized_frame = selected_frame.resize((self.canvas.winfo_width(), self.canvas.winfo_height()))

            self.image.paste(resized_frame, (0, 0), resized_frame)

            self.update_canvas()
            self.undo_stack.append(self.image.copy())

        frames_win = ctk.CTkToplevel(app)
        frames_win.title(self._("Frames"))

        frames_names = [
            "frame1",
            "frame2",
            "frame3",
            "frame4",
            "frame5",
            "frame6",
            "frame7",
        ]
        frames_thumbnails = [
            ctk.CTkImage(light_image=Image.open(resource(f"frames_preview/{name}.png")), size=(100, 100))
            for name in frames_names
        ]

        frames = [Image.open(resource(f"frames/{name}.png")) for name in frames_names]

        row = 0
        column = 0

        for i, image in enumerate(frames_thumbnails):
            frames_btn = ctk.CTkButton(
                frames_win,
                text=None,
                image=image,
                command=lambda i=i: on_frames_click(i),
            )
            frames_btn.grid(column=column, row=row, padx=10, pady=10)

            column += 1
            if column == 2:
                column = 0
                row += 1

    # Shape creation functions
    def create_shape(self, shape):
        def start_shape(event):
            self.shape_x, self.shape_y = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            self.get_contrast_color()

            shape_methods = {
                "Rectangle": self.canvas.create_rectangle,
                "Oval": self.canvas.create_oval,
                "Line": self.canvas.create_line,
                "Fill rectangle": self.canvas.create_rectangle,
                "Fill oval": self.canvas.create_oval,
            }

            create_method = shape_methods.get(shape)
            if create_method:
                param = "fill" if shape == "Line" else "outline"
                self.shape_id = create_method(
                    self.shape_x, self.shape_y, self.shape_x, self.shape_y, **{param: self.contrast_color}
                )

        def draw_shape(event):
            if not hasattr(self, "shape_x"):
                return
            x, y = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            self.canvas.coords(self.shape_id, self.shape_x, self.shape_y, x, y)

        def end_shape(event):
            if not hasattr(self, "shape_x"):
                return
            x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            if self.shape_x < x:
                x0, x1 = self.shape_x, x
            else:
                x0, x1 = x, self.shape_x
            if self.shape_y < y:
                y0, y1 = self.shape_y, y
            else:
                y0, y1 = y, self.shape_y

            if shape == "Rectangle":
                self.draw.rectangle([x0, y0, x1, y1], outline=self.brush_color, width=self.tool_size)
            elif shape == "Oval":
                self.draw.ellipse([x0, y0, x1, y1], outline=self.brush_color, width=self.tool_size)
            elif shape == "Line":
                self.draw.line([self.shape_x, self.shape_y, x, y], fill=self.brush_color, width=self.tool_size)
                # for rounded ends
                self.draw.ellipse(
                    [
                        self.shape_x - self.tool_size / 2,
                        self.shape_y - self.tool_size / 2,
                        self.shape_x + self.tool_size / 2,
                        self.shape_y + self.tool_size / 2,
                    ],
                    fill=self.brush_color,
                )
                self.draw.ellipse(
                    [
                        x - self.tool_size / 2,
                        y - self.tool_size / 2,
                        x + self.tool_size / 2,
                        y + self.tool_size / 2,
                    ],
                    fill=self.brush_color,
                )
            elif shape == "Fill rectangle":
                self.draw.rectangle([x0, y0, x1, y1], fill=self.brush_color)
            elif shape == "Fill oval":
                self.draw.ellipse([x0, y0, x1, y1], fill=self.brush_color)
            self.update_canvas()
            self.undo_stack.append(self.image.copy())

        if shape == "Fill rectangle" or shape == "Fill oval":
            self.set_tool("shape", shape, None, None, None, "plus")
        else:
            self.set_tool("shape", shape, self.shape_size, 1, 50, "plus")

        self.canvas.unbind("<Button-1>")
        self.canvas.bind("<ButtonPress-1>", start_shape)
        self.canvas.bind("<B1-Motion>", draw_shape)
        self.canvas.bind("<ButtonRelease-1>", end_shape)

    def effects(self):
        def post_actions():
            self.update_canvas()
            self.draw = ImageDraw.Draw(self.image)
            self.undo_stack.append(self.image.copy())

        def remove_all_effects():
            self.image = image_copy
            post_actions()

        def blur():
            radius = blur_slider.get()
            self.image = image_copy.filter(ImageFilter.GaussianBlur(radius=radius))
            post_actions()

        def detail():
            factor = detail_slider.get()
            enhancer = ImageEnhance.Sharpness(image_copy)
            self.image = enhancer.enhance(factor)
            post_actions()

        def contour():
            self.image = image_copy.filter(ImageFilter.CONTOUR)
            post_actions()

        def grayscale():
            self.image = ImageOps.grayscale(image_copy)
            post_actions()

        def mirror():
            self.image = ImageOps.mirror(image_copy)
            post_actions()

        def metal():
            self.image = image_copy.filter(ImageFilter.EMBOSS)
            post_actions()

        effects_win = ctk.CTkToplevel(app)
        effects_win.title(self._("Effects"))
        effects_win.geometry("250x500")

        effects_frame = ctk.CTkScrollableFrame(effects_win)
        effects_frame.pack(fill=ctk.BOTH, expand=True)

        remove_all_effects_button = ctk.CTkButton(
            effects_win,
            text=self._("Remove all effects"),
            command=remove_all_effects,
            fg_color="red",
            text_color="white",
        )
        remove_all_effects_button.pack(padx=10, pady=10)

        # Blur
        blur_frame = ctk.CTkFrame(effects_frame)
        blur_frame.pack(padx=10, pady=10)

        blur_label = ctk.CTkLabel(blur_frame, text=self._("Blur"))
        blur_label.pack(padx=10, pady=10)

        blur_slider = ctk.CTkSlider(blur_frame, from_=0, to=20)
        blur_slider.pack(padx=10, pady=10)

        blur_button = ctk.CTkButton(blur_frame, text=self._("Apply to picture"), command=blur)
        blur_button.pack(padx=10, pady=10)

        # Detail
        detail_frame = ctk.CTkFrame(effects_frame)
        detail_frame.pack(padx=10, pady=10)

        detail_label = ctk.CTkLabel(detail_frame, text=self._("Detail"))
        detail_label.pack(padx=10, pady=10)

        detail_slider = ctk.CTkSlider(detail_frame, from_=1, to=20)
        detail_slider.pack(padx=10, pady=10)

        detail_button = ctk.CTkButton(detail_frame, text=self._("Apply to picture"), command=detail)
        detail_button.pack(padx=10, pady=10)

        effects_dict = {  # dictionary for effects which without slider
            "Contour": contour,
            "Grayscale": grayscale,
            "Mirror": mirror,
            "Metal": metal,
        }

        for effect_name, effect_command in effects_dict.items():
            effect_frame = ctk.CTkFrame(effects_frame)
            effect_frame.pack(padx=10, pady=10)

            effect_label = ctk.CTkLabel(effect_frame, text=self._(effect_name))
            effect_label.pack(padx=10, pady=10)

            effect_button = ctk.CTkButton(effect_frame, text=self._("Apply to picture"), command=effect_command)
            effect_button.pack(padx=10, pady=10)

        image_copy = self.image.copy()

        effects_win.grab_set()  # Disable main window

    def show_gallery(self):
        self.my_gallery = ctk.CTkToplevel(app)
        self.my_gallery.title(self._("Brushshe Gallery (loading...)"))
        self.my_gallery.geometry("650x580")

        gallery_scrollable_frame = ctk.CTkScrollableFrame(self.my_gallery, label_text=self._("My Gallery"))
        gallery_scrollable_frame.pack(fill=ctk.BOTH, expand=True)

        gallery_frame = ctk.CTkFrame(gallery_scrollable_frame)
        gallery_frame.pack(padx=10, pady=10)

        row = 0
        column = 0

        is_image_found = False

        for filename in listdir(self.gallery_folder):
            if filename.endswith(".png"):
                is_image_found = True
                img_path = self.gallery_folder / filename
                img = Image.open(img_path)

                button_image = ctk.CTkImage(img, size=(250, 250))
                image_button = ctk.CTkButton(
                    gallery_frame,
                    image=button_image,
                    text=None,
                    command=lambda img_path=img_path: self.open_image(img_path),
                )
                image_button.grid(row=row, column=column, padx=10, pady=10)

                delete_image_button = ctk.CTkButton(
                    image_button,
                    text="x",
                    fg_color="red",
                    text_color="white",
                    width=30,
                    command=lambda img_path=img_path: self.delete_image(img_path),
                )
                delete_image_button.place(x=5, y=5)
                CTkToolTip(delete_image_button, message=self._("Delete"))

                column += 1
                if column == 2:
                    column = 0
                    row += 1

        if not is_image_found:
            gallery_frame.configure(label_text=self._("My gallery (empty)"))

        self.my_gallery.title(self._("Brushshe Gallery"))

    def delete_image(self, img_path):
        confirm_delete = CTkMessagebox(
            title=self._("Confirm delete"),
            message=self._("Are you sure you want to delete the picture?"),
            icon=resource("icons/question.png"),
            icon_size=(100, 100),
            option_1=self._("Yes"),
            option_2=self._("No"),
            sound=True,
        )
        if confirm_delete.get() == self._("Yes") and path.exists(str(img_path)):
            remove(str(img_path))
            self.my_gallery.destroy()
            self.show_gallery()

    def about_program(self):
        about_text = self._(
            "Brushshe is a painting program where you can create whatever you like.\n\n"
            "An eagle named Brucklin is its mascot.\n\n"
        )
        about_msg = CTkMessagebox(
            title=self._("About program"),
            message=about_text + "v1.7.0",
            icon=resource("icons/brucklin.png"),
            icon_size=(150, 191),
            option_1="OK",
            option_2="GitHub",
            height=400,
        )
        if about_msg.get() == "GitHub":
            webbrowser.open(r"https://github.com/limafresh/Brushshe")

    def new_picture(self, color):
        self.bg_color = color
        img_width = self.canvas_frame.winfo_width() - self.width_slider.winfo_height() - self.h_scrollbar.winfo_height()
        img_height = (
            self.canvas_frame.winfo_height() - self.height_slider.winfo_width() - self.v_scrollbar.winfo_width()
        )
        self.width_slider.set(img_width)
        self.height_slider.set(img_height)

        self.image = Image.new("RGB", (img_width, img_height), color)
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.configure(width=img_width, height=img_height, scrollregion=self.canvas.bbox("all"))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.update_canvas()
        self.undo_stack.append(self.image.copy())

    def change_tool_size(self, value):
        self.tool_size = int(value)
        if self.current_tool == "brush":
            self.brush_size = int(value)
        elif self.current_tool == "eraser":
            self.eraser_size = int(value)
        elif self.current_tool == "shape":
            self.shape_size = int(value)
        elif self.current_tool == "sticker":
            self.sticker_size = int(value)
        elif self.current_tool == "text":
            self.font_size = int(value)
        self.tool_size_label.configure(text=self.tool_size)
        self.tool_size_tooltip.configure(message=self.tool_size)

    def brush(self):
        self.set_tool("brush", "Brush", self.brush_size, 1, 50, "pencil")

        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<ButtonRelease-1>")

        self.canvas.bind("<Button-1>", self.paint)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)

    def eraser(self):
        self.set_tool("eraser", "Eraser", self.eraser_size, 1, 50, "target")

        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<ButtonRelease-1>")

        self.canvas.bind("<Button-1>", self.paint)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)

    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self.image = self.undo_stack[-1].copy()
            self.draw = ImageDraw.Draw(self.image)
            if self.image.width != self.canvas.winfo_width() or self.image.height != self.canvas.winfo_height():
                self.canvas.configure(
                    width=self.image.width, height=self.image.height, scrollregion=self.canvas.bbox("all")
                )
                self.width_slider.set(self.image.width)
                self.height_slider.set(self.image.height)
            self.update_canvas()

    def redo(self):
        if len(self.redo_stack) > 0:
            self.image = self.redo_stack.pop().copy()
            self.undo_stack.append(self.image.copy())
            self.draw = ImageDraw.Draw(self.image)
            if self.image.width != self.canvas.winfo_width() or self.image.height != self.canvas.winfo_height():
                self.canvas.configure(
                    width=self.image.width, height=self.image.height, scrollregion=self.canvas.bbox("all")
                )
                self.width_slider.set(self.image.width)
                self.height_slider.set(self.image.height)
            self.update_canvas()

    def save_to_gallery(self):
        file_path = self.gallery_folder / f"{uuid4()}.png"
        while file_path.exists():
            file_path = self.gallery_folder / f"{uuid4()}.png"
        self.image.save(file_path)

        CTkMessagebox(
            title=self._("Saved"),
            message=self._(
                'The picture has been successfully saved to the gallery ("My Gallery" in the menu at the top)!'
            ),
            icon=resource("icons/saved.png"),
            icon_size=(100, 100),
        )

    def change_color(self, new_color):
        self.brush_color = new_color

    def other_color_choice(self):
        askcolor = AskColor(title=self._("Choose a different brush color"))
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            self.brush_color = self.obtained_color
            self.other_color_btn.pack(side=ctk.RIGHT, padx=1)
            self.other_color_btn.configure(fg_color=self.obtained_color)
            self.other_color_tooltip.configure(message=self.obtained_color)

    def select_other_color_btn(self):
        self.brush_color = self.obtained_color

    def open_image(self, openimage):
        self.bg_color = "white"
        self.image = Image.open(openimage)
        self.draw = ImageDraw.Draw(self.image)
        self.picture_postconfigure()

    def open_file_error(self, e):
        message_text = self._("Error - cannot open file:")
        CTkMessagebox(
            title=self._("Oh, unfortunately, it happened"),
            message=f"{message_text} {e}",
            icon=resource("icons/cry.png"),
            icon_size=(100, 100),
            sound=True,
        )

    def get_contrast_color(self):
        stat = ImageStat.Stat(self.image)
        r, g, b = stat.mean[:3]
        self.contrast_color = "#232323" if (r + g + b) / 3 > 127 else "#e8e8e8"

    def rotate(self, degree):
        rotated_image = self.image.rotate(degree, expand=True)
        self.image = rotated_image
        self.picture_postconfigure()

    def create_screenshot(self):
        self.withdraw()
        self.iconify()
        self.after(200)
        self.image = ImageGrab.grab()
        self.deiconify()
        self.picture_postconfigure()

    def picture_postconfigure(self):
        self.canvas.configure(width=self.image.width, height=self.image.height)
        self.width_slider.set(self.image.width)
        self.height_slider.set(self.image.height)

        self.update_canvas()
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.undo_stack.append(self.image.copy())

    def set_tool(self, tool, tool_name, tool_size, from_, to, cursor):
        self.current_tool = tool
        if tool_size is None and from_ is None and to is None:
            self.tool_label.configure(text=self._(tool_name))
            self.tool_size_slider.pack_forget()
            self.tool_size_label.pack_forget()
        else:
            self.tool_label.configure(text=self._(tool_name) + ":")
            self.tool_size = tool_size
            self.tool_size_slider.configure(from_=from_, to=to)
            self.tool_size_slider.set(self.tool_size)
            self.tool_size_slider.pack(side=ctk.LEFT, padx=1)
            self.tool_size_label.configure(text=self.tool_size)
            self.tool_size_label.pack(side=ctk.LEFT, padx=1)
            self.tool_size_tooltip.configure(message=self.tool_size)
        self.canvas.configure(cursor=cursor)


app = Brushshe()
app.mainloop()
