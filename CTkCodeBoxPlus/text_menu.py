import customtkinter
import tkinter
import sys


class TextMenu(tkinter.Menu):
    """Popup text menu for CTkCodeBox.

    Provides a context (right-click) menu for a CTkCodeBox widget with
    common edit actions: Copy, Paste, Cut, Select All and, when history is
    enabled, Undo/Redo. Menu item availability is updated just before the menu
    is shown. Accelerator labels adapt to the platform (Cmd on macOS, Ctrl
    elsewhere).

    Notes:
        Original author: Akash Bora (Akascape) — https://github.com/Akascape
        Modified by: xzyqox (KiTant) — https://github.com/KiTant
    """
    def __init__(self,
                 widget,
                 fg_color=None,
                 text_color=None,
                 hover_color=None,
                 **kwargs):
        """Initialize a TextMenu instance.

        Args:
            widget: The CTkCodeBox widget instance this menu controls.
            fg_color: Menu background color. Defaults to the current theme.
            text_color: Menu text color. Defaults to the current theme.
            hover_color: Active item background color. Defaults to the current theme.
            **kwargs: Additional arguments passed to tkinter.Menu.
        """

        super().__init__(tearoff=False, title="menu", borderwidth=0, bd=0, relief="flat", **kwargs)
        
        self.fg_color = customtkinter.ThemeManager.theme["CTkFrame"]["top_fg_color"] if fg_color is None else fg_color
        self.text_color = customtkinter.ThemeManager.theme["CTkLabel"]["text_color"] if text_color is None else text_color
        self.hover_color = customtkinter.ThemeManager.theme["CTkButton"]["hover_color"] if hover_color is None else hover_color
        
        self.widget = widget
        
        # Platform-aware accelerator labels (Cmd on macOS, Ctrl elsewhere)
        def accel_label(s: str) -> str:
            return s.replace("Ctrl", "Cmd") if sys.platform == "darwin" else s

        self.add_command(label="Copy", command=self.widget.copy_text, accelerator=accel_label("Ctrl+C"))
        self.add_command(label="Paste", command=self.widget.paste_text, accelerator=accel_label("Ctrl+V"))
        self.add_command(label="Cut", command=self.widget.cut_text, accelerator=accel_label("Ctrl+X"))
        self.add_command(label="Select All", command=self.widget.select_all_text, accelerator=accel_label("Ctrl+A"))
        if self.widget.cget("history_enabled"):
            self.add_separator()
            self.add_command(label="Undo", command=self.widget.undo, accelerator=accel_label("Ctrl+Z"))
            self.add_command(label="Redo", command=self.widget.redo, accelerator=accel_label("Ctrl+Shift+Z"))

        self.widget.bind("<Button-3>", lambda event: self.do_popup(event))
        self.widget.bind("<Button-2>", lambda event: self.do_popup(event))
        
    def do_popup(self, event):
        """Show the popup menu at the event location.

        Args:
            event: The mouse event whose screen coordinates are used to position
                the menu.

        This updates menu item states and applies appearance-mode colors before
        showing the menu.
        """
        
        super().config(bg=self.widget._apply_appearance_mode(self.fg_color),
                       fg=self.widget._apply_appearance_mode(self.text_color),
                       activebackground=self.widget._apply_appearance_mode(self.hover_color))
        # Update state of menu entries before showing
        self._update_states()
        self.tk_popup(event.x_root, event.y_root) 
                
    def _update_states(self):
        """Update enabled/disabled state of menu items based on widget/clipboard state.

        Considers current selection, presence of text content, clipboard text
        availability, and undo/redo history (when available).
        """
        # Selection present?
        try:
            has_selection = bool(self.widget.tag_ranges("sel"))
        except tkinter.TclError:
            has_selection = False
        # Any text content?
        try:
            has_text = self.widget.compare("end-1c", "!=", "1.0")
        except tkinter.TclError:
            has_text = False
        # Clipboard text?
        try:
            clip = self.clipboard_get()
            has_clip = isinstance(clip, str) and len(clip) > 0
        except tkinter.TclError:
            has_clip = False
        # Undo history?
        try:
            has_undo = len(self.widget._undo_stack) > 0
        except tkinter.TclError:
            has_undo = False
        # Redo history?
        try:
            has_redo = len(self.widget._redo_stack) > 0
        except tkinter.TclError:
            has_redo = False

        # Apply states
        def set_state(label, enabled):
            try:
                self.entryconfig(label, state=("normal" if enabled else "disabled"))
            except Exception:
                pass

        set_state("Cut", has_selection)
        set_state("Copy", has_selection)
        set_state("Paste", has_clip)
        set_state("Select All", has_text)
        set_state("Undo", has_undo)
        set_state("Redo", has_redo)
