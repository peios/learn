---
title: Constants and Paths
description: Ports, sockets, filesystem locations, environment, and limits, in one place.
---

## Network and sockets

| What | Value |
|---|---|
| Listener | TCP `0.0.0.0:8080`, plain HTTP (atrium-server) |
| Mirror websocket | `GET /ws` on the same origin |
| Control descriptors | Descriptor 3 in atrium-server and atrium-session |
| Logon authority | `/run/logon.sock` (client) |
| Jobs channel | `/run/services/peinit/jobs.sock` (client, one connection per operation) |

## Filesystem

| What | Where |
|---|---|
| Binaries | `/usr/sbin/atriumd`, `/usr/libexec/atrium/atrium-server`, `/usr/libexec/atrium/atrium-session` |
| Applications | `/usr/share/atrium/apps/<id>/manifest.toml` |
| Service definition | `/usr/share/regim/atriumd-service.reg` (applied by an image's autoapply) |
| Shell assets | Served at `/shell/…`: `shell.js`, `shell.css`, `icons.js`, `sdk.js`, `tokens.css` — compiled into atrium-session |

## Session host environment

`HOME`, `USER`, `LOGNAME`, `PATH`, `SHELL`, `ATRIUM_SESSION` (logon
session id), `ATRIUM_DISPLAY_NAME`. Applications' exec children
inherit the session host's environment.

## Limits and defaults

| What | Value |
|---|---|
| Cookie | 256-bit random, `HttpOnly`, `SameSite=Strict` |
| exec output cap | 1 MiB, then kill + `truncated` |
| exec runtime cap | 300 s |
| Frame handshake grace | 1.2 s |
| Websocket reconnect | 300 ms × failures, capped 3 s; liveness check each 3rd failure |
| Session job stop timeout | 10 s |
| Window title cap | 120 characters |
| pty terminal type | `xterm-256color` |

## Development overrides

`ATRIUM_LISTEN`, `ATRIUM_APPS_DIR`, `ATRIUM_SERVER`, `ATRIUM_SESSION`
(binary path), `ATRIUM_JOBS_SOCKET`; `atriumd --unrestricted` runs
the whole stack under one identity on a KACS-less host. The `atrium`
source tree's `tools/dev/` holds the fake-atriumd harness and browser
drivers these serve.
