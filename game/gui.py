"""The game window: track, cars, RAM and stack readouts, and boost buttons."""

from guizero import Box, Drawing, PushButton, Text, Window

import config
from boosts import BOOSTS
from car import Car

BACKGROUND = "#1e1e1e"
TEXT_COLOUR = "white"


class Gui:
    def __init__(self, app, game, my_car_image, opponent_car_image):
        self.app = app
        self.game = game
        app.bg = BACKGROUND

        top_box = Box(app, width="fill", align="top")
        self.ram_text = Text(top_box, size=20, color=TEXT_COLOUR)
        self.stack_text = Text(top_box, size=14, color=TEXT_COLOUR)
        lap_box = Box(top_box, width="fill")
        self.my_laps_text = Text(lap_box, size=16, color=TEXT_COLOUR, align="left")
        self.opponent_laps_text = Text(lap_box, size=16, color=TEXT_COLOUR, align="right")

        button_box = Box(app, layout="grid", align="bottom")
        self.buttons = [
            PushButton(button_box, text=f"{boost.name} [{boost.cost}]",
                       command=game.cast, args=[index], grid=[index, 0])
            for index, boost in enumerate(BOOSTS)
        ]
        for button in self.buttons:
            button.text_color = TEXT_COLOUR

        self.drawing = Drawing(app, width=config.DRAWING_SIZE, height=config.DRAWING_SIZE)
        self.drawing.rectangle(
            config.TRACK_MARGIN, config.TRACK_MARGIN,
            config.DRAWING_SIZE - config.TRACK_MARGIN,
            config.DRAWING_SIZE - config.TRACK_MARGIN,
            color="black", outline=True, outline_color="white",
        )
        self.my_car = Car(self.drawing, game.me, my_car_image)
        self.opponent_car = Car(self.drawing, game.opponent, opponent_car_image)

        app.repeat(config.FRAME_MS, self._frame)
        app.repeat(1000, self._recharge)
        app.repeat(100, self._refresh_text)
        self._refresh_text()

    def _frame(self):
        self.game.process_inbox()
        self.game.tick()
        size = config.DRAWING_SIZE
        lapped = self.my_car.move(size, size)
        lapped |= self.opponent_car.move(size, size)
        if lapped:
            self.game.record_lap(self.my_car.laps, self.opponent_car.laps)
            if self.game.winner:
                self._show_result()

    def _recharge(self):
        self.game.me.recharge()
        self.game.opponent.recharge()

    def _refresh_text(self):
        game = self.game
        self.ram_text.value = f"RAM: {int(game.me.ram)} / {game.me.max_ram}"
        if not len(game.stack):
            stack = "Stack: empty"
        elif game.resolving:
            stack = f"Resolving: {game.stack.describe(game.my_id)}"
        else:
            stack = (f"Stack: {game.stack.describe(game.my_id)}"
                     f"  (resolves in {game.seconds_until_resolve():.0f}s)")
        if game.opponent_left:
            stack += "  |  Opponent disconnected"
        self.stack_text.value = stack
        self.my_laps_text.value = f"Your laps: {self.my_car.laps}/{game.max_laps}"
        self.opponent_laps_text.value = (
            f"Opponent laps: {self.opponent_car.laps}/{game.max_laps}")
        for button in self.buttons:
            if game.resolving or game.winner:
                button.disable()
            else:
                button.enable()

    def _show_result(self):
        self.app.cancel(self._frame)
        self.app.cancel(self._recharge)
        self._refresh_text()
        if self.game.winner == "me":
            headline, detail = "Congratulations", "You won!"
        elif self.game.winner == "tie":
            headline, detail = "Photo finish", "It's a tie!"
        else:
            headline, detail = "Good effort", "Your opponent won!"
        window = Window(self.app, title="Race over", width=600, height=300, bg=BACKGROUND)
        Text(window, text=headline, size=48, color=TEXT_COLOUR)
        Text(window, text=detail, size=32, color=TEXT_COLOUR)
