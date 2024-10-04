import sys
from tkinter import mainloop

from . import Browser, URL

from .parsers import HTMLParser
body = URL(sys.argv[1]).request()
nodes = HTMLParser(body).parse()
HTMLParser.print_tree(nodes)
quit()

if len(sys.argv) < 2:
    print("Usage: browser.py <url>")
    quit()

Browser().load(URL(sys.argv[1]))
mainloop()
