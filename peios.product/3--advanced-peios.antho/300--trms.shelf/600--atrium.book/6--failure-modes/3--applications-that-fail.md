---
title: Applications That Fail
description: Broken manifests, refused capabilities, dead commands and dead terminals — each failure names itself.
---

**A missing tile.** An application that should be in the Toolbox and
is not has a manifest problem: unparsable TOML, or an `id` that does
not match its directory. Both are skipped with a line on the session
host's log naming the file.

**A capability refusal.** An `exec` for a program outside the
allowlist, or a `pty-open` without `pty = true`, is answered with an
error naming the application, the request and the manifest —
delivered to the asking frame, where the SDK rejects the promise. The
declarative layer prints it into the target element; the Terminal
shows it in place of the "shell exited" banner.

**A command that dies or floods.** exec's reply distinguishes an exit
code, a signal, and `truncated: true` — the last meaning the session
killed it at the output cap or the timeout, and the record of which
is on the session log. Output already streamed stays streamed.

**A terminal that exits instantly** is the shell exiting, and the
banner carries the refusal when there was one instead of an exit. A
pseudo-terminal that cannot be opened at all reads as `openpty`
failing in the message; on Peios that has one historical cause worth
knowing — a devpts mount without its synthesised-SD policy, under
which every slave is unopenable (peinit TRM §2.3).

**One tab wrong, others right** points at the mirror rather than the
session: the state is per-session, but delivery is per-tab. A reload
of the odd tab resynchronises it from the snapshot; the console's
websocket log says what it missed.
