"""
CustomTkinter Code Viewer Widget
Original Author (CTkCodeBox): Akash Bora (Akascape) | https://github.com/Akascape
Author (CTkCodeBoxPlus): xzyqox (KiTant) | https://github.com/KiTant
License: MIT
Homepage: https://github.com/KiTant/CTkCodeBoxPlus
"""

__version__ = '1.4.1'

from .ctk_code_box import CTkCodeBox
from .dataclasses import *
from .constants import common_langs
from .custom_exception_classes import *
from .text_menu import TextMenu
from .add_line_nums import AddLineNums
from .keybinding import unregister_keybind, register_keybind
from .search_replace_window import SearchReplaceWindow

__all__ = ["CTkCodeBox", "HistorySettings", "MenuSettings", "SearchWindowSettings", "NumberingSettings",
           "AddLineNums", "unregister_keybind", "register_keybind", "CTkCodeBoxError", "KeybindingSettings",
           "LanguageNotAvailableError", "ThemeNotAvailableError", "LexerError", "ConfigureBadType",
           "SearchReplaceWindow", "ReplaceResult", "TextMenu", "common_langs"]