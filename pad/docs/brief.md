# Brief

## The starting point

ZAPAD (getzapad.com) pairs a Rabbit r1 creation with a signed menu-bar connector on
macOS or Windows. The connector reports which application is in the foreground; the r1
shows a 3×3 keypad belonging to that application, up to three pages deep, with the side
button paging through. Tapping a key runs its assigned shortcut. Tapping a knob or
slider hands the scroll wheel to that control until another is deliberately selected.
Custom keypads can be recorded by pressing a key combination on the desktop.

It works. Two things about it are wrong for this use.

**It relays over the internet.** The documentation states that an r1 shows "Desktop
Offline" when the connector has no network connection, so the two halves find each other
through a third party rather than directly. That is latency on a control that is
supposed to feel like a knob, and a dependency on someone else's infrastructure for a
device that sits next to the machine it controls.

**It follows the application, not the work.** Almost everything worth controlling in
this case runs in a browser — the Plotville generators, `send.`, `proof.`. To ZAPAD
those are all one application called Chrome, sharing one keypad.

## What this build does instead

Everything on the LAN, and the pad keys off the active browser tab as well as the
foreground app. Each generator gets its own face. Keys can call an endpoint directly
rather than impersonating a keyboard, which means a key labelled `send` can be an actual
request to the fleet instead of a simulated ⌘P into a browser window.

## Why it's worth building

Carl runs five plotters (Roland DXY-990, Roland GRX-300AR, two HP 7475A, Mutoh iP-500)
from a Mac-side Flask app. Plotting is a physical, watching activity — you stand at the
machine. A wheel and a few keys in the hand is a better console for that than a trackpad
across the room. The generative tools have the same shape: a seed to re-roll, a few
parameters to nudge, a save. That is a control surface, not a UI.

Illustrator is the other clear case, and the one that justifies it on its own — a real
desktop application, used constantly, where a physical wheel for stroke weight or blend
steps beats dragging a slider.

## What is deliberately out of scope

- Any hosted service, account, or relay.
- Windows support. macOS only.
- An application catalogue. Keypads are hand-authored config, versioned in the repo.
- On-device shortcut recording, at least until the rest works. Editing config in a text
  editor is fine and arguably better.
- Anything to do with plotter output or SVG. This is a control surface. It draws a
  keypad on a small screen.

## Open questions Carl has not settled

Listed in `docs/open-questions.md`. Do not resolve them by choosing quietly.
