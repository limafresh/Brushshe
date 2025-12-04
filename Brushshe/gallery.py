# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import hashlib
import os
import sys
from pathlib import Path

# from threading import Thread
import customtkinter as ctk
import messagebox
from core.scroll import scroll
from core.tooltip import Tooltip
from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from PIL import Image
from translator import _


def show(open_image):
    global my_gallery, open_image_func, progressbar, gallery_frame, gallery_scrollable_frame
    open_image_func = open_image

    my_gallery = ctk.CTkToplevel()
    my_gallery.title(_("Brushshe Gallery"))
    my_gallery.geometry("650x580")

    menu = CTkMenuBar(my_gallery)
    gallery_menu = menu.add_cascade(_("My Gallery"))
    g_dropdown = CustomDropdownMenu(widget=gallery_menu)
    g_dropdown.add_option(option=_("Refresh"), command=lambda: load_buttons())
    g_dropdown.add_option(option=_("Clear cache"), command=lambda: clear_thumbs_cache())

    progressbar = ctk.CTkProgressBar(my_gallery, mode="intermediate")
    progressbar.pack(padx=10, pady=10, fill="x")

    gallery_scrollable_frame = ctk.CTkScrollableFrame(my_gallery)
    gallery_scrollable_frame.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
    scroll(gallery_scrollable_frame)

    gallery_frame = ctk.CTkFrame(gallery_scrollable_frame)
    gallery_frame.pack(padx=10, pady=10)

    # Threads work bad with Tkinter event_loop.
    # Cache must be enough for normal work after first open gallery.
    # Thread(target=load_buttons, daemon=True).start()

    load_buttons()


def load_buttons():
    global my_gallery, open_image_func, progressbar, gallery_frame, gallery_scrollable_frame

    preview_size = 160
    row = 0
    column = 0
    is_image_found = False

    progressbar.start()

    gallery_scrollable_frame.configure(label_text=None)
    for child in gallery_frame.winfo_children():
        child.destroy()

    cache_folder = user_cache_dir("brushshe")
    try:
        os.makedirs(cache_folder, exist_ok=True)
    except Exception:
        print("Warning: Can't use cache directory")
        cache_folder = None

    try:
        gallery_file_list = sorted(Path(gallery_folder).iterdir(), key=os.path.getmtime, reverse=True)

        for filename in gallery_file_list:
            if filename.suffix == ".png":
                is_image_found = True
                img_path = str(filename)

                image_tmp_2 = get_image_from_cache(
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

                    set_image_to_cache(
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

                image_button = ctk.CTkButton(
                    gallery_frame,
                    image=ctk.CTkImage(image_tmp_2, size=(w, h)),
                    width=preview_size + 10,
                    height=preview_size + 10,
                    text=None,
                    fg_color="transparent",
                    hover=None,
                    command=lambda img_path=img_path: open_image_func(img_path),
                    cursor="hand1",
                )
                image_button.grid(row=row, column=column, padx=10, pady=10)

                delete_image_button = ctk.CTkButton(
                    image_button,
                    text="X",
                    fg_color="red",
                    hover_color="#cc0000",
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


def delete_image(img_path):
    global my_gallery, open_image_func
    msg = messagebox.confirm_delete()
    if msg.get() == _("Yes") and os.path.exists(str(img_path)):
        os.remove(str(img_path))
        # my_gallery.destroy()
        # show(open_image_func)
        load_buttons()


def get_cache_name(name, size, mtime):
    s_name = "{0}_{1}_{2}".format(name, size, mtime)
    return hashlib.sha1(s_name.encode("utf-8")).hexdigest()


def set_image_to_cache(cache_folder, image, name, size, mtime, suffix):
    if cache_folder is None:
        return
    im_name = get_cache_name(name, size, mtime)
    try:
        os.makedirs(os.path.normpath(cache_folder + "/thumbs/"), exist_ok=True)
        image.save(os.path.normpath(cache_folder + "/thumbs/" + im_name + suffix))
    except Exception:
        # Can't be saved.
        pass
        # print("Warning: cached file can't be saved")


def clear_thumbs_cache():
    cache_folder = user_cache_dir("brushshe")

    try:
        os.makedirs(cache_folder, exist_ok=True)
    except Exception:
        print("Warning: Can't use cache directory")
        return

    cache_thumbs_folder = os.path.normpath(cache_folder + "/thumbs/")

    try:
        thumbs_list = Path(cache_thumbs_folder).iterdir()
        for filename in thumbs_list:
            if filename.suffix == ".png":
                os.remove(filename)
    except Exception:
        print("Warning: Can't clear thumbs cache.")
        return


def get_image_from_cache(cache_folder, name, size, mtime, suffix):
    if cache_folder is None:
        return
    im_name = get_cache_name(name, size, mtime)
    try:
        image = Image.open(os.path.normpath(cache_folder + "/thumbs/" + im_name + suffix))
    except Exception:
        # Cache not found
        image = None
        # print("Warning: cached file not found")
    return image


""" ------- """

# FIXME: Need just use 'platformdirs' or 'appdirs' and do not go bananas.
if sys.platform == "win32":
    platform = "windows"
elif sys.platform == "darwin":
    platform = "macos"
else:
    platform = "linux"  # Can be Android or FreeBSD too.


def _get_win_folder_from_environ(csidl_name):
    env_var_name = {
        "CSIDL_APPDATA": "APPDATA",
        "CSIDL_COMMON_APPDATA": "ALLUSERSPROFILE",
        "CSIDL_LOCAL_APPDATA": "LOCALAPPDATA",
    }[csidl_name]
    return os.environ[env_var_name]


def _get_win_folder_from_registry(csidl_name):
    import winreg as _winreg

    shell_folder_name = {
        "CSIDL_APPDATA": "AppData",
        "CSIDL_COMMON_APPDATA": "Common AppData",
        "CSIDL_LOCAL_APPDATA": "Local AppData",
    }[csidl_name]
    key = _winreg.OpenKey(
        _winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
    )
    dir, type = _winreg.QueryValueEx(key, shell_folder_name)
    return dir


if platform == "windows":
    try:
        import winreg as _winreg  # noqa: F401
    except ImportError:
        _get_win_folder = _get_win_folder_from_environ
    else:
        _get_win_folder = _get_win_folder_from_registry


def user_cache_dir(app_name=None, app_author=None, opinion=True):
    if platform == "windows":
        if app_author is None:
            app_author = app_name
        path = os.path.normpath(_get_win_folder("CSIDL_LOCAL_APPDATA"))
        if app_name:
            if app_author is not False:
                path = os.path.join(path, app_author, app_name)
            else:
                path = os.path.join(path, app_name)
            if opinion:
                path = os.path.join(path, "Cache")
    elif platform == "macos":
        path = os.path.expanduser("~/Library/Caches")
        if app_name:
            path = os.path.join(path, app_name)
    else:
        path = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        if app_name:
            path = os.path.join(path, app_name)
    return path


if platform == "windows":
    images_folder = Path(os.environ["USERPROFILE"]) / "Pictures"
else:
    images_folder = Path(os.environ.get("XDG_PICTURES_DIR", str(Path.home())))
gallery_folder = images_folder / "Brushshe Images"


if not gallery_folder.exists():
    gallery_folder.mkdir(parents=True)

my_gallery = None
open_image_func = None
