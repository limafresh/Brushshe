# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math

metadata = {"description": "Adds a star drawing feature", "tool": ["Star", 2, 1, 50, "cross"]}

app = None
x1, y1, x2, y2 = None, None, None, None
preview_id = None


def start_star(event):
    global x1, y1
    x1, y1 = event.x, event.y


def get_star_points(x1, y1, x2, y2):
    left = min(x1, x2)
    top = min(y1, y2)

    width = abs(x2 - x1)
    height = abs(y2 - y1)

    cx = left + width / 2
    cy = top + height / 2

    outer_rx = width / 2
    outer_ry = height / 2

    inner_rx = outer_rx * 0.4
    inner_ry = outer_ry * 0.4

    points = []

    for i in range(10):
        angle = math.radians(-90 + i * 36)

        if i % 2 == 0:
            rx = outer_rx
            ry = outer_ry
        else:
            rx = inner_rx
            ry = inner_ry

        x = cx + rx * math.cos(angle)
        y = cy + ry * math.sin(angle)

        points.extend((x, y))

    return points


def draw_star(event):
    global preview_id

    app.canvas.delete(preview_id)

    points = get_star_points(x1, y1, event.x, event.y)

    preview_id = app.canvas.create_line(points, fill=app.get_contrast_color(), smooth=False)


def end_star(event):
    app.canvas.delete(preview_id)

    points = get_star_points(x1, y1, event.x, event.y)

    for i in range(0, len(points) - 2, 2):
        app.draw_line(int(points[i]), int(points[i + 1]), int(points[i + 2]), int(points[i + 3]))

    app.draw_line(int(points[-2]), int(points[-1]), int(points[0]), int(points[1]))

    app.update_canvas()
    app.record_action()


def register(brushshe):
    global app
    app = brushshe

    app.canvas.bind("<ButtonPress-1>", start_star)
    app.canvas.bind("<B1-Motion>", draw_star)
    app.canvas.bind("<ButtonRelease-1>", end_star)
