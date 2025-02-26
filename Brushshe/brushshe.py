import json
import webbrowser
from collections import deque
from locale import getlocale
from os import environ, listdir, name, path
from pathlib import Path
from tkinter import PhotoImage
from uuid import uuid4

import customtkinter as ctk
from brushshe_color_picker import AskColor
from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps, ImageTk

PATH = path.dirname(path.realpath(__file__))


class Brushshe(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Brushshe")
        self.geometry("680x600")
        if name == "nt":
            self.iconbitmap(path.join(PATH, "icons/icon.ico"))
        else:
            self.iconphoto(True, PhotoImage(file=path.join(PATH, "icons/icon.png")))
        ctk.set_default_color_theme(path.join(PATH, "brushshe_theme.json"))
        ctk.set_appearance_mode("system")
        self.protocol("WM_DELETE_WINDOW", self.when_closing)

        # Get system locale
        locale = getlocale()

        if isinstance(locale, tuple):
            language_code = getlocale()[0][:2].lower()
        elif isinstance(locale, str):
            language_code = locale[:2].lower()
        else:
            language_code = None

        self.translations = {}
        self.load_language(language_code)
        self.initialization()

    """Translate app"""

    def load_language(self, language_code):
        if language_code == "en":
            pass
        else:
            try:
                with open(
                    path.join(PATH, f"locales/{language_code}.json"),
                    "r",
                    encoding="utf-8",
                ) as f:
                    self.translations = json.load(f)
            except FileNotFoundError:
                print(f"File for language '{language_code}' not found.")
                self.translations = {}

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

        new_menu = menu.add_cascade(self._("New"))
        new_dropdown = CustomDropdownMenu(widget=new_menu)

        for color in self.colors:
            new_dropdown.add_option(option=None, bg_color=color, command=lambda c=color: self.new_picture(c))
        new_dropdown.add_separator()
        new_dropdown.add_option(option=self._("Other color"), command=self.other_bg_color)

        add_menu = menu.add_cascade(self._("Add"))
        add_dropdown = CustomDropdownMenu(widget=add_menu)
        smile_icon = ctk.CTkImage(light_image=Image.open(path.join(PATH, "icons/smile.png")), size=(50, 50))
        add_dropdown.add_option(
            option=self._("Stickers"),
            image=smile_icon,
            command=self.show_stickers_choice,
        )
        text_icon = ctk.CTkImage(light_image=Image.open(path.join(PATH, "icons/text.png")), size=(50, 50))
        add_dropdown.add_option(self._("Text"), image=text_icon, command=self.show_text_window)
        frame_icon = ctk.CTkImage(light_image=Image.open(path.join(PATH, "icons/frame.png")), size=(50, 50))
        add_dropdown.add_option(option=self._("Frames"), image=frame_icon, command=self.show_frame_choice)
        effects_icon = ctk.CTkImage(light_image=Image.open(path.join(PATH, "icons/effects.png")), size=(50, 50))
        add_dropdown.add_option(
            option=self._("Effects"), image=effects_icon, command=lambda: self.after(1000, self.effects)
        )

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
            shapes_dropdown.add_option(
                option=self._(shape), command=lambda shape=shape: self.create_shape(shape.lower())
            )

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

        eraser_icon = ctk.CTkImage(light_image=Image.open(path.join(PATH, "icons/eraser.png")), size=(20, 20))
        eraser = ctk.CTkButton(tools_frame, text=None, width=35, image=eraser_icon, command=self.eraser)
        eraser.pack(side=ctk.LEFT, padx=1)

        undo_icon = ctk.CTkImage(
            light_image=Image.open(path.join(PATH, "icons/undo_light.png")),
            dark_image=Image.open(path.join(PATH, "icons/undo_dark.png")),
            size=(20, 20),
        )
        undo_button = ctk.CTkButton(tools_frame, text=None, width=35, image=undo_icon, command=self.undo)
        undo_button.pack(side=ctk.LEFT, padx=1)

        self.tool_label = ctk.CTkLabel(tools_frame, text=self._("Brush:"))
        self.tool_label.pack(side=ctk.LEFT, padx=1)

        size_slider = ctk.CTkSlider(tools_frame, from_=1, to=50, command=self.change_brush_size)
        self.brush_size = 2
        size_slider.set(self.brush_size)
        size_slider.pack(side=ctk.LEFT, padx=1)

        self.brush_size_label = ctk.CTkLabel(tools_frame, text="2")
        self.brush_size_label.pack(side=ctk.LEFT, padx=1)

        save_to_gallery_btn = ctk.CTkButton(
            tools_frame,
            text=self._("Save to gallery"),
            width=70,
            command=self.save_to_gallery,
        )
        save_to_gallery_btn.pack(side=ctk.RIGHT, padx=1)

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

        self.canvas = ctk.CTkCanvas(self.canvas_frame)
        self.canvas.pack()

        """Palette"""
        self.palette = ctk.CTkFrame(self)
        self.palette.pack(side=ctk.BOTTOM, fill=ctk.X)

        for color in self.colors:
            color_btn = ctk.CTkButton(
                self.palette,
                fg_color=color,
                text=None,
                width=35,
                border_width=2,
                command=lambda c=color: self.change_color(c),
            )
            color_btn.pack(side=ctk.LEFT, padx=1)

        choice_other_color = ctk.CTkButton(
            self.palette,
            text=self._("Other"),
            width=70,
            command=self.other_color_choise,
        )
        choice_other_color.pack(side=ctk.RIGHT, padx=1)

        self.other_color_btn = ctk.CTkButton(
            self.palette,
            text=None,
            width=35,
            border_width=2,
            command=self.select_other_color_btn,
        )

        """ Initialization """
        self.color = "black"
        self.bg_color = "white"
        self.undo_stack = deque(maxlen=10)

        self.update()  # update interface before calculate picture size
        self.new_picture("white")

        self.prev_x, self.prev_y = (None, None)

        self.font_size = 24
        self.font_path = path.join(PATH, "fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf")
        self.size_a = 100

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<Button-3>", self.eyedropper)

        self.canvas.configure(cursor="pencil")

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
        self.stickers = [Image.open(path.join(PATH, f"stickers/{name}.png")) for name in stickers_names]

    """ Functionality """

    def when_closing(self):
        closing_msg = CTkMessagebox(
            title=self._("You are leaving Brushshe"),
            message=self._("Continue?"),
            option_1=self._("Yes"),
            option_2=self._("No"),
            icon=path.join(PATH, "icons/question.png"),
            icon_size=(100, 100),
            sound=True,
        )
        if closing_msg.get() == self._("Yes"):
            app.destroy()
        else:
            pass

    def paint(self, event):
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)
        if self.prev_x is not None and self.prev_y is not None:
            self.draw_thick_line(self.prev_x, self.prev_y, event.x, event.y)
            self.update_canvas()
        self.prev_x, self.prev_y = event.x, event.y

    def stop_paint(self, event):
        self.prev_x, self.prev_y = (None, None)
        self.undo_stack.append(self.image.copy())

    def draw_thick_line(self, x1, y1, x2, y2):
        steps = max(abs(x2 - x1), abs(y2 - y1))

        for i in range(steps):
            t = i / steps
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)

            self.draw.ellipse(
                [
                    x - self.brush_size // 2,
                    y - self.brush_size // 2,
                    x + self.brush_size // 2,
                    y + self.brush_size // 2,
                ],
                fill=self.color,
                outline=self.color,
            )

    def update_canvas(self):
        self.canvas.delete("all")

        self.img_tk = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=ctk.NW, image=self.img_tk)

    def crop_picture(self, event):
        new_image = Image.new("RGB", (self.canvas.winfo_width(), self.canvas.winfo_height()), self.bg_color)
        new_image.paste(self.image, (0, 0))
        self.image = new_image
        self.draw = ImageDraw.Draw(self.image)
        self.update_canvas()

    def eyedropper(self, event):
        # Get the coordinates of the click event
        x, y = event.x, event.y

        color = self.image.getpixel((x, y))
        self.obtained_color = "#{:02x}{:02x}{:02x}".format(*color)

        self.color = self.obtained_color
        self.other_color_btn.pack(side=ctk.RIGHT, padx=1)
        self.other_color_btn.configure(fg_color=self.obtained_color)
        self.tool_label.configure(text=self._("Brush:"))
        self.canvas.configure(cursor="pencil")

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
                icon=path.join(PATH, "icons/saved.png"),
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
                    self.canvas.bind("<Button-1>", lambda event: self.add_sticker(event, sticker_image))
                    self.canvas.configure(cursor="")
                except Exception as e:
                    self.open_file_error(e)

        def update_btn():
            for widget in stickers_frame.winfo_children():
                widget.destroy()
            row = 0
            column = 0
            for image in self.stickers:
                sticker_image = image.resize((self.size_a, self.size_a))
                sticker_ctkimage = ctk.CTkImage(light_image=image, size=(self.size_a, self.size_a))
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

        sticker_choose = ctk.CTkToplevel(app)
        sticker_choose.geometry("350x420")
        sticker_choose.title(self._("Choose a sticker"))

        tabview = ctk.CTkTabview(sticker_choose, command=update_btn)
        tabview.add(self._("Choose a sticker"))
        tabview.add(self._("Sticker size"))
        tabview.add(self._("Sticker from file"))
        tabview.set(self._("Choose a sticker"))
        tabview.pack(fill=ctk.BOTH, expand=True)

        stickers_frame = ctk.CTkScrollableFrame(tabview.tab(self._("Choose a sticker")))
        stickers_frame.pack(fill=ctk.BOTH, expand=True)

        self.st_size_label = ctk.CTkLabel(tabview.tab(self._("Sticker size")), text=self.size_a)
        self.st_size_label.pack(padx=10, pady=10)
        self.st_slider = ctk.CTkSlider(
            tabview.tab(self._("Sticker size")),
            from_=10,
            to=175,
            command=self.change_sticker_size,
        )
        self.st_slider.set(self.size_a)
        self.st_slider.pack(padx=10, pady=10)
        set_default = ctk.CTkButton(
            tabview.tab(self._("Sticker size")),
            text=self._("Return as it was"),
            command=self.set_default_stickers_size,
        )
        set_default.pack(padx=10, pady=10)

        self.sticker_from_file_btn = ctk.CTkButton(
            tabview.tab(self._("Sticker from file")),
            text=self._("Choose sticker from file\nthen click where you want\nit on the picture"),
            command=sticker_from_file,
        )
        self.sticker_from_file_btn.pack(padx=10, pady=10)

        update_btn()

    def set_current_sticker(self, sticker_image):  # Choose a sticker
        self.canvas.bind("<Button-1>", lambda event: self.add_sticker(event, sticker_image))
        self.canvas.configure(cursor="")

    def add_sticker(self, event, sticker_image):  # Add a sticker
        self.canvas.unbind("<ButtonRelease-1>")

        if sticker_image.mode == "RGBA":
            self.image.paste(
                sticker_image, (event.x - sticker_image.width // 2, event.y - sticker_image.height // 2), sticker_image
            )
        else:
            self.image.paste(sticker_image, (event.x - sticker_image.width // 2, event.y - sticker_image.height // 2))

        self.update_canvas()

        self.canvas.unbind("<Button-1>")
        self.canvas.configure(cursor="pencil")
        self.undo_stack.append(self.image.copy())

    def change_sticker_size(self, value):
        self.size_a = int(self.st_slider.get())
        self.st_size_label.configure(text=self.size_a)

    def set_default_stickers_size(self):
        self.size_a = 100
        self.st_size_label.configure(text=self.size_a)
        self.st_slider.set(self.size_a)

    def add_text(self, event, text):  # Add text
        self.canvas.unbind("<ButtonRelease-1>")
        imagefont = ImageFont.truetype(self.font_path, self.font_size)

        bbox = self.draw.textbbox((event.x, event.y), text, font=imagefont)

        # Text size
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        self.draw.text((event.x - text_width // 2, event.y - text_height // 2), text, fill=self.color, font=imagefont)

        self.update_canvas()
        self.undo_stack.append(self.image.copy())
        self.canvas.unbind("<Button-1>")
        self.canvas.configure(cursor="pencil")
        if self.tx_message_label.winfo_exists():
            self.tx_message_label.configure(text="\n")

    def show_text_window(self):
        def change_text_size(size):
            self.font_size = int(size)
            self.tx_size_label.configure(text=self.font_size)

        def optionmenu_callback(value):
            self.font_path = fonts_dict.get(value)
            self.imagefont = ImageFont.truetype(self.font_path, self.font_size)

        def add_text_ready():
            self.tx_message_label.configure(text=self._("Now click where you\nwant it on the picture"))
            text = tx_entry.get()
            self.canvas.bind("<Button-1>", lambda event, t=text: self.add_text(event, text))
            self.canvas.configure(cursor="")

        text_win = ctk.CTkToplevel(app)
        text_win.title(self._("Add text to a picture"))

        tx_entry = ctk.CTkEntry(text_win, placeholder_text=self._("Enter text..."))
        tx_entry.pack(padx=10, pady=10)

        self.tx_size_label = ctk.CTkLabel(text_win, text=self.font_size)
        self.tx_size_label.pack(padx=10, pady=10)

        tx_size_slider = ctk.CTkSlider(text_win, from_=11, to=96, command=change_text_size)
        tx_size_slider.set(self.font_size)
        tx_size_slider.pack(padx=10, pady=10)

        fonts_label = ctk.CTkLabel(text_win, text=self._("Fonts:"))
        fonts_label.pack(padx=10, pady=10)

        fonts_dict = {
            "Open Sans": path.join(PATH, "fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf"),
            "Sigmar": path.join(PATH, "fonts/Sigmar/Sigmar-Regular.ttf"),
            "Playwrite IT Moderna": path.join(
                PATH, "fonts/Playwrite_IT_Moderna/PlaywriteITModerna-VariableFont_wght.ttf"
            ),
            "Monomakh": path.join(PATH, "fonts/Monomakh/Monomakh-Regular.ttf"),
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
            ctk.CTkImage(light_image=Image.open(path.join(PATH, f"frames_preview/{name}.png")), size=(100, 100))
            for name in frames_names
        ]

        frames = [Image.open(path.join(PATH, f"frames/{name}.png")) for name in frames_names]

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
            self.shape_start_x = event.x
            self.shape_start_y = event.y
            if self.shape == "rectangle":
                self.shape_id = self.canvas.create_rectangle(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    outline=self.color,
                )
            elif self.shape == "oval":
                self.shape_id = self.canvas.create_oval(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    outline=self.color,
                )
            elif self.shape == "line":
                self.shape_id = self.canvas.create_line(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    fill=self.color,
                    capstyle=ctk.ROUND,
                )
            elif self.shape == "fill rectangle":
                self.shape_id = self.canvas.create_rectangle(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    fill=self.color,
                    outline=self.color,
                )
            elif self.shape == "fill oval":
                self.shape_id = self.canvas.create_oval(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    fill=self.color,
                    outline=self.color,
                )

        def draw_shape(event):
            self.canvas.coords(self.shape_id, self.shape_start_x, self.shape_start_y, event.x, event.y)

        def end_shape(event):
            if self.shape == "rectangle":
                self.draw.rectangle(
                    [self.shape_start_x, self.shape_start_y, event.x, event.y],
                    outline=self.color,
                    width=self.brush_size,
                )
            elif self.shape == "oval":
                self.draw.ellipse(
                    [self.shape_start_x, self.shape_start_y, event.x, event.y],
                    outline=self.color,
                    width=self.brush_size,
                )
            elif self.shape == "line":
                self.draw.line(
                    [self.shape_start_x, self.shape_start_y, event.x, event.y],
                    fill=self.color,
                    width=self.brush_size,
                )
                # for rounded ends
                self.draw.ellipse(
                    [
                        self.shape_start_x - self.brush_size / 2,
                        self.shape_start_y - self.brush_size / 2,
                        self.shape_start_x + self.brush_size / 2,
                        self.shape_start_y + self.brush_size / 2,
                    ],
                    fill=self.color,
                )
                self.draw.ellipse(
                    [
                        event.x - self.brush_size / 2,
                        event.y - self.brush_size / 2,
                        event.x + self.brush_size / 2,
                        event.y + self.brush_size / 2,
                    ],
                    fill=self.color,
                )
            elif self.shape == "fill rectangle":
                self.draw.rectangle(
                    [self.shape_start_x, self.shape_start_y, event.x, event.y],
                    fill=self.color,
                )
            elif self.shape == "fill oval":
                self.draw.ellipse(
                    [self.shape_start_x, self.shape_start_y, event.x, event.y],
                    fill=self.color,
                )
            self.update_canvas()
            self.undo_stack.append(self.image.copy())
            self.canvas.unbind("<ButtonPress-1>")
            self.canvas.unbind("<ButtonRelease-1>")

            self.canvas.bind("<B1-Motion>", self.paint)
            self.canvas.configure(cursor="pencil")

        self.shape = shape
        self.canvas.bind("<ButtonPress-1>", start_shape)
        self.canvas.bind("<B1-Motion>", draw_shape)
        self.canvas.bind("<ButtonRelease-1>", end_shape)

        self.canvas.configure(cursor="plus")

        self.after(200)  # A little delay, otherwise it doesn't work

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

        effects_win = ctk.CTkToplevel(app)
        effects_win.title(self._("Effects"))

        remove_all_effects_button = ctk.CTkButton(
            effects_win, text=self._("Remove all effects"), command=remove_all_effects
        )
        remove_all_effects_button.pack(padx=10, pady=10)

        # Blur
        blur_frame = ctk.CTkFrame(effects_win)
        blur_frame.pack(padx=10, pady=10)

        blur_label = ctk.CTkLabel(blur_frame, text=self._("Blur"))
        blur_label.pack(padx=10, pady=10)

        blur_slider = ctk.CTkSlider(blur_frame, from_=0, to=20)
        blur_slider.pack(padx=10, pady=10)

        blur_button = ctk.CTkButton(blur_frame, text=self._("Apply to picture"), command=blur)
        blur_button.pack(padx=10, pady=10)

        # Detail
        detail_frame = ctk.CTkFrame(effects_win)
        detail_frame.pack(padx=10, pady=10)

        detail_label = ctk.CTkLabel(detail_frame, text=self._("Detail"))
        detail_label.pack(padx=10, pady=10)

        detail_slider = ctk.CTkSlider(detail_frame, from_=1, to=20)
        detail_slider.pack(padx=10, pady=10)

        detail_button = ctk.CTkButton(detail_frame, text=self._("Apply to picture"), command=detail)
        detail_button.pack(padx=10, pady=10)

        # Contour
        contour_frame = ctk.CTkFrame(effects_win)
        contour_frame.pack(padx=10, pady=10)

        contour_label = ctk.CTkLabel(contour_frame, text=self._("Contour"))
        contour_label.pack(padx=10, pady=10)

        contour_button = ctk.CTkButton(contour_frame, text=self._("Apply to picture"), command=contour)
        contour_button.pack(padx=10, pady=10)

        # Grayscale
        grayscale_frame = ctk.CTkFrame(effects_win)
        grayscale_frame.pack(padx=10, pady=10)

        grayscale_label = ctk.CTkLabel(grayscale_frame, text=self._("Grayscale"))
        grayscale_label.pack(padx=10, pady=10)

        grayscale_button = ctk.CTkButton(grayscale_frame, text=self._("Apply to picture"), command=grayscale)
        grayscale_button.pack(padx=10, pady=10)

        image_copy = self.image.copy()

        effects_win.grab_set()  # Disable main window

    def show_gallery(self):
        my_gallery = ctk.CTkToplevel(app)
        my_gallery.title(self._("Brushshe Gallery"))
        my_gallery.geometry("650x580")

        gallery_frame = ctk.CTkScrollableFrame(my_gallery, label_text=self._("My Gallery"))
        gallery_frame.pack(fill=ctk.BOTH, expand=True)

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

                column += 1
                if column == 2:
                    column = 0
                    row += 1

        if not is_image_found:
            gallery_frame.configure(label_text=self._("My gallery (empty)"))

    def about_program(self):
        about_text = self._(
            "Brushshe is a painting program where you can create whatever you like.\n\n"
            "An eagle named Brucklin is its mascot.\n\n"
        )
        about_msg = CTkMessagebox(
            title=self._("About program"),
            message=about_text + "v1.0.2",
            icon=path.join(PATH, "icons/brucklin.png"),
            icon_size=(150, 191),
            option_1="OK",
            option_2="GitHub",
            height=400,
        )
        if about_msg.get() == "GitHub":
            webbrowser.open(r"https://github.com/limafresh/Brushshe")

    def new_picture(self, color):
        self.bg_color = color
        img_width = self.canvas_frame.winfo_width() - self.width_slider.winfo_height()
        img_height = self.canvas_frame.winfo_height() - self.height_slider.winfo_width()
        self.width_slider.set(img_width)
        self.height_slider.set(img_height)

        self.image = Image.new("RGB", (img_width, img_height), color)
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.configure(width=img_width, height=img_height)
        self.update_canvas()
        self.undo_stack.append(self.image.copy())

    def change_brush_size(self, size):
        self.brush_size = int(size)
        self.brush_size_label.configure(text=self.brush_size)

    def eraser(self):
        self.color = self.bg_color
        self.tool_label.configure(text=self._("Eraser:"))
        self.canvas.configure(cursor="plus")

    def undo(self):
        if len(self.undo_stack) > 1:
            self.undo_stack.pop()
            self.image = self.undo_stack[-1].copy()
            self.draw = ImageDraw.Draw(self.image)
            if self.image.width != self.canvas.winfo_width() or self.image.height != self.canvas.winfo_height():
                self.canvas.configure(width=self.image.width, height=self.image.height)
            self.update_canvas()

    def save_to_gallery(self):
        self.image.save(f"{self.gallery_folder}/{uuid4()}.png")

        CTkMessagebox(
            title=self._("Saved"),
            message=self._(
                'The picture has been successfully saved to the gallery ("My Gallery" in the menu at the top)!'
            ),
            icon=path.join(PATH, "icons/saved.png"),
            icon_size=(100, 100),
        )

    def change_color(self, new_color):
        self.color = new_color
        self.tool_label.configure(text=self._("Brush:"))
        self.canvas.configure(cursor="pencil")

    def other_color_choise(self):
        try:
            askcolor = AskColor(title=self._("Choose a different brush color"))
            self.obtained_color = askcolor.get()
            if self.obtained_color:
                self.color = self.obtained_color
                self.other_color_btn.pack(side=ctk.RIGHT, padx=1)
                self.other_color_btn.configure(fg_color=self.obtained_color)
                self.tool_label.configure(text=self._("Brush:"))
                self.canvas.configure(cursor="pencil")
        except:  # noqa: E722
            pass

    def select_other_color_btn(self):
        self.color = self.obtained_color
        self.tool_label.configure(text=self._("Brush:"))
        self.canvas.configure(cursor="pencil")

    def open_image(self, openimage):
        self.bg_color = "white"
        self.image = Image.open(openimage)
        self.draw = ImageDraw.Draw(self.image)

        img_width, img_height = self.image.size
        self.canvas.configure(width=img_width, height=img_height)
        self.width_slider.set(img_width)
        self.height_slider.set(img_height)

        self.update_canvas()
        self.undo_stack.append(self.image.copy())

    def open_file_error(self, e):
        message_text = self._("Error - cannot open file:")
        CTkMessagebox(
            title=self._("Oh, unfortunately, it happened"),
            message=f"{message_text} {e}",
            icon=path.join(PATH, "icons/cry.png"),
            icon_size=(100, 100),
            sound=True,
        )


app = Brushshe()
app.mainloop()
