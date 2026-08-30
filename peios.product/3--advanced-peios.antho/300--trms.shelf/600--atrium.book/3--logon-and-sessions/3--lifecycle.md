---
title: Lifecycle
description: What ends a session, what merely detaches a browser, and how a shell that has lost its session finds its way home.
---

A browser closing changes nothing on the machine. The interactive
session keeps running; the browser's cookie still names it; returning
to the page resumes the same desktop. Detachment is free.

What ends an interactive session:

| Event | Path |
|---|---|
| Logout | The server drops the cookie and session link, tells atriumd, and atriumd stops the peinit job |
| The session host exits | atriumd's pidfd poll notices; the token is dropped, which releases the logon session |
| atriumd exits | atrium-server dies with it (parent-death signal); session hosts see their control socket close and exit |
| The machine reboots | Everything above |

The logon token is held by atriumd for the session's life and dropped
when the session ends; dropping the last token reference is what
retires the kernel's logon session.

On the browser side, the shell treats its websocket as expendable.
Requests made while the socket is connecting are queued and flushed on
open, so a click during the first half-second is not lost. Reconnection
backs off from 300 ms to 3 s, retries immediately when the tab regains
focus or the network returns, and every third failure asks
`/api/whoami` over plain HTTP whether the session still exists — a
stale cookie (the machine rebooted; the session was logged out
elsewhere) answers with a redirect, and the shell reloads onto the
login page rather than retrying a socket that can never connect.
