import socket
import subprocess
import ssl


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
