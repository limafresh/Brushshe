# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import data
from core.bezier import make_bezier
from core.bhbrush import bh_draw_line
from PIL import ImageDraw
from utils import colors


class Shapes:
    def create_shape(self, shape):
        x_begin, y_begin = None, None

        def start_shape(event):
            nonlocal x_begin, y_begin

            self.shape_x, self.shape_y = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
            x_begin, y_begin = self.canvas_to_pict_xy(event.x, event.y)
            colors.get_contrast_color()

            shape_methods = {
                "Rectangle": self.ui.canvas.create_rectangle,
                "Oval": self.ui.canvas.create_oval,
                "Line": self.ui.canvas.create_line,
                "Fill rectangle": self.ui.canvas.create_rectangle,
                "Fill oval": self.ui.canvas.create_oval,
            }

            create_method = shape_methods.get(shape)
            if create_method:
                param = "fill" if shape == "Line" else "outline"
                self.shape_id = create_method(
                    self.shape_x, self.shape_y, self.shape_x, self.shape_y, **{param: self.contrast_color}
                )

        def draw_shape(event):
            if not hasattr(self, "shape_x"):
                return
            x, y = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
            self.ui.canvas.coords(self.shape_id, self.shape_x, self.shape_y, x, y)

        def end_shape(event):
            nonlocal x_begin, y_begin

            if not hasattr(self, "shape_x"):
                return

            x_end, y_end = self.canvas_to_pict_xy(event.x, event.y)

            if x_begin < x_end:
                x0, x1 = x_begin, x_end
            else:
                x0, x1 = x_end, x_begin
            if y_begin < y_end:
                y0, y1 = y_begin, y_end
            else:
                y0, y1 = y_end, y_begin

            if self.selected_mask_img is None:
                tmp_draw = ImageDraw.Draw(self.image)
            else:
                tmp_image = self.image.copy()
                tmp_draw = ImageDraw.Draw(tmp_image)

            color = self.get_tool_main_color()

            if shape == "Rectangle":
                tmp_draw.rectangle([x0, y0, x1, y1], outline=data.brush_color, width=data.tool_size)
            elif shape == "Oval":
                tmp_draw.ellipse([x0, y0, x1, y1], outline=data.brush_color, width=data.tool_size)
            elif shape == "Line":
                # self.draw_line(x_begin, y_begin, x_end, y_end)
                bh_draw_line(
                    tmp_draw, x_begin, y_begin, x_end, y_end, color, data.tool_size, data.brush_shape, self.current_tool
                )
            elif shape == "Fill rectangle":
                tmp_draw.rectangle([x0, y0, x1, y1], fill=data.brush_color)
            elif shape == "Fill oval":
                tmp_draw.ellipse([x0, y0, x1, y1], fill=data.brush_color)
            else:
                print("Warning: Incorrect shape.")

            if self.selected_mask_img is None:
                pass
            else:
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
                del tmp_image

            self.update_canvas()
            self.record_action()

            # Removing unnecessary variables for normal selection of the next shape in the menu
            #   and disabling other side effects.
            del self.shape_x, self.shape_y
            self.ui.canvas.delete(self.shape_id)

        if shape == "Fill rectangle" or shape == "Fill oval":
            self.set_tool("shape", shape, None, None, None, "cross")
        else:
            self.set_tool("shape", shape, data.shape_size, 1, 50, "cross")

        self.ui.canvas.bind("<ButtonPress-1>", start_shape)
        self.ui.canvas.bind("<B1-Motion>", draw_shape)
        self.ui.canvas.bind("<ButtonRelease-1>", end_shape)

    def bezier_shape(self):
        # Simple 4th point (cubic) Bezier curve.

        canvas_points = []
        image_points = []
        bezier_id = None

        # Clear canvas.
        self.update_canvas()

        def start(event):
            nonlocal canvas_points, image_points, bezier_id

            if len(canvas_points) == 0:
                colors.get_contrast_color()

                cx, cy = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)

                canvas_points.append((cx, cy))
                image_points.append(self.canvas_to_pict_xy(event.x, event.y))

                bezier_id = self.ui.canvas.create_line(
                    cx, cy, cx, cy, fill=self.contrast_color, tag="tools"
                )  # smooth="bezier"

        def drawing(event):
            nonlocal canvas_points, bezier_id

            if bezier_id is None or len(canvas_points) == 0:
                return

            cx, cy = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
            len_p = len(canvas_points)
            canvas_points_tmp = canvas_points.copy()

            if len_p <= 1:
                canvas_points_tmp.append((cx, cy))
            else:
                canvas_points_tmp.append(canvas_points_tmp[len_p - 1])
                canvas_points_tmp[len_p - 1] = (cx, cy)

            ts = [t / 32.0 for t in range(33)]  # 32 lines for preview.
            b = make_bezier(canvas_points_tmp)
            points = b(ts)

            # Do 2d array flat for canvas.coords
            points_flat = [j for sub in points for j in sub]

            self.ui.canvas.coords(bezier_id, *points_flat)

        def end(event):
            nonlocal canvas_points, image_points, bezier_id

            if bezier_id is None or len(canvas_points) == 0:
                return

            cx, cy = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
            px, py = self.canvas_to_pict_xy(event.x, event.y)
            len_p = len(canvas_points)
            stop = False

            if len_p <= 1:
                canvas_points.append((cx, cy))
                image_points.append((px, py))
            else:
                tx, ty = canvas_points[len_p - 2]

                if cx == tx and cy == ty and len_p > 2:
                    stop = True
                else:
                    canvas_points.append(canvas_points[len_p - 1])
                    canvas_points[len_p - 1] = (cx, cy)

                    len_ip = len(image_points)
                    image_points.append(image_points[len_ip - 1])
                    image_points[len_ip - 1] = (px, py)

            # Finish
            if len(canvas_points) >= 4 or stop:
                # Calculate segments count.
                max_segments = 0
                points_len = len(image_points)
                for ii, ip in enumerate(image_points):
                    if ii < points_len - 1:
                        max_segments += max(
                            abs(image_points[ii][0] - image_points[ii + 1][0]),
                            abs(image_points[ii][1] - image_points[ii + 1][1]),
                        )
                max_segments = max_segments // 3
                if max_segments < 32:
                    max_segments = 32

                # Draw on picture.
                ts = [t / max_segments for t in range(int(max_segments + 1))]
                b = make_bezier(image_points)
                points = b(ts)
                points_len = len(points)

                color = self.get_tool_main_color()

                if self.selected_mask_img is None:
                    tmp_image = self.image
                    tmp_draw = ImageDraw.Draw(tmp_image)
                else:
                    tmp_image = self.image.copy()
                    tmp_draw = ImageDraw.Draw(tmp_image)

                for it, tt in enumerate(points):
                    if it < points_len - 1:
                        bh_draw_line(
                            tmp_draw,
                            int(points[it][0]),
                            int(points[it][1]),
                            int(points[it + 1][0]),
                            int(points[it + 1][1]),
                            color,
                            data.tool_size,
                            data.brush_shape,
                            self.current_tool,
                        )

                if self.selected_mask_img is None:
                    pass
                else:
                    self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
                    del tmp_image

                self.ui.canvas.delete(bezier_id)
                self.update_canvas()
                self.record_action()

                # Reset nonlocal variables.
                canvas_points = []
                image_points = []
                bezier_id = None

        self.set_tool("shape", "Bezier", data.shape_size, 1, 50, "cross")

        self.ui.canvas.bind("<ButtonPress-1>", start)
        self.ui.canvas.bind("<B1-Motion>", drawing)
        self.ui.canvas.bind("<ButtonRelease-1>", end)
        self.ui.canvas.bind("<Motion>", drawing)
