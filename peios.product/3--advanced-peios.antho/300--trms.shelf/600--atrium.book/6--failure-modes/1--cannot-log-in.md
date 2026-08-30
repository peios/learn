---
title: Cannot Log In
description: Where a failed browser logon actually failed — the authority, the session job, or the network path — and what each looks like.
---

A browser logon crosses four systems, and the error surface says which
one refused.

**"Incorrect username or password"** is authd refusing the
credentials — the uniform rendering of every retryable denial. The
specific denial is on atriumd's log (kmsg-mirrored, so the serial
console has it).

**"Could not start a session"** means the logon succeeded but the
session host did not start: atriumd's job submission failed. atriumd's
log carries peinit's refusal — `BAD_TOKEN`, a jobs-socket error, or a
failed launch, with the job's cause when one was created. The logon
token is dropped on this path, so nothing lingers.

**"Session host unavailable"** on the login page means atrium-server
could not reach atriumd at all — atriumd is down or restarting, and
peinit's view of the `atriumd` service is the place to look.

**Nothing loads at all**: nothing is listening on 8080 (the service
is down), or the network path is wrong — on a QEMU dev image the port
is user-mode-NAT forwarded and reachable only through the host's
forward, not the guest address.

A logon that succeeds but lands on a desktop that immediately bounces
back to the login page is a session that died at birth: the pidfd
noticed the host exit before the first request arrived. peinit's job
record holds the exit.
