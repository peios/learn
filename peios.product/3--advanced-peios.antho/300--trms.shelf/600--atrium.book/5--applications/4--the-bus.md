---
title: The Bus
description: postMessage to the shell, an envelope the shell stamps, and replies that return to exactly the frame that asked.
---

An application frame holds no socket and no cookie. Its one channel is
`postMessage` to the parent shell — the only browser mechanism that
survives every isolation boundary Atrium may later put around a frame
(foreign origins, sandboxed frames with an opaque origin). The path of
a request:

```
app frame → postMessage → shell → websocket → session host
```

The shell identifies the sending frame by its `contentWindow` and
stamps the window id onto the relayed message. An application cannot
name its window and therefore cannot speak as another; the session
never authenticates applications, because the shell has already
vouched for which window is talking and the session knows which
application owns that window.

Replies and streams route the same way in reverse — to the one tab
whose frame asked, then by `postMessage` into that frame — correlated
by a request id the SDK mints per call.

The bus is a control plane. A round trip costs postMessage in and out
plus the websocket, which is invisible next to the network for
anything a human triggers, and measured throughput is comfortable for
terminal-scale streaming. The recorded posture is *control on the
bus, bytes on a channel*: an application that ever ships sustained
bulk data gets a dedicated channel then, authenticated by a
per-window token handed over the bus — machinery that exists as a
design, not in this version, because nothing has needed it.
