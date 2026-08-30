---
title: The Shell Loses the Session
description: What a dropped websocket looks like, what the shell does about it by itself, and when it gives up and reloads.
---

The shell's websocket drops for ordinary reasons — the machine
rebooted, the laptop slept, the service restarted — and the shell is
built to make most of them invisible.

While disconnected, requests queue rather than drop; the browser
console notes each (`session: queued until connected`). Reconnection
backs off 300 ms → 3 s, and a tab regaining focus or the network
coming back retries immediately. Each websocket close is logged to
the console with its code, which is the first thing worth reading
when a shell seems dead.

Every third failed attempt, the shell asks `/api/whoami` whether the
session behind its cookie still exists. A redirect answer means it
does not — the machine rebooted, or the session was ended elsewhere —
and the shell reloads, landing on the login page. Without that check
a tab surviving a reboot would retry its websocket forever, since its
cookie can never bind again.

What is lost across an interactive session's death is the session:
open windows, terminals and their processes. What is never lost is
anything the browser held alone, because the browser holds nothing
alone.

If windows open but an application's frame stays blank past the
handshake grace, the failure is inside the frame — its console (the
browser's, for that frame) has the SDK's report, and the session
host's log has the serving side.
