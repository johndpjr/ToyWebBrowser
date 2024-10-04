import tkinter as tk
import tkinter.font

from . import URL, Text, Element
from .parsers import HTMLParser


FONTS = {}


def get_font(size, weight, style):
    # No caching
    # return tk.font.Font(size=size, weight=weight, slant=style)
    # With caching
    key = (size, weight, style)
    if key not in FONTS:
        font = tk.font.Font(size=size, weight=weight, slant=style)
        label = tk.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class Layout:
    HSTEP, VSTEP = 13, 18
    WIDTH, HEIGHT = 800, 600

    def __init__(self, tokens: list[Text | Element]):
        self.tokens = tokens
        self.display_list = []

        self.cursor_x = self.HSTEP
        self.cursor_y = self.VSTEP

        self.weight = "normal"
        self.style = "roman"
        self.size = 12

        self.line = []
        for tok in tokens:
            self.token(tok)
        self.flush()

    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += self.VSTEP

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)
        if self.cursor_x + w > self.WIDTH - self.HSTEP:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = self.HSTEP
        self.line = []


class Browser:
    WIDTH, HEIGHT = 800, 600
    VSTEP = 18
    SCROLL_STEP = 100

    def __init__(self):
        self.window = tk.Tk()
        self.canvas = tk.Canvas(
            self.window,
            width=self.WIDTH,
            height=self.HEIGHT
        )
        self.window.resizable()
        self.canvas.pack()
        self.scroll = 0
        self.display_list = []
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Down>", self.scrolldown)
        # Support scrolling events (2-2)
        self.window.bind("<Button-4>", self.scrollup)
        self.window.bind("<Button-5>", self.scrolldown)

    def load(self, url: URL):
        body = url.request()
        tokens = lex(body)
        self.display_list = Layout(tokens).display_list
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, word, font in self.display_list:
            if y > self.scroll + self.HEIGHT: continue
            if y + font.metrics("linespace") < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=word, font=font, anchor="nw")

    def scrollup(self, e):
        self.scroll -= self.SCROLL_STEP
        self.draw()

    def scrolldown(self, e):
        self.scroll += self.SCROLL_STEP
        self.draw()
