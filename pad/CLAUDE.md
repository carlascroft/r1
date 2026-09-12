# CLAUDE.md — pad.

Read this before touching anything. `docs/brief.md` is the concept, `docs/protocol.md`
is the wire format, `docs/milestones.md` is the build order. Do not skip ahead in the
build order — milestone 0 can invalidate the whole architecture.

`pad.` is a placeholder name. Carl will rename it. Do not invent a name, a tagline, a
logo, or any product lore. If a name is needed in code, use `pad` as the directory and
package name and leave the display string in one place so renaming is one edit.

## What this is

A Rabbit r1 creation plus a Mac-side server that together turn the r1 into a physical
control surface for Carl's desktop. The r1 shows a 3×3 keypad that follows what he's
working in; pressing a key fires a keyboard shortcut, a shell command, or an HTTP call
to one of his own tools.

It is a local reimplementation of the idea behind ZAPAD (getzapad.com), which does the
same thing but relays through a server on the internet. Everything here stays on the
LAN. That is the whole point — do not add a cloud service, an account system, telemetry,
or a hosted relay at any stage, and do not suggest one as a fallback when local
networking is awkward.

## Two halves

- `r1/` — the creation. A single self-hosted page at 240×282 rendered in a Flutter
  webview. Plain HTML/CSS/JS, Canvas 2D only, no build step, no framework, no bundler.
- `mac/` — the host. Python. Serves `r1/` over plain HTTP, reports the foreground app,
  synthesises input, and holds the websocket.

## Hard constraints on the r1 side

These come from the device and have already cost time once. They are not negotiable
and not worth re-testing.

- Canvas 2D only. No WebGL.
- Never `touchstart` with `preventDefault()` — it crashes the webview. Use
  `pointerdown` / `pointerup`.
- Hardware events arrive as window events: `sideClick`, `longPressStart`,
  `longPressEnd`, `scrollUp`, `scrollDown`.
- Persistence is `localStorage` or async `window.creationStorage.plain` (base64).
- Voice, if ever used here, is `CreationVoiceHandler.postMessage('start'|'stop')` with
  the transcript arriving via `onPluginMessage` as `{type:'sttEnded', transcript}`.
- Install is a QR encoding `{title, url, description, iconUrl, themeColor}`.
- Reference: github.com/andr3w-hilton/rabbit-r1-creations-public — `R1_CREATION_TIPS.md`.

Anything you are unsure of about the device SDK, mark in the code with a comment
beginning `VERIFY:` and tell Carl in your summary. Do not guess silently.

## Visual direction

The drawn-grid direction, already established across Carl's other creations. Follow
`mockups/pad-mockup.html` — it is the reference, not a suggestion.

- Black ground. Grid lines drawn in the accent colour and always present.
- Deformation is the present, fill is the state. A pressed key is a filled cell. An
  unassigned slot stays drawn rather than blank.
- Power Grotesk, light weights, to match the rabbitOS interface. Fall back to Inter.
- 1px lines hold up on the panel. Verified on device.
- Pixel glyphs, not icon fonts, not SVG icon sets.
- Sentence case. Lowercase labels. No emoji.
- Accent colour is **undecided** — the mockup uses the orange object family. Put it in
  one CSS custom property and do not scatter literals.

## Working agreement

- Carl is moving his development into Claude Code partly to learn git and GitHub.
  Before any git operation, say in one or two plain sentences what the command does and
  why it is the right one here, then run it. Do not lecture, do not do it silently.
- Build, then let him look at it on the device. He iterates by looking.
- When something is conceptually wrong he will say so directly. Diagnose the cause and
  rebuild that part properly rather than patching around it.
- Do not invent content to fill a gap — no placeholder shortcuts he didn't ask for, no
  fake app catalogue, no sample data presented as real. An empty slot is fine.
- Keep the r1 side dependency-free. The Mac side may use pip packages; list every one
  in `mac/requirements.txt` with a one-line reason in the README.
