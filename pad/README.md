# pad.

A Rabbit r1 creation and a Mac-side host that together make the r1 a physical control
surface for the desktop. Everything runs on the local network.

Name is a placeholder.

## Read in this order

| | |
|---|---|
| `CLAUDE.md` | constraints, device rules, working agreement — read every session |
| `docs/brief.md` | what this is and why it isn't the off-the-shelf version |
| `docs/protocol.md` | proposed wire format between the two halves |
| `docs/milestones.md` | build order, starting with a spike that can invalidate everything |
| `docs/open-questions.md` | decisions that are Carl's, not Claude's |
| `config/keypads.example.json` | the shape of a pad |
| `mockups/pad-mockup.html` | the interface reference — open in a browser |
| `spikes/probe.html` | milestone 0 |

## Start here

Milestone 0 passed: the r1 webview loads a page and opens a websocket over plain HTTP
on the LAN. The wrinkle is the installer, which only accepts an `https://` URL, so the
install points at `spikes/hop/` on GitHub Pages (deployed from `main`), which navigates
straight on to the Mac. The Mac's address is one constant in `spikes/hop/index.html`.

```
pip3 install -r mac/requirements.txt
python3 mac/serve.py
```

That serves `r1/` on port 8080, prints the Mac's LAN address, answers the websocket at
`/ws`, and reports what is in front. The probe stays at `/spikes/probe.html`. Open the
`install.html` address it prints in a browser on the Mac and scan the QR with the r1
camera; one install serves every milestone. The host logs every request and every
change of foreground app.

`mac/requirements.txt`, one line each:

- `pyobjc-framework-Cocoa` — `NSWorkspace`, which app is in front.
- `pyobjc-framework-Quartz` — `CGEvent`, the synthesised keystrokes.
- `pyobjc-framework-ApplicationServices` — `AXIsProcessTrusted`, whether this process
  may post them.

The first press asks macOS for Accessibility permission for whatever launched
`python3` (Terminal, usually). Until it is granted the device says so in its bottom
band and presses are logged but nothing happens on the Mac.

## Repo layout once building starts

```
r1/       the creation — plain HTML/CSS/JS, no build step
mac/      the host — python, serves r1/ and holds the socket
config/   keypads.json, hand-authored and versioned
docs/     the documents above
mockups/  interface reference
spikes/   throwaway tests
```

`config/keypads.json` is the live file. `keypads.example.json` stays as the documented
shape.

## Known cost

The host synthesises keyboard input, so macOS requires Accessibility permission for
whichever process posts the events. Running the host as a bare Python script means
granting that to Terminal, which is coarse. Wrapping it as a `.app` fixes it and is
deliberately left until after milestone 6.
