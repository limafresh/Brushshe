import math


class BhPoint:
    def __init__(
        self,
        x: float,
        y: float,
        pressure: float = 1,
        *args,
        **kwargs,
    ):
        self.x = x
        self.y = y
        self.pressure = pressure

        # Will need in future.

        # self.distance = 0
        # self.velocity = 0
        # self.direction = 0


class BhHistory:
    def __init__(self, limit_length: int = 256):
        max_length = 256
        self.history = []
        self.limit_length = limit_length
        if self.limit_length > max_length:
            self.limit_length = max_length

    def add_point(self, point: BhPoint):
        if len(self.history) < self.limit_length:
            self.history.append(point)
        else:
            del self.history[0]
            self.history.append(point)

    def get_history(self):
        return self.history

    def get_history_length(self):
        return len(self.history)

    def get_last_points(self, count):
        ll = self.get_history_length()
        if count <= ll:
            return self.history[ll - count : ll - 1]
        else:
            return self.history

    def get_smoothing_point(self, smoothing_quality, smoothing_factor):
        ll = self.get_history_length()
        if ll == 0:
            return None
        if ll == 1:
            return self.history[0]

        coords_x = 0.0
        coords_y = 0.0
        velocity = 0.01  # TODO: Get from BhPoint
        velocity_sum = 0.0
        scale_sum = 0.0
        gaussian_weight = 0.0
        gaussian_weight_sqr = smoothing_factor * smoothing_factor

        max_index = ll - 1
        min_index = max(0, ll - smoothing_quality)

        if gaussian_weight_sqr != 0.0:
            gaussian_weight = 1 / (math.sqrt(2 * math.pi) * smoothing_factor)

        last_point = self.history[max_index]

        for index in range(max_index, min_index, -1):
            rate = 0.0
            next_coord = self.history[index]

            if gaussian_weight_sqr != 0.0:
                velocity_sum += velocity * 100
                rate = gaussian_weight * math.exp(-velocity_sum * velocity_sum / (2 * gaussian_weight_sqr))

            scale_sum += rate
            coords_x += rate * next_coord.x
            coords_y += rate * next_coord.y

        if scale_sum == 0.0:
            return last_point
        else:
            coords_x /= scale_sum
            coords_y /= scale_sum
            return BhPoint(coords_x, coords_y, last_point.pressure)
