# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys


def resource(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


def shorten_filename(filename: str, max_length: int = 20) -> str:
    if len(filename) > max_length:
        return filename[: max_length - 3] + "..."
    else:
        return filename


def rgb_tuple_to_rgba_tuple(color, alpha: int):
    try:
        res = (color[0], color[1], color[2], alpha)
    except Exception:
        print("Error: Wrong color.")
        res = (0, 0, 0, 0)
    return res


def color_diff(color1: float | tuple[int, ...], color2: float | tuple[int, ...]) -> float:
    first = color1 if isinstance(color1, tuple) else (color1,)
    second = color2 if isinstance(color2, tuple) else (color2,)
    return sum(abs(first[i] - second[i]) for i in range(len(second)))
