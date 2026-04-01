"""
Keybinding system for customtkinter

Provides layout-independent keyboard keybind registration that works across
platforms and keyboard layouts by physical keycode logic.

Usage:
    from .keybinding import register_keybind
    register_keybind(root, "Ctrl+S", on_save)
    register_keybind(textbox, "F1", on_help)  # child widget is accepted
    register_keybind(entry, "Ctrl+Return", on_submit, bind_scope='widget')  # bind only to widget
    # cross-platform pseudo-modifier: CmdOrCtrl (Command on macOS, Control elsewhere)
    register_keybind(root, "CmdOrCtrl+P", on_print)

    from .keybinding import unregister_keybind
    unregister_keybind(root, "CmdOrCtrl+P")              # remove all callbacks for this keybind on target
    unregister_keybind(entry, "Ctrl+Return", on_submit)  # remove specific callback

Notes:
    - You can pass either a toplevel/root (tk.Tk, tk.Toplevel, CTk, CTkToplevel)
      or ANY Tk/CustomTkinter widget (e.g., CTkTextbox, CTkEntry).
    - By default bindings attach to the widget's toplevel (window). Use bind_scope='widget'
      to bind only to the specified widget (fires when the widget has focus).

Author: xzyqox (KiTant) | https://github.com/KiTant
"""
from __future__ import annotations
from typing import Callable, Dict, List, Any, Tuple
import warnings
import sys
import time

# Global storage for keybindings, layout-independent
_GLOBAL_KEY_BINDINGS: Dict[int, Dict[str, Dict[int, List[Callable]]]] = {}
# Last event per group id (toplevel or its transient master) for deduplication:
# group_id -> (keycode, modifier, timestamp)
_LAST_KEY_EVENT: Dict[int, Tuple[int, str, float]] = {}
# Store handlers for unbinding: target_id -> {handler_attr: handler_func}
_HANDLER_STORAGE: Dict[int, Dict[str, Callable]] = {}
_PLATFORM_KEYMAPS = None


def _cleanup_stale_events() -> None:
    """Remove stale entries from _LAST_KEY_EVENT (older than 1 second)."""
    current_time = time.time()
    stale_keys = [k for k, v in _LAST_KEY_EVENT.items() if current_time - v[2] > 1.0]
    for k in stale_keys:
        del _LAST_KEY_EVENT[k]


def _cleanup_target(target_id: int) -> None:
    """Clean up all bindings for a destroyed target."""
    if target_id in _GLOBAL_KEY_BINDINGS:
        del _GLOBAL_KEY_BINDINGS[target_id]
    if target_id in _HANDLER_STORAGE:
        del _HANDLER_STORAGE[target_id]
    # Clean up stale events for this target's group
    if target_id in _LAST_KEY_EVENT:
        del _LAST_KEY_EVENT[target_id]


def _get_platform_keymaps() -> Tuple[Dict[str, int], Dict[str, int]]:
    global _PLATFORM_KEYMAPS
    if not _PLATFORM_KEYMAPS:
        _PLATFORM_KEYMAPS = _build_platform_keymaps()
    return _PLATFORM_KEYMAPS


def _build_platform_keymaps() -> Tuple[Dict[str, int], Dict[str, int]]:
    """Return (function_keys, special_keys) dicts for the current platform.

    This centralizes platform keycodes to avoid duplication.
    """
    if sys.platform == 'win32':
        function_keys = {
            'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115, 'F5': 116, 'F6': 117,
            'F7': 118, 'F8': 119, 'F9': 120, 'F10': 121, 'F11': 122, 'F12': 123,
            'F13': 124, 'F14': 125, 'F15': 126, 'F16': 127, 'F17': 128, 'F18': 129,
            'F19': 130, 'F20': 131, 'F21': 132, 'F22': 133, 'F23': 134, 'F24': 135
        }
        special_keys = {
            'DELETE': 46, 'DEL': 46,
            'INSERT': 45, 'INS': 45,
            'HOME': 36, 'END': 35,
            'PAGE_UP': 33, 'PAGEUP': 33, 'PGUP': 33,
            'PAGE_DOWN': 34, 'PAGEDOWN': 34, 'PGDN': 34,
            'UP': 38, 'DOWN': 40, 'LEFT': 37, 'RIGHT': 39,
            'TAB': 9,
            'ENTER': 13, 'RETURN': 13,
            'ESCAPE': 27, 'ESC': 27,
            'SPACE': 32,
            'BACKSPACE': 8,
            'PLUS': 187, 'EQUAL': 187, '=': 187,  # Main keyboard =/+ key
            'NUMPAD_PLUS': 107, 'NUMPAD_ADD': 107,  # Numpad +
            'MINUS': 189, 'HYPHEN': 189, '-': 189,  # Main keyboard -/_ key
            'NUMPAD_MINUS': 109, 'NUMPAD_SUBTRACT': 109,  # Numpad -
            'COMMA': 188, ',': 188,
            'PERIOD': 190, '.': 190
        }
    elif sys.platform == 'darwin':
        function_keys = {
            'F1': 122, 'F2': 120, 'F3': 99,  'F4': 118, 'F5': 96,  'F6': 97,
            'F7': 98,  'F8': 100, 'F9': 101, 'F10': 109, 'F11': 103, 'F12': 111,
            'F13': 105, 'F14': 107, 'F15': 113, 'F16': 106, 'F17': 64,  'F18': 79,
            'F19': 80,  'F20': 81
        }
        special_keys = {
            'DELETE': 117, 'DEL': 117,  # Forward Delete (both unified)
            'BACKSPACE': 51,  # Backspace key
            'INSERT': 114,
            'HOME': 115, 'END': 119,
            'PAGE_UP': 116, 'PAGEUP': 116, 'PGUP': 116,
            'PAGE_DOWN': 121, 'PAGEDOWN': 121, 'PGDN': 121,
            'UP': 126, 'DOWN': 125, 'LEFT': 123, 'RIGHT': 124,
            'TAB': 48,
            'ENTER': 36, 'RETURN': 76,  # keypad Enter = 76
            'ESCAPE': 53, 'ESC': 53,
            'SPACE': 49,
            'PLUS': 69, 'EQUAL': 69, '=': 69,  # Main keyboard =/+ key
            'NUMPAD_PLUS': 78, 'NUMPAD_ADD': 78,  # Numpad +
            'MINUS': 27, 'HYPHEN': 27, '-': 27,  # Main keyboard -/_ key
            'NUMPAD_MINUS': 75, 'NUMPAD_SUBTRACT': 75,  # Numpad -
            'COMMA': 43, ',': 43,
            'PERIOD': 47, '.': 47
        }
    else:
        function_keys = {
            'F1': 67,  'F2': 68,  'F3': 69,  'F4': 70,  'F5': 71,  'F6': 72,
            'F7': 73,  'F8': 74,  'F9': 75,  'F10': 76,  'F11': 95,  'F12': 96,
            'F13': 191, 'F14': 192, 'F15': 193, 'F16': 194, 'F17': 195, 'F18': 196,
            'F19': 197, 'F20': 198, 'F21': 199, 'F22': 200, 'F23': 201, 'F24': 202
        }
        special_keys = {
            'DELETE': 119, 'DEL': 119,
            'INSERT': 118, 'INS': 118,
            'HOME': 110, 'END': 115,
            'PAGE_UP': 112, 'PAGEUP': 112, 'PGUP': 112,
            'PAGE_DOWN': 117, 'PAGEDOWN': 117, 'PGDN': 117,
            'UP': 111, 'DOWN': 116, 'LEFT': 113, 'RIGHT': 114,
            'TAB': 23,
            'ENTER': 36, 'RETURN': 36,
            'ESCAPE': 9, 'ESC': 9,
            'SPACE': 65,
            'BACKSPACE': 22,
            'PLUS': 21, 'EQUAL': 21, '=': 21,  # Main keyboard =/+ key
            'NUMPAD_PLUS': 86, 'NUMPAD_ADD': 86,  # Numpad +
            'MINUS': 20, 'HYPHEN': 20, '-': 20,  # Main keyboard -/_ key
            'NUMPAD_MINUS': 82, 'NUMPAD_SUBTRACT': 82,  # Numpad -
            'COMMA': 59, ',': 59,
            'PERIOD': 60, '.': 60
        }
    return function_keys, special_keys


def _get_transient_master(widget: Any) -> Any | None:
    """Return transient master toplevel for the widget's toplevel, if any."""
    try:
        tl = widget.winfo_toplevel()
        trans_path = tl.tk.call('wm', 'transient', tl._w)
        if trans_path:
            return tl.nametowidget(trans_path).winfo_toplevel()
    except Exception:
        return None
    return None


def _get_group_id(widget: Any) -> int:
    """Return group id: transient master id if present, else widget's toplevel id.
    Uses Python's id() instead of winfo_id() to avoid potential ID reuse 
    collisions when widgets are destroyed and recreated by the OS.
    """
    try:
        tl = widget.winfo_toplevel()
        master = _get_transient_master(tl) or None
        return id(master or tl)
    except Exception:
        return 0  # Fallback for invalid widgets


def _parse_modifiers(mod_tokens: List[str]) -> Tuple[str, List[str]]:
    """Normalize a list of modifier tokens into a canonical key and Tk names.

    Returns:
        mods_key: canonical string like 'ctrl', 'ctrl+shift', or 'none'
        tk_mods: list of Tk modifier names like ['Control', 'Shift']
    """
    if not mod_tokens:
        return 'none', []

    # Map input tokens to canonical modifiers
    canonical: set[str] = set()
    for tok in mod_tokens:
        t = tok.strip().lower()
        if not t:
            continue
        if t in ('ctrl', 'control', 'ctl'):
            canonical.add('ctrl')
        elif t in ('alt', 'option'):
            canonical.add('alt')
        elif t in ('shift',):
            canonical.add('shift')
        elif t in ('cmd', 'command'):
            canonical.add('cmd')
        elif t == 'cmdorctrl':
            canonical.add('cmd' if sys.platform == 'darwin' else 'ctrl')
        else:
            # unsupported modifier
            raise ValueError(f"Unsupported modifier: {tok}")

    if not canonical:
        return 'none', []

    # Stable order for key and Tk list
    order = ['ctrl', 'alt', 'shift', 'cmd']
    tk_map = {'ctrl': 'Control', 'alt': 'Alt', 'shift': 'Shift', 'cmd': 'Command'}
    in_order = [m for m in order if m in canonical]

    mods_key = '+'.join(in_order)
    tk_mods = [tk_map[m] for m in in_order]
    return mods_key, tk_mods


def register_keybind(widget_or_root: Any, keybind: str, callback: Callable, *, bind_scope: str = 'window') -> None:
    """Register a keyboard keybind that works regardless of keyboard layout.

    Supported Modifiers: Ctrl, Alt, Shift, Cmd (macOS)
    Supported Keys: A-Z, 0-9, F1-F12, Delete, Insert, Home, End, Page_Up, Page_Down, etc.
    Supports both single keys (F1, F2, Delete) and modified keys (Ctrl+S, Alt+F4)

    Args:
        widget_or_root: Any Tk/CustomTkinter widget or a toplevel/root.
        keybind: Keybind string in format 'Modifier+Key' or just 'Key' (e.g., "Ctrl+S", "Alt+F4", "F1")
        callback: Function to call when the keybind is triggered
        bind_scope: Where to bind the handler. Options:
            - 'window': bind on the widget's toplevel so the shortcut works for the entire window
            - 'widget': bind directly on the provided widget (fires when that widget has focus)
    """
    if not keybind or not isinstance(keybind, str):
        return

    # Resolve toplevel/root from any widget
    try:
        root = widget_or_root.winfo_toplevel()
    except Exception:
        # Fall back to the provided object if it already behaves like a root
        root = widget_or_root

    # Determine actual binding target based on scope
    if bind_scope not in ('window', 'widget'):
        warnings.warn(f"register_keybind: unknown bind_scope '{bind_scope}', defaulting to 'window'")
        bind_scope = 'window'

    target = root if bind_scope == 'window' else widget_or_root

    # Ensure target has the minimal Tk API we need
    if not hasattr(target, 'winfo_id') or not hasattr(target, 'bind'):
        warnings.warn("register_keybind: provided object does not expose Tk widget API")
        return

    # Parse keybind string (e.g., "Ctrl+S", "Alt+F4", "F1", "Delete")
    parts = [p.strip() for p in keybind.split('+')]

    # Determine modifiers and key
    if len(parts) == 1:
        mods_key, tk_mods = 'none', []
        key = parts[0]
    else:
        *mods, key = parts
        try:
            mods_key, tk_mods = _parse_modifiers(mods)
        except ValueError:
            return

    # Enhanced key mapping including function keys and special keys
    key_upper = key.upper()

    # Platform-specific keycode dictionaries
    function_keys, special_keys = _get_platform_keymaps()

    # Determine keycode
    if key_upper in function_keys:
        keycode = function_keys[key_upper]
    elif key_upper in special_keys:
        keycode = special_keys[key_upper]
    elif len(key) == 1 and key.isalnum():
        # Regular alphanumeric keys (A-Z, 0-9)
        keycode = ord(key_upper)
    else:
        # Unsupported key
        warnings.warn(f"Unsupported key in keybind: {key}")
        return

    # Store binding info
    target_id = id(target)
    bindings = _GLOBAL_KEY_BINDINGS.setdefault(target_id, {})
    modifier_bindings = bindings.setdefault(mods_key, {})
    callbacks = modifier_bindings.setdefault(keycode, [])
    # Keep only a single callback per keybind within a window.
    # Replace any existing different callback to avoid multiple firings.
    if callbacks == [callback]:
        pass
    else:
        callbacks.clear()
        callbacks.append(callback)

    # Create unique handler attribute name for this modifier combination
    handler_attr = f"_ctk_keybinder_{mods_key.replace('+', '_')}_binding"

    # Ensure we have the generic handler only once per root per modifier
    if not hasattr(target, handler_attr):
        def _handle_key_press(event, mod=mods_key, t_id=target_id, tgt=target):
            _cleanup_stale_events()
            # Only handle if the event focus is within the same window group as the target
            try:
                focus_widget = event.widget or tgt.focus_displayof() or tgt.focus_get()
                if not focus_widget:
                    return
                active_tl = focus_widget.winfo_toplevel()
                # Compare group ids (toplevel or its transient master)
                group_active = _get_group_id(active_tl)
                group_target = _get_group_id(tgt)
                if group_active != group_target:
                    return
            except Exception:
                # If we cannot determine focus/toplevel reliably, do not handle
                return

            # Create event signature for deduplication per target
            current_time = time.time()
            group_id = _get_group_id(tgt)
            last = _LAST_KEY_EVENT.get(group_id)
            if last and last[0] == event.keycode and last[1] == mod and current_time - last[2] < 0.1:
                return
            _LAST_KEY_EVENT[group_id] = (event.keycode, mod, current_time)

            modifier_dict = _GLOBAL_KEY_BINDINGS.get(t_id, {}).get(mod, {})
            cb_list = modifier_dict.get(event.keycode, [])
            if cb_list:
                for cb in list(cb_list):  # iterate over a copy; may modify original
                    try:
                        cb()
                    except Exception as e:
                        warnings.warn(f"Error in keybind callback: {e}")
                        # Auto-prune stale/broken callback to avoid future warnings
                        try:
                            store = _GLOBAL_KEY_BINDINGS.get(t_id, {}).get(mod, {})
                            lst = store.get(event.keycode)
                            if lst and cb in lst:
                                lst.remove(cb)
                                if not lst:
                                    del store[event.keycode]
                                    # If modifier has no keys left, remove it
                                    parent = _GLOBAL_KEY_BINDINGS.get(t_id, {})
                                    if not store and mod in parent:
                                        del parent[mod]
                                        # If target has no mods left, remove it
                                        if not parent and t_id in _GLOBAL_KEY_BINDINGS:
                                            del _GLOBAL_KEY_BINDINGS[t_id]
                        except Exception:
                            pass
                return "break"

        # Bind to chosen target (window or widget)
        if mods_key == 'none':
            target.bind('<KeyPress>', _handle_key_press, add='+')
        else:
            event_pattern = '<' + '-'.join(tk_mods + ['KeyPress']) + '>'
            target.bind(event_pattern, _handle_key_press, add='+')

        setattr(target, handler_attr, True)

        # Store handler for later unbinding
        if target_id not in _HANDLER_STORAGE:
            _HANDLER_STORAGE[target_id] = {}
        _HANDLER_STORAGE[target_id][handler_attr] = _handle_key_press

        # Set up cleanup on window destroy
        # <Destroy> bubbles up from child widgets to parents.
        # We must only cleanup when the target itself is destroyed, not a child.
        def _on_destroy(event, t_id=target_id, tgt=target):
            try:
                if str(event.widget) == str(getattr(tgt, '_w', '')):
                    _cleanup_target(t_id)
            except Exception:
                pass
        try:
            # Only bind to toplevel for destroy event
            if bind_scope == 'window':
                target.bind('<Destroy>', _on_destroy, add='+')
            else:
                # For widget scope, also bind to the toplevel
                try:
                    root.bind('<Destroy>', _on_destroy, add='+')
                except Exception:
                    pass
        except Exception:
            pass

    # Remove previous bind_all routing to avoid duplicate firings. We rely on
    # per-window binding with active-window guard above.


def unregister_keybind(widget_or_root: Any, keybind: str, callback: Callable | None = None, *, bind_scope: str = 'window') -> bool:
    """Unregister keybind from a window or a specific widget.

    Args:
        widget_or_root: Any Tk/CustomTkinter widget or a toplevel/root.
        keybind: Keybind string 'Modifier+Key' or just 'Key'. Supports 'CmdOrCtrl'.
        callback: Optional specific callback to remove. If None, removes all callbacks for this keybind.
        bind_scope: 'window' to target the widget's toplevel, or 'widget' to target only the widget.

    Returns:
        True if something was removed, False otherwise.
    """
    if not keybind or not isinstance(keybind, str):
        return False

    # Resolve target
    try:
        root = widget_or_root.winfo_toplevel()
    except Exception:
        root = widget_or_root

    if bind_scope not in ('window', 'widget'):
        bind_scope = 'window'
    target = root if bind_scope == 'window' else widget_or_root

    if not hasattr(target, 'winfo_id'):
        return False

    # Parse keybind (allow multiple modifiers)
    parts = [p.strip() for p in keybind.split('+')]
    if len(parts) == 1:
        mods_key, _tk_mods = 'none', []
        key = parts[0]
    else:
        *mods, key = parts
        try:
            mods_key, _tk_mods = _parse_modifiers(mods)
        except ValueError:
            return False

    key_upper = key.upper()

    # Platform-specific keycode dictionaries (same as in register_keybind)
    function_keys, special_keys = _get_platform_keymaps()

    if key_upper in function_keys:
        keycode = function_keys[key_upper]
    elif key_upper in special_keys:
        keycode = special_keys[key_upper]
    elif len(key) == 1 and key.isalnum():
        keycode = ord(key_upper)
    else:
        return False

    target_id = id(target)
    bindings = _GLOBAL_KEY_BINDINGS.get(target_id)
    if not bindings:
        return False
    mod_dict = bindings.get(mods_key)
    if not mod_dict:
        return False

    removed = False
    if keycode in mod_dict:
        if callback is None:
            del mod_dict[keycode]
            removed = True
        else:
            try:
                mod_dict[keycode].remove(callback)
                removed = True
                if not mod_dict[keycode]:
                    del mod_dict[keycode]
            except ValueError:
                pass

    # Cleanup empty containers and unbind Tk handlers if needed
    if removed and not mod_dict:
        del bindings[mods_key]
        # Unbind the Tk handler when no more callbacks for this modifier
        handler_attr = f"_ctk_keybinder_{mods_key.replace('+', '_')}_binding"
        if target_id in _HANDLER_STORAGE and handler_attr in _HANDLER_STORAGE[target_id]:
            handler = _HANDLER_STORAGE[target_id][handler_attr]
            try:
                if mods_key == 'none':
                    target.unbind('<KeyPress>', handler)
                else:
                    # Reconstruct the event pattern
                    order = ['ctrl', 'alt', 'shift', 'cmd']
                    tk_map = {'ctrl': 'Control', 'alt': 'Alt', 'shift': 'Shift', 'cmd': 'Command'}
                    canonical_parts = mods_key.split('+')
                    tk_mods = [tk_map[m] for m in order if m in canonical_parts]
                    event_pattern = '<' + '-'.join(tk_mods + ['KeyPress']) + '>'
                    target.unbind(event_pattern, handler)
                del _HANDLER_STORAGE[target_id][handler_attr]
                if hasattr(target, handler_attr):
                    delattr(target, handler_attr)
            except Exception:
                pass
            if not _HANDLER_STORAGE[target_id]:
                del _HANDLER_STORAGE[target_id]
    if removed and not bindings:
        del _GLOBAL_KEY_BINDINGS[target_id]

    return removed
