# Protocol — proposal, not settled

This is a starting shape. Change it if the build argues for something better, but change
it deliberately and say so in the commit message.

## Transport

One websocket, r1 → Mac, opened on load and reopened on drop with a backoff. The Mac
serves the creation over plain HTTP from the same origin, so the page and the socket
share scheme and host and no mixed-content rule applies.

    http://<mac-lan-ip>:8080/        the creation
    ws://<mac-lan-ip>:8080/ws        the socket

The Mac binds to the LAN interface, not `127.0.0.1`. It is on a home or studio network,
behind a router, and there is no authentication in the first version. If Carl wants a
pairing code later it goes on top of this, not into it.

## Messages: Mac → r1

Sent on connect and whenever the value changes. The r1 holds no truth of its own beyond
which page it is showing and which continuous control is held.

    {"t":"context", "app":"com.adobe.illustrator", "name":"Adobe Illustrator", "title":"schlep.svg", "url":null}
    {"t":"context", "app":"com.google.Chrome", "name":"Google Chrome", "title":"schlep.", "url":"http://localhost:5173/schlep"}

`name` is the application's own display name, for the device to show while no pad
matches. `title` and `url` are null until the milestones that read them.

    {"t":"pad", "id":"illustrator", "label":"illustrator", "pages":[ ...see config... ]}

    {"t":"value", "control":"stroke-weight", "value":0.35, "unit":"pt"}

    {"t":"status", "state":"linked"}
    {"t":"status", "state":"offline", "reason":"accessibility permission not granted"}

Status reasons are shown to Carl on the device. Write them as a plain statement of what
is wrong, never an apology and never a raw exception string.

## Messages: r1 → Mac

    {"t":"press", "pad":"illustrator", "page":0, "slot":4}
    {"t":"hold",  "pad":"illustrator", "page":0, "slot":4}
    {"t":"select","control":"stroke-weight"}
    {"t":"turn",  "control":"stroke-weight", "delta":1}
    {"t":"release"}

`delta` is ±1 per wheel detent. Acceleration, if any, is decided on the Mac so the r1
stays a dumb surface.

## Context resolution

The Mac decides which pad applies, in this order:

1. If the foreground app is a browser and the active tab URL matches a `match` pattern
   in a pad, use that pad.
2. Otherwise if a pad's `app` matches the foreground bundle identifier, use that pad.
3. Otherwise send the pad with `"id": "default"`.

The r1 never decides. It draws what it is told.

## Actions

A slot's action is resolved and executed entirely on the Mac. Three kinds:

- `key` — a synthesised keystroke. Modifiers plus a key.
- `shell` — a command, run without a shell where possible.
- `http` — a request to one of Carl's own endpoints.

`http` is the one that matters. It is what makes a key on this pad different from a key
on a keyboard, and it is how `send.` and `proof.` get a real console.

## Rate and safety

- Debounce wheel input on the Mac at the same 120 ms used elsewhere in the tooling if it
  proves necessary. Start without it and measure.
- No action fires on connect, on pad change, or on reconnect. Only on an explicit press.
- Log every executed action to stdout with a timestamp. Carl will want to see what the
  pad actually did when something surprising happens.
