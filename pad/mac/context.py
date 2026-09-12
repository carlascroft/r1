"""
What is in front on the Mac.

Milestone 1: the foreground application, read from NSWorkspace through pyobjc a few
times a second. Window title and browser tab come later (milestone 6) and need
Accessibility and AppleScript respectively; nothing here needs a permission.

make_reader() returns a zero-argument callable. Each call returns a context message
(see docs/protocol.md) or raises ContextError with a plain statement of what is wrong,
which the host forwards to the device as a status reason.

NSWorkspace only learns about activations while the main thread's run loop is
turning, so the host polls from the main thread and calls pump() between reads
instead of sleeping. Without that, frontmostApplication returns the same app forever.
"""
import os
import time


class ContextError(Exception):
    """A reason the context cannot be read. The text is shown on the device."""


def pump(seconds):
    """Turn the Cocoa run loop for a while (main thread only); plain sleep elsewhere."""
    try:
        from Foundation import NSDate, NSRunLoop
    except ImportError:
        time.sleep(seconds)
        return
    NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(seconds))


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
        # Called on the main thread between pump() calls, so the workspace's view
        # of the front app is current. VERIFY on the device run that switching apps
        # on the mac changes what the host logs.
        app = workspace.frontmostApplication()
        if app is None:
            # Fall back to scanning for the active process; some launches leave
            # frontmostApplication nil for a moment.
            for running in workspace.runningApplications():
                if running.isActive():
                    app = running
                    break
        if app is None:
            raise ContextError("no application in front")
        return _message(app.bundleIdentifier() or None, app.localizedName() or None)

    return read
