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
cd spikes
python3 -m http.server 8080 --bind 0.0.0.0
```

Find the Mac's LAN address (`ipconfig getifaddr en0`), build an install QR pointing at
`http://<that-address>:8080/probe.html`, install it on the r1, and read the three lines
on screen. The websocket line is expected to fail at this stage — there is no socket
server yet. The first two lines are the ones that matter.

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
