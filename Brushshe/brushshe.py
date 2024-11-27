import json
import webbrowser
from gc import disable as garbage_collector_disable
from locale import getlocale
from os import environ, listdir, name
from pathlib import Path
from tkinter import Listbox, PhotoImage, font
from uuid import uuid4

import customtkinter as ctk
from CTkColorPicker import AskColor
from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageDraw, ImageGrab, ImageTk


class Brushshe(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Brushshe")
        self.geometry("650x580")
        self.minsize(650, 580)
        self.iconphoto(True, PhotoImage(file="icons/icon.png"))
        ctk.set_default_color_theme("brushshe_theme.json")
        ctk.set_appearance_mode("system")
        self.protocol("WM_DELETE_WINDOW", self.when_closing)

        language_code = getlocale()[0].split("_")[0]

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
                    f"locales/{language_code}.json",
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
        file_dropdown.add_option(option=self._("Open from file"), command=self.open_image)
        file_dropdown.add_option(option=self._("Export to PC"), command=self.export)

        bg_menu = menu.add_cascade(self._("Background"))
        bg_dropdown = CustomDropdownMenu(widget=bg_menu)

        for color in self.colors:
            bg_dropdown.add_option(option=None, bg_color=color, command=lambda c=color: self.change_bg(c))
        bg_dropdown.add_separator()
        bg_dropdown.add_option(option=self._("Other color"), command=self.other_bg_color)

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
        self.stickers = [Image.open(f"stickers/{name}.png") for name in stickers_names]

        add_menu = menu.add_cascade(self._("Add"))
        add_dropdown = CustomDropdownMenu(widget=add_menu)
        smile_icon = ctk.CTkImage(light_image=Image.open("icons/smile.png"), size=(50, 50))
        add_dropdown.add_option(
            option=self._("Stickers"),
            image=smile_icon,
            command=self.show_stickers_choice,
        )
        text_icon = ctk.CTkImage(light_image=Image.open("icons/text.png"), size=(50, 50))
        text_submenu = add_dropdown.add_submenu(self._("Text"), image=text_icon)
        text_submenu.add_option(option=self._("Add text to a picture"), command=self.add_text_window_show)
        text_submenu.add_option(option=self._("Customize text for insertion"), command=self.text_settings)
        frame_icon = ctk.CTkImage(light_image=Image.open("icons/frame.png"), size=(50, 50))
        add_dropdown.add_option(option=self._("Frames"), image=frame_icon, command=self.show_frame_choice)

        shapes_menu = menu.add_cascade(self._("Shapes"))
        shapes_dropdown = CustomDropdownMenu(widget=shapes_menu)
        shapes_dropdown.add_option(option=self._("Rectangle"), command=lambda: self.create_shape("rectangle"))
        shapes_dropdown.add_option(option=self._("Oval"), command=lambda: self.create_shape("oval"))
        shapes_dropdown.add_option(option=self._("Line"), command=lambda: self.create_shape("line"))
        shapes_dropdown.add_option(
            option=self._("Fill rectangle"),
            command=lambda: self.create_shape("fill rectangle"),
        )
        shapes_dropdown.add_option(option=self._("Fill oval"), command=lambda: self.create_shape("fill oval"))

        menu.add_cascade(self._("My Gallery"), command=self.show_gallery)

        other_menu = menu.add_cascade(self._("More"))
        other_dropdown = CustomDropdownMenu(widget=other_menu)
        theme_submenu = other_dropdown.add_submenu(self._("Theme"))
        theme_submenu.add_option(option=self._("System"), command=lambda: self.change_theme("system"))
        theme_submenu.add_option(option=self._("Light"), command=lambda: self.change_theme("light"))
        theme_submenu.add_option(option=self._("Dark"), command=lambda: self.change_theme("dark"))
        other_dropdown.add_option(option=self._("About program"), command=self.about_program)

        tools_frame = ctk.CTkFrame(self)  # Toolbar
        tools_frame.pack(side=ctk.TOP, fill=ctk.X)

        clean_btn = ctk.CTkButton(tools_frame, text=self._("Clear all"), width=50, command=self.clean_all)
        clean_btn.pack(side=ctk.LEFT, padx=1)

        eraser_icon = ctk.CTkImage(light_image=Image.open("icons/eraser.png"), size=(20, 20))
        eraser = ctk.CTkButton(tools_frame, text=None, width=35, image=eraser_icon, command=self.eraser)
        eraser.pack(side=ctk.LEFT, padx=1)

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

        self.canvas = ctk.CTkCanvas(self, bg="white")  # Canvas
        self.canvas.pack(fill=ctk.BOTH, expand=True)

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
        self.draw = ImageDraw.Draw(self.image)
        self.photo = None

        self.prev_x = None
        self.prev_y = None

        self.font_size = 24
        self.tk_font = ctk.CTkFont(size=self.font_size)
        self.size_a = 100

        garbage_collector_disable()  # Because the enabled gc thinks that the added stickers and text are garbage

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)

        self.canvas.configure(cursor="pencil")
        self.current_tool = None

        # Defining the Gallery Folder Path
        if name == "nt":  # For Windows
            images_folder = Path(environ["USERPROFILE"]) / "Pictures"
        else:  # For macOS and Linux
            images_folder = Path(environ.get("XDG_PICTURES_DIR"))

        self.gallery_folder = images_folder / "Brushshe Images"

        if not self.gallery_folder.exists():
            self.gallery_folder.mkdir(parents=True)

    """ Functionality """

    def when_closing(self):
        closing_msg = CTkMessagebox(
            title=self._("You are leaving Brushshe"),
            message=self._("Save the picture?"),
            option_1=self._("No"),
            option_2=self._("Go back to save"),
            icon="icons/question.png",
            icon_size=(100, 100),
            sound=True,
        )
        response = closing_msg.get()
        if response == self._("No"):
            app.destroy()
        else:
            pass

    def paint(self, cur):
        if self.prev_x and self.prev_y:
            self.canvas.create_line(
                self.prev_x,
                self.prev_y,
                cur.x,
                cur.y,
                width=self.brush_size,
                fill=self.color,
                smooth=True,
                capstyle=ctk.ROUND,
            )
        self.prev_x, self.prev_y = cur.x, cur.y

    def stop_paint(self, cur):
        self.prev_x, self.prev_y = (None, None)

    def open_image(self):
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[
                (self._("Images"), "*png* *jpg* *jpeg* *gif*"),
                (self._("All files"), "*.*"),
            ]
        )
        message_text = self._("Error - cannot open file:")
        if file_path:
            try:
                image = Image.open(file_path)
                self.image = image
                self.draw = ImageDraw.Draw(self.image)
                self.canvas.delete("all")
                self.canvas.configure(bg="white")
                self.photo = ImageTk.PhotoImage(self.image)
                self.canvas.create_image(0, 0, anchor=ctk.NW, image=self.photo)
            except Exception as e:
                CTkMessagebox(
                    title=self._("Oh, unfortunately, it happened"),
                    message=f"{message_text} {e}",
                    icon="icons/cry.png",
                    icon_size=(100, 100),
                    sound=True,
                )

    def export(self):
        # Canvas positions
        x0 = self.canvas.winfo_rootx()
        y0 = self.canvas.winfo_rooty()
        x1 = x0 + self.canvas.winfo_width()
        y1 = y0 + self.canvas.winfo_height()

        # Canvas content
        canvas_img = ImageGrab.grab(bbox=(x0, y0, x1, y1))

        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[(self._("All files"), "*.*")],
        )
        if file_path:
            canvas_img.save(file_path)

    def change_bg(self, new_color):
        self.canvas.configure(bg=new_color)
        if self.tool_label.cget("text") == self._("Eraser:"):
            self.eraser()

    def other_bg_color(self):
        pick_color = AskColor(title=self._("Choose a different background color"))
        bg_getcolor = pick_color.get()
        if bg_getcolor:
            self.canvas.configure(bg=bg_getcolor)

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
        self.current_sticker = image
        if self.current_sticker:
            self.canvas.bind("<Button-1>", self.add_sticker)
            self.canvas.configure(cursor="")

    def add_sticker(self, event):  # Add a sticker
        self.canvas.create_image(event.x, event.y, anchor="center", image=self.current_sticker)
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
        self.canvas.create_text(event.x, event.y, text=text, fill=self.color, font=self.tk_font)
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
            self.canvas.create_image(0, 0, anchor="nw", image=self.frame_image)

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
            ctk.CTkImage(light_image=Image.open(f"frames_preview/{name}.png"), size=(100, 100)) for name in frames_names
        ]

        frames = [Image.open(f"frames/{name}.png") for name in frames_names]

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
                    width=self.brush_size,
                    outline=self.color,
                    fill=self.color,
                )
            elif self.shape == "fill oval":
                self.shape_id = self.canvas.create_oval(
                    self.shape_start_x,
                    self.shape_start_y,
                    self.shape_start_x,
                    self.shape_start_y,
                    width=self.brush_size,
                    outline=self.color,
                    fill=self.color,
                )

        def draw_shape(event):
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

        self.canvas.configure(cursor="crosshair")

        self.after(100)  # A little delay, otherwise it doesn't work

    def show_gallery(self):  # Gallery
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
                icon="icons/question.png",
                icon_size=(100, 100),
                sound=True,
            )
            response = open_msg.get()
            if response == self._("Return"):
                pass
            else:
                image = Image.open(img_path)
                self.image = image
                self.draw = ImageDraw.Draw(self.image)
                self.canvas.delete("all")
                self.canvas.configure(bg="white")
                self.photo = ImageTk.PhotoImage(self.image)
                self.canvas.create_image(0, 0, anchor=ctk.NW, image=self.photo)

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

    def change_theme(self, theme):
        ctk.set_appearance_mode(theme)

    def about_program(self):
        about_text = self._(
            "Brushshe is a painting program where you can create whatever you like.\n\n"
            "An eagle named Brucklin is its mascot.\n\n"
        )
        about_msg = CTkMessagebox(
            title=self._("About program"),
            message=about_text + "v0.11",
            icon="icons/brucklin.png",
            icon_size=(150, 191),
            option_1="OK",
            option_2="GitHub",
            height=400,
        )
        response = about_msg.get()
        if response == "GitHub":
            webbrowser.open(r"https://github.com/limafresh/Brushshe")

    def clean_all(self):
        self.canvas.delete("all")

    def change_brush_size(self, size):
        self.brush_size = int(size)
        self.brush_size_label.configure(text=self.brush_size)

    def eraser(self):
        self.color = self.canvas.cget("bg")
        self.tool_label.configure(text=self._("Eraser:"))
        self.canvas.configure(cursor="crosshair")
        self.current_tool = "eraser"

    def save_image(self):
        # Canvas positions
        x0 = self.canvas.winfo_rootx()
        y0 = self.canvas.winfo_rooty()
        x1 = x0 + self.canvas.winfo_width()
        y1 = y0 + self.canvas.winfo_height()

        # Canvas content
        canvas_img = ImageGrab.grab(bbox=(x0, y0, x1, y1))

        image_name = f"{self.gallery_folder}/{uuid4()}.png"

        CTkMessagebox(
            title=self._("Saved"),
            message=self._(
                'The picture has been successfully saved to the gallery ("My Gallery" in the menu at the top)!'
            ),
            icon="icons/saved.png",
            icon_size=(100, 100),
        )

        canvas_img.save(image_name)

    def change_color(self, new_color):
        self.color = new_color
        self.tool_label.configure(text=self._("Brush:"))
        if self.current_tool == "eraser":
            self.canvas.configure(cursor="pencil")
            self.current_tool = None

    def other_color_choise(self):
        try:
            pick_color = AskColor(title=self._("Choose a different brush color"))
            self.getcolor = pick_color.get()
            if self.getcolor:
                self.color = self.getcolor
                self.other_color_btn.pack(side=ctk.RIGHT, padx=1)
                self.other_color_btn.configure(fg_color=self.getcolor)
                self.tool_label.configure(text=self._("Brush:"))
                if self.current_tool == "eraser":
                    self.canvas.configure(cursor="pencil")
                    self.current_tool = None
        except:  # noqa: E722
            pass

    def select_other_color_btn(self):
        self.color = self.getcolor
        self.tool_label.configure(text="Brush:")
        if self.current_tool == "eraser":
            self.canvas.configure(cursor="pencil")
            self.current_tool = None


app = Brushshe()
app.mainloop()
