# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk
from constants import Constants
from PIL import Image, ImageTk
from ui import messagebox
from ui.CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from ui.scroll import scroll
from ui.tooltip import Tooltip
from utils import cache
from utils.common import shorten_filename
from utils.translator import _


class Gallery(ctk.CTkToplevel):
    def __init__(self, icon: ImageTk.PhotoImage, open_image: Callable):
        super().__init__()

        self.title(_("Brushshe Gallery"))
        self.geometry("650x580")
        self.wm_iconbitmap()
        self.after(300, lambda: self.iconphoto(False, icon))

        self._open_image = open_image

        menu = CTkMenuBar(self)
        gallery_menu = menu.add_cascade(_("My Gallery"))
        gallery_dropdown = CustomDropdownMenu(widget=gallery_menu)
        gallery_dropdown.add_option(option=_("Refresh"), command=self._load_buttons)
        gallery_dropdown.add_option(option=_("Clear cache"), command=cache.clear_gallery_thumbs_cache)

        self._progressbar = ctk.CTkProgressBar(self, mode="intermediate")
        self._progressbar.pack(padx=10, pady=10, fill="x")

        self._scrollable_frame = ctk.CTkScrollableFrame(self)
        self._scrollable_frame.pack(fill="both", expand=True, padx=0, pady=0)
        scroll(self._scrollable_frame)

        self._frame = ctk.CTkFrame(self._scrollable_frame)
        self._frame.pack(padx=10, pady=10)

        self._load_buttons()

    def _load_buttons(self):
        preview_size = 160
        row = 0
        column = 0
        images_number = 0

        self._progressbar.start()

        self._scrollable_frame.configure(label_text=None)

        for child in self._frame.winfo_children():
            child.destroy()

        cache_folder: str = cache.user_cache_dir("brushshe")
        try:
            os.makedirs(cache_folder, exist_ok=True)
        except Exception:
            print("Warning: Can't use cache directory")
            cache_folder = None

        try:
            file_list = sorted(Path(Constants.GALLERY_FOLDER).iterdir(), key=os.path.getmtime, reverse=True)

            for filename in file_list:
                if filename.suffix == ".png":
                    images_number += 1

                    img_path = str(filename)
                    img_file_name = os.path.basename(img_path)
                    name_without_ext, ext = os.path.splitext(img_file_name)

                    image_tmp_2 = self._get_image_from_cache(
                        cache_folder,
                        img_path,
                        os.path.getsize(img_path),
                        os.path.getmtime(img_path),
                        filename.suffix,
                    )
                    if image_tmp_2 is None:
                        image_tmp = Image.open(img_path)
                        rate = image_tmp.width / image_tmp.height
                        max_wh = max(image_tmp.width, image_tmp.height)
                        max_wh = min(max_wh, preview_size)
                        if rate > 1:
                            w = int(max_wh)
                            h = int(max_wh / rate)
                        else:
                            h = int(max_wh)
                            w = int(max_wh * rate)

                        image_tmp_2 = image_tmp.resize((w, h), Image.BOX)
                        del image_tmp

                        cache.set_image_to_cache(
                            cache_folder,
                            image_tmp_2,
                            img_path,
                            os.path.getsize(img_path),
                            os.path.getmtime(img_path),
                            filename.suffix,
                        )
                    else:
                        w = image_tmp_2.width
                        h = image_tmp_2.height

                    image_frame = ctk.CTkFrame(self._frame)
                    image_frame.grid(row=row, column=column, padx=10, pady=10)

                    image_button = ctk.CTkButton(
                        image_frame,
                        image=ctk.CTkImage(image_tmp_2, size=(w, h)),
                        width=preview_size + 10,
                        height=preview_size + 10,
                        text=None,
                        fg_color="transparent",
                        hover=None,
                        command=lambda img_path=img_path: self._open_image(img_path),
                        cursor="hand1",
                    )
                    image_button.grid(row=0, column=0)

                    delete_image_button = ctk.CTkButton(
                        image_frame,
                        text="X",
                        fg_color="red",
                        hover_color="#cc0000",
                        text_color="white",
                        width=30,
                        command=lambda img_path=img_path: self._delete_image(img_path),
                    )
                    delete_image_button.place(x=5, y=5)
                    Tooltip(delete_image_button, message=_("Delete"))

                    label_content = shorten_filename(name_without_ext)
                    filename_label = ctk.CTkLabel(image_frame, text=label_content, cursor="xterm")
                    filename_label.grid(row=1, column=0)

                    filename_label.bind(
                        "<Button-1>",
                        lambda e, parent=image_frame, text=name_without_ext, img_path=img_path, extension=ext: (
                            self._on_filename_label_click(e, parent, text, img_path, extension)
                        ),
                    )

                    column += 1
                    if column >= 3:
                        column = 0
                        row += 1

            self._progressbar.stop()
            self._progressbar.pack_forget()

            self._scrollable_frame.configure(label_text=f"{_('My Gallery')} ({images_number})")
        except Exception as e:
            print(e)

    def _on_filename_label_click(self, event, parent: ctk.CTkFrame, text: str, img_path: str, extension: str):
        event.widget.destroy()

        filename_entry = ctk.CTkEntry(parent)
        filename_entry.grid(row=1, column=0)
        filename_entry.insert(0, text)

        filename_entry.bind(
            "<Return>", lambda event: self._on_entry_return(filename_entry, parent, text, img_path, extension)
        )
        filename_entry.focus()

    def _on_entry_return(
        self, filename_entry: ctk.CTkEntry, parent: ctk.CTkFrame, text: str, img_path: str, extension: str
    ):
        new_text = filename_entry.get()
        new_path = os.path.join(os.path.dirname(img_path), new_text + extension)

        if not os.path.exists(new_path):
            os.rename(img_path, new_path)
            label_text = new_text
        else:
            msg = messagebox.overwrite_file()
            if msg.get() == _("Yes"):
                os.replace(img_path, new_path)
                self._load_buttons()
                return
            else:
                label_text = text

        label_content = shorten_filename(label_text)

        filename_entry.destroy()

        new_filename_label = ctk.CTkLabel(parent, text=label_content, cursor="xterm")
        new_filename_label.grid(row=1, column=0)

        new_filename_label.bind(
            "<Button-1>", lambda e: self._on_filename_label_click(e, parent, label_text, new_path, extension)
        )

    def _delete_image(self, img_path: str):
        msg = messagebox.confirm_delete()
        if msg.get() == _("Yes") and os.path.exists(str(img_path)):
            os.remove(str(img_path))
            self._load_buttons()

    def _get_image_from_cache(self, cache_folder: str, name: str, size: int, mtime: float, suffix: str):
        if cache_folder is None:
            return
        im_name = cache.get_cache_name(name, size, mtime)
        try:
            image = Image.open(os.path.normpath(cache_folder + "/thumbs/" + im_name + suffix))
        except Exception:
            image = None
            print("Warning: cached file not found")
        return image
