"""
CustomTkinter Code Viewer Widget
Original Author (CTkCodeBox): Akash Bora (Akascape) | https://github.com/Akascape
Author (CTkCodeBoxPlus): xzyqox (KiTant) | https://github.com/KiTant
License: MIT
Homepage: https://github.com/KiTant/CTkCodeBoxPlus
"""

__version__ = '1.2'

from .ctk_code_box import CTkCodeBox
from .dataclasses import *
from .custom_exception_classes import *
from .text_menu import TextMenu
from .add_line_nums import AddLineNums
from .keybinding import _unregister_keybind, _register_keybind
