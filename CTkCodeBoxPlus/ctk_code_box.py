"""
CTkCodeBox
Original Author (CTkCodeBox): Akash Bora (Akascape) | https://github.com/Akascape
Author (CTkCodeBoxPlus): xzyqox (KiTant) | https://github.com/KiTant
License: MIT
"""

import customtkinter
from .text_menu import TextMenu
from .add_line_nums import AddLineNums
from pygments import lex, lexer
from pygments.styles import get_style_by_name, get_all_styles
from .constants import common_langs
from .custom_exception_classes import *
from .dataclasses import *
from .keybinding import _register_keybind
from typing import Union
import pyperclip


class CTkCodeBox(customtkinter.CTkTextbox):
    """A code-oriented CTk textbox with syntax highlighting and UX helpers.

    CTkCodeBox wraps a CTkTextbox to provide:
    - Pygments-based syntax highlighting with theme support
    - Optional line numbers, smarter selection, and current-line highlight
    - Indentation helpers (Tab/Shift+Tab, auto-indent on Return)
    - Simple history (Undo/Redo) with typing cooldown
    - Platform-aware keybindings (Cmd on macOS, Ctrl elsewhere)

    Emits:
        <<ContentChanged>> on both the inner textbox and the wrapper whenever
        content changes via the provided APIs.
    """
    def __init__(self,
                 master: Union[customtkinter.CTkBaseClass, customtkinter.CTk, customtkinter.CTkToplevel],
                 language: Union[str, lexer.Lexer],
                 height: int = 200,
                 theme: str = "solarized-light",
                 numbering_settings: NumberingSettings = NumberingSettings(),
                 menu_settings: MenuSettings = MenuSettings(),
                 wrap: bool = True,
                 select_color: str = None,
                 cursor_color: str = None,
                 highlight_current_line: bool = True,
                 highlight_current_line_color: str = None,
                 history_settings: HistorySettings = HistorySettings(),
                 indent_width: int = 4,
                 **kwargs):
        """Initialize a CTkCodeBox instance.

        Args:
            master: Parent widget.
            language: Pygments language name (str) or a lexer class.
            height: Widget height in pixels (passed to CTkTextbox).
            theme: Pygments style name used for highlighting.
            numbering_settings: NumberingSettings object for the line nums.
            menu_settings: MenuSettings object for the context menu.
            wrap: Enable word wrap.
            select_color: Override selection background color.
            cursor_color: Cursor color I (blinking).
            highlight_current_line: Highlight the active line.
            highlight_current_line_color: Explicit color for active line.
            history_settings: HistorySettings object for custom history.
            indent_width: Number of spaces for indent/outdent.
            **kwargs: Additional arguments passed to CTkTextbox.
        """
        # Do not enable Tk's built-in undo/history
        if 'undo' in kwargs and history_settings.enabled:
            try:
                del kwargs['undo']
            except Exception:
                kwargs.pop('undo', None)
        super().__init__(master, height=height, **kwargs)

        # Wrap management
        self.wrap_enabled = bool(wrap)
        self.set_wrap(self.wrap_enabled)
        if numbering_settings.enabled:
            self.line_nums = AddLineNums(self, text_color=numbering_settings.color,
                                         justify=numbering_settings.justify,
                                         padx=numbering_settings.padx,
                                         auto_padx=numbering_settings.auto_padx)

        self.select_color = select_color
        if select_color:
            self._textbox.config(selectbackground=self.select_color)
        else:
            self._apply_selection_colors()
        self.cursor_color = cursor_color

        if self.cursor_color:
            self._textbox.config(insertbackground=self.cursor_color)

        self.bind('<KeyRelease>', self.update_code)  # When a key is released, update the code
        self.bind('<<ContentChanged>>', self.update_code)
        # Use keybindings for common editing actions (widget scope)
        _register_keybind(self, "CmdOrCtrl+A", lambda: self.select_all_text(), bind_scope='widget')
        _register_keybind(self, "CmdOrCtrl+X", lambda: self.cut_text(), bind_scope='widget')
        _register_keybind(self, "CmdOrCtrl+C", lambda: self.copy_text(), bind_scope='widget')
        _register_keybind(self, "CmdOrCtrl+V", lambda: self.paste_text(), bind_scope='widget')
        _register_keybind(self, "CmdOrCtrl+Shift+Z", lambda: self.redo(), bind_scope='widget')
        _register_keybind(self, "CmdOrCtrl+Z", lambda: self.undo(), bind_scope='widget')

        # Custom history (undo/redo)
        self._undo_stack = []
        self._redo_stack = []
        self._history_typing_cooldown = None
        self.history_settings = history_settings

        # Job id for debounced highlighting
        self._highlight_job = None

        # Current line highlighting settings
        self._highlight_current_line = bool(highlight_current_line)
        self._current_line_color = highlight_current_line_color
        self.tag_config("current_line", background=self._get_current_line_color())
        # Ensure current_line is always below selection and other tags
        try:
            self.tag_lower("current_line")
        except Exception:
            pass

        # Update current-line highlight on common events
        self.bind('<KeyRelease>', lambda e: self._update_current_line(), add=True)
        self.bind('<ButtonRelease-1>', lambda e: self._update_current_line(), add=True)
        self.bind('<<Selection>>', lambda e: self._update_current_line(), add=True)
        self.bind('<FocusIn>', lambda e: self._update_current_line(), add=True)
        # Re-apply selection colors on focus (helps when theme changes)
        self.bind('<FocusIn>', lambda e: self._apply_selection_colors(), add=True)

        # Indentation settings and keybindings
        self.indent_width = int(indent_width)
        # Register layout/platform-independent editing keys
        _register_keybind(self, 'TAB', lambda: self._on_tab(), bind_scope='widget')
        # Use Shift-Tab for outdent;
        _register_keybind(self, 'Shift+TAB', lambda: self._on_shift_tab(), bind_scope='widget')
        _register_keybind(self, 'RETURN', lambda: self._on_return(), bind_scope='widget')

        self.theme_name = theme
        self.all_themes = list(get_all_styles())

        self.language = language
        self.check_lexer()
        self.configure_tags()
        self.edited = False
        # Capture initial state for history
        self._history_push_current()
        # Capture history for general typing
        self.bind("<KeyPress>", self._on_keypress_history, add=True)
        self.bind("<Shift-KeyPress>", self._on_keypress_history, add=True)
        # Quote wrapping on selection
        self.bind("<KeyPress-'>", self._on_quote_single, add=True)
        self.bind('<KeyPress-">', self._on_quote_double, add=True)
        self.bind("<KeyPress-grave>", self._on_backtick, add=True)          # `
        # Bracket/angle wrapping on selection
        self.bind("<KeyPress-parenleft>", self._on_parenleft, add=True)      # (
        self.bind("<KeyPress-bracketleft>", self._on_bracketleft, add=True)  # [
        self.bind("<KeyPress-braceleft>", self._on_braceleft, add=True)      # {
        self.bind("<KeyPress-less>", self._on_less, add=True)                # <
        # Pair backspace handler
        self.bind("<KeyPress-BackSpace>", self._on_backspace, add=True)

        # Smarter selection on double-click and triple-click
        self.bind("<Double-Button-1>", self._on_double_click, add=True)
        self.bind("<Triple-Button-1>", self._on_triple_click, add=True)

        if menu_settings.enabled:
            self.text_menu = TextMenu(self, fg_color=menu_settings.fg_color, text_color=menu_settings.text_color, hover_color=menu_settings.hover_color)

    def check_lexer(self):
        """Resolve and set the lexer.

        If `language` is a string, pick a lexer from common languages.
        otherwise treat `language` as a Pygments lexer class.

        Raises:
            LanguageNotAvailableError: When string language is unknown.
        """
        if type(self.language) is str:
            if self.language.lower() in common_langs:
                self.lexer = common_langs[self.language.lower()]
            else:
                raise LanguageNotAvailableError("This language is not available, try to pass the pygments lexer instead. \nAvailable lexers: https://pygments.org/docs/lexers")
        else:
            self.lexer = self.language

    def configure_tags(self):
        """Configure all syntax tags for the current Pygments theme.

        Raises:
            ThemeNotAvailableError: If the requested theme is not installed.
        """
        if self.theme_name not in self.all_themes:
            raise ThemeNotAvailableError(f"Invalid theme name: {self.theme_name}, \nAvailable themes: {self.all_themes}")
        style = get_style_by_name(self.theme_name)
        for token, values in style:
            foreground = values['color']
            if foreground:
                self.tag_config(str(token), foreground=f'#{foreground}')

    def update_code(self, event=None, edited=True):
        """Schedule a debounced re-highlight and update edited flag."""
        self._schedule_highlight()
        if edited:
            self.edited = True

    def _schedule_highlight(self, delay: int = 100):
        """Debounce highlighting to improve performance while typing."""
        if getattr(self, "_highlight_job", None):
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(delay, self._apply_highlight)

    def _apply_highlight(self):
        """Apply syntax highlighting to the current content."""
        code = self.get('0.0', 'end-1c')
        self.clear_code()
        self.highlight_code(code)
        self._highlight_job = None
        # Refresh current line highlight after re-tagging
        self._update_current_line()

    def clear_code(self):
        """Remove all highlighting tags while preserving selection."""
        for tag in self.tag_names():
            # Preserve current selection while re-highlighting
            if tag == "sel":
                continue
            self.tag_remove(tag, '0.0', 'end')

    def _select_all(self):
        """Select the entire buffer content."""
        self.tag_add("sel", "1.0", "end-1c")

    def insert(self, index, chars, push_history=True, *tags):
        """Insert text and trigger a non-editing highlight update.

        Mirrors tkinter.Text.insert signature to maintain API parity.
        """
        if push_history:
            self._history_push_current()
        super().insert(index, chars, *tags)
        self.update_code(edited=False)
        self.edited = False

    def highlight_code(self, code):
        """Tokenize code with Pygments and apply tags.

        Raises:
            LexerError: If the provided lexer fails to tokenize the input.
        """
        try:
            tokens = list(lex(code, self.lexer()))
        except Exception as e:
            raise LexerError("Not a valid lexer. Available lexers: https://pygments.org/docs/lexers") from e
        start_line = 1
        start_index = 0
        for token in tokens:
            end_line, end_index = self.index(f'{start_line}.{start_index}+{len(token[1])} chars').split('.')
            self.tag_add(str(token[0]), f'{start_line}.{start_index}', f'{end_line}.{end_index}')
            start_line = end_line
            start_index = end_index

    def _configure_type_check(self, arg, needType, argName):
        def _check(needT, isList=False):
            matching = False
            if isinstance(arg, needT):
                matching = True
            else:
                if not isList:
                    raise ConfigureBadType(f'Type of provided arg "{argName}" should be {needT}, not {type(arg)}')
            return matching
        if isinstance(needType, list):
            anyMatch = False
            for t in needType:
                anyMatch = _check(t, True)
                if anyMatch:
                    break
            if not anyMatch:
                raise ConfigureBadType(f'Type of provided arg "{argName}" should be one of next: {needType}, not {type(arg)}')
            return anyMatch
        else:
            return _check(needType)

    def configure(self, param=None, **kwargs):  # param here ONLY for tklinenums module
        """Extended configure with CTkCodeBox options.
        Re-highlights when theme or language changes.
        Remaining options are passed to the base widget.
        Args:
            **kwargs: Configuration parameters
                    (Supports additional keyword options: theme, language, wrap_enabled, history_enabled,
                    select_color, cursor_color, history_max, history_cooldown, highlight_current_line,
                    current_line_color, history_settings, numbering_padx, numbering_auto_padx, indent_width)
        Raises:
            ConfigureBadType: If a type of provided kwargs not the right one
        """
        one_action_handlers = {
            "history_enabled": [self.set_history_enabled, bool],
            "history_max": [self.set_history_limit, int],
            "history_cooldown": [lambda val: setattr(self.history_settings, "cooldown", val), int],
            "history_settings": [lambda val: setattr(self, "history_settings", val), HistorySettings],
            "numbering_padx": [lambda val: self.line_nums.set_padx(val), int],
            "numbering_auto_padx": [lambda val: setattr(self.line_nums, "auto_padx", val), bool],
            "indent_width": [lambda val: setattr(self, "indent_width", val), int],
            "wrap_enabled": [self.set_wrap, bool]
        }
        for param, value in list(kwargs.items()):
            if (param in one_action_handlers and
                    self._configure_type_check(value, one_action_handlers[param][1], param)):
                one_action_handlers[param][0](value)
                kwargs.pop(param)
        if "theme" in kwargs and self._configure_type_check(kwargs["theme"], str, "theme"):
            self.theme_name = kwargs.pop("theme")
            self.configure_tags()
        if "language" in kwargs and self._configure_type_check(kwargs["language"], [str, lexer.Lexer], "language"):
            self.language = kwargs.pop("language")
            self.check_lexer()
        if "select_color" in kwargs and self._configure_type_check(kwargs["select_color"], str, "select_color"):
            self.select_color = kwargs.pop("select_color")
            self._textbox.config(selectbackground=self.select_color)
        else:
            # Keep default selection color updated if user hasn't provided one
            self._apply_selection_colors()
        if "cursor_color" in kwargs and self._configure_type_check(kwargs["cursor_color"], str, "cursor_color"):
            self.cursor_color = kwargs.pop("cursor_color")
            self._textbox.config(insertbackground=self.cursor_color)
        if (("highlight_current_line" in kwargs and self._configure_type_check(kwargs["highlight_current_line"], bool, "highlight_current_line"))
                or ("current_line_color" in kwargs and self._configure_type_check(kwargs["current_line_color"], str, "current_line_color"))
                or ("highlight_current_line_color" in kwargs and self._configure_type_check(kwargs["highlight_current_line_color"], str, "highlight_current_line_color"))):
            self._highlight_current_line = kwargs.pop("highlight_current_line", self._highlight_current_line)
            self._current_line_color = kwargs.pop("current_line_color", kwargs.pop("highlight_current_line_color", self._current_line_color))
            self.tag_config("current_line", background=self._get_current_line_color())

        # Re-apply highlighting if theme or language changed
        self._schedule_highlight(0)
        if kwargs:
            super().configure(**kwargs)

    def cget(self, param):
        """Get configuration parameter value with support for custom parameters.
        Args:
            param: Parameter name to retrieve
        Returns:
            Parameter value
        """
        custom_params = {
            "theme": lambda: self.theme_name,
            "wrap_enabled": lambda: self.wrap_enabled,
            "edited": self.is_edited,
            "undo_stack": lambda: self._undo_stack,
            "redo_stack": lambda: self._redo_stack,
            "history_cd_active": lambda: True if self._history_typing_cooldown else False,
            "all_themes": lambda: self.all_themes,
            "common_langs": lambda: common_langs,
            "text_menu": lambda: self.text_menu,
            "line_nums": lambda: self.line_nums,
            "history_enabled": lambda: self.history_settings.enabled,
            "history_max": lambda: self.history_settings.max,
            "history_cooldown": lambda: self.history_settings.cooldown,
            "history_settings": lambda: self.history_settings,
            "numbering_auto_padx": lambda: self.line_nums.auto_padx,
            "language": lambda: self.language,
            "select_color": lambda: self.select_color,
            "cursor_color": lambda: self.cursor_color,
            "highlight_current_line": lambda: self._highlight_current_line,
            "current_line_color": lambda: self._current_line_color,
            "highlight_current_line_color": lambda: self._current_line_color,
        }
        if param in custom_params:
            return custom_params[param]()
        return super().cget(param)

    # General helpers
    def set_wrap(self, enabled: bool):
        """Enable/disable word wrap."""
        self.wrap_enabled = bool(enabled)
        super().configure(wrap=("word" if self.wrap_enabled else "none"))

    def toggle_wrap(self):
        """Toggle wrap mode."""
        self.set_wrap(not self.wrap_enabled)

    def is_edited(self) -> bool:
        """Return True if the text has been edited since last reset."""
        return bool(self.edited)

    def reset_edited(self):
        """Reset edited state flag to False."""
        self.edited = False

    # Current line highlight
    def _get_current_line_color(self) -> str:
        """Compute the current-line background color based on theme/override."""
        if not self._highlight_current_line:
            return ""
        if self._current_line_color:
            return self._current_line_color
        # Derive a subtle line color from widget background
        try:
            bg = self._apply_appearance_mode(self.cget("fg_color"))
            if isinstance(bg, tuple):
                bg = bg[0]
            if isinstance(bg, str) and bg.startswith('#') and len(bg) == 7:
                r = int(bg[1:3], 16)
                g = int(bg[3:5], 16)
                b = int(bg[5:7], 16)
                # Lighten subtly by ~5% for a less bright current-line highlight
                lr = min(255, int(r + (255 - r) * 0.05))
                lg = min(255, int(g + (255 - g) * 0.05))
                lb = min(255, int(b + (255 - b) * 0.05))
                return f"#{lr:02x}{lg:02x}{lb:02x}"
        except Exception:
            pass
        return "#e6e6e6"  # Fallback light gray

    def _update_current_line(self):
        """Refresh the current-line highlight tag around the insert cursor."""
        if not self._highlight_current_line:
            return
        try:
            self.tag_remove("current_line", "1.0", "end")
            insert_index = self.index("insert")
            line_start = f"{insert_index.split('.')[0]}.0"
            line_end = f"{insert_index.split('.')[0]}.0 lineend"
            self.tag_add("current_line", line_start, line_end)
            # Ensure color is up-to-date if theme changes
            self.tag_config("current_line", background=self._get_current_line_color())
            # Place current_line under other tags and do not cover selected text
            try:
                self.tag_lower("current_line")
            except Exception:
                pass
            try:
                if self.tag_ranges("sel"):
                    self.tag_remove("current_line", "sel.first", "sel.last")
            except Exception:
                pass
        except Exception:
            pass

    # Indentation and auto-indent
    def _on_tab(self, event=None):
        """Indent selection or insert spaces at the caret.
        Returns:
             "break" to stop default Tab behavior.
        """
        try:
            self._history_push_current()
            if self.tag_ranges("sel"):
                # Indent selected lines
                start_line = int(self.index("sel.first").split(".")[0])
                end_line = int(self.index("sel.last").split(".")[0])
                spaces = " " * self.indent_width
                for line in range(start_line, end_line + 1):
                    self.insert(f"{line}.0", spaces)
                self._notify_content_changed()
            else:
                self.insert("insert", " " * self.indent_width)
                self._notify_content_changed()
        except Exception:
            pass
        return "break"

    # Selection highlight colors
    def _apply_selection_colors(self):
        """Apply a darker, high-contrast selection color by default.
        If user provided select_color, this is a no-op.
        """
        try:
            if self.select_color:
                return
            bg = self._apply_appearance_mode(self.cget("fg_color"))
            if isinstance(bg, tuple):
                bg = bg[0]
            sel_bg = None
            sel_fg = None
            # Compute simple luminance to decide contrast
            def _hex_to_rgb(h):
                return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
            if isinstance(bg, str) and bg.startswith('#') and len(bg) == 7:
                r, g, b = _hex_to_rgb(bg)
                # Relative luminance approximation
                luminance = (0.2126 * (r/255.0)) + (0.7152 * (g/255.0)) + (0.0722 * (b/255.0))
                if luminance > 0.6:
                    # Light theme: light blue selection for readability
                    sel_bg = '#9bbcf7'
                    sel_fg = '#000000'
                else:
                    # Dark theme: medium blue selection with light text
                    sel_bg = '#1f3370'
                    sel_fg = '#ffffff'
            # Apply
            if sel_bg:
                try:
                    self._textbox.config(selectbackground=sel_bg)
                except Exception:
                    pass
                try:
                    self._textbox.config(selectforeground=sel_fg)
                except Exception:
                    pass
                try:
                    # Keep inactive selection visible but unobtrusive
                    self._textbox.config(inactiveselectbackground=sel_bg)
                except Exception:
                    pass
        except Exception:
            pass

    def _on_shift_tab(self, event=None):
        """Outdent selection or current line by one indent width.
        Returns:
            "break" to stop default Shift+Tab behavior.
        """
        try:
            self._history_push_current()
            if self.tag_ranges("sel"):
                start_line = int(self.index("sel.first").split(".")[0])
                end_line = int(self.index("sel.last").split(".")[0])
                for line in range(start_line, end_line + 1):
                    self._outdent_line(line)
                self._notify_content_changed()
            else:
                line = int(self.index("insert").split(".")[0])
                self._outdent_line(line)
                self._notify_content_changed()
        except Exception:
            pass
        return "break"

    def _outdent_line(self, line:int):
        """Remove up to indent_width leading spaces (or a single tab) from a line."""
        try:
            # Remove up to indent_width spaces (or a single tab) from line start
            start = f"{line}.0"
            first_chars = self.get(start, f"{line}.0+{self.indent_width}c")
            remove = 0
            if first_chars.startswith("\t"):
                remove = 1
            else:
                for ch in first_chars:
                    if ch == ' ' and remove < self.indent_width:
                        remove += 1
                    else:
                        break
            if remove > 0:
                self.delete(start, f"{line}.0+{remove}c")
        except Exception:
            pass

    def _on_return(self, event=None):
        """Insert newline and preserve leading whitespace for auto-indent.
        Returns:
            "break" to stop default return behavior.
        """
        try:
            # Auto-indent: copy leading whitespace from current line
            self._history_push_current()
            line_start = self.index("insert linestart")
            before_cursor = self.get(line_start, self.index("insert"))
            leading_ws = ''
            for ch in before_cursor:
                if ch in (' ', '\t'):
                    leading_ws += ch
                else:
                    break
            self.insert("insert", "\n" + leading_ws)
            self._notify_content_changed()
        except Exception:
            pass
        return "break"

    # Public API helpers
    def _notify_content_changed(self):
        """Notify that content changed (wrapper and inner textbox emit <<ContentChanged>>)."""
        try:
            try:
                self._textbox.event_generate("<<ContentChanged>>")
            except Exception:
                pass
            self.event_generate("<<ContentChanged>>")
        except Exception:
            pass

    def cut_text(self):
        """Cut selected text to clipboard and notify change.
        Returns:
            "Not found selected" when nothing is selected.
            "Success" when success
            Exception if something goes wrong
        """
        try:
            if not self.tag_ranges("sel"):
                return "Not found selected"
            self._history_push_current()
            text = self.get("sel.first", "sel.last")
            pyperclip.copy(text)
            self.delete("sel.first", "sel.last")
            self._notify_content_changed()
            return "Success"
        except Exception:
            return Exception

    def copy_text(self):
        """Copy selected text to clipboard.
        Returns:
            "Not found selected" when nothing is selected.
            "Success" when success
            Exception if something goes wrong
        """
        try:
            if not self.tag_ranges("sel"):
                return "Not found selected"
            text = self.get("sel.first", "sel.last")
            pyperclip.copy(text)
            return "Success"
        except Exception:
            return Exception

    def paste_text(self):
        """Paste clipboard text, replacing selection if present, and refresh highlighting/lines.
        Returns:
            "Clipboard empty" when clipboard is empty.
            "Success" when success
            Exception if something goes wrong
        """
        try:
            text = pyperclip.paste()
        except Exception:
            text = ""
        try:
            if not text:
                return "Clipboard empty"
            self._history_push_current()
            if self.tag_ranges("sel"):
                # Replace selection
                self.delete("sel.first", "sel.last")
            # Insert at cursor
            self.insert(self.index('insert'), text)
            self._notify_content_changed()
            # Ensure quick re-highlight for multi-line pastes
            self._schedule_highlight(0)
            return "Success"
        except Exception:
            return Exception

    def clear_all_text(self):
        """Delete all content and notify change.
        Returns:
            "Success" when success
            Exception if something goes wrong
        """
        try:
            self._history_push_current()
            self.delete("1.0", "end")
            self._notify_content_changed()
            return "Success"
        except Exception:
            return Exception

    def select_all_text(self):
        """Select all content.
        Returns:
            "Success" when success
            Exception if something goes wrong
        """
        try:
            self.tag_add("sel", "1.0", "end-1c")
            return "Success"
        except Exception:
            return Exception

    # History API
    def set_history_enabled(self, enabled: bool):
        """Enable/disable the internal undo/redo history."""
        self.history_settings.enabled = bool(enabled)

    def set_history_limit(self, limit: int):
        """Set maximum number of undo frames to keep.
        Returns:
            "Success" when success
            Exception if something goes wrong
        """
        try:
            self.history_settings.max = max(0, int(limit))
            # Trim if needed
            if self.history_settings.max and len(self._undo_stack) > self.history_settings.max:
                self._undo_stack = self._undo_stack[-self.history_settings.max:]
            return "Success"
        except Exception:
            return Exception

    def clear_history(self):
        """Clear undo and redo stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    def undo(self):
        """Undo the last change if history is enabled.
        Returns:
            "Nothing to undo" when undo stack is empty or history is disabled.
            "Success" when success
            Exception if something goes wrong
        """
        if not self.history_settings.enabled or not self._undo_stack:
            return "Nothing to undo"
        try:
            current = self._save_state()
            state = self._undo_stack.pop()
            self._redo_stack.append(current)
            self._restore_state(state)
            self._notify_content_changed()
            return "Success"
        except Exception:
            return Exception

    def redo(self):
        """Redo the last undone change if available.
        Returns:
            "Nothing to redo" when redo stack is empty or history is disabled.
            "Success" when success
            Exception if something goes wrong
        """
        if not self.history_settings.enabled or not self._redo_stack:
            return "Nothing to redo"
        try:
            current = self._save_state()
            state = self._redo_stack.pop()
            self._undo_stack.append(current)
            self._restore_state(state)
            self._notify_content_changed()
            return "Success"
        except Exception:
            return Exception

    # Internal history helpers
    def _save_state(self):
        """Capture current text, cursor index, and selection as a history state."""
        try:
            text = self.get('1.0', 'end-1c')
        except Exception:
            text = ''
        insert_index = self.index('insert')
        sel = None
        try:
            if self.tag_ranges('sel'):
                sel = (self.index('sel.first'), self.index('sel.last'))
        except Exception:
            sel = None
        return {
            'text': text,
            'insert': insert_index,
            'sel': sel,
        }

    def _restore_state(self, state):
        """Restore text, cursor, and selection from a history state and re-highlight."""
        try:
            self.delete('1.0', 'end')
            if state.get('text'):
                super().insert('1.0', state['text'])
            # Restore insert position
            try:
                self.mark_set('insert', state.get('insert', '1.0'))
            except Exception:
                pass
            # Restore selection
            self.tag_remove('sel', '1.0', 'end')
            if state.get('sel'):
                try:
                    self.tag_add('sel', state['sel'][0], state['sel'][1])
                except Exception:
                    pass
            # Refresh highlight
            self._schedule_highlight(0)
        except Exception:
            pass

    def _history_push_current(self):
        """Push a snapshot of the current buffer state onto the undo stack."""
        if not self.history_settings.enabled:
            return
        try:
            state = self._save_state()
            self._undo_stack.append(state)
            # Limit size
            if self.history_settings.max and len(self._undo_stack) > self.history_settings.max:
                self._undo_stack = self._undo_stack[-self.history_settings.max:]
            # Clear redo on new action
            self._redo_stack.clear()
        except Exception:
            pass

    def _on_keypress_history(self, event):
        """Typing into undo frames and snapshot when replacing selection."""
        if not self.history_settings.enabled:
            return
        try:
            ks = getattr(event, 'keysym', '')
            # Ignore non-editing keys and ones we already handle
            if ks in ("Shift_L","Shift_R","Control_L","Control_R","Alt_L","Alt_R","Meta_L","Meta_R",
                      "Caps_Lock","Num_Lock","Scroll_Lock","Escape","F1","F2","F3","F4","F5","F6",
                      "F7","F8","F9","F10","F11","F12","Left","Right","Up","Down","Home","End",
                      "Next"):
                return
            is_content_key = bool(getattr(event, 'char', '')) or ks in ("BackSpace","Delete","Return","Tab")
            if not is_content_key:
                return
            if self._history_typing_cooldown is None:
                self._history_push_current()
                self._history_typing_cooldown = self.after(self.history_settings.cooldown, self._reset_history_cooldown)
        except Exception:
            pass

    # Chars wrapping
    def _on_quote_single(self, event=None):
        """Wrap selection with single quotes or insert paired quotes."""
        return self._handle_chars_wrap("'")

    def _on_quote_double(self, event=None):
        """Wrap selection with double quotes or insert paired quotes."""
        return self._handle_chars_wrap('"')

    def _on_parenleft(self, event=None):
        """Wrap selection with parentheses or insert ()."""
        return self._handle_chars_wrap('()')

    def _on_bracketleft(self, event=None):
        """Wrap selection with brackets or insert []."""
        return self._handle_chars_wrap('[]')

    def _on_braceleft(self, event=None):
        """Wrap selection with braces or insert {}."""
        return self._handle_chars_wrap('{}')

    def _on_less(self, event=None):
        """Wrap selection with angle brackets or insert <>."""
        return self._handle_chars_wrap('<>')

    def _on_backtick(self, event=None):
        """Wrap selection with backticks or insert paired backticks."""
        return self._handle_chars_wrap('`')

    def _handle_chars_wrap(self, chars: str):
        """Handle wrapping/insertion behavior for paired characters.

        If text is selected, wraps it with the given pair. Otherwise inserts a
        paired sequence and places the caret between them.
        """
        try:
            # Determine pair
            if len(chars) == 1:
                open_ch = chars[0]
                close_ch = chars[0]
            else:
                open_ch = chars[0]
                close_ch = chars[1]

            if self.tag_ranges("sel"):
                self._history_push_current()
                start = self.index("sel.first")
                end = self.index("sel.last")
                # Insert right first to preserve start index
                self.insert(end, close_ch)
                self.insert(start, open_ch)
                # Keep original inner selection
                try:
                    new_start = self.index(f"{start} +1c")
                    new_end = self.index(f"{end} +1c")
                    self.tag_remove("sel", "1.0", "end")
                    self.tag_add("sel", new_start, new_end)
                except Exception:
                    pass
                self._notify_content_changed()
                return "break"
            else:
                # Auto add pair when no selection, unless adjacent char already closes
                try:
                    next_ch = self.get("insert", "insert +1c")
                except Exception:
                    next_ch = ""
                try:
                    prev_ch = self.get("insert -1c", "insert")
                except Exception:
                    prev_ch = ""
                if next_ch == close_ch:
                    return None
                if open_ch == close_ch and prev_ch == open_ch:
                    return None

                # Perform auto-pair insertion
                self._history_push_current()
                self.insert("insert", open_ch + close_ch)
                # Move cursor between the pair
                try:
                    self.mark_set("insert", "insert -1c")
                except Exception:
                    pass
                self._notify_content_changed()
                return "break"
        except Exception:
            pass
        return None

    def _on_backspace(self, event=None):
        """Smart-backspace: delete paired quotes/brackets if cursor is between them.
        Returns:
            "break" to stop default backspace behavior.
        """
        self._history_push_current()
        self._notify_content_changed()
        try:
            # If there is a selection, let default backspace handle it (history is handled elsewhere)
            if self.tag_ranges('sel'):
                return None
            # Check if we're between a pair: (), [], {}, <>, '' , "", ``
            prev_ch = self.get("insert -1c", "insert") if self.compare("insert", '>', '1.0') else ''
            next_ch = self.get("insert", "insert +1c")
            pairs = {('(', ')'), ('[', ']'), ('{', '}'), ('<', '>')}
            if prev_ch and next_ch:
                if (prev_ch, next_ch) in pairs or (prev_ch == next_ch and prev_ch in ('"', "'", '`')):
                    self.delete("insert -1c", "insert +1c")
                    return "break"
        except Exception:
            pass
        return None

    # Double-click smart selection (token expansion only)
    def _on_double_click(self, event):
        """Expand selection to a token at clicked index (word/space/special).
        Returns:
            "break" to stop default double click behavior.
        """
        try:
            idx = self.index(f"@{event.x},{event.y}")
            # Token selection
            start, end = self._expand_token_at_index(idx)
            if start and end and self.compare(start, '<', end):
                self.tag_remove('sel', '1.0', 'end')
                self.tag_add('sel', start, end)
                return "break"
        except Exception:
            pass
        return None

    def _on_triple_click(self, event):
        """Select the entire clicked line.
        Returns:
            "break" to stop default triple click behavior.
        """
        try:
            line_start = self.index(f"@{event.x},{event.y} linestart")
            line_end = self.index(f"@{event.x},{event.y} lineend")
            self.tag_remove('sel', '1.0', 'end')
            self.tag_add('sel', line_start, line_end)
            return "break"
        except Exception:
            return None

    def _expand_token_at_index(self, idx):
        """Return token span around index based on simple character classes.

        Returns:
            A tuple (start_index, end_index) or (None, None) when no token
            can be expanded at the given index.
        """
        try:
            ch = self.get(idx, self.index(f"{idx} +1c"))
            if ch == "\n":
                return None, None
            # Classify function
            def cls(c):
                if c == "\n":
                    return 'nl'
                if c.isspace():
                    return 'space'
                if c.isalnum() or c == '_':
                    return 'word'
                return 'special'
            cur_class = cls(ch)
            # Do not expand special characters: select only this char
            if cur_class == 'special':
                return self.index(idx), self.index(f"{idx} +1c")
            # Expand left
            left = self.index(idx)
            while True:
                prev = self.index(f"{left} -1c")
                if self.compare(prev, '<', '1.0'):
                    break
                c = self.get(prev, left)
                if cls(c) != cur_class:
                    break
                left = prev
            # Expand right
            right = self.index(idx)
            doc_end = self.index('end-1c')
            while True:
                nxt = self.index(f"{right} +1c")
                if self.compare(nxt, '>', doc_end):
                    break
                c = self.get(right, nxt)
                if cls(c) != cur_class:
                    break
                right = nxt
            return left, right
        except Exception:
            return None, None

    def _reset_history_cooldown(self):
        """Reset the typing timer for history snapshots."""
        self._history_typing_cooldown = None
