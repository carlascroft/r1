"""
What is in front on the Mac.

Milestone 1: the foreground application, read from NSWorkspace through pyobjc a few
times a second. Window title and browser tab come later (milestone 6) and need
Accessibility and AppleScript respectively; nothing here needs a permission.

make_reader() returns a zero-argument callable. Each call returns a context message
(see docs/protocol.md) or raises ContextError with a plain statement of what is wrong,
which the host forwards to the device as a status reason.
"""
import os


class ContextError(Exception):
    """A reason the context cannot be read. The text is shown on the device."""


def _message(app, name):
    return {"t": "context", "app": app, "name": name, "title": None, "url": None}


def make_reader():
    # Development only: lets the host run on a machine that is not a Mac, so the
    # socket and the device face can be exercised. Never set this on the real host.
    fake = os.environ.get("PAD_FAKE_APP")
    if fake:
        return lambda: _message(fake, fake.split(".")[-1])

    try:
        from AppKit import NSWorkspace  # pyobjc-framework-Cocoa
    except ImportError:
        def missing():
            raise ContextError("pyobjc is not installed on the mac")
        return missing

    workspace = NSWorkspace.sharedWorkspace()

    def read():
        # VERIFY: frontmostApplication is documented as safe to call off the main
        # thread; the host polls it from a worker thread. Confirm on the device run.
        app = workspace.frontmostApplication()
        if app is None:
            raise ContextError("no application in front")
        return _message(app.bundleIdentifier() or None, app.localizedName() or None)

    return read
