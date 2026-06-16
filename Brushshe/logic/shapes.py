# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from core.bezier import make_bezier
from core.bhbrush import bh_draw_line
from PIL import ImageDraw


class Shapes:
    def create_shape(self, shape):
        self.x_begin, self.y_begin = None, None
        self.shape = shape

        if shape == "Fill rectangle" or shape == "Fill oval":
            self.set_tool("shape", shape, None, None, None, "cross")
        else:
            self.set_tool("shape", shape, self.shape_size, 1, 50, "cross")

        self.ui.canvas.bind("<ButtonPress-1>", self.start_shape)
        self.ui.canvas.bind("<B1-Motion>", self.draw_shape)
        self.ui.canvas.bind("<ButtonRelease-1>", self.end_shape)

    def start_shape(self, event):
        self.shape_x, self.shape_y = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
        self.x_begin, self.y_begin = self.canvas_to_pict_xy(event.x, event.y)
        self.get_contrast_color()

        shape_methods = {
            "Rectangle": self.ui.canvas.create_rectangle,
            "Oval": self.ui.canvas.create_oval,
            "Line": self.ui.canvas.create_line,
            "Fill rectangle": self.ui.canvas.create_rectangle,
            "Fill oval": self.ui.canvas.create_oval,
        }

        create_method = shape_methods.get(self.shape)
        if create_method:
            param = "fill" if self.shape == "Line" else "outline"
            self.shape_id = create_method(
                self.shape_x, self.shape_y, self.shape_x, self.shape_y, **{param: self.contrast_color}
            )

    def draw_shape(self, event):
        if not hasattr(self, "shape_x"):
            return
        x, y = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
        self.ui.canvas.coords(self.shape_id, self.shape_x, self.shape_y, x, y)

    def end_shape(self, event):
        if not hasattr(self, "shape_x"):
            return

        x_end, y_end = self.canvas_to_pict_xy(event.x, event.y)

        if self.x_begin < x_end:
            x0, x1 = self.x_begin, x_end
        else:
            x0, x1 = x_end, self.x_begin
        if self.y_begin < y_end:
            y0, y1 = self.y_begin, y_end
        else:
            y0, y1 = y_end, self.y_begin

        if self.selected_mask_img is None:
            tmp_draw = ImageDraw.Draw(self.image)
        else:
            tmp_image = self.image.copy()
            tmp_draw = ImageDraw.Draw(tmp_image)

        color = self.get_tool_main_color()

        if self.shape == "Rectangle":
            tmp_draw.rectangle([x0, y0, x1, y1], outline=self.brush_color, width=self.tool_size)
        elif self.shape == "Oval":
            tmp_draw.ellipse([x0, y0, x1, y1], outline=self.brush_color, width=self.tool_size)
        elif self.shape == "Line":
            # self.draw_line(x_begin, y_begin, x_end, y_end)
            bh_draw_line(
                tmp_draw,
                self.x_begin,
                self.y_begin,
                x_end,
                y_end,
                color,
                self.tool_size,
                self.brush_shape,
                self.current_tool,
            )
        elif self.shape == "Fill rectangle":
            tmp_draw.rectangle([x0, y0, x1, y1], fill=self.brush_color)
        elif self.shape == "Fill oval":
            tmp_draw.ellipse([x0, y0, x1, y1], fill=self.brush_color)
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

    def bezier_shape(self):
        # Simple 4th point (cubic) Bezier curve.

        self.canvas_points = []
        self.image_points = []
        self.bezier_id = None

        # Clear canvas.
        self.update_canvas()

        self.set_tool("shape", "Bezier", self.shape_size, 1, 50, "cross")

        self.ui.canvas.bind("<ButtonPress-1>", self.start_bezier)
        self.ui.canvas.bind("<B1-Motion>", self.draw_bezier)
        self.ui.canvas.bind("<ButtonRelease-1>", self.end_bezier)
        self.ui.canvas.bind("<Motion>", self.draw_bezier)

    def start_bezier(self, event):
        if len(self.canvas_points) == 0:
            self.get_contrast_color()

            cx, cy = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)

            self.canvas_points.append((cx, cy))
            self.image_points.append(self.canvas_to_pict_xy(event.x, event.y))

            self.bezier_id = self.ui.canvas.create_line(
                cx, cy, cx, cy, fill=self.contrast_color, tag="tools"
            )  # smooth="bezier"

    def draw_bezier(self, event):
        if self.bezier_id is None or len(self.canvas_points) == 0:
            return

        cx, cy = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
        len_p = len(self.canvas_points)
        canvas_points_tmp = self.canvas_points.copy()

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

        self.ui.canvas.coords(self.bezier_id, *points_flat)

    def end_bezier(self, event):
        if self.bezier_id is None or len(self.canvas_points) == 0:
            return

        cx, cy = self.ui.canvas.canvasx(event.x), self.ui.canvas.canvasy(event.y)
        px, py = self.canvas_to_pict_xy(event.x, event.y)
        len_p = len(self.canvas_points)
        stop = False

        if len_p <= 1:
            self.canvas_points.append((cx, cy))
            self.image_points.append((px, py))
        else:
            tx, ty = self.canvas_points[len_p - 2]

            if cx == tx and cy == ty and len_p > 2:
                stop = True
            else:
                self.canvas_points.append(self.canvas_points[len_p - 1])
                self.canvas_points[len_p - 1] = (cx, cy)

                len_ip = len(self.image_points)
                self.image_points.append(self.image_points[len_ip - 1])
                self.image_points[len_ip - 1] = (px, py)

        # Finish
        if len(self.canvas_points) >= 4 or stop:
            # Calculate segments count.
            max_segments = 0
            points_len = len(self.image_points)
            for ii, ip in enumerate(self.image_points):
                if ii < points_len - 1:
                    max_segments += max(
                        abs(self.image_points[ii][0] - self.image_points[ii + 1][0]),
                        abs(self.image_points[ii][1] - self.image_points[ii + 1][1]),
                    )
            max_segments = max_segments // 3
            if max_segments < 32:
                max_segments = 32

            # Draw on picture.
            ts = [t / max_segments for t in range(int(max_segments + 1))]
            b = make_bezier(self.image_points)
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
                        self.tool_size,
                        self.brush_shape,
                        self.current_tool,
                    )

            if self.selected_mask_img is None:
                pass
            else:
                self.image.paste(tmp_image, (0, 0), self.selected_mask_img)
                del tmp_image

            self.ui.canvas.delete(self.bezier_id)
            self.update_canvas()
            self.record_action()

            # Reset nonlocal variables.
            self.canvas_points = []
            self.image_points = []
            self.bezier_id = None
