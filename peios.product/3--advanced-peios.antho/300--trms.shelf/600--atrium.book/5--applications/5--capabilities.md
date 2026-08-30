---
title: Capabilities
description: The manifest's [capabilities] table — exec's allowlist, limits and streams, and pty's terminal — checked by the session at request time.
---

An application's manifest declares what it may ask the session to do.
The session host reads the manifest from disk at each request — the
installed manifest is the truth, and there is no registration to go
stale. An application with no `[capabilities]` table can render, talk
on the bus, and nothing else.

## exec

```toml
[capabilities]
exec = ["peipkg", "svctl"]
```

`{ kind: "exec", cmd: [argv…] }` runs a program as the user. The
first argv element is matched against the list — `"*"` allows any
program — and a refusal names the application, the program and the
manifest, so a denial reads as an explanation rather than a mystery.

No shell is involved: argv is executed as given, in the user's home,
with the session's environment. Output streams back as it happens,
stdout and stderr separately labelled; the final reply carries the
exit code or signal. Two limits protect the session: one megabyte of
streamed output and five minutes of runtime, past either of which the
process is killed and the reply says `truncated`.

## pty

```toml
[capabilities]
pty = true
```

`{ kind: "pty-open", cols, rows }` opens a pseudo-terminal running
the user's `$SHELL` as a session leader with the slave as its
controlling terminal, `TERM=xterm-256color`. Output streams like
exec's; input and window sizes travel as fire-and-forget
`pty-input` / `pty-resize` messages naming the opening request; the
opening request's reply arrives when the shell exits. Closing the
window hangs up the terminal's whole process group.

Capabilities narrow what may be *asked*; identity never changes.
Everything either capability runs is the user, in the session's
process tree, indistinguishable from work the user did at a console —
which is also why the model is honest: an application granted
`exec = ["*"]` has been granted the user, and a manifest is the place
that grant is visible.
