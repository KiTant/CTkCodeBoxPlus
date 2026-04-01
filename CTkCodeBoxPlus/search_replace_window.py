"""
SearchReplaceWindow
Author: xzyqox (KiTant) | https://github.com/KiTant
License: MIT
"""

import customtkinter
from typing import List, Tuple, TYPE_CHECKING
from .dataclasses import SearchWindowSettings
if TYPE_CHECKING:
    from .ctk_code_box import CTkCodeBox


class SearchReplaceWindow(customtkinter.CTkToplevel):
    """A search/replace dialog for CTkCodeBox.
    Provides a GUI for the search() and replace() methods of CTkCodeBox,
    with options for case matching, whole words, and regex mode.
    """
    def __init__(
        self,
        codebox: "CTkCodeBox",
        settings: SearchWindowSettings,
        **kwargs
    ):
        """Initialize the search/replace window.
        Args:
            codebox: The CTkCodeBox instance to search in.
            settings: SearchWindowSettings
            **kwargs: Additional arguments passed to CTkToplevel.
        """
        super().__init__(**kwargs)
        self.codebox = codebox
        self.settings = settings
        self.title(settings.title)
        self.geometry(f"{settings.width}x{settings.height}")
        self.resizable(True, False)
        self.attributes("-topmost", True)

        # Match tracking
        self._matches: List[Tuple[str, str]] = []
        self._current_match_index: int = -1

        self._create_widgets()
        self._bind_events()

        # Focus on search entry
        self.after(100, self._entry_search.focus_set)

    def _create_widgets(self):
        """Create all widgets for the dialog."""
        # Main frame
        self._frame_main = customtkinter.CTkFrame(self)
        self._frame_main.pack(fill="both", expand=True, padx=10, pady=10)

        # Search row
        self._label_search = customtkinter.CTkLabel(self._frame_main,
                                                    text=f'{self.settings.display_text_translation["find"]}:', width=80)
        self._label_search.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self._entry_search = customtkinter.CTkEntry(self._frame_main,
                                                    placeholder_text=f'{self.settings.display_text_translation["search_pattern"]}...')
        self._entry_search.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        # Replace row
        self._label_replace = customtkinter.CTkLabel(self._frame_main, text=f'{self.settings.display_text_translation["replace"]}:', width=80)
        self._label_replace.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self._entry_replace = customtkinter.CTkEntry(self._frame_main,
                                                     placeholder_text=f'{self.settings.display_text_translation["replace_with"]}...')
        self._entry_replace.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        # Options row
        self._checkbox_match_case = customtkinter.CTkCheckBox(
            self._frame_main, text=self.settings.display_text_translation["match_case"]
        )
        self._checkbox_match_case.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self._checkbox_words = customtkinter.CTkCheckBox(
            self._frame_main, text=self.settings.display_text_translation["whole_words"]
        )
        self._checkbox_words.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self._checkbox_regex = customtkinter.CTkCheckBox(
            self._frame_main, text="Regex"
        )
        self._checkbox_regex.grid(row=2, column=2, padx=5, pady=5, sticky="w")

        # Buttons row
        self._button_prev = customtkinter.CTkButton(
            self._frame_main, text=self.settings.display_text_translation["prev"],
            width=60, command=self._on_prev
        )
        self._button_prev.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        self._button_next = customtkinter.CTkButton(
            self._frame_main, text=self.settings.display_text_translation["next"],
            width=60, command=self._on_next
        )
        self._button_next.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        self._button_replace = customtkinter.CTkButton(
            self._frame_main, text=self.settings.display_text_translation["replace"], width=80, command=self._on_replace
        )
        self._button_replace.grid(row=3, column=2, padx=5, pady=5, sticky="e")

        # Replace all row
        self._button_replace_all = customtkinter.CTkButton(
            self._frame_main, text=self.settings.display_text_translation["replace_all"], command=self._on_replace_all
        )
        self._button_replace_all.grid(row=4, column=0, padx=5, pady=5, sticky="w")

        self._button_find = customtkinter.CTkButton(
            self._frame_main, text=self.settings.display_text_translation["find"], width=60, command=self._on_search
        )
        self._button_find.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        self._label_status = customtkinter.CTkLabel(self._frame_main, text="")
        self._label_status.grid(row=4, column=2, padx=5, pady=5, sticky="e")

        # Close button
        self._button_close = customtkinter.CTkButton(
            self._frame_main, text=self.settings.display_text_translation["close"], command=self._on_close
        )
        self._button_close.grid(row=5, column=0, columnspan=3, padx=5, pady=10, sticky="ew")

        # Configure grid weights
        self._frame_main.columnconfigure(1, weight=1)

    def _bind_events(self):
        """Bind events for the dialog."""
        self._entry_search.bind("<Return>", lambda e: self._on_search())
        self._entry_search.bind("<KeyRelease>", self._on_search_key_release)
        self.bind("<Escape>", lambda e: self._on_close())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Re-search when options change
        self._checkbox_match_case.configure(command=self._on_option_changed)
        self._checkbox_words.configure(command=self._on_option_changed)
        self._checkbox_regex.configure(command=self._on_option_changed)

    def _get_search_options(self) -> dict:
        """Get current search options from checkboxes."""
        return {
            "match_case": self._checkbox_match_case.get(),
            "words": self._checkbox_words.get(),
            "regex": self._checkbox_regex.get(),
        }

    def _on_option_changed(self):
        """Re-search when an option checkbox changes."""
        pattern = self._entry_search.get()
        if pattern:
            self._on_search()

    def _on_search_key_release(self, event=None):
        """Trigger search on key release (live search)."""
        pattern = self._entry_search.get()
        if not pattern:
            self._matches = []
            self._current_match_index = -1
            self.codebox.clear_search_highlight()
            self._update_status()
            return
        self._on_search()

    def _on_search(self) -> List[Tuple[str, str]]:
        """Execute search and update matches."""
        pattern = self._entry_search.get()
        if not pattern:
            self._matches = []
            self._current_match_index = -1
            self.codebox.clear_search_highlight()
            self._update_status()
            return []

        options = self._get_search_options()
        self._matches = self.codebox.search(
            pattern,
            match_case=options["match_case"],
            words=options["words"],
            regex=options["regex"],
        )
        self._current_match_index = -1 if not self._matches else 0
        self._update_status()

        # Jump to first match
        if self._matches:
            self._go_to_match(0)

        return self._matches

    def _go_to_match(self, index: int, select: bool = False):
        """Navigate to a specific match by index.
        Args:
            index: Match index to navigate to.
            select: If True, select the match text in codebox.
        """
        if not self._matches or index < 0 or index >= len(self._matches):
            return

        self._current_match_index = index
        start, end = self._matches[index]

        # Scroll to match
        self.codebox.see(start)

        if select:
            # Select the match text
            self.codebox.tag_remove("sel", "1.0", "end")
            self.codebox.tag_add("sel", start, end)

    def _on_next(self):
        """Go to next match."""
        if not self._matches:
            return
        next_index = (self._current_match_index + 1) % len(self._matches)
        self._go_to_match(next_index, select=True)
        self._update_status()

    def _on_prev(self):
        """Go to previous match."""
        if not self._matches:
            return
        prev_index = (self._current_match_index - 1) % len(self._matches)
        self._go_to_match(prev_index, select=True)
        self._update_status()

    def _on_replace(self):
        """Replace current match and go to next."""
        if not self._matches or self._current_match_index < 0:
            return

        pattern = self._entry_search.get()
        replacement = self._entry_replace.get()
        options = self._get_search_options()

        # Get current match range
        start, end = self._matches[self._current_match_index]

        # Replace only in current match range
        result = self.codebox.replace(
            symbols_to_find=pattern,
            symbols_to_replace=replacement,
            replace_all=False,
            index_range=(start, end),
            match_case=options["match_case"],
            words=options["words"],
            regex=options["regex"],
        )

        if result.count > 0:
            # Re-search to update matches
            self._on_search()

    def _on_replace_all(self):
        """Replace all matches."""
        pattern = self._entry_search.get()
        if not pattern:
            return

        replacement = self._entry_replace.get()
        options = self._get_search_options()

        result = self.codebox.replace(
            symbols_to_find=pattern,
            symbols_to_replace=replacement,
            replace_all=True,
            match_case=options["match_case"],
            words=options["words"],
            regex=options["regex"],
        )

        if result.error:
            self._label_status.configure(text=f'{self.settings.display_text_translation["error"]}: {result.error}')
        else:
            self._label_status.configure(text=f'{self.settings.display_text_translation["replaced"]}: {result.count}')
            self._matches = []
            self._current_match_index = -1
            self.codebox.clear_search_highlight()

    def _update_status(self):
        """Update status label with match count and position."""
        total = len(self._matches)
        if total == 0:
            self._label_status.configure(text=self.settings.display_text_translation["no_matches"])
        else:
            current = self._current_match_index + 1
            self._label_status.configure(text=f"{current}/{total}")

    def _on_close(self):
        """Close the window and clear highlights."""
        self.codebox.clear_search_highlight()
        self.codebox._search_window_active = None
        self.destroy()


__all__ = ["SearchReplaceWindow"]
