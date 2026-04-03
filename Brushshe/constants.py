# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
from pathlib import Path


class Constants:
    """Version"""

    VERSION_MAJOR = "2"
    VERSION_MINOR = "6"
    VERSION_PATCH = "0"
    CODENAME = "Yerevan"
    VERSION = f'{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH} "{CODENAME}"'

    STANDART_PALETTES = ["default", "4bit", "vintage", "seven"]

    IMG_EXTENSIONS = [
        ".png",
        ".jpeg",
        ".gif",
        ".bmp",
        ".dds",
        ".dib",
        ".eps",
        ".icns",
        ".ico",
        ".im",
        ".mpo",
        ".pcx",
        ".ppm",
        ".sgi",
        ".tga",
        ".tiff",
        ".webp",
        ".pdf",  # only for save, not for open
    ]
    SAVE_IMG_FILETYPES = [(ext.upper().lstrip("."), "*" + ext) for ext in IMG_EXTENSIONS]
    OPEN_IMG_FILETYPES = [(ext.upper().lstrip("."), "*" + ext) for ext in IMG_EXTENSIONS[:-1]]  # without PDF

    # Width and height of all sticker images - 88 px
    # Width and height of new sticker images - 512 px
    STICKERS_NAMES = [
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
        "brushshe",
        "brucklin",
        "grass",
        "rain",
        "strawberry",
        "butterfly",
        "flower2",
    ]

    FONTS_DICT = {
        "Open Sans": "assets/fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf",
        "Monomakh": "assets/fonts/Monomakh/Monomakh-Regular.ttf",
        "Pacifico": "assets/fonts/Pacifico/Pacifico-Regular.ttf",
        "Comforter": "assets/fonts/Comforter/Comforter-Regular.ttf",
        "Rubik Bubbles": "assets/fonts/Rubik_Bubbles/RubikBubbles-Regular.ttf",
        "Press Start 2P": "assets/fonts/Press_Start_2P/PressStart2P-Regular.ttf",
    }
    FONTS = list(FONTS_DICT.keys())

    FRAMES_NAMES = [
        "frame1",
        "frame2",
        "frame3",
        "frame4",
        "frame5",
        "frame6",
        "frame7",
    ]

    EFFECTS_VALUES = [
        "Blur",
        "Detail",
        "Contour",
        "Grayscale",
        "Mirror",
        "Metal",
        "Inversion",
        "Brightness",
        "Contrast",
    ]

    LANGUAGES = {"Українська": "uk", "English": "en", "Русский": "ru", "Deutsch": "de", "हिन्दी": "hi", "Italiano": "it"}

    GALLERY_FOLDER = (
        Path(os.environ["USERPROFILE"]) / "Pictures"
        if os.name == "nt"
        else Path(os.environ.get("XDG_PICTURES_DIR", str(Path.home())))
    ) / "Brushshe Images"
    ADDONS_FOLDER = Path.home() / ".brushshe" / "addons"
