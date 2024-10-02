import socket
import subprocess
import ssl
import tkinter as tk
import tkinter.font


class URL:
    HTTP_PORT = 80
    HTTPS_PORT = 443

    def __init__(self, url: str):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["file", "http", "https"]
        if self.scheme == "http":
            self.port = self.HTTP_PORT
        elif self.scheme == "https":
            self.port = self.HTTPS_PORT

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        if self.scheme == "file":
            subprocess.call(("xdg-open", self.path))
            return None
        # Connect to remote server
        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        # Request
        request = f"GET {self.path} HTTP/1.1\r\n"
        request += f"Host: {self.host}\r\n"
        request += "Connection: close\r\n"
        request += "User-Agent: ToyWebBrowser/v0.0\r\n"
        request += "\r\n"
        s.send(request.encode("utf8"))
        # Response
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        content = response.read()
        s.close()
        return content


FONTS = {}


class Text:
    def __init__(self, text):
        self.text = text


class Tag:
    def __init__(self, tag):
        self.tag = tag


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


def lex(body: str):
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer: out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        elif not in_tag:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out


class Layout:
    HSTEP, VSTEP = 13, 18
    WIDTH, HEIGHT = 800, 600

    def __init__(self, tokens: list[Text | Tag]):
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


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: browser.py <url>")
        quit()
    Browser().load(URL(sys.argv[1]))
    tk.mainloop()
