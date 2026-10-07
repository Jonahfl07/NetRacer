"""A car that drives clockwise around the edge of the track."""

import os

import config

RIGHT, DOWN, LEFT, UP = "right", "down", "left", "up"


class Car:
    def __init__(self, drawing, player, colour, draw_offset=0, image_path=None):
        self.drawing = drawing
        self.player = player
        self.draw_offset = draw_offset
        self._is_image = bool(image_path and os.path.exists(image_path))
        self._canvas = drawing.tk
        if self._is_image:
            self._shape = drawing.image(0, 0, image_path)
        else:
            self._shape = drawing.oval(
                0, 0, config.CAR_SIZE, config.CAR_SIZE,
                color=colour, outline=2, outline_color="#2b2b3b",
            )
        self.reset()

    def reset(self):
        self.x = config.TRACK_MARGIN
        self.y = config.TRACK_MARGIN
        self.direction = RIGHT
        self.laps = 0
        self._redraw()

    def move(self, width, height):
        """Advance one frame. Returns True if this move completed a lap."""
        if not self.player.speed:
            return False
        # Keep the fractional part: rounding the step down made a 25% boost do nothing.
        step = config.MOVE_STEP * self.player.speed
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
        x = self.x + self.draw_offset
        y = self.y + self.draw_offset
        if self._is_image:
            self._canvas.coords(self._shape, x, y)
        else:
            self._canvas.coords(self._shape, x, y, x + config.CAR_SIZE, y + config.CAR_SIZE)
