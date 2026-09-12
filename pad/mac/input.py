"""
Synthesised input on the Mac.

Milestone 2: keystrokes through Quartz CGEvent. Modifier keys are pressed as real
key events around the main key, not only set as flags, because some applications
(Adobe's among them) ignore flag-only shortcuts.

Accessibility permission attaches to the process that posts the events. For a bare
script that is Terminal (or whatever launched python3). trusted() answers whether
this process has it; the host reports the answer on the device rather than failing
silently, and every posted keystroke is logged by the caller.
"""
import time

# Virtual key codes for a US layout (Carbon's kVK_* values). Letters and digits
# are the ANSI positions; punctuation names follow what the config author types.
KEYCODES = {
    "a": 0x00, "s": 0x01, "d": 0x02, "f": 0x03, "h": 0x04, "g": 0x05, "z": 0x06, "x": 0x07,
    "c": 0x08, "v": 0x09, "b": 0x0B, "q": 0x0C, "w": 0x0D, "e": 0x0E, "r": 0x0F, "y": 0x10,
    "t": 0x11, "1": 0x12, "2": 0x13, "3": 0x14, "4": 0x15, "6": 0x16, "5": 0x17, "=": 0x18,
    "9": 0x19, "7": 0x1A, "-": 0x1B, "8": 0x1C, "0": 0x1D, "]": 0x1E, "o": 0x1F, "u": 0x20,
    "[": 0x21, "i": 0x22, "p": 0x23, "l": 0x25, "j": 0x26, "'": 0x27, "k": 0x28, ";": 0x29,
    "\\": 0x2A, ",": 0x2B, "/": 0x2C, "n": 0x2D, "m": 0x2E, ".": 0x2F, "`": 0x32,
    "return": 0x24, "enter": 0x24, "tab": 0x30, "space": 0x31, "delete": 0x33, "backspace": 0x33,
    "escape": 0x35, "esc": 0x35, "forwarddelete": 0x75, "home": 0x73, "end": 0x77,
    "pageup": 0x74, "pagedown": 0x79, "left": 0x7B, "right": 0x7C, "down": 0x7D, "up": 0x7E,
    "f1": 0x7A, "f2": 0x78, "f3": 0x63, "f4": 0x76, "f5": 0x60, "f6": 0x61, "f7": 0x62,
    "f8": 0x64, "f9": 0x65, "f10": 0x6D, "f11": 0x67, "f12": 0x6F,
}

MODIFIERS = {
    # name → (key code, event flag)
    "cmd": (0x37, 1 << 20), "command": (0x37, 1 << 20),
    "shift": (0x38, 1 << 17),
    "alt": (0x3A, 1 << 19), "option": (0x3A, 1 << 19), "opt": (0x3A, 1 << 19),
    "ctrl": (0x3B, 1 << 18), "control": (0x3B, 1 << 18),
}

GLYPHS = {"cmd": "⌘", "command": "⌘", "shift": "⇧", "alt": "⌥", "option": "⌥", "opt": "⌥",
          "ctrl": "⌃", "control": "⌃"}


class InputError(Exception):
    """A reason input cannot be synthesised. The text is shown on the device."""


def hint(keys):
    """'cmd', "'" → ⌘' — the short form shown under a key label on the device."""
    return "".join(GLYPHS.get(k.lower(), k.upper() if len(k) == 1 else k) for k in keys)


def parse(keys):
    """Split a config key list into (modifier list, main key code)."""
    mods, main = [], None
    for k in keys:
        name = k.lower()
        if name in MODIFIERS:
            mods.append(MODIFIERS[name])
        elif name in KEYCODES:
            if main is not None:
                raise InputError("more than one non-modifier key in %r" % (keys,))
            main = KEYCODES[name]
        else:
            raise InputError("unknown key %r" % k)
    if main is None:
        raise InputError("no key to press in %r" % (keys,))
    return mods, main


def trusted():
    """Does this process hold Accessibility permission? Prompts the system dialog
    the first time it is asked, so the answer can change while the host runs."""
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
    except ImportError:
        return False
    if not hasattr(trusted, "_asked"):
        trusted._asked = True
        return bool(AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": True}))
    return bool(AXIsProcessTrustedWithOptions(None))


def keystroke(keys):
    """Press and release a shortcut such as ['cmd', "'"]. Raises InputError."""
    mods, main = parse(keys)
    try:
        from Quartz import (CGEventCreateKeyboardEvent, CGEventPost, CGEventSetFlags,
                            kCGHIDEventTap)
    except ImportError:
        raise InputError("pyobjc quartz is not installed on the mac")
    flags = 0
    for _, flag in mods:
        flags |= flag

    def post(code, down, with_flags):
        ev = CGEventCreateKeyboardEvent(None, code, down)
        CGEventSetFlags(ev, with_flags)
        CGEventPost(kCGHIDEventTap, ev)

    held = 0
    for code, flag in mods:
        held |= flag
        post(code, True, held)
    post(main, True, flags)
    post(main, False, flags)
    for code, flag in reversed(mods):
        held &= ~flag
        post(code, False, held)
    time.sleep(0.01)  # let the event stream settle before anything else is posted
