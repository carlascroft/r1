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

Milestone 0 tests whether the r1's webview will load a page over plain HTTP from the
LAN. If it will not, the local architecture does not work and the plan changes before
any code is written.

```
python3 mac/serve.py
```

That serves `spikes/` on port 8080, prints the Mac's LAN address, and answers the
websocket at `/ws`, so all three lines on the probe can pass. Open the `install.html`
address it prints in a browser on the Mac, scan the QR with the r1 camera, open the
creation on the device, and read the three lines on screen. The host logs every
request, so the terminal shows what the device managed to reach even if the screen
does not.

The host is standard library only; nothing to install for the spike.

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
