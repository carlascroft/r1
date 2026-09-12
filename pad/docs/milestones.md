# Build order

Each milestone ends with something Carl can look at on the device or on the machine.
Do not start the next one until the current one has been seen.

## 0 — Can the device talk to the LAN at all?

**Everything below depends on this and it may fail.**

The creation is a page in a Flutter webview. Carl's other creations are hosted on
Cloudflare Pages over HTTPS; a page served over HTTPS cannot open a `ws://` or `http://`
connection to a LAN address, so this build serves the creation itself over plain HTTP
from the Mac. The unknown is whether rabbitOS's webview permits cleartext HTTP at all —
Android applications can disable it in the manifest, and if this one has, the whole
local architecture has to change.

`spikes/probe.html` is the test. Serve it from the Mac on the LAN, generate an install
QR pointing at `http://<mac-ip>:8080/`, install it on the r1, and look at the screen. It
reports, in order: the page loaded, the fetch succeeded, the websocket opened.

If it fails at the first line, stop and tell Carl. The fallback options are a locally
trusted certificate, or tunnelling, or accepting a relay — all of them are worse and one
of them contradicts the brief, so that is a conversation, not a decision you make.

**Finding, first attempt.** The r1 installer rejects a QR whose `url` is `http://`
("invalid creation code") before the webview loads anything. The community tips confirm
the install URL must be HTTPS. So the install has to go through `spikes/hop.html`, served
over HTTPS from the same GitHub Pages host as the other creations, which then navigates
to `http://<mac-ip>:8080/probe.html`. A top-level navigation from https to http is not
mixed content in a browser, so the hop is where cleartext permission shows itself. If it
lands, the architecture holds with one permanent wrinkle: the install URL carries the
Mac's LAN address, so a changed address means a rescan. If the device stays on the hop
page, the webview refuses cleartext and the conversation above applies.

**Result.** The installer also rejected an https URL with the address in the query
string on a `.html` path; it accepted `…/pad/spikes/hop/?v=1`, the same shape as the
other creations, with the address inside the hop. The hop landed and all three probe
lines passed on the device. Cleartext HTTP and `ws://` work from the r1 webview.
The install URL never needs to change again; the hop decides where it lands.

## 1 — Context on screen

The Mac reports the foreground application; the r1 displays the bundle identifier as
text. No keypad, no actions, no config. Just proof that the loop closes and that
switching applications on the Mac changes what the device shows.

Foreground app via `NSWorkspace.frontmostApplication` through pyobjc, polled a few times
a second.

## 2 — One pad, one key, one keystroke

Hard-code a single pad. Press a key on the r1, get a keystroke on the Mac. Quartz
`CGEvent` is the mechanism.

Accessibility permission attaches to the process that posts the events, which for a bare
Python script means granting it to Terminal. That is acceptable for now. Note it in the
README and leave a `.app` wrapper for later.

## 3 — Config-driven pads

Load `config/keypads.json`. Implement the context resolution order in
`docs/protocol.md`. Pads for Illustrator and for a default. Still key actions only.

## 4 — The drawn interface

Replace the text screen with the real one, from `mockups/pad-mockup.html`. Three pages,
side button pages through, pressed state as fill, unassigned slots drawn.

## 5 — Continuous controls

Tap to hold a control, wheel adjusts, stays held until another is picked. Needs the Mac
to send a starting value, which for Illustrator means the value has to come from
somewhere — probably a scripted read, possibly not available. If it is not, the control
is relative-only and shows the delta rather than a value. Decide with Carl; the mockup
shows an absolute value and may be wrong.

## 6 — Browser tab awareness and http actions

Active tab URL from Chrome via AppleScript. Pads matched on URL. `http` actions calling
Carl's own endpoints. This is where the build stops being a Stream Deck clone.

## Later, unscheduled

Offline face. Edit mode. Shortcut recording on device. A `.app` wrapper and a menu-bar
item. None of these before 6.
