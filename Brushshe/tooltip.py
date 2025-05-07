# Fork of Akascape's CTkToolTip

import time

from customtkinter import CTkFrame, CTkLabel, CTkToplevel, StringVar


class Tooltip(CTkToplevel):
    def __init__(
        self,
        widget: any = None,
        message: str = None,
        delay: float = 0.2,
        follow: bool = True,
        x_offset: int = +20,
        y_offset: int = +10,
        **message_kwargs,
    ):
        super().__init__()

        self.withdraw()
        self.overrideredirect(True)
        self.resizable(width=True, height=True)

        self.messageVar = StringVar()
        self.message = message
        self.messageVar.set(self.message)

        self.widget = widget
        self.delay = delay
        self.follow = follow
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.disable = False

        self.status = "outside"
        self.last_moved = 0

        self.frame = CTkFrame(self, border_width=1)
        self.frame.pack(padx=0, pady=0, fill="both", expand=True)

        self.message_label = CTkLabel(self.frame, textvariable=self.messageVar, **message_kwargs)
        self.message_label.pack(fill="both", padx=10, pady=2, expand=True)

        self.widget.bind("<Enter>", self.on_enter, add="+")
        self.widget.bind("<Leave>", self.on_leave, add="+")
        self.widget.bind("<Motion>", self.on_enter, add="+")
        self.widget.bind("<B1-Motion>", self.on_enter, add="+")
        self.widget.bind("<Destroy>", lambda _: self.hide(), add="+")

    def show(self) -> None:
        self.disable = False

    def on_enter(self, event) -> None:
        if self.disable:
            return
        self.last_moved = time.time()

        if self.status == "outside":
            self.status = "inside"

        if not self.follow:
            self.status = "inside"
            self.withdraw()

        root_width = self.winfo_screenwidth()
        widget_x = event.x_root
        space_on_right = root_width - widget_x
        text_width = self.message_label.winfo_reqwidth()
        offset_x = self.x_offset
        if space_on_right < text_width + 20:  # Adjust the threshold as needed
            offset_x = -text_width - 20  # Negative offset when space is limited on the right side
        self.geometry(f"+{event.x_root + offset_x}+{event.y_root + self.y_offset}")
        self.after(int(self.delay * 1000), self._show)

    def on_leave(self, event=None) -> None:
        if self.disable:
            return
        self.status = "outside"
        self.withdraw()

    def _show(self) -> None:
        if not self.widget.winfo_exists():
            self.hide()
            self.destroy()

        if self.status == "inside" and time.time() - self.last_moved >= self.delay:
            self.status = "visible"
            self.deiconify()

    def hide(self) -> None:
        if not self.winfo_exists():
            return
        self.withdraw()
        self.disable = True

    def is_disabled(self) -> None:
        return self.disable

    def get(self) -> None:
        return self.messageVar.get()

    def configure(self, message: str = None, delay: float = None, **kwargs):
        if delay:
            self.delay = delay

        self.messageVar.set(message)
        self.message_label.configure(**kwargs)
