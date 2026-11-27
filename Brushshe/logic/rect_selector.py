# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Callable

from customtkinter import CTkCanvas

from . import state


class RectSelector:
    def __init__(self, canvas: CTkCanvas, canvas_to_pict_xy: Callable, tag: str):
        self.canvas = canvas
        self.canvas_to_pict_xy = canvas_to_pict_xy
        self.tag = tag

        self.reset_positions()

    def reset_positions(self):
        self.x_begin = None
        self.y_begin = None
        self.x_end = None
        self.y_end = None

    def update(self, event):
        x, y = self.canvas_to_pict_xy(event.x, event.y)

        if self.x_begin is None or self.y_begin is None:
            self.x_begin = x
            self.y_begin = y

        self.x_end = x
        self.y_end = y

        x_max = state.image.width - 1
        y_max = state.image.height - 1

        self.x_begin = max(self.x_begin, 0)
        self.x_begin = min(self.x_begin, x_max)
        self.y_begin = max(self.y_begin, 0)
        self.y_begin = min(self.y_begin, y_max)
        self.x_end = max(self.x_end, 0)
        self.x_end = min(self.x_end, x_max)
        self.y_end = max(self.y_end, 0)
        self.y_end = min(self.y_end, y_max)

        x1 = min(self.x_begin, self.x_end)
        x2 = max(self.x_begin, self.x_end)
        y1 = min(self.y_begin, self.y_end)
        y2 = max(self.y_begin, self.y_end)

        self.canvas.delete(self.tag)
        self.draw_dashed_rect(x1, y1, x2, y2)

    def draw_dashed_rect(self, x1: float, y1: float, x2: float, y2: float):
        self.canvas.create_rectangle(
            int(x1 * state.zoom),
            int(y1 * state.zoom),
            int((x2 + 1) * state.zoom - 1),
            int((y2 + 1) * state.zoom - 1),
            outline="white",
            width=1,
            tag=self.tag,
        )
        self.canvas.create_rectangle(
            int(x1 * state.zoom),
            int(y1 * state.zoom),
            int((x2 + 1) * state.zoom - 1),
            int((y2 + 1) * state.zoom - 1),
            outline="black",
            width=1,
            tag=self.tag,
            dash=(5, 5),
        )

    def finish(self) -> tuple[float, float, float, float] | None:
        if self.x_begin is None or self.y_begin is None:
            return

        x1 = min(self.x_begin, self.x_end)
        x2 = max(self.x_begin, self.x_end)
        y1 = min(self.y_begin, self.y_end)
        y2 = max(self.y_begin, self.y_end)

        self.canvas.delete(self.tag)

        self.reset_positions()

        return x1, y1, x2, y2
