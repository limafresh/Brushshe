# A hack for normal CTkScrollableFrame scrolling on Linux

import sys


def scroll_on_gallery(event):
    global widget
    if event.num == 5 or event.delta < 0:
        count = 1
    if event.num == 4 or event.delta > 0:
        count = -1
    widget._parent_canvas.yview("scroll", count, "units")


def set_scroll_event(event):
    global widget
    widget._parent_canvas.bind_all("<MouseWheel>", lambda e: scroll_on_gallery(e))
    widget._parent_canvas.bind_all("<Button-4>", lambda e: scroll_on_gallery(e))
    widget._parent_canvas.bind_all("<Button-5>", lambda e: scroll_on_gallery(e))


def remove_scroll_event(event):
    global widget
    widget._parent_canvas.unbind_all("<MouseWheel>")
    widget._parent_canvas.unbind_all("<Button-4>")
    widget._parent_canvas.unbind_all("<Button-5>")


def scroll(target_widget):
    global widget
    if sys.platform == "linux":
        widget = target_widget
        widget.bind("<Enter>", lambda e: set_scroll_event(e))
        widget.bind("<Leave>", lambda e: remove_scroll_event(e))


widget = None
