import json
import webbrowser
from collections import deque
from locale import getlocale
from os import environ, listdir, name, path
from pathlib import Path
from tkinter import Listbox, PhotoImage, font
from uuid import uuid4

import customtkinter as ctk
from brushshe_color_picker import AskColor
from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageEnhance, ImageFilter, ImageGrab, ImageOps, ImageTk

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
            "white",
        ]

        """ Interface """

        menu = CTkMenuBar(self)  # Menu

        file_menu = menu.add_cascade(self._("File"))
        file_dropdown = CustomDropdownMenu(widget=file_menu)
        file_dropdown.add_option(option=self._("Open from file"), command=self.open_from_file)
        export_submenu = file_dropdown.add_submenu(self._("Export to PC"))
        # 1000 - a slight delay so that when taking a snapshot of the picture the menu has time to hide
        formats = ["PNG", "JPG", "GIF", "BMP", "TIFF", "WEBP", "ICO", "PPM", "PGM", "PBM"]
        for fmt in formats:
            export_submenu.add_option(
                option=fmt, command=lambda fmt=fmt: self.after(1000, lambda: self.export(f".{fmt.lower()}"))
            )

        bg_menu = menu.add_cascade(self._("Background"))
        bg_dropdown = CustomDropdownMenu(widget=bg_menu)

        for color in self.colors:
            bg_dropdown.add_option(option=None, bg_color=color, command=lambda c=color: self.canvas.configure(bg=c))
        bg_dropdown.add_separator()
        bg_dropdown.add_option(option=self._("Other color"), command=self.other_bg_color)

        add_menu = menu.add_cascade(self._("Add"))
        add_dropdown = CustomDropdownMenu(widget=add_menu)
        smile_icon = ctk.CTkImage(light_image=Image.open(path.join(PATH, "icons/smile.png")), size=(50, 50))
        add_dropdown.add_option(
            option=self._("Stickers"),
            image=smile_icon,
            command=self.show_stickers_choice,
        )
        text_icon = ctk.CTkImage(light_image=Image.open(path.join(PATH, "icons/text.png")), size=(50, 50))
        text_submenu = add_dropdown.add_submenu(self._("Text"), image=text_icon)
        text_submenu.add_option(option=self._("Add text to a picture"), command=self.add_text_window_show)
        text_submenu.add_option(option=self._("Customize text for insertion"), command=self.text_settings)
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
            "Arrow",
            "Double ended arrow",
            "Fill rectangle",
            "Fill oval",
            "Fill triangle",
            "Fill diamond",
        ]
        for shape in shape_options:
            shapes_dropdown.add_option(
                option=self._(shape), command=lambda shape=shape: self.create_shape(shape.lower())
            )

        menu.add_cascade(self._("My Gallery"), command=self.show_gallery)

        other_menu = menu.add_cascade(self._("More"))
        other_dropdown = CustomDropdownMenu(widget=other_menu)
        theme_submenu = other_dropdown.add_submenu(self._("Theme"))
        theme_submenu.add_option(option=self._("System"), command=lambda: ctk.set_appearance_mode("system"))
        theme_submenu.add_option(option=self._("Light"), command=lambda: ctk.set_appearance_mode("light"))
        theme_submenu.add_option(option=self._("Dark"), command=lambda: ctk.set_appearance_mode("dark"))
        other_dropdown.add_option(option=self._("About program"), command=self.about_program)

        tools_frame = ctk.CTkFrame(self)  # Toolbar
        tools_frame.pack(side=ctk.TOP, fill=ctk.X)

        clean_btn = ctk.CTkButton(tools_frame, text=self._("Clear all"), width=50, command=self.clean_all)
        clean_btn.pack(side=ctk.LEFT, padx=1)

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

        save_button = ctk.CTkButton(
            tools_frame,
            text=self._("Save to gallery"),
            width=70,
            command=self.save_image,
        )
        save_button.pack(side=ctk.RIGHT, padx=1)

        self.canvas_frame = ctk.CTkFrame(self)  # Canvas
        self.canvas_frame.pack_propagate(False)
        self.canvas_frame.pack(fill=ctk.BOTH, expand=True)

        width_slider = ctk.CTkSlider(
            self.canvas_frame,
            from_=100,
            to=2000,
            orientation="horizontal",
            command=lambda val: self.canvas.configure(width=int(val)),
        )
        width_slider.set(500)
        width_slider.pack(side=ctk.BOTTOM, fill=ctk.X)

        height_slider = ctk.CTkSlider(
            self.canvas_frame,
            from_=100,
            to=2000,
            orientation="vertical",
            command=lambda val: self.canvas.configure(height=int(val)),
        )
        height_slider.set(500)
        height_slider.pack(side=ctk.LEFT, fill=ctk.Y)

        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="white", highlightthickness=0)
        self.canvas.pack()

        self.palette = ctk.CTkFrame(self)  # Palette
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
        self.image = Image.new("RGB", (800, 600), "white")

        self.prev_x, self.prev_y = (None, None)

        self.font_size = 24
        self.tk_font = ctk.CTkFont(size=self.font_size)
        self.size_a = 100

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)
        self.canvas.bind("<Button-3>", self.eyedropper)

        self.canvas.configure(cursor="pencil")

        self.undo_stack = deque(maxlen=10)
        self.current_items = []

        # Defining the Gallery Folder Path
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

        self.update_canvas_size()

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
        if self.prev_x and self.prev_y:
            item = self.canvas.create_line(
                self.prev_x,
                self.prev_y,
                event.x,
                event.y,
                width=self.brush_size,
                fill=self.color,
                smooth=True,
                capstyle=ctk.ROUND,
            )
            self.current_items.append(item)
        self.prev_x, self.prev_y = event.x, event.y

    def stop_paint(self, event):
        self.undo_stack.append(self.current_items)
        self.current_items = []
        self.prev_x, self.prev_y = (None, None)

    def eyedropper(self, event):
        # Get the coordinates of the click event
        x, y = event.x, event.y

        self.capture_canvas_content()

        color = self.canvas_content.getpixel((x, y))
        self.obtained_color = "#{:02x}{:02x}{:02x}".format(*color)

        self.color = self.obtained_color
        self.other_color_btn.pack(side=ctk.RIGHT, padx=1)
        self.other_color_btn.configure(fg_color=self.obtained_color)
        self.tool_label.configure(text=self._("Brush:"))
        self.canvas.configure(cursor="pencil")

    def update_canvas_size(self):
        img_width, img_height = self.image.size
        self.canvas.config(width=img_width, height=img_height)

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
                message_text = self._("Error - cannot open file:")
                CTkMessagebox(
                    title=self._("Oh, unfortunately, it happened"),
                    message=f"{message_text} {e}",
                    icon=path.join(PATH, "icons/cry.png"),
                    icon_size=(100, 100),
                    sound=True,
                )

    def export(self, extension):
        self.capture_canvas_content()

        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[(self._("All files"), "*.*")],
        )
        if file_path:
            self.canvas_content.save(file_path)
            CTkMessagebox(
                title=self._("Exported"),
                message=self._("The picture has been successfully exported to your computer in format")
                + f" {extension}!",
                icon=path.join(PATH, "icons/saved.png"),
                icon_size=(100, 100),
            )

    def other_bg_color(self):
        askcolor = AskColor(title=self._("Choose a different background color"))
        obtained_bg_color = askcolor.get()
        if obtained_bg_color:
            self.canvas.configure(bg=obtained_bg_color)

    def show_stickers_choice(self):
        def update_btn():
            for widget in stickers_frame.winfo_children():
                widget.destroy()
            row = 0
            column = 0
            for image in self.stickers:
                resized_image = image.resize((self.size_a, self.size_a))
                image = ImageTk.PhotoImage(resized_image)
                sticker_btn = ctk.CTkButton(
                    stickers_frame,
                    text=None,
                    image=image,
                    command=lambda img=image: self.set_current_sticker(img),
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

        update_btn()

    def set_current_sticker(self, image):  # Choose a sticker
        self.canvas.bind("<Button-1>", lambda event: self.add_sticker(event, image))
        self.canvas.configure(cursor="")

    def add_sticker(self, event, image):  # Add a sticker
        item = self.canvas.create_image(event.x, event.y, anchor="center", image=image)
        self.add_to_undo_stack(item)
        self.canvas.unbind("<Button-1>")
        self.canvas.configure(cursor="pencil")

    def change_sticker_size(self, value):
        self.size_a = int(self.st_slider.get())
        self.st_size_label.configure(text=self.size_a)

    def set_default_stickers_size(self):
        self.size_a = 100
        self.st_size_label.configure(text=self.size_a)
        self.st_slider.set(self.size_a)

    def add_text_window_show(self):  # Choose text
        dialog = ctk.CTkInputDialog(
            title=self._("Enter text,"),
            text=self._("then click where you want it on the picture"),
        )
        text = dialog.get_input()
        if text:
            self.canvas.bind("<Button-1>", lambda event, t=text: self.add_text(event, text))
            self.canvas.configure(cursor="")

    def add_text(self, event, text):  # Add text
        self.tk_font = ctk.CTkFont(family=self.tk_font["family"], size=self.font_size)
        item = self.canvas.create_text(event.x, event.y, text=text, fill=self.color, font=self.tk_font)
        self.add_to_undo_stack(item)
        self.canvas.unbind("<Button-1>")
        self.canvas.configure(cursor="pencil")

    def text_settings(self):
        def change_text_size(size):
            self.font_size = int(size)
            self.tx_size_label.configure(text=self.font_size)

        def listbox_callback(event):
            selected_font = fonts_listbox.get(fonts_listbox.curselection())
            self.tk_font = ctk.CTkFont(family=selected_font, size=self.font_size)

        text_settings = ctk.CTkToplevel(app)
        text_settings.title(self._("Customize text"))

        self.tx_size_label = ctk.CTkLabel(text_settings, text=self.font_size)
        self.tx_size_label.pack(padx=10, pady=10)
        tx_size_slider = ctk.CTkSlider(text_settings, from_=11, to=96, command=change_text_size)
        tx_size_slider.set(self.font_size)
        tx_size_slider.pack(padx=10, pady=10)

        fonts_label = ctk.CTkLabel(text_settings, text=self._("System fonts:"))
        fonts_label.pack(padx=10, pady=10)
        fonts = list(font.families())
        fonts_listbox = Listbox(text_settings)
        fonts_listbox.pack(padx=10, pady=10)
        for f in fonts:
            fonts_listbox.insert(ctk.END, f)
        fonts_listbox.bind("<<ListboxSelect>>", listbox_callback)

    def show_frame_choice(self):
        def on_frames_click(index):
            selected_frame = frames[index]
            resized_image = selected_frame.resize((self.canvas.winfo_width(), self.canvas.winfo_height()))
            self.frame_image = ImageTk.PhotoImage(resized_image)
            item = self.canvas.create_image(0, 0, anchor="nw", image=self.frame_image)
            self.add_to_undo_stack(item)

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
                item = self.shape_id = self.canvas.create_rectangle(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    outline=self.color,
                )
            elif self.shape == "oval":
                item = self.shape_id = self.canvas.create_oval(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    outline=self.color,
                )
            elif self.shape == "line":
                item = self.shape_id = self.canvas.create_line(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    fill=self.color,
                    capstyle=ctk.ROUND,
                )
            elif self.shape == "arrow":
                item = self.shape_id = self.canvas.create_line(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    fill=self.color,
                    arrow=ctk.LAST,
                    arrowshape=(self.brush_size * 2, self.brush_size * 2, self.brush_size * 2),
                )
            elif self.shape == "double ended arrow":
                item = self.shape_id = self.canvas.create_line(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    fill=self.color,
                    arrow=ctk.BOTH,
                    arrowshape=(self.brush_size * 2, self.brush_size * 2, self.brush_size * 2),
                )
            elif self.shape == "fill rectangle":
                item = self.shape_id = self.canvas.create_rectangle(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    outline=self.color,
                    fill=self.color,
                )
            elif self.shape == "fill oval":
                item = self.shape_id = self.canvas.create_oval(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    outline=self.color,
                    fill=self.color,
                )
            elif self.shape == "fill triangle":
                item = self.shape_id = self.canvas.create_polygon(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    outline=self.color,
                    fill=self.color,
                )
            elif self.shape == "fill diamond":
                item = self.shape_id = self.canvas.create_polygon(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    outline=self.color,
                    fill=self.color,
                )
            self.add_to_undo_stack(item)

        def draw_shape(event):
            if self.shape == "fill triangle":
                self.canvas.coords(
                    self.shape_id,
                    self.shape_start_x,
                    self.shape_start_y,
                    event.x,
                    event.y,
                    2 * self.shape_start_x - event.x,
                    event.y,
                )
            elif self.shape == "fill diamond":
                self.canvas.coords(
                    self.shape_id,
                    self.shape_start_x,
                    self.shape_start_y - (event.y - self.shape_start_y),  # Top vertex
                    self.shape_start_x + (event.x - self.shape_start_x),  # Right vertex
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y + (event.y - self.shape_start_y),  # Bottom vertex
                    self.shape_start_x - (event.x - self.shape_start_x),  # Left vertex
                    self.shape_start_y,
                )
            else:
                self.canvas.coords(self.shape_id, self.shape_start_x, self.shape_start_y, event.x, event.y)

        def end_shape(event):
            self.canvas.unbind("<ButtonPress-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<ButtonRelease-1>")

            self.canvas.bind("<B1-Motion>", self.paint)
            self.canvas.bind("<ButtonRelease-1>", self.stop_paint)

            self.canvas.configure(cursor="pencil")

        self.shape = shape
        self.canvas.bind("<ButtonPress-1>", start_shape)
        self.canvas.bind("<B1-Motion>", draw_shape)
        self.canvas.bind("<ButtonRelease-1>", end_shape)

        self.canvas.configure(cursor="plus")

        self.after(200)  # A little delay, otherwise it doesn't work

    def effects(self):
        def remove_all_effects():
            canvas_img_tk = ImageTk.PhotoImage(self.canvas_content)
            self.canvas.create_image(0, 0, anchor="nw", image=canvas_img_tk)
            self.canvas.image = canvas_img_tk
            self.undo_stack.clear()

        def blur():
            radius = blur_slider.get()
            blurred_img = self.canvas_content.filter(ImageFilter.GaussianBlur(radius=radius))
            blurred_img_tk = ImageTk.PhotoImage(blurred_img)
            self.canvas.create_image(0, 0, anchor="nw", image=blurred_img_tk)
            self.canvas.image = blurred_img_tk
            self.undo_stack.clear()

        def detail():
            factor = detail_slider.get()
            enhancer = ImageEnhance.Sharpness(self.canvas_content)
            detailed_img = enhancer.enhance(factor)
            detailed_img_tk = ImageTk.PhotoImage(detailed_img)
            self.canvas.create_image(0, 0, anchor="nw", image=detailed_img_tk)
            self.canvas.image = detailed_img_tk
            self.undo_stack.clear()

        def contour():
            contoured_img = self.canvas_content.filter(ImageFilter.CONTOUR)
            contoured_img_tk = ImageTk.PhotoImage(contoured_img)
            self.canvas.create_image(0, 0, anchor="nw", image=contoured_img_tk)
            self.canvas.image = contoured_img_tk
            self.undo_stack.clear()

        def grayscale():
            grayscale_img = ImageOps.grayscale(self.canvas_content)
            grayscale_img_tk = ImageTk.PhotoImage(grayscale_img)
            self.canvas.create_image(0, 0, anchor="nw", image=grayscale_img_tk)
            self.canvas.image = grayscale_img_tk
            self.undo_stack.clear()

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

        self.capture_canvas_content()

        effects_win.grab_set()  # Disable main window

    def show_gallery(self):
        my_gallery = ctk.CTkToplevel(app)
        my_gallery.title(self._("Brushshe Gallery"))
        my_gallery.geometry("650x580")

        gallery_frame = ctk.CTkScrollableFrame(my_gallery, label_text=self._("My Gallery"))
        gallery_frame.pack(fill=ctk.BOTH, expand=True)

        row = 0
        column = 0

        def open_from_gallery(img_path):
            open_msg_message = self._(
                "The drawing you are currently drawing will be lost if it is not saved "
                "and replaced with a drawing from the gallery.\n\n"
                "Continue?"
            )
            open_msg_message = self._(open_msg_message)
            open_msg = CTkMessagebox(
                title=self._("Opening a picture"),
                message=open_msg_message,
                option_1=self._("Yes"),
                option_2=self._("Return"),
                icon=path.join(PATH, "icons/question.png"),
                icon_size=(100, 100),
                sound=True,
            )
            if open_msg.get() == self._("Return"):
                pass
            else:
                self.open_image(img_path)

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
                    command=lambda img_path=img_path: open_from_gallery(img_path),
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
            message=about_text + "v0.17",
            icon=path.join(PATH, "icons/brucklin.png"),
            icon_size=(150, 191),
            option_1="OK",
            option_2="GitHub",
            height=400,
        )
        if about_msg.get() == "GitHub":
            webbrowser.open(r"https://github.com/limafresh/Brushshe")

    def clean_all(self):
        self.canvas.delete("all")
        self.undo_stack.clear()

    def change_brush_size(self, size):
        self.brush_size = int(size)
        self.brush_size_label.configure(text=self.brush_size)

    def eraser(self):
        self.color = self.canvas.cget("bg")
        self.tool_label.configure(text=self._("Eraser:"))
        self.canvas.configure(cursor="plus")

    def undo(self):
        if self.undo_stack:
            items = self.undo_stack.pop()
            for i in items:
                self.canvas.delete(i)

    def save_image(self):
        self.capture_canvas_content()
        self.canvas_content.save(f"{self.gallery_folder}/{uuid4()}.png")

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

    def add_to_undo_stack(self, item):
        self.current_items.append(item)
        self.undo_stack.append(self.current_items)
        self.current_items = []

    def capture_canvas_content(self):
        self.canvas_content = ImageGrab.grab(
            bbox=(
                self.canvas.winfo_rootx(),
                self.canvas.winfo_rooty(),
                self.canvas.winfo_rootx() + self.canvas.winfo_width(),
                self.canvas.winfo_rooty() + self.canvas.winfo_height(),
            )
        )

    def open_image(self, openimage):
        self.canvas.delete("all")
        self.canvas.configure(bg="white")

        self.image = Image.open(openimage)
        self.photo = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=ctk.NW, image=self.photo)

        self.update_canvas_size()
        self.undo_stack.clear()


app = Brushshe()
app.mainloop()
