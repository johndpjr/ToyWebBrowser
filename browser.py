import socket
import subprocess
import ssl
import tkinter as tk


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


def lex(body: str):
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text


def layout(text: str, width: int):
    HSTEP, VSTEP = 13, 18
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= width - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list


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
        self.window.resizable(True, True)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.window.bind("<Configure>", self.resize)
        self.scroll = 0
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Down>", self.scrolldown)
        # Support scrolling events (2-2)
        self.window.bind("<Button-4>", self.scrollup)
        self.window.bind("<Button-5>", self.scrolldown)

    def load(self, url: URL):
        body = url.request()
        self.text = lex(body)
        self.display_list = layout(self.text, self.WIDTH)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + self.HEIGHT: continue
            if y + self.VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def resize(self, e):
        self.window.geometry(f"{e.width}x{e.height}")
        self.display_list = layout(self.text, e.width)

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
