# CTkCodeBoxPlus

A code editor widget for customtkinter (Enhanced Edition).
![image](https://github.com/user-attachments/assets/a22c6142-afc8-4239-840f-76e06ef7c668)


## Features
- Multiple language support
- Code syntax highlighting
- Line highlighting (Enhanced)
- Auto-Indent and Outdent (Enhanced)
- Custom history with undo and redo (Enhanced)
- Smart selection on double and triple click (Enhanced)
- Implemented actions like copy, paste, cut (Enhanced)
- Keybindings for implemented actions (Enhanced)
- Multiple Themes
- Right-click menu (Enhanced)
- Line numbers on left side
- Fully customizable
- Easy to Use

## Installation

```bash
pip install CTkCodeBoxPlus
```

## Simple Usage
```python
import customtkinter
from CTkCodeBoxPlus import *

root = customtkinter.CTk()

codebox = CTkCodeBox(root, language="python")
codebox.pack(padx=10, pady=10, expand=True,fill="both")

root.mainloop()
```

### Arguments
| Parameter                        | Type                     | Default           | Description                                            |
|----------------------------------|--------------------------|-------------------|--------------------------------------------------------|
| **master**                       | Widget                   | -                 | Parent widget                                          |
| **language**                     | str/pygments.lexer.Lexer | -                 | Pygments language name (str) or a lexer class          |
| **height**                       | int                      | 200               | Widget height in pixels (passed to CTkTextbox)         |
| **theme**                        | str                      | "solarized-light" | Pygments style name used for highlighting              |
| **line_numbering**               | bool                     | True              | Enable line numbers                                    |
| **numbering_color**              | str                      | None              | Color for line numbers                                 |
| **menu**                         | bool                     | True              | Enable context menu                                    |
| **menu_fg_color**                | str                      | None              | Context menu background color                          |
| **menu_text_color**              | str                      | None              | Context menu text color                                |
| **menu_hover_color**             | str                      | None              | Context menu active background color                   |
| **wrap**                         | bool                     | True              | Enable word wrap                                       |
| **select_color**                 | str                      | None              | Override selection background color                    |
| **cursor_color**                 | str                      | None              | Cursor color I (blinking)                              |
| **highlight_current_line**       | bool                     | True              | Highlight the active line                              |
| **highlight_current_line_color** | str                      | None              | Explicit color for active line                         |
| **history_enabled**              | bool                     | True              | Enable built-in undo/redo history                      |
| **history_cooldown** (ms)        | int                      | 2500              | Cooldown for pushing history in _on_keypress_history() |
| **history_max**                  | int                      | 100               | Maximum undo frames to keep.                           |
| **indent_width**                 | int                      | 4                 | Number of spaces for indent/outdent.                   |
| ****kwargs**                     | various                  | -                 | Additional CTkTextBox parameters                       |

### Methods
- **.insert(index, code, push_history)**: Insert code/text in the box and trigger a non-editing highlight update with pushing history (if push_history is True)
- **.get(index1, index2)**: Get code/text from the box
- **.configure(kwargs)**: Change parameters of the codebox
- **.cget(parameter)**: Get the parameter value from the codebox by name
- **.update_code()**: Schedule a debounced re-highlight and update edited flag
- **.clear_code()**: Remove all highlighting tags while preserving selection
- **.set_wrap(enabled)**: Enable/disable word wrap
- **.toggle_wrap()**: Toggle wrap mode
- **.is_edited()**: Return True if the text has been edited since last reset
- **.reset_edited()**: Reset edited state flag to False
- **.cut_text()**: Cut selected text to clipboard and notify change
- **.copy_text()**: Copy selected text to clipboard
- **.paste_text()**: Paste clipboard text, replacing selection if present, and refresh highlighting/lines with notify change
- **.clear_all_text()**: Delete all content and notify change
- **.select_all_text()**: Select all content
- **.set_history_enabled(enabled)**: Enable/disable the internal undo/redo history
- **.set_history_limit(limit)**: Set maximum number of undo frames to keep
- **.clear_history()**: Clear undo and redo stacks
- **.undo()**: Undo the last change if history is enabled
- **.redo()**: Redo the last undone change if available

<br>
<a href="https://github-readme-tech-stack.vercel.app">
<img src="https://github-readme-tech-stack.vercel.app/api/cards?title=Languages&lineCount=4&width=520&bg=%230D1117&badge=%23161B22&border=%2321262D&titleColor=%2358A6FF&line1=python%2Cpython%2Cfff800%3BCplusplus%2C%2B%2B%2C7bc9b1%3Bcplusplus%2Csharp%2C6c3bb2%3BCplusplus%2C+%2C4a82cc%3Bjavascript%2Cjavascript%2Cf0fc0d%3B&line2=lua%2Clua%2C5d72e6%3BRust%2Crust%2Ce62323%3Bperl%2Cperl%2C92d5d3%3Bkotlin%2Ckotlin%2C6dfa21%3Bruby%2Cruby%2Cff0000%3B&line3=swift%2Cswift%2Cfe811b%3Bphp%2Cphp%2C3749b3%3Breact%2Creact%2Cd3ff00%3Bjson%2Cjson%2Cffe300%3Bgo%2Cgo%2C11ffdc%3B&line4=yaml%2Cyaml%2C6dc2af%3Bxml%2Cxml%2C63f030%3Bcss%2Ccss%2C1ff9f2%3Bhtml%2Chtml%2C2bc5b4%3BTypescript%2CTypescript%2C42b1c2%3BJAVA%2Cjava%2Ceffc00%3B" alt="Languages" />
</a>

More lexers available here: https://pygments.org/docs/lexers/

## Color Themes
```
abap, arduino, autumn, borland, colorful, default, dracula, emacs, 
friendly_grayscale, friendly, fruity, github-dark, gruvbox-dark, 
gruvbox-light, igor, inkpot, lightbulb, lilypond, lovelace, manni, material, 
monokai, murphy, native, nord-darker, nord, one-dark, paraiso-dark, paraiso-light, 
pastie, perldoc, rainbow_dash, rrt, sas, solarized-dark, solarized-light, staroffice, 
stata-dark, stata-light, tango, trac, vim, vs, xcode, zenburn
```
More style examples given here: https://pygments.org/styles/

---

## Support & Issues

- **GitHub Issues**: [Report bugs or request features](https://github.com/KiTant/CTkCodeBoxPlus/issues)
- **Discussions**: [Community support and questions](https://github.com/KiTant/CTkCodeBoxPlus/discussions)

---

## Authors

- **Original Author**: [Akash Bora (Akascape)](https://github.com/Akascape) - CTkCodeBox
- **Author**: [xzyqox (KiTant)](https://github.com/KiTant) - CTkCodeBoxPlus (Enhanced version with new\better features)

---

## License

This project is licensed under the MIT License.

---
