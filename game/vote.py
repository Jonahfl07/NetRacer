"""The lap vote that opens a race: both players pick, then one vote is drawn at random."""

import time

from guizero import Box, Text

import config
from widgets import (BOOST_GREEN, DARK, FONT, CanvasButton,
                     make_canvas, rounded_rect)

SPIN_SECONDS = 2.5      # how long the draw flickers between the two votes
HOLD_SECONDS = 1.5      # how long the winning number stays up before the race starts
FLICKER_SECONDS = 0.12
CARD_WIDTH = 760
CARD_HEIGHT = 260


class VoteScreen:
    def __init__(self, app, game, on_done):
        self.game = game
        self.on_done = on_done
        self.done = False
        self.box = Box(app, width="fill", height="fill")
        Box(self.box, width=1, height=70)
        Text(self.box, text="Vote on the race length", size=26, font=FONT, color=DARK)
        Text(self.box, text="You each vote for a number of laps, then one of the two votes is picked at random.",
             size=13, font=FONT, color=DARK)
        Box(self.box, width=1, height=14)
        self.card = make_canvas(self.box, CARD_WIDTH, CARD_HEIGHT)
        Box(self.box, width=1, height=14)
        row = Box(self.box, layout="grid")
        self.buttons = [
            CanvasButton(row, f"{laps}\nLAPS", BOOST_GREEN, lambda laps=laps: game.cast_vote(laps),
                         140, 100, font_size=16, grid=[column, 0])
            for column, laps in enumerate(config.LAP_OPTIONS)
        ]
        app.repeat(80, self.update)
        self.update()

    def update(self):
        if self.done:
            return
        game = self.game
        can_vote = game.my_vote is None and not game.opponent_left
        for button in self.buttons:
            button.set_enabled(can_vote)
        self._draw_card()
        if game.chosen_laps is not None and game.reveal_seconds() >= SPIN_SECONDS + HOLD_SECONDS:
            self.done = True
            self.box.destroy()
            self.on_done()

    def _draw_card(self):
        canvas = self.card.tk
        canvas.delete("all")
        game = self.game
        rounded_rect(canvas, 4, 4, CARD_WIDTH - 4, CARD_HEIGHT - 4, radius=16,
                     fill="white", outline=DARK, width=2)
        centre = CARD_WIDTH / 2
        if game.opponent_left:
            self._message(canvas, "Your opponent has disconnected")
        elif game.chosen_laps is None:
            if game.my_vote is None:
                self._message(canvas, "Pick how many laps you want to race")
            elif game.opponent_vote is None:
                self._message(canvas, f"You voted for {game.my_vote} laps.\nWaiting for your opponent...")
            else:
                self._message(canvas, "Both votes are in...")
        else:
            self._draw_reveal(canvas, centre)

    def _message(self, canvas, text):
        canvas.create_text(CARD_WIDTH / 2, CARD_HEIGHT / 2, text=text, justify="center",
                           width=CARD_WIDTH - 60, font=(FONT, 20, "bold"), fill=DARK)

    def _draw_reveal(self, canvas, centre):
        game = self.game
        elapsed = game.reveal_seconds()
        spinning = elapsed < SPIN_SECONDS
        shown = ([game.my_vote, game.opponent_vote][int(elapsed / FLICKER_SECONDS) % 2]
                 if spinning else game.chosen_laps)
        for x, owner, vote, colour in ((30, "YOU", game.my_vote, config.MY_COLOUR),
                                       (CARD_WIDTH - 230, "OPPONENT", game.opponent_vote,
                                        config.OPPONENT_COLOUR)):
            picked = not spinning and vote == game.chosen_laps
            rounded_rect(canvas, x, 70, x + 200, 170, radius=12, fill=colour, outline=DARK,
                         width=5 if picked else 2)
            canvas.create_text(x + 100, 120, text=f"{owner}\n{vote} laps", justify="center",
                               font=(FONT, 15, "bold"), fill=DARK)
        canvas.create_text(centre, 120, text=str(shown), font=(FONT, 56, "bold"), fill=DARK)
        canvas.create_text(centre, 216, font=(FONT, 18, "bold"), fill=DARK,
                           text="Picking a vote at random..." if spinning
                           else f"{game.chosen_laps} laps it is!")
