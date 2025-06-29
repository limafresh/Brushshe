import os
import sys
from pathlib import Path
from threading import Thread

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from PIL import Image
from tooltip import Tooltip
from translator import _


def resource(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def show(open_image):
    global my_gallery, open_image_func
    open_image_func = open_image

    my_gallery = ctk.CTkToplevel()
    my_gallery.title(_("Brushshe Gallery"))
    my_gallery.geometry("650x580")

    progressbar = ctk.CTkProgressBar(my_gallery, mode="intermediate")
    progressbar.pack(padx=10, pady=10, fill="x")
    progressbar.start()

    gallery_scrollable_frame = ctk.CTkScrollableFrame(my_gallery, label_text=_("My Gallery"))
    gallery_scrollable_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

    gallery_frame = ctk.CTkFrame(gallery_scrollable_frame)
    gallery_frame.pack(padx=10, pady=10)

    def load_buttons():
        preview_size = 160
        row = 0
        column = 0
        is_image_found = False

        try:
            gallery_file_list = sorted(Path(gallery_folder).iterdir(), key=os.path.getmtime, reverse=True)

            for filename in gallery_file_list:
                if filename.suffix == ".png":
                    is_image_found = True
                    img_path = str(filename)

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

                    image_button = ctk.CTkButton(
                        gallery_frame,
                        image=ctk.CTkImage(image_tmp_2, size=(w, h)),
                        width=preview_size + 10,
                        height=preview_size + 10,
                        text=None,
                        command=lambda img_path=img_path: open_image_func(img_path),
                    )
                    image_button.grid(row=row, column=column, padx=10, pady=10)

                    delete_image_button = ctk.CTkButton(
                        image_button,
                        text="X",
                        fg_color="red",
                        text_color="white",
                        width=30,
                        command=lambda img_path=img_path: delete_image(img_path),
                    )
                    delete_image_button.place(x=5, y=5)
                    Tooltip(delete_image_button, message=_("Delete"))

                    column += 1
                    if column >= 3:
                        column = 0
                        row += 1

            progressbar.stop()
            progressbar.pack_forget()

            if not is_image_found:
                gallery_scrollable_frame.configure(label_text=_("My gallery (empty)"))
        except Exception as e:
            print(e)

    Thread(target=load_buttons, daemon=True).start()


def delete_image(img_path):
    global my_gallery, open_image_func
    confirm_delete = CTkMessagebox(
        title=_("Confirm delete"),
        message=_("Are you sure you want to delete the picture?"),
        icon=resource("icons/question.png"),
        icon_size=(100, 100),
        option_1=_("Yes"),
        option_2=_("No"),
        sound=True,
    )
    if confirm_delete.get() == _("Yes") and os.path.exists(str(img_path)):
        os.remove(str(img_path))
        my_gallery.destroy()
        show(open_image_func)


if os.name == "nt":  # For Windows
    images_folder = Path(os.environ["USERPROFILE"]) / "Pictures"
else:  # For macOS and Linux
    images_folder = Path(os.environ.get("XDG_PICTURES_DIR", str(Path.home())))

gallery_folder = images_folder / "Brushshe Images"

if not gallery_folder.exists():
    gallery_folder.mkdir(parents=True)

my_gallery = None
open_image_func = None
