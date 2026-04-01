from dataclasses import dataclass, asdict, field
from typing import Optional


@dataclass(frozen=True)
class SearchWindowSettings:
    enabled: bool = True
    title: str = "Search & Replace"
    width: int = 400
    height: int = 250
    display_text_translation: dict = field(default_factory=lambda: {
        "find": "Find",
        "search_pattern": "Search pattern",
        "replace": "Replace",
        "replace_with": "Replace with",
        "replace_all": "Replace All",
        "match_case": "Match case",
        "whole_words": "Whole words",
        "prev": "Prev",
        "next": "Next",
        "close": "Close",
        "error": "Error",
        "replaced": "Replaced",
        "no_matches": "No matches"
    })


@dataclass(frozen=True)
class MenuSettings:
    enabled: bool = True
    fg_color: Optional[str] = None
    text_color: Optional[str] = None
    hover_color: Optional[str] = None
    commands: dict = field(default_factory=lambda: {
        # label: (special type for states or "", callable or attribute of codebox in str, displaying accelerator,
        # additional check (callable with return or attr of codebox in str for cget) or None)
        # or "separator": additional check (callable with return or attr of codebox in str for cget) or None
        "Copy": ("has_selection", "copy_text", "Ctrl+C", None),
        "Paste": ("has_clip", "paste_text", "Ctrl+V", None),
        "Cut": ("has_selection", "cut_text", "Ctrl+X", None),
        "Select All": ("has_text", "select_all_text", "Ctrl+A", None),
        "Search & Replace": ("has_text", "open_search_window", "Ctrl+F", None),
        "separator": "history_enabled",
        "Undo": ("has_undo", "undo", "Ctrl+Z", "history_enabled"),
        "Redo": ("has_redo", "redo", "Ctrl+Shift+Z", "history_enabled"),
    })


@dataclass()
class HistorySettings:
    enabled: bool = False
    cooldown: int = 1500  # ms
    max: int = 100
    built_in_undo: bool = False


@dataclass(frozen=True)
class NumberingSettings:
    enabled: bool = True
    color: Optional[str] = None
    justify: str = "left"
    padx: int = 30
    auto_padx: bool = True


@dataclass(frozen=True)
class KeybindingSettings:  # If you want to disable keybind just write ""
    # Keybindings for common editing actions (widget scope)
    R_select_all_text: str = "CmdOrCtrl+A"
    R_cut_text: str = "CmdOrCtrl+X"
    R_copy_text: str = "CmdOrCtrl+C"
    R_paste_text: str = "CmdOrCtrl+V"
    R_redo: str = "CmdOrCtrl+Shift+Z"
    R_undo: str = "CmdOrCtrl+Z"
    R_open_search_window: str = "CmdOrCtrl+F"
    # Indentation keybinds
    R__on_tab: str = "TAB"
    # Use Shift-Tab for outdent;
    R__on_shift_tab: str = "Shift+TAB"
    R__on_return: str = "RETURN"
    # Quote wrapping on selection
    B__on_quote_single: str = "<KeyPress-'>"
    B__on_quote_double: str = '<KeyPress-">'
    B__on_backtick: str = "<KeyPress-grave>"  # `
    # Bracket/angle wrapping on selection
    B__on_parenleft: str = "<KeyPress-parenleft>"  # (
    B__on_bracketleft: str = "<KeyPress-bracketleft>"  # [
    B__on_braceleft: str = "<KeyPress-braceleft>"  # {
    B__on_less: str = "<KeyPress-less>"  # <
    # Pair backspace handler
    B__on_backspace: str = "<KeyPress-BackSpace>"
    # Smarter selection on double-click and triple-click
    B__on_double_click: str = "<Double-Button-1>"
    B__on_triple_click: str = "<Triple-Button-1>"


@dataclass(frozen=True)
class ReplaceResult:
    """Result of a replace operation."""
    count: int
    error: Optional[str] = None


__all__ = ["SearchWindowSettings", "MenuSettings", "HistorySettings", "NumberingSettings", "KeybindingSettings",
           "ReplaceResult", "asdict"]
