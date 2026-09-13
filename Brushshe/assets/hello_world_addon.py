# Any copyright is dedicated to the Public Domain.
# https://creativecommons.org/publicdomain/zero/1.0/

import math
import random

metadata = {"author": "limafresh", "version": "1.0.0", "description": "Draws a simple picture on canvas"}


def register(brushshe):
    colors = ["green", "red", "orange", "pink", "purple", "yellow"]

    brushshe.set_addon_tool_size(10)

    cx, cy = 250, 250
    r = 150
    points = []

    for i in range(5):
        angle = math.radians(90 + i * 72)
        x = cx + r * math.cos(angle)
        y = cy - r * math.sin(angle)
        points.append((x, y))

    order = [0, 2, 4, 1, 3, 0]

    for i in range(len(order) - 1):
        brushshe.change_color(random.choice(colors))

        x1, y1 = points[order[i]]
        x2, y2 = points[order[i + 1]]

        brushshe.draw_line(int(x1), int(y1), int(x2), int(y2))
