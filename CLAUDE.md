# CLAUDE.md — r1 creations

Custom creations for the rabbit r1, part of the Plotville practice. Each creation
is a self-contained webpage rendered in the r1's webview. Design language: the
"drawn direction" — a physical grid of coloured lines on black.

## Repo layout

- One folder per creation: `index.html` (the app) + `install.html` (QR install page).
- Everything is vanilla HTML/CSS/JS in a single file per app. No build step, no
  frameworks, no bundler. Keep it that way.
- `podcast/worker.js` is a Cloudflare Worker (CORS proxy for RSS + iTunes search).
  It is deployed by pasting into the Cloudflare dashboard, not served by Pages.

## Deployment

- Hosting: Cloudflare Pages, auto-deploys from this repo on every push to main.
  Pushing IS deploying. The r1 fetches `index.html` fresh on every open, so code
  changes reach the device on next open — no reinstall.
- Only the install URL is cached by the device. Bump `?v=N` in an app's
  `install.html` and rescan the QR only when the install payload itself changes.
- `install.html` QR payload is JSON: `{title, url, description, iconUrl, themeColor}`.
  `themeColor` is the card colour in the r1 stack.

## r1 hardware constraints (hard rules — violating these breaks on device)

- Screen is exactly 240×282 px. Viewport meta: `width=240, initial-scale=1.0, user-scalable=no`.
  `body { width:240px; height:282px; overflow:hidden; }`.
- Canvas 2D only. NO WebGL (Flutter webview doesn't support it).
- NEVER use `touchstart`/`touchend` with `preventDefault()` — crashes the webview.
  Use `pointerdown`/`pointerup` with no preventDefault.
- No `onclick` in innerHTML strings — always `addEventListener`.
- Native events on `window`: `sideClick`, `longPressStart`, `longPressEnd`,
  `scrollUp`, `scrollDown`. Double side-click fires two sideClick ~50ms apart.
- Voice: `CreationVoiceHandler.postMessage('start')` / `('stop')`; transcript
  arrives at `window.onPluginMessage` as `{type:'sttEnded', transcript}`.
- Storage: `localStorage` for simple data; `window.creationStorage.plain`
  (async, base64-encode values) for data that must survive reinstall.
- LLM bridge exists: `PluginMessageHandler.postMessage(JSON.stringify({message, useLLM,
  wantsR1Response, wantsJournalEntry}))`; response via `onPluginMessage` (`data.data` JSON
  string or `data.message`).
- Exit: `closeWebView.postMessage("")`.
- Hardware is weak: cap rendering ~30fps, sleep the physics when the fabric settles,
  avoid heavy per-frame allocation.
- Reference (running log of gotchas): github.com/andr3w-hilton/rabbit-r1-creations-public
  → R1_CREATION_TIPS.md.

## Design system — the drawn direction

- The grid IS the display: 1px lines of one colour on black (#000), 12px pitch,
  field margins 12px, foot caption strip at the bottom (11px, lowercase).
- The fabric is a damped spring grid (see any existing index.html for the engine).
  Constitution: **deformation is the present; fill is the state; completed things
  become marks that outlive the fabric** (persisted, lime).
- Nothing steps or eases on a schedule — motion is physical: impulses, plucks,
  agitation, targets. The fabric never resets; it recovers in seconds.
- Colour families: cyan #2EF0FF time · orange #E26422 the object · pink #FF2E9E
  ledgers · lime #D6FF2E feed + marks/completion · violet #C9A6FF media ·
  paper #F2F2EE tools. Background always black.
- Type: Power Grotesk, light (300) large / regular (400) small, lowercase, no bold.
  Font files are optional (`fonts/` beside each index.html); system sans fallback
  is acceptable and expected.
- Interaction grammar: scroll = choose/seek (a fold in the fabric) · tap = open /
  commit / play-pause / literal reading (2s overlay) · hold = sustained pressure
  (record, queue, snip, reset — destructive holds are armed: first hold warns in
  the caption, second confirms) · side button = back/home.
- Sound: bent sine tones (WebAudio), created lazily on first gesture; UI tones go
  silent while media plays.
- Copy is lowercase, dry, short. Naming of creations is Carl's — leave placeholder
  titles in install.html for him to set; never invent lore, provenance, or specifics.

## Working conventions

- Test in a desktop browser first: every app has keyboard fallbacks
  (arrows = scroll, Enter/click = tap, space = hold, Escape = side button).
- When changing an app, keep it a single self-contained index.html.
- Headless-test pure logic (parsers, timers, state machines) with node where practical.

## Git tutoring

Carl is using this project to learn git and GitHub. When running git commands:
explain what each command does and why, in one or two plain sentences, before
running it. Prefer small, frequent commits with clear messages. Introduce concepts
(status, diff, log, branches, reverting) as they naturally arise rather than all
at once. Never force-push.
