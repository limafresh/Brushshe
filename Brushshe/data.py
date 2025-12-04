# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
from collections import deque

import customtkinter as ctk
from config_loader import config
from core.bhcomposer import BhComposer
from PIL import Image


def resource(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def init():
    global autosave_var, is_gradient_fill, is_sticker_use_real_size, is_insert_smoothing
    autosave_var = ctk.BooleanVar(value=config.getboolean("Brushshe", "autosave"))
    is_gradient_fill = ctk.StringVar(value="off")
    is_sticker_use_real_size = ctk.StringVar(value="off")
    is_insert_smoothing = ctk.StringVar(value="off")


"""Version"""
version_prefix = ""
version_major = "2"
version_minor = "4"
version_patch = "0"
version_suffix = ' "Windhoek"'

version_full = "{0}{1}.{2}.{3}{4}".format(version_prefix, version_major, version_minor, version_patch, version_suffix)

"""Other variables"""
autosave_var, is_gradient_fill, is_sticker_use_real_size, is_insert_smoothing = None, None, None, None

# Max tail can not be more 4 MB = 1024 (width) x 1024 (height) x 4 (rgba).
# canvas_tail_size: Max = 1024. Default = 128. Min = 16.
canvas_tail_size = 128
# If None - no crop, if set - need check out of crop.
canvas_tails_area = None

brush_color = "black"
second_brush_color = "white"
bg_color = "white"
brush_shape = "circle"

undo_stack = deque(maxlen=config.getint("Brushshe", "undo_levels"))
redo_stack = deque(maxlen=config.getint("Brushshe", "undo_levels"))
zoom = 1
selected_mask_img = None  # Can be gray_image or None

brush_size = 2
eraser_size = 4
spray_size = 10
shape_size = 2
sticker_size = 100
font_size = 24

is_brush_smoothing = config.getboolean("Brushshe", "smoothing")
brush_smoothing_factor = config.getint("Brushshe", "brush_smoothing_factor")  # Between: 3..64
brush_smoothing_quality = config.getint("Brushshe", "brush_smoothing_quality")  # Between: 1..64

composer = BhComposer(0, 0)  # Empty init.
composer.mask_type = 0  # Type: 0 - fill, 1 - ants

current_file = None
prev_x, prev_y = None, None
current_font = "Open Sans"
font_path = resource("assets/fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf")
is_reset_settings_after_exiting = False

"""Stickers"""
# Width and height of all sticker images - 88 px
# Width and height of new sticker images - 512 px
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
    "strawberry",
    "butterfly",
    "flower2",
]
stickers = [Image.open(resource(f"assets/stickers/{name}.png")) for name in stickers_names]

"""Fonts"""
fonts_dict = {
    "Open Sans": "assets/fonts/Open_Sans/OpenSans-VariableFont_wdth,wght.ttf",
    "Monomakh": "assets/fonts/Monomakh/Monomakh-Regular.ttf",
    "Pacifico": "assets/fonts/Pacifico/Pacifico-Regular.ttf",
    "Comforter": "assets/fonts/Comforter/Comforter-Regular.ttf",
    "Rubik Bubbles": "assets/fonts/Rubik_Bubbles/RubikBubbles-Regular.ttf",
    "Press Start 2P": "assets/fonts/Press_Start_2P/PressStart2P-Regular.ttf",
}
fonts = list(fonts_dict.keys())

"""Frames"""
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
    ctk.CTkImage(
        Image.open(resource(f"assets/frames_preview/{name}.png")),
        size=(100, 100),
    )
    for name in frames_names
]

frames = [Image.open(resource(f"assets/frames/{name}.png")) for name in frames_names]

"""Effects"""
effect_values = [
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
