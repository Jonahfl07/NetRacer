"""A car that drives clockwise around the edge of the track."""

import os

import config

RIGHT, DOWN, LEFT, UP = "right", "down", "left", "up"


class Car:
    def __init__(self, drawing, player, image_path=None):
        self.drawing = drawing
        self.player = player
        self.x = config.TRACK_MARGIN
        self.y = config.TRACK_MARGIN
        self.direction = RIGHT
        self.laps = 0
        self._is_image = bool(image_path and os.path.exists(image_path))
        if self._is_image:
            self._shape = drawing.image(self.x, self.y, image_path)
        else:
            # No sprite available: draw a square in the player's colour.
            self._shape = drawing.rectangle(
                self.x, self.y, self.x + config.CAR_SIZE, self.y + config.CAR_SIZE,
                color=player.colour,
            )

    def move(self, width, height):
        """Advance one frame. Returns True if this move completed a lap."""
        if not self.player.speed:
            return False
        step = max(1, int(config.MOVE_STEP * self.player.speed))
        min_x = min_y = config.TRACK_MARGIN
        max_x = width - config.TRACK_MARGIN - config.CAR_SIZE
        max_y = height - config.TRACK_MARGIN - config.CAR_SIZE
        lap_done = False

        if self.direction == RIGHT:
            self.x += step
            if self.x >= max_x:
                self.x, self.direction = max_x, DOWN
        elif self.direction == DOWN:
            self.y += step
            if self.y >= max_y:
                self.y, self.direction = max_y, LEFT
        elif self.direction == LEFT:
            self.x -= step
            if self.x <= min_x:
                self.x, self.direction = min_x, UP
        elif self.direction == UP:
            self.y -= step
            if self.y <= min_y:
                # Back at the top-left corner: that's a lap.
                self.y, self.direction = min_y, RIGHT
                self.laps += 1
                lap_done = True
                print(f"{self.player.name} completed lap {self.laps}")

        self._redraw()
        return lap_done

    def _redraw(self):
        canvas = self.drawing.tk
        if self._is_image:
            canvas.coords(self._shape, self.x, self.y)
        else:
            canvas.coords(self._shape, self.x, self.y,
                          self.x + config.CAR_SIZE, self.y + config.CAR_SIZE)
