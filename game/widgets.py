"""Colours and canvas-drawn widgets shared by every screen."""

from guizero import Drawing

BACKGROUND = "#dedfff"
DARK = "#2b2b3b"
PURPLE = "#9494ff"
BOOST_GREEN = "#c2f5c9"
HACK_RED = "#ff6b6b"
DISABLED = "#cfd0e0"
DISABLED_TEXT = "#8a8a9c"
FONT = "Helvetica"


def rounded_rect(canvas, x1, y1, x2, y2, radius=12, **options):
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **options)


def make_canvas(parent, width, height, **layout):
    drawing = Drawing(parent, width=width, height=height, **layout)
    drawing.tk.config(bg=BACKGROUND, highlightthickness=0, bd=0)
    return drawing


class CanvasButton:
    """A clickable rounded rectangle that can be greyed out."""

    def __init__(self, parent, text, colour, command, width, height, font_size=13, **layout):
        self.text = text
        self.colour = colour
        self.command = command
        self.width = width
        self.height = height
        self.font_size = font_size
        self.enabled = True
        self.drawing = make_canvas(parent, width, height, **layout)
        self.canvas = self.drawing.tk
        self.drawing.when_clicked = lambda event: self._clicked()
        self._draw()

    def set_enabled(self, enabled):
        if enabled != self.enabled:
            self.enabled = enabled
            self._draw()

    def _clicked(self):
        if self.enabled:
            self.command()

    def _draw(self):
        canvas = self.canvas
        canvas.delete("all")
        canvas.config(cursor="hand2" if self.enabled else "arrow")
        fill = self.colour if self.enabled else DISABLED
        rounded_rect(canvas, 8, 8, self.width - 8, self.height - 8, radius=12,
                     fill=fill, outline=DARK if self.enabled else DISABLED_TEXT, width=2)
        canvas.create_text(
            self.width / 2, self.height / 2, text=self.text, justify="center",
            width=self.width - 24, font=(FONT, self.font_size, "bold"),
            fill=DARK if self.enabled else DISABLED_TEXT,
        )
