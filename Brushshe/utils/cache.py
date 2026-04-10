# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import hashlib
import os
import sys
from pathlib import Path

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
        print("Warning: cached file can't be saved")


def clear_gallery_thumbs_cache():
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
