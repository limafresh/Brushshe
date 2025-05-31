class BhPoint():

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


class BhHistory():
    def __init__(
        self,
        max_length: int = 512
    ):
        self.history = []
        self.max_length = max_length

    def addPoint(self, point: BhPoint):
        if len(self.history) < self.max_length:
            self.history.append(point)
        else:
            del self.history[0]
            self.history.append(point)

    def getHistory(self):
        return self.history

    def getHistoryLength(self):
        return len(self.history)
