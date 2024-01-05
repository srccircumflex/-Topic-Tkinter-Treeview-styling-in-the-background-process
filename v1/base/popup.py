from typing import Literal
from tkinter import Tk


class PopupRoot(Tk):

    window_mode: str
    title_label: str

    fullscreen_height: int
    fullscreen_width: int

    def __init__(
            self,
            window_mode: Literal["dead", "headless", "fullscreen", "top"] = False,
            title: str = "Column Select",
    ):
        Tk.__init__(self)
        self.resizable(False, False)

        self.window_mode = window_mode
        self.title_label = title

        self.fullscreen_height = int(self.winfo_screenheight() * 0.0756)
        self.fullscreen_width = int(self.winfo_screenwidth() * 0.062)

        if window_mode:
            _drag = True
            if window_mode == "dead":
                self.overrideredirect(True)
            elif window_mode == "headless":
                self.wm_attributes('-type', 'splash')
            elif window_mode == "fullscreen":
                self.wm_attributes('-type', 'splash')
                _drag = False
            else:
                self.title(title)

            self.attributes('-topmost', True)

            if _drag:
                wx, wy = 0, 0

                def drag(event):
                    nonlocal wx, wy
                    wx, wy = event.x, event.y

                def move_window(event):
                    self.geometry('+{0}+{1}'.format(event.x_root - wx, event.y_root - wy))

                self.bind('<Button-1>', drag)
                self.bind('<B1-Motion>', move_window)

        self.title(title)

    def resize(self, height: int, width: int):
        self.configure(height=height, width=width)
        self.focus_force()
