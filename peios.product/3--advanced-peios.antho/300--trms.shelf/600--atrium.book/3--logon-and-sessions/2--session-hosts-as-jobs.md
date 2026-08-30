---
title: Session Hosts as Jobs
description: A session host is a peinit job submitted with the logon token as its identity — Atrium never forks as anyone but itself.
---

On a successful logon, atriumd submits one job to
`/run/services/peinit/jobs.sock` (PSPU §7):

- **Identity**: the logon token authd just minted, attached to the
  submission as a `KACS_SCM_TOKEN`. The kernel gates the attach and
  peinit duplicates the token to the job's primary — atriumd holds the
  token but never installs it, on itself or anyone.
- **Program**: `/usr/libexec/atrium/atrium-session`, no arguments.
- **Descriptors**: the session's control socket, named
  `atrium-control`, which peinit places on descriptor 3.
- **Environment**: `HOME`, `USER`, `LOGNAME`, `PATH`, `SHELL` (from
  the logon profile; `/bin/sh` when the profile names none), plus
  `ATRIUM_SESSION` (the logon session id) and `ATRIUM_DISPLAY_NAME`.
  The working directory is the profile's home when that directory
  exists, `/` otherwise — a missing home starts a session rather than
  failing one.
- **Stop**: `stop_timeout` of 10 seconds.

The response carries the job's pidfd, which joins atriumd's poll loop;
a session host's death is noticed there, and the cause is read back
from peinit's job record while it is retained. Logging out sends the
jobs channel a `stop` — SIGTERM, then peinit's kill after the stop
timeout, cgroup-wide.

A jobs-channel connection is opened per operation and dropped: peinit
closes idle jobs connections, and a logon is rare enough that a kept
connection would be found dead exactly when it was next needed.

Because peinit is the parent, session hosts survive an atriumd
restart as processes — but atriumd's table and the server's cookies do
not, so a restarted Atrium does not know them and users log in afresh.
Reattachment through peinit's job listing is possible machinery that
this version does not have.
