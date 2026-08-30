---
title: The Mirror
description: One websocket per tab; a snapshot, then events; requests in, broadcasts out. The session owns the state and every tab agrees.
---

Each browser tab's shell opens one websocket to its session host at
`/ws` (forwarded by atrium-server like any other connection). The
session sends a **snapshot** — the window list, the focus, the chord
table — and from then on **events**; the shell sends **requests**.

State flows one way. A shell never changes anything locally: clicking
a tile sends `launch`, and the tab that asked learns of the resulting
window the same way every other tab does, from the broadcast. That is
what makes two tabs agree without trying: there is nothing to
reconcile, because nothing but the session ever decides.

The session pushes facts, not markup. An event names what changed —
`window.opened`, `focus`, `window.closed`, `window.minimized`,
`window.titled` — and each shell works out the DOM consequences. The
constraint behind this is the iframe: a window's frame is a live
application, and re-parenting or re-rendering it reloads the app, so
frames are created once and only ever shown or hidden.

Requests that fail — an unknown app, a closed window — produce an
`error` message to the asking tab alone. Errors are not state, and no
other mirror hears them. The same routing carries application
request/reply traffic (§5.4): replies and streams go only to the tab
whose frame asked.

Window ids are minted by the session. Titles are session state too —
an application renaming its window (§5.3) changes every mirror's
sidebar at once.

The websocket implementation in the session host is a deliberately
small subset of RFC 6455: text, close and ping frames, client masking
required, no fragmentation or extensions. Every write to one
connection is serialised through one lock — a pong interleaving with a
broadcast mid-frame would corrupt the stream, and did, once.
