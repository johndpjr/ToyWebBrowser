import sys
from tkinter import mainloop

from . import Browser, URL


if len(sys.argv) < 2:
    print("Usage: browser.py <url>")
    quit()

Browser().load(URL(sys.argv[1]))
mainloop()
