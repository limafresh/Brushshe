# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math

metadata = {"description": "Adds a heart drawing feature", "tool": ["Heart", 2, 1, 50, "cross"]}

app = None
x1, y1, x2, y2 = None, None, None, None
preview_id = None


def start_heart(event):
    global x1, y1
    x1, y1 = event.x, event.y


def get_heart_points(x1, y1, x2, y2):
    left = min(x1, x2)
    top = min(y1, y2)

    width = abs(x2 - x1)
    height = abs(y2 - y1)

    cx = left + width / 2
    cy = top + height / 2

    points = []

    for t in range(0, 361, 5):
        a = math.radians(t)

        x = cx + width * 16 * math.sin(a) ** 3 / 34

        y = cy - height * (13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)) / 34

        points.extend((x, y))

    return points


def draw_heart(event):
    global preview_id

    app.canvas.delete(preview_id)

    points = get_heart_points(x1, y1, event.x, event.y)

    preview_id = app.canvas.create_line(points, fill=app.get_contrast_color(), smooth=False)


def end_heart(event):
    app.canvas.delete(preview_id)

    points = get_heart_points(x1, y1, event.x, event.y)

    for i in range(0, len(points) - 2, 2):
        app.draw_line(int(points[i]), int(points[i + 1]), int(points[i + 2]), int(points[i + 3]))

    app.draw_line(int(points[-2]), int(points[-1]), int(points[0]), int(points[1]))

    app.update_canvas()
    app.record_action()


def register(brushshe):
    global app
    app = brushshe

    app.canvas.bind("<ButtonPress-1>", start_heart)
    app.canvas.bind("<B1-Motion>", draw_heart)
    app.canvas.bind("<ButtonRelease-1>", end_heart)
