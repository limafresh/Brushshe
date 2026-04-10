# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
from pathlib import Path

import customtkinter as ctk
from constants import Constants
from PIL import Image
from ui import messagebox
from ui.CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from ui.scroll import scroll
from ui.tooltip import Tooltip
from utils import cache
from utils.common import shorten_filename
from utils.translator import _


class Gallery:
    def show_gallery(self):
        my_gallery = ctk.CTkToplevel()
        my_gallery.title(_("Brushshe Gallery"))
        my_gallery.geometry("650x580")
        my_gallery.wm_iconbitmap()
        my_gallery.after(300, lambda: my_gallery.iconphoto(False, self.iconpath))

        menu = CTkMenuBar(my_gallery)
        gallery_menu = menu.add_cascade(_("My Gallery"))
        g_dropdown = CustomDropdownMenu(widget=gallery_menu)
        g_dropdown.add_option(option=_("Refresh"), command=self.load_gallery_buttons)
        g_dropdown.add_option(option=_("Clear cache"), command=cache.clear_gallery_thumbs_cache)

        self.gallery_progressbar = ctk.CTkProgressBar(my_gallery, mode="intermediate")
        self.gallery_progressbar.pack(padx=10, pady=10, fill="x")

        self.gallery_scrollable_frame = ctk.CTkScrollableFrame(my_gallery)
        self.gallery_scrollable_frame.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        scroll(self.gallery_scrollable_frame)

        self.gallery_frame = ctk.CTkFrame(self.gallery_scrollable_frame)
        self.gallery_frame.pack(padx=10, pady=10)

        # Threads work bad with Tkinter event_loop.
        # Cache must be enough for normal work after first open gallery.
        # Thread(target=load_buttons, daemon=True).start()

        self.load_gallery_buttons()

    def load_gallery_buttons(self):
        preview_size = 160
        row = 0
        column = 0
        images_number = 0

        self.gallery_progressbar.start()

        self.gallery_scrollable_frame.configure(label_text=None)
        for child in self.gallery_frame.winfo_children():
            child.destroy()

        cache_folder = cache.user_cache_dir("brushshe")
        try:
            os.makedirs(cache_folder, exist_ok=True)
        except Exception:
            print("Warning: Can't use cache directory")
            cache_folder = None

        try:
            gallery_file_list = sorted(Path(Constants.GALLERY_FOLDER).iterdir(), key=os.path.getmtime, reverse=True)

            for filename in gallery_file_list:
                if filename.suffix == ".png":
                    images_number += 1

                    img_path = str(filename)
                    img_file_name = os.path.basename(img_path)
                    name_without_ext, ext = os.path.splitext(img_file_name)

                    image_tmp_2 = self.get_image_from_cache(
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
                        if max_wh > preview_size:
                            max_wh = preview_size
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

                    image_frame = ctk.CTkFrame(self.gallery_frame)
                    image_frame.grid(row=row, column=column, padx=10, pady=10)

                    image_button = ctk.CTkButton(
                        image_frame,
                        image=ctk.CTkImage(image_tmp_2, size=(w, h)),
                        width=preview_size + 10,
                        height=preview_size + 10,
                        text=None,
                        fg_color="transparent",
                        hover=None,
                        command=lambda img_path=img_path: self.logic.open_image(img_path),
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
                        command=lambda img_path=img_path: self.delete_gallery_image(img_path),
                    )
                    delete_image_button.place(x=5, y=5)
                    Tooltip(delete_image_button, message=_("Delete"))

                    label_content = shorten_filename(name_without_ext)
                    filename_label = ctk.CTkLabel(image_frame, text=label_content, cursor="xterm")
                    filename_label.grid(row=1, column=0)

                    filename_label.bind(
                        "<Button-1>",
                        lambda e, parent=image_frame, text=name_without_ext, img_path=img_path, extension=ext: (
                            self.on_gallery_filename_label_click(e, parent, text, img_path, extension)
                        ),
                    )

                    column += 1
                    if column >= 3:
                        column = 0
                        row += 1

            self.gallery_progressbar.stop()
            self.gallery_progressbar.pack_forget()

            self.gallery_scrollable_frame.configure(label_text=f"{_('My Gallery')} ({images_number})")

        except Exception as e:
            print(e)

    def on_gallery_filename_label_click(self, event, parent, text, img_path, extension):
        event.widget.destroy()

        filename_entry = ctk.CTkEntry(parent)
        filename_entry.grid(row=1, column=0)
        filename_entry.insert(0, text)

        def on_return(event):
            new_text = filename_entry.get()
            new_path = os.path.join(os.path.dirname(img_path), new_text + extension)

            if not os.path.exists(new_path):
                os.rename(img_path, new_path)
                label_text = new_text
            else:
                msg = messagebox.overwrite_file()
                if msg.get() == _("Yes"):
                    os.replace(img_path, new_path)
                else:
                    label_text = text

            label_content = shorten_filename(label_text)

            filename_entry.destroy()

            new_filename_label = ctk.CTkLabel(parent, text=label_content, cursor="xterm")
            new_filename_label.grid(row=1, column=0)

            new_filename_label.bind(
                "<Button-1>", lambda e: self.on_gallery_filename_label_click(e, parent, label_text, new_path, extension)
            )

        filename_entry.bind("<Return>", on_return)
        filename_entry.focus()

    def delete_gallery_image(self, img_path):
        msg = messagebox.confirm_delete()
        if msg.get() == _("Yes") and os.path.exists(str(img_path)):
            os.remove(str(img_path))
            self.load_gallery_buttons()

    def get_image_from_cache(self, cache_folder, name, size, mtime, suffix):
        if cache_folder is None:
            return
        im_name = cache.get_cache_name(name, size, mtime)
        try:
            image = Image.open(os.path.normpath(cache_folder + "/thumbs/" + im_name + suffix))
        except Exception:
            image = None
            print("Warning: cached file not found")
        return image
