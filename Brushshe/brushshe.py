import json
import os
import sys
import webbrowser
from collections import deque
from locale import getlocale
from pathlib import Path
from tkinter import PhotoImage
from uuid import uuid4

import customtkinter as ctk
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
from tools.bezier import make_bezier
from tools.brush_palette import BrushPalette
from tools.color_picker import AskColor
from tools.file_dialog import FileDialog


def resource(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class Brushshe(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("680x600")
        if os.name == "nt":
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
        file_dropdown.add_option(option=self._("Save to device"), command=self.save_to_device)
        file_dropdown.add_separator()
        file_dropdown.add_option(option=self._("Rotate right"), command=lambda: self.rotate(-90))
        file_dropdown.add_option(option=self._("Rotate left"), command=lambda: self.rotate(90))
        file_dropdown.add_separator()
        file_dropdown.add_option(option=self._("Change size..."), command=self.change_size)

        new_menu = menu.add_cascade(self._("New"))
        new_dropdown = CustomDropdownMenu(widget=new_menu)

        for color in self.colors:
            new_dropdown.add_option(option=None, bg_color=color, command=lambda c=color: self.new_picture(c))
        new_dropdown.add_separator()
        new_dropdown.add_option(option=self._("Other color"), command=self.other_bg_color)
        new_dropdown.add_option(option=self._("Create screenshot"), command=self.create_screenshot)

        view_menu = menu.add_cascade(self._("View"))
        view_dropdown = CustomDropdownMenu(widget=view_menu)
        view_dropdown.add_option(option=self._("Zoom In"), command=self.zoom_in)
        view_dropdown.add_option(option=self._("Zoom Out"), command=self.zoom_out)
        view_dropdown.add_separator()
        view_dropdown.add_option(option=self._("Reset"), command=self.reset_zoom)

        add_menu = menu.add_cascade(self._("Add"))
        add_dropdown = CustomDropdownMenu(widget=add_menu)
        smile_icon = ctk.CTkImage(Image.open(resource("icons/smile.png")), size=(50, 50))
        add_dropdown.add_option(option=self._("Stickers"), image=smile_icon, command=self.show_stickers_choice)
        text_icon = ctk.CTkImage(Image.open(resource("icons/text.png")), size=(50, 50))
        add_dropdown.add_option(option=self._("Text"), image=text_icon, command=self.show_text_window)
        frame_icon = ctk.CTkImage(Image.open(resource("icons/frame.png")), size=(50, 50))
        add_dropdown.add_option(option=self._("Frames"), image=frame_icon, command=self.show_frame_choice)
        effects_icon = ctk.CTkImage(Image.open(resource("icons/effects.png")), size=(50, 50))
        add_dropdown.add_option(option=self._("Effects"), image=effects_icon, command=self.effects)

        shapes_menu = menu.add_cascade(self._("Shapes"))
        shapes_dropdown = CustomDropdownMenu(widget=shapes_menu)
        shape_options = ["Rectangle", "Oval", "Line", "Fill rectangle", "Fill oval"]
        for shape in shape_options:
            shapes_dropdown.add_option(option=self._(shape), command=lambda shape=shape: self.create_shape(shape))
        shapes_dropdown.add_option(option=self._("Bezier curve"), command=self.bezier_shape)

        menu.add_cascade(self._("My Gallery"), command=self.show_gallery)

        other_menu = menu.add_cascade(self._("More"))
        other_dropdown = CustomDropdownMenu(widget=other_menu)
        theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        ctk.CTkCheckBox(
            other_dropdown,
            text=self._("Dark theme"),
            variable=theme_var,
            onvalue="Dark",
            offvalue="Light",
            command=lambda: ctk.set_appearance_mode(theme_var.get()),
        ).pack(padx=10, pady=10)
        other_dropdown.add_option(option=self._("About program"), command=self.about_program)

        """Toolbar"""
        tools_frame = ctk.CTkFrame(self)
        tools_frame.pack(side=ctk.TOP, fill=ctk.X)

        # Brush size used to paint all the icons in the toolbar: 50

        brush_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/brush_light.png")),
            dark_image=Image.open(resource("icons/brush_dark.png")),
            size=(22, 22),
        )
        brush_button = ctk.CTkButton(tools_frame, text=None, width=30, image=brush_icon, command=self.brush)
        brush_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(brush_button, message=self._("Brush"), text_color="gray14")

        eraser_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/eraser_light.png")),
            dark_image=Image.open(resource("icons/eraser_dark.png")),
            size=(22, 22),
        )
        eraser_button = ctk.CTkButton(tools_frame, text=None, width=30, image=eraser_icon, command=self.eraser)
        eraser_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(eraser_button, message=self._("Eraser"), text_color="gray14")

        fill_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/fill_light.png")),
            dark_image=Image.open(resource("icons/fill_dark.png")),
            size=(22, 22),
        )
        fill_button = ctk.CTkButton(tools_frame, text=None, width=30, image=fill_icon, command=self.start_fill)
        fill_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(fill_button, message=self._("Fill"), text_color="gray14")

        recoloring_brush_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/recoloring_brush_light.png")),
            dark_image=Image.open(resource("icons/recoloring_brush_dark.png")),
            size=(22, 22),
        )
        recoloring_brush_button = ctk.CTkButton(
            tools_frame,
            text=None,
            width=30,
            image=recoloring_brush_icon,
            command=self.recoloring_brush,
        )
        recoloring_brush_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(recoloring_brush_button, message=self._("Recoloring Brush"), text_color="gray14")

        undo_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/undo_light.png")),
            dark_image=Image.open(resource("icons/undo_dark.png")),
            size=(22, 22),
        )
        undo_button = ctk.CTkButton(
            tools_frame,
            text=None,
            width=30,
            image=undo_icon,
            fg_color=tools_frame.cget("fg_color"),
            hover=False,
            command=self.undo,
        )
        undo_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(undo_button, message=self._("Undo") + " (Ctrl+Z)", text_color="gray14")

        redo_icon = ctk.CTkImage(
            light_image=Image.open(resource("icons/redo_light.png")),
            dark_image=Image.open(resource("icons/redo_dark.png")),
            size=(22, 22),
        )
        redo_button = ctk.CTkButton(
            tools_frame,
            text=None,
            width=30,
            image=redo_icon,
            fg_color=tools_frame.cget("fg_color"),
            hover=False,
            command=self.redo,
        )
        redo_button.pack(side=ctk.LEFT, padx=1)
        CTkToolTip(redo_button, message=self._("Redo") + " (Ctrl+Y)", text_color="gray14")

        self.tool_label = ctk.CTkLabel(tools_frame, text=None)
        self.tool_label.pack(side=ctk.LEFT, padx=1)

        self.tool_size_slider = ctk.CTkSlider(tools_frame, command=self.change_tool_size)
        self.tool_size_tooltip = CTkToolTip(self.tool_size_slider, text_color="gray14")

        self.tool_size_label = ctk.CTkLabel(tools_frame, text=None)

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
            command=lambda val: self.canvas.configure(width=int(val * self.zoom)),
        )
        self.width_slider.pack(side=ctk.BOTTOM, fill=ctk.X)
        self.width_slider.bind("<ButtonRelease-1>", self.crop_picture)
        self.width_tooltip = CTkToolTip(self.width_slider, text_color="gray14")

        self.height_slider = ctk.CTkSlider(
            self.canvas_frame,
            from_=100,
            to=2000,
            orientation="vertical",
            command=lambda val: self.canvas.configure(height=int(val * self.zoom)),
        )
        self.height_slider.pack(side=ctk.LEFT, fill=ctk.Y)
        self.height_slider.bind("<ButtonRelease-1>", self.crop_picture)
        self.height_tooltip = CTkToolTip(self.height_slider, text_color="gray14")

        self.v_scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical")
        self.v_scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y)

        self.h_scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="horizontal")
        self.h_scrollbar.pack(side=ctk.BOTTOM, fill=ctk.X)

        self.canvas = ctk.CTkCanvas(
            self.canvas_frame, yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set
        )
        self.canvas.pack(anchor="nw")  # As in most drawing programs

        self.v_scrollbar.configure(command=self.canvas.yview)
        self.h_scrollbar.configure(command=self.canvas.xview)

        """Palette"""
        self.bottom_docker = ctk.CTkFrame(self, corner_radius=0)
        self.bottom_docker.pack(side=ctk.BOTTOM, fill=ctk.X)

        self.brush_palette = BrushPalette(
            self.bottom_docker,
            click_main_btn=self.main_color_choice,
            click_second_btn=self.second_color_choice,
            click_flip_btn=self.flip_brush_colors,
        )
        self.brush_palette.pack(side=ctk.LEFT, padx=2)

        self.palette_widget = ctk.CTkFrame(
            self.bottom_docker,
        )
        self.palette_widget.pack(side=ctk.LEFT, fill=ctk.X, padx=2, pady=2)

        for color in self.colors:
            tmp_btn = ctk.CTkButton(
                self.palette_widget,
                fg_color=color,
                hover=False,
                text=None,
                width=30,
                height=30,
                border_width=2,
                corner_radius=15,
                command=lambda c=color: self.change_color(c),
            )
            tmp_btn.pack(side=ctk.LEFT, padx=1, pady=1)
            tmp_btn.bind("<Button-3>", lambda event, obj=tmp_btn: self.color_choice_bth(event, obj))

        ctk.CTkButton(self.bottom_docker, text=self._("Other"), command=self.main_color_choice).pack(
            side=ctk.RIGHT, padx=1
        )

        """ Initialization """
        self.brush_color = "black"
        self.second_brush_color = "white"
        self.bg_color = "white"
        self.undo_stack = deque(maxlen=10)
        self.redo_stack = deque(maxlen=10)

        self.brush_size = 2
        self.eraser_size = 4
        self.shape_size = 2
        self.sticker_size = 100
        self.font_size = 24
        self.zoom = 1

        self.update()  # update interface before calculate picture size
        self.brush()
        self.new_picture(self.bg_color)

        self.prev_x, self.prev_y = (None, None)
        self.font_path = resource("fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf")
        self.canvas.bind("<Button-3>", self.eyedropper)

        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-y>", lambda e: self.redo())
        self.bind("<Control-s>", lambda e: self.save_to_gallery())

        self.bind("<Key-x>", lambda e: self.flip_brush_colors())
        self.bind("<Key-b>", lambda e: self.brush())
        self.bind("<Key-e>", lambda e: self.eraser())

        # Default zooming keys for mani painting programs.
        self.bind("<Key-equal>", lambda e: self.zoom_in(e))  # Key "=" -> ("+" without Shift)
        self.bind("<Key-minus>", lambda e: self.zoom_out(e))

        # Scroll on mouse
        # Windows OS
        self.canvas.bind("<MouseWheel>", self.scroll_on_canvasy)
        self.canvas.bind("<Shift-MouseWheel>", self.scroll_on_canvasx)
        # Linux OS
        self.canvas.bind("<Button-4>", self.scroll_on_canvasy)
        self.canvas.bind("<Button-5>", self.scroll_on_canvasy)
        self.canvas.bind("<Shift-Button-4>", self.scroll_on_canvasx)
        self.canvas.bind("<Shift-Button-5>", self.scroll_on_canvasx)

        """Defining the Gallery Folder Path"""
        if os.name == "nt":  # For Windows
            images_folder = Path(os.environ["USERPROFILE"]) / "Pictures"
        else:  # For macOS and Linux
            images_folder = Path(os.environ.get("XDG_PICTURES_DIR", str(Path.home())))

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

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

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
            self.destroy()

    def scroll_on_canvasy(self, event):
        if event.num == 5 or event.delta < 0:
            count = 1
        if event.num == 4 or event.delta > 0:
            count = -1
        self.canvas.yview_scroll(count, "units")

    def scroll_on_canvasx(self, event):
        if event.num == 5 or event.delta < 0:
            count = 1
        if event.num == 4 or event.delta > 0:
            count = -1
        self.canvas.xview_scroll(count, "units")

    def zoom_in(self, event=None):
        if 1 < self.zoom < 2:  # Need if zoom not integer but more 1 and less 2
            self.zoom = 1

        if 1 <= self.zoom < 6:  # Zooming limited up by 6. More value has optimization problems.
            self.zoom += 1
        elif self.zoom < 1:
            self.zoom *= 2
        self.update_canvas()
        self.force_resize_canvas()

    def zoom_out(self, event=None):
        if 1 < self.zoom:
            self.zoom -= 1
        elif 0.05 < self.zoom <= 1:  # Zooming limited down by 0.05.
            self.zoom /= 2
        self.update_canvas()
        self.force_resize_canvas()

    def reset_zoom(self, event=None):
        self.zoom = 1
        self.update_canvas()
        self.force_resize_canvas()

    def canvas_to_pict_xy(self, x, y):
        return self.canvas.canvasx(x) // self.zoom, self.canvas.canvasy(y) // self.zoom

    def paint(self, event):
        x, y = self.canvas_to_pict_xy(event.x, event.y)
        if self.prev_x is not None and self.prev_y is not None:
            self.draw_line(self.prev_x, self.prev_y, x, y)
        else:
            self.draw_line(x, y, x, y)

        # TODO: In this place need use some other method
        #  without destroying and recreating all on canvas
        #  OR temporally drawing only on canvas.
        self.update_canvas()

        self.prev_x, self.prev_y = x, y

    def stop_paint(self, event):
        self.prev_x, self.prev_y = (None, None)
        self.update_canvas()
        self.undo_stack.append(self.image.copy())

    def draw_line(self, x1, y1, x2, y2):
        if self.current_tool == "brush":
            color = self.brush_color
        elif self.current_tool == "eraser":
            color = self.bg_color
        else:
            # For shape, etc.
            color = self.brush_color

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
        if hasattr(self, "canvas") is False or hasattr(self, "image") is False:
            return

        self.canvas.delete("all")
        if self.zoom == 1:
            canvas_image = self.image
        else:
            canvas_image = self.image.resize(
                (int(self.image.width * self.zoom), int(self.image.height * self.zoom)), Image.NEAREST
            )
        self.img_tk = ImageTk.PhotoImage(canvas_image)
        self.canvas.create_image(0, 0, anchor=ctk.NW, image=self.img_tk)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def force_resize_canvas(self):
        self.canvas.configure(
            width=int(self.image.width * self.zoom),
            height=int(self.image.height * self.zoom),
        )

    def crop_picture(self, event=None):
        new_image = Image.new("RGB", (int(self.width_slider.get()), int(self.height_slider.get())), self.bg_color)
        new_image.paste(self.image, (0, 0))
        self.image = new_image
        self.draw = ImageDraw.Draw(self.image)

        self.update_canvas()
        self.force_resize_canvas()

        self.undo_stack.append(self.image.copy())
        self.width_tooltip.configure(message=self.image.width)
        self.height_tooltip.configure(message=self.image.height)

    def eyedropper(self, event):
        # Get the coordinates of the click event
        x, y = self.canvas_to_pict_xy(event.x, event.y)

        color = self.image.getpixel((x, y))
        self.obtained_color = "#{:02x}{:02x}{:02x}".format(*color)

        self.brush_color = self.obtained_color
        self.brush_palette.main_color = self.obtained_color

    def start_fill(self):  # beta
        self.set_tool("fill", "Fill", None, None, None, "spraycan")
        self.canvas.bind("<Button-1>", self.fill)

    def fill(self, event):
        x, y = self.canvas_to_pict_xy(event.x, event.y)
        ImageDraw.floodfill(self.image, (x, y), ImageColor.getrgb(self.brush_color))
        self.update_canvas()
        self.undo_stack.append(self.image.copy())

    def open_from_file(self):
        dialog = FileDialog(self, self._("Open from file"))
        if dialog.path:
            try:
                self.open_image(dialog.path)
            except Exception as e:
                self.open_file_error(e)

    def save_to_device(self):
        dialog = FileDialog(self, self._("Save to device"), True, self._("Enter name for save..."))
        if dialog.path:
            self.image.save(dialog.path)
            CTkMessagebox(
                title=self._("Saved"),
                message=self._("The picture has been successfully saved to your device in format")
                + f" {dialog.extension}!",
                icon=resource("icons/saved.png"),
                icon_size=(100, 100),
                sound=True,
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

        sticker_choose = ctk.CTkToplevel(self)
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
            sticker_ctkimage = ctk.CTkImage(sticker_image, size=(100, 100))
            ctk.CTkButton(
                stickers_frame,
                text=None,
                image=sticker_ctkimage,
                command=lambda img=sticker_image: self.set_current_sticker(img),
            ).grid(row=row, column=column, padx=10, pady=10)
            column += 1
            if column == 2:
                column = 0
                row += 1

        ctk.CTkButton(
            tabview.tab(self._("Sticker from file")),
            text=self._("Choose sticker from file\nthen click where you want\nit on the picture"),
            command=sticker_from_file,
        ).pack(padx=10, pady=10)

    def set_current_sticker(self, sticker_image):  # Choose a sticker
        self.set_tool("sticker", "Stickers", self.sticker_size, 10, 175, "cross")
        self.canvas.bind("<Button-1>", lambda event: self.add_sticker(event, sticker_image))

    def add_sticker(self, event, sticker_image):  # Add a sticker
        sticker_image = sticker_image.resize((self.tool_size, self.tool_size))
        x, y = self.canvas_to_pict_xy(event.x, event.y)
        x, y = int(x), int(y)
        if sticker_image.mode == "RGBA":
            self.image.paste(
                sticker_image, (x - sticker_image.width // 2, y - sticker_image.height // 2), sticker_image
            )
        else:
            self.image.paste(sticker_image, (x - sticker_image.width // 2, y - sticker_image.height // 2))

        self.update_canvas()
        self.undo_stack.append(self.image.copy())

    def add_text(self, event, text):  # Add text
        x, y = self.canvas_to_pict_xy(event.x, event.y)
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
            self.canvas.bind("<Button-1>", lambda event, t=text: self.add_text(event, text))

        text_win = ctk.CTkToplevel(self)
        text_win.title(self._("Add text to a picture"))

        tx_entry = ctk.CTkEntry(text_win, placeholder_text=self._("Enter text..."))
        tx_entry.pack(padx=10, pady=10)

        ctk.CTkLabel(text_win, text=self._("Fonts:")).pack(padx=10, pady=10)

        fonts_dict = {
            "Open Sans": "fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf",
            "Sigmar": "fonts/Sigmar/Sigmar-Regular.ttf",
            "Playwrite IT Moderna": "fonts/Playwrite_IT_Moderna/PlaywriteITModerna-VariableFont_wght.ttf",
            "Monomakh": "fonts/Monomakh/Monomakh-Regular.ttf",
        }
        fonts = list(fonts_dict.keys())

        ctk.CTkOptionMenu(text_win, values=fonts, command=optionmenu_callback).pack(padx=10, pady=10)
        ctk.CTkButton(text_win, text="OK", command=add_text_ready).pack(padx=10, pady=10)

        self.tx_message_label = ctk.CTkLabel(text_win, text="\n")
        self.tx_message_label.pack(padx=10, pady=10)

    def show_frame_choice(self):
        def on_frames_click(index):
            selected_frame = frames[index]
            resized_frame = selected_frame.resize((self.image.width, self.image.height))

            self.image.paste(resized_frame, (0, 0), resized_frame)

            self.update_canvas()
            self.undo_stack.append(self.image.copy())

        frames_win = ctk.CTkToplevel(self)
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
            ctk.CTkImage(Image.open(resource(f"frames_preview/{name}.png")), size=(100, 100)) for name in frames_names
        ]

        frames = [Image.open(resource(f"frames/{name}.png")) for name in frames_names]

        row = 0
        column = 0

        for i, image in enumerate(frames_thumbnails):
            ctk.CTkButton(frames_win, text=None, image=image, command=lambda i=i: on_frames_click(i)).grid(
                column=column, row=row, padx=10, pady=10
            )
            column += 1
            if column == 2:
                column = 0
                row += 1

    # Shape creation functions
    def create_shape(self, shape):
        x_begin, y_begin = None, None

        def start_shape(event):
            nonlocal x_begin, y_begin

            self.shape_x, self.shape_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            x_begin, y_begin = self.canvas_to_pict_xy(event.x, event.y)
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
            x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self.canvas.coords(self.shape_id, self.shape_x, self.shape_y, x, y)

        def end_shape(event):
            nonlocal x_begin, y_begin

            if not hasattr(self, "shape_x"):
                return

            x_end, y_end = self.canvas_to_pict_xy(event.x, event.y)

            if x_begin < x_end:
                x0, x1 = x_begin, x_end
            else:
                x0, x1 = x_end, x_begin
            if y_begin < y_end:
                y0, y1 = y_begin, y_end
            else:
                y0, y1 = y_end, y_begin

            if shape == "Rectangle":
                self.draw.rectangle([x0, y0, x1, y1], outline=self.brush_color, width=self.tool_size)
            elif shape == "Oval":
                self.draw.ellipse([x0, y0, x1, y1], outline=self.brush_color, width=self.tool_size)
            elif shape == "Line":
                # self.draw.line([x_begin, y_begin, x_end, y_end], fill=self.brush_color, width=self.tool_size)
                self.draw_line(x_begin, y_begin, x_end, y_end)
            elif shape == "Fill rectangle":
                self.draw.rectangle([x0, y0, x1, y1], fill=self.brush_color)
            elif shape == "Fill oval":
                self.draw.ellipse([x0, y0, x1, y1], fill=self.brush_color)

            self.update_canvas()
            self.undo_stack.append(self.image.copy())

            # Removing unnecessary variables for normal selection of the next shape in the menu
            #   and disabling other side effects.
            del self.shape_x, self.shape_y

        if shape == "Fill rectangle" or shape == "Fill oval":
            self.set_tool("shape", shape, None, None, None, "cross")
        else:
            self.set_tool("shape", shape, self.shape_size, 1, 50, "cross")

        self.canvas.bind("<ButtonPress-1>", start_shape)
        self.canvas.bind("<B1-Motion>", draw_shape)
        self.canvas.bind("<ButtonRelease-1>", end_shape)

    def bezier_shape(self):
        # Simple 4th point (cubic) Bezier curve.

        canvas_points = []
        image_points = []
        bezier_id = None

        # Clear canvas.
        self.update_canvas()

        def start(event):
            nonlocal canvas_points, image_points, bezier_id

            if len(canvas_points) == 0:
                self.get_contrast_color()

                cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

                canvas_points.append((cx, cy))
                image_points.append(self.canvas_to_pict_xy(event.x, event.y))

                bezier_id = self.canvas.create_line(cx, cy, cx, cy, fill=self.contrast_color)  # smooth="bezier"

        def drawing(event):
            nonlocal canvas_points, bezier_id

            if bezier_id is None or len(canvas_points) == 0:
                return

            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            len_p = len(canvas_points)
            canvas_points_tmp = canvas_points.copy()

            if len_p <= 1:
                canvas_points_tmp.append((cx, cy))
            else:
                canvas_points_tmp.append(canvas_points_tmp[len_p - 1])
                canvas_points_tmp[len_p - 1] = (cx, cy)

            ts = [t / 32.0 for t in range(33)]  # 32 lines for preview.
            b = make_bezier(canvas_points_tmp)
            points = b(ts)

            # Do 2d array flat for canvas.coords
            points_flat = [j for sub in points for j in sub]

            self.canvas.coords(bezier_id, *points_flat)

        def end(event):
            nonlocal canvas_points, image_points, bezier_id

            if bezier_id is None or len(canvas_points) == 0:
                return

            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            px, py = self.canvas_to_pict_xy(event.x, event.y)
            len_p = len(canvas_points)
            stop = False

            if len_p <= 1:
                canvas_points.append((cx, cy))
                image_points.append((px, py))
            else:
                tx, ty = canvas_points[len_p - 2]

                if cx == tx and cy == ty and len_p > 2:
                    stop = True
                else:
                    canvas_points.append(canvas_points[len_p - 1])
                    canvas_points[len_p - 1] = (cx, cy)

                    len_ip = len(image_points)
                    image_points.append(image_points[len_ip - 1])
                    image_points[len_ip - 1] = (px, py)

            # Finish
            if len(canvas_points) >= 4 or stop:
                # Calculate segments count.
                max_segments = 0
                points_len = len(image_points)
                for ii, ip in enumerate(image_points):
                    if ii < points_len - 1:
                        max_segments += max(
                            abs(image_points[ii][0] - image_points[ii + 1][0]),
                            abs(image_points[ii][1] - image_points[ii + 1][1]),
                        )
                max_segments = max_segments // 3
                if max_segments < 32:
                    max_segments = 32

                # Draw on picture.
                ts = [t / max_segments for t in range(int(max_segments + 1))]
                b = make_bezier(image_points)
                points = b(ts)
                points_len = len(points)
                for it, tt in enumerate(points):
                    if it < points_len - 1:
                        # It's can work with float too, but with more artifacts.
                        self.draw_line(
                            int(points[it][0]), int(points[it][1]), int(points[it + 1][0]), int(points[it + 1][1])
                        )

                self.canvas.delete(bezier_id)
                self.update_canvas()
                self.undo_stack.append(self.image.copy())

                # Reset nonlocal variables.
                canvas_points = []
                image_points = []
                bezier_id = None

        self.set_tool("shape", "Bezier", self.shape_size, 1, 50, "cross")

        self.canvas.bind("<ButtonPress-1>", start)
        self.canvas.bind("<B1-Motion>", drawing)
        self.canvas.bind("<ButtonRelease-1>", end)
        self.canvas.bind("<Motion>", drawing)

    def recoloring_brush(self):
        self.set_tool("brush", "R. Brush", self.brush_size, 1, 50, "pencil")

        prev_x = None
        prev_y = None

        def begin(event):
            nonlocal prev_x, prev_y

            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_recoloring_brush(x, y, x, y)
            prev_x, prev_y = x, y

            draw_brush_halo(x, y)

        def drawing(event):
            nonlocal prev_x, prev_y

            if prev_x is None:
                return

            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_recoloring_brush(x, y, prev_x, prev_y)
            prev_x, prev_y = x, y

            self.update_canvas()  # force=False  # Do not delete tools shapes.

            draw_brush_halo(x, y)

        def end(event):
            nonlocal prev_x, prev_y

            if prev_x is None:
                return

            prev_x, prev_y = None, None

            self.update_canvas()  # force=True
            self.undo_stack.append(self.image.copy())

        def move(event):
            x, y = self.canvas_to_pict_xy(event.x, event.y)
            draw_brush_halo(x, y)

        def draw_recoloring_brush(x1, y1, x2, y2):
            color = ImageColor.getrgb(self.brush_color)
            color_from = ImageColor.getrgb(self.second_brush_color)

            d1 = (self.tool_size - 1) // 2
            d2 = self.tool_size // 2
            # dd = (d2 - d1) / 2
            max_x = self.image.width
            max_y = self.image.height

            x = x1
            y = y1
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy

            # It's for circuit brush, but it work too slow.
            # ((ii - x - dd) ** 2 + (jj - y - dd) ** 2 < ((d1 + d2 + .5)/2) ** 2

            # buffer = set()
            is_line = False

            while True:
                if self.tool_size <= 1:
                    if self.image.getpixel((x, y)) == color_from:
                        self.draw.point([x, y], fill=color)
                else:
                    if is_line is False:
                        for ii in range(int(x - d1), int(x + d2 + 1)):
                            for jj in range(int(y - d1), int(y + d2 + 1)):
                                if (
                                    ii >= 0
                                    and ii < max_x
                                    and jj >= 0
                                    and jj < max_y
                                    and self.image.getpixel((ii, jj)) == color_from
                                ):
                                    self.image.putpixel((ii, jj), color)
                                    # buffer.add((ii, jj))
                    else:
                        # Now we can check firsts or lasts lines only.

                        # Checking horizontal movement.
                        if sx > 0:
                            ii = int(x + d2)
                        else:
                            ii = int(x - d1)

                        for jj in range(int(y - d1), int(y + d2 + 1)):
                            if (
                                ii >= 0
                                and ii < max_x
                                and jj >= 0
                                and jj < max_y
                                and self.image.getpixel((ii, jj)) == color_from
                            ):
                                self.image.putpixel((ii, jj), color)
                                # buffer.add((ii, jj))

                        # Checking vertical movement.
                        if sy > 0:
                            jj = int(y + d2)
                        else:
                            jj = int(y - d1)

                        for ii in range(int(x - d1), int(x + d2 + 1)):
                            if (
                                ii >= 0
                                and ii < max_x
                                and jj >= 0
                                and jj < max_y
                                and self.image.getpixel((ii, jj)) == color_from
                            ):
                                self.image.putpixel((ii, jj), color)
                                # buffer.add((ii, jj))

                if abs(x - x2) < 1 and abs(y - y2) < 1:
                    # self.draw.point([*buffer], fill=color)
                    break

                e2 = err * 2
                if e2 > -dy:
                    err -= dy
                    x += sx
                if e2 < dx:
                    err += dx
                    y += sy

                is_line = True

        def draw_brush_halo(x, y):
            on_canvas = self.canvas.find_all()
            for ii in on_canvas:
                tmp = self.canvas.itemcget(ii, "tag")
                if tmp == "tools":
                    self.canvas.delete(ii)

            d1 = (self.tool_size - 1) // 2
            d2 = self.tool_size // 2 + 1
            # dd = (d2 - d1) / 2

            self.canvas.create_rectangle(
                int((x - d1) * self.zoom - 1),
                int((y - d1) * self.zoom - 1),
                int((x + d2) * self.zoom),
                int((y + d2) * self.zoom),
                outline="white",
                width=1,
                tag="tools",
            )
            self.canvas.create_rectangle(
                int((x - d1) * self.zoom),
                int((y - d1) * self.zoom),
                int((x + d2) * self.zoom - 1),
                int((y + d2) * self.zoom - 1),
                outline="black",
                width=1,
                tag="tools",
            )

        self.update_canvas()  # force=True

        self.canvas.bind("<Button-1>", begin)
        self.canvas.bind("<B1-Motion>", drawing)
        self.canvas.bind("<ButtonRelease-1>", end)
        self.canvas.bind("<Motion>", move)

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

        def inversion():
            self.image = ImageOps.invert(image_copy)
            post_actions()

        effects_win = ctk.CTkToplevel(self)
        effects_win.title(self._("Effects"))
        effects_win.geometry("250x500")

        effects_frame = ctk.CTkScrollableFrame(effects_win)
        effects_frame.pack(fill=ctk.BOTH, expand=True)

        ctk.CTkButton(
            effects_win,
            text=self._("Remove all effects"),
            command=remove_all_effects,
            fg_color="red",
            text_color="white",
        ).pack(padx=10, pady=10)

        # Blur
        blur_frame = ctk.CTkFrame(effects_frame)
        blur_frame.pack(padx=10, pady=10)

        ctk.CTkLabel(blur_frame, text=self._("Blur")).pack(padx=10, pady=10)

        blur_slider = ctk.CTkSlider(blur_frame, from_=0, to=20)
        blur_slider.pack(padx=10, pady=10)

        ctk.CTkButton(blur_frame, text=self._("Apply to picture"), command=blur).pack(padx=10, pady=10)

        # Detail
        detail_frame = ctk.CTkFrame(effects_frame)
        detail_frame.pack(padx=10, pady=10)

        ctk.CTkLabel(detail_frame, text=self._("Detail")).pack(padx=10, pady=10)

        detail_slider = ctk.CTkSlider(detail_frame, from_=1, to=20)
        detail_slider.pack(padx=10, pady=10)

        ctk.CTkButton(detail_frame, text=self._("Apply to picture"), command=detail).pack(padx=10, pady=10)

        effects_dict = {  # dictionary for effects which without slider
            "Contour": contour,
            "Grayscale": grayscale,
            "Mirror": mirror,
            "Metal": metal,
            "Inversion": inversion,
        }

        for effect_name, effect_command in effects_dict.items():
            effect_frame = ctk.CTkFrame(effects_frame)
            effect_frame.pack(padx=10, pady=10)

            ctk.CTkLabel(effect_frame, text=self._(effect_name)).pack(padx=10, pady=10)

            ctk.CTkButton(effect_frame, text=self._("Apply to picture"), command=effect_command).pack(padx=10, pady=10)

        image_copy = self.image.copy()

        effects_win.grab_set()  # Disable main window

    def show_gallery(self):
        self.my_gallery = ctk.CTkToplevel(self)
        self.my_gallery.title(self._("Brushshe Gallery (loading...)"))
        self.my_gallery.geometry("650x580")

        gallery_scrollable_frame = ctk.CTkScrollableFrame(self.my_gallery, label_text=self._("My Gallery"))
        gallery_scrollable_frame.pack(fill=ctk.BOTH, expand=True)

        gallery_frame = ctk.CTkFrame(gallery_scrollable_frame)
        gallery_frame.pack(padx=10, pady=10)

        row = 0
        column = 0

        is_image_found = False

        for filename in os.listdir(self.gallery_folder):
            if filename.endswith(".png"):
                is_image_found = True
                img_path = self.gallery_folder / filename

                image_button = ctk.CTkButton(
                    gallery_frame,
                    image=ctk.CTkImage(Image.open(img_path), size=(250, 250)),
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
            gallery_scrollable_frame.configure(label_text=self._("My gallery (empty)"))

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
        if confirm_delete.get() == self._("Yes") and os.path.exists(str(img_path)):
            os.remove(str(img_path))
            self.my_gallery.destroy()
            self.show_gallery()

    def about_program(self):
        about_text = self._(
            "Brushshe is a painting program where you can create whatever you like.\n\n"
            "An eagle named Brucklin is its mascot.\n\n"
        )
        about_msg = CTkMessagebox(
            title=self._("About program"),
            message=about_text + "v1.14.0",
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
        self.width_tooltip.configure(message=img_width)
        self.height_tooltip.configure(message=img_height)

        self.image = Image.new("RGB", (img_width, img_height), color)
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.configure(width=img_width, height=img_height, scrollregion=self.canvas.bbox("all"))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        self.update_canvas()
        self.force_resize_canvas()

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

        self.canvas.bind("<Button-1>", self.paint)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)

    def eraser(self):
        self.set_tool("eraser", "Eraser", self.eraser_size, 1, 50, "target")

        self.canvas.bind("<Button-1>", self.paint)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)

    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self.image = self.undo_stack[-1].copy()
            self.draw = ImageDraw.Draw(self.image)
            if self.image.width != self.canvas.winfo_width() or self.image.height != self.canvas.winfo_height():
                self.width_slider.set(self.image.width)
                self.height_slider.set(self.image.height)
                self.force_resize_canvas()
            self.update_canvas()

    def redo(self):
        if len(self.redo_stack) > 0:
            self.image = self.redo_stack.pop().copy()
            self.undo_stack.append(self.image.copy())
            self.draw = ImageDraw.Draw(self.image)
            if self.image.width != self.canvas.winfo_width() or self.image.height != self.canvas.winfo_height():
                self.width_slider.set(self.image.width)
                self.height_slider.set(self.image.height)
                self.force_resize_canvas()
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
            sound=True,
        )

    def change_color(self, new_color):
        self.brush_color = new_color
        self.brush_palette.main_color = self.brush_color

    def main_color_choice(self):
        askcolor = AskColor(title=self._("Color select"))
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            self.brush_color = self.obtained_color
            self.brush_palette.main_color = self.obtained_color

    def second_color_choice(self):
        askcolor = AskColor(title=self._("Color select"))
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            self.second_brush_color = self.obtained_color
            self.brush_palette.second_color = self.obtained_color

    def color_choice_bth(self, event, btn):
        askcolor = AskColor(title=self._("Color select"))
        self.obtained_color = askcolor.get()
        if self.obtained_color:
            # self.main_brush_color = self.obtained_color
            # self.brush_palette.main_color = self.obtained_color
            btn.configure(
                fg_color=self.obtained_color,
                hover_color=self.obtained_color,
                command=lambda c=self.obtained_color: self.change_color(c),
            )

    def flip_brush_colors(self):
        self.brush_color = self.brush_palette.second_color
        self.second_brush_color = self.brush_palette.main_color

        self.brush_palette.main_color = self.brush_color
        self.brush_palette.second_color = self.second_brush_color

    def open_image(self, openimage):
        self.bg_color = "white"
        self.image = Image.open(openimage)
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
        self.width_slider.set(self.image.width)
        self.height_slider.set(self.image.height)
        self.width_tooltip.configure(message=self.image.width)
        self.height_tooltip.configure(message=self.image.height)

        self.update_canvas()
        self.force_resize_canvas()

        self.draw = ImageDraw.Draw(self.image)
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.undo_stack.append(self.image.copy())

    def set_tool(self, tool, tool_name, tool_size, from_, to, cursor):
        self.current_tool = tool

        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<Motion>")

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

        self.update_canvas()  # force = True

    def change_size(self):
        def size_sb_callback(value):
            if value == self._("Crop"):
                ready_size_button.configure(command=crop)
            elif value == self._("Scale"):
                ready_size_button.configure(command=scale)

        def crop():
            try:
                self.width_slider.set(int(width_entry.get()))
                self.height_slider.set(int(height_entry.get()))
                self.crop_picture()
            except Exception:
                pass

        def scale():
            try:
                scaled_image = self.image.resize((int(width_entry.get()), int(height_entry.get())), Image.NEAREST)
                self.image = scaled_image
                self.picture_postconfigure()
            except Exception:
                pass

        change_size_toplevel = ctk.CTkToplevel(self)
        change_size_toplevel.title(self._("Change size..."))

        size_sb = ctk.CTkSegmentedButton(
            change_size_toplevel, values=[self._("Crop"), self._("Scale")], command=size_sb_callback
        )
        size_sb.pack(padx=10, pady=10)
        size_sb.set(self._("Crop"))

        width_height_frame = ctk.CTkFrame(change_size_toplevel)
        width_height_frame.pack(padx=10, pady=10)

        width_entry = ctk.CTkEntry(width_height_frame, placeholder_text=self._("Width"))
        width_entry.pack(side="left", padx=10, pady=10)
        height_entry = ctk.CTkEntry(width_height_frame, placeholder_text=self._("Height"))
        height_entry.pack(side="right", padx=10, pady=10)

        ready_size_button = ctk.CTkButton(change_size_toplevel, text="OK", command=crop)
        ready_size_button.pack(padx=10, pady=10)


app = Brushshe()
app.mainloop()
