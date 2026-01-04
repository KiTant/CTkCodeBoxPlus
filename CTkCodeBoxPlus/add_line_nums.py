import customtkinter
from tklinenums import TkLineNumbers


class AddLineNums(TkLineNumbers):
    """
    Line numbers widget for CTkCodeBox (uses TkLineNumbers)
    """
    def __init__(self,
                 master,
                 text_color=None,
                 justify="left",
                 padx=30,
                 auto_padx=True,
                 **kwargs):

        self.master = master
        self.text_color = self.master.cget("border_color") if text_color is None else text_color
        self.fg_color = self.master.cget("fg_color")
        self.auto_padx = auto_padx
        if self.auto_padx:
            padx = padx * (int(self.master.cget("font").cget("size")) / 10)

        customtkinter.windows.widgets.appearance_mode.CTkAppearanceModeBaseClass.__init__(self)

        super().__init__(self.master, self.master, justify=justify,
                         colors=(self.master._apply_appearance_mode(self.text_color),
                                 self.master._apply_appearance_mode(self.fg_color)),
                         relief="flat", height=self.master.winfo_reqheight(), **kwargs)

        padding = self.master.cget("border_width") + self.master.cget("corner_radius")

        self.grid(row=0, column=0, sticky="nsw", padx=(padding, 0), pady=padding-1)

        self.master._textbox.grid_configure(padx=(padx, 0))
        self.master._textbox.lift()
        self.master._textbox.configure(yscrollcommand=self.set_scrollbar)
        self.master._textbox.bind("<<ContentChanged>>", lambda e: self.after(20, self.redraw), add=True)
        self.master.bind("<Key>", lambda e: self.after(20, self.redraw), add=True)

    def set_scrollbar(self, x, y):
        self.redraw(x, y)
        self.master._y_scrollbar.set(x, y)

    def set_padx(self, padx=30):
        if self.auto_padx:
            padx = padx * (int(self.master.cget("font").cget("size")) / 10)
        self.master._textbox.grid_configure(padx=(padx, 0))

    def _set_appearance_mode(self, mode_string):
        self.colors = (self.master._apply_appearance_mode(self.text_color),
                       self.master._apply_appearance_mode(self.fg_color))
        self.set_colors()
