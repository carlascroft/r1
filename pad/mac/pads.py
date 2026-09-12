"""
Which pad the device is shown, and what its slots do.

Milestone 3: pads come from config/keypads.json, hand-authored and versioned. The
example file documents the shape. The file is re-read whenever it changes on disk,
so editing it in a text editor is the whole editing workflow. A file that fails to
load keeps the last good set of pads and reports why on the device.

Resolution order (docs/protocol.md): a browser tab url matching a pad's `match`,
then the front app's bundle id matching a pad's `app`, then the pad with id `default`.
"""
import fnmatch
import json
import os

from input import InputError, hint, parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config", "keypads.json")
EXAMPLE = os.path.join(ROOT, "config", "keypads.example.json")
BROWSERS = {"com.google.Chrome", "com.apple.Safari", "org.mozilla.firefox", "com.brave.Browser",
            "com.microsoft.edgemac", "company.thebrowser.Browser"}
KINDS = {"key", "shell", "http"}
SLOTS = 9
MAX_PAGES = 3


class ConfigError(Exception):
    """A reason the config cannot be used. The text is shown on the device."""


def _check(condition, message):
    if not condition:
        raise ConfigError(message)


def validate(doc):
    """Raise ConfigError with a plain statement of the first thing wrong."""
    _check(isinstance(doc, dict) and isinstance(doc.get("pads"), list), "config needs a list of pads")
    seen = set()
    for pad in doc["pads"]:
        _check(isinstance(pad, dict) and isinstance(pad.get("id"), str), "every pad needs an id")
        pid = pad["id"]
        _check(pid not in seen, "pad id %r is used twice" % pid)
        seen.add(pid)
        _check(isinstance(pad.get("label"), str), "pad %r needs a label" % pid)
        pages = pad.get("pages")
        _check(isinstance(pages, list) and 1 <= len(pages) <= MAX_PAGES,
               "pad %r needs 1 to %d pages" % (pid, MAX_PAGES))
        for p, page in enumerate(pages):
            _check(isinstance(page, list) and len(page) == SLOTS,
                   "pad %r page %d needs exactly %d slots" % (pid, p + 1, SLOTS))
            for n, slot in enumerate(page):
                if slot is None:
                    continue
                where = "pad %r page %d slot %d" % (pid, p + 1, n + 1)
                _check(isinstance(slot, dict) and isinstance(slot.get("label"), str), where + " needs a label")
                action = slot.get("action")
                if action is None:
                    continue
                _check(isinstance(action, dict) and action.get("kind") in KINDS,
                       where + " has an action of unknown kind")
                if action["kind"] == "key":
                    try:
                        parse(action.get("keys") or [])
                    except InputError as e:
                        raise ConfigError("%s: %s" % (where, e))
                elif action["kind"] == "http":
                    _check(isinstance(action.get("url"), str), where + " http action needs a url")
                elif action["kind"] == "shell":
                    _check(isinstance(action.get("cmd"), (str, list)), where + " shell action needs a cmd")
        for control in pad.get("controls", []):
            _check(isinstance(control, dict) and isinstance(control.get("id"), str)
                   and isinstance(control.get("label"), str), "pad %r has a control without id and label" % pid)
    _check("default" in seen, "config needs a pad with id 'default'")
    return doc


class Pads:
    """The live config: reloads itself when the file changes."""

    def __init__(self, path=CONFIG):
        self.path = path
        self.pads = []
        self.error = None      # plain statement, or None when the file is good
        self._stamp = object()   # never equal to a real stamp, so the first refresh always runs

    def refresh(self):
        """Re-read the file if it changed. Returns True when the set of pads changed."""
        try:
            stamp = os.stat(self.path).st_mtime_ns
        except OSError:
            stamp = None
        if stamp == self._stamp:
            return False
        self._stamp = stamp
        if stamp is None:
            self.error = "no config/keypads.json on the mac"
            return False
        try:
            with open(self.path) as f:
                doc = validate(json.load(f))
        except ValueError as e:
            self.error = "config/keypads.json is not valid json (%s)" % str(e).split(":")[0].lower()
            return False
        except ConfigError as e:
            self.error = "config: %s" % e
            return False
        self.error = None
        self.pads = doc["pads"]
        return True

    def resolve(self, context):
        """The pad that applies to what is in front."""
        app = (context or {}).get("app")
        url = (context or {}).get("url")
        if url and app in BROWSERS:
            bare = url.split("://", 1)[-1]
            for pad in self.pads:
                pattern = pad.get("match")
                if pattern and (fnmatch.fnmatchcase(bare, pattern) or fnmatch.fnmatchcase(url, pattern)):
                    return pad
        for pad in self.pads:
            if pad.get("app") and pad["app"] == app:
                return pad
        for pad in self.pads:
            if pad["id"] == "default":
                return pad
        return None


def to_device(pad):
    """The pad as the device sees it: labels, glyphs and hints, never the actions."""
    pages = []
    for page in pad["pages"]:
        slots = []
        for slot in page:
            if slot is None:
                slots.append(None)
                continue
            action = slot.get("action")
            slots.append({
                "label": slot["label"],
                "glyph": slot.get("glyph"),
                "hint": hint(action["keys"]) if action and action["kind"] == "key" else None,
                "assigned": action is not None,
            })
        pages.append(slots)
    return {"t": "pad", "id": pad["id"], "label": pad["label"], "pages": pages,
            "controls": pad.get("controls", [])}


def slot_action(pad, page, slot):
    """The action behind a slot, or None if nothing is assigned there."""
    try:
        entry = pad["pages"][page][slot]
    except (IndexError, TypeError):
        return None
    return entry.get("action") if entry else None
