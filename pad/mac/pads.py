"""
Which pad the device is shown, and what its slots do.

Milestone 2: one hard-coded pad, one key, taken from config/keypads.example.json so
nothing here is invented. Milestone 3 replaces this with config/keypads.json and the
context resolution order in docs/protocol.md.
"""
from input import hint

PAD = {
    "id": "illustrator",
    "label": "illustrator",
    "app": "com.adobe.illustrator",
    "pages": [[
        {"label": "grid", "glyph": "grid", "action": {"kind": "key", "keys": ["cmd", "'"]}},
        None, None,
        None, None, None,
        None, None, None,
    ]],
    "controls": [],
}


def current_pad(context):
    """The pad that applies to what is in front. Milestone 2 ignores the context."""
    return PAD


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
