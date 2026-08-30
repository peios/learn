---
title: The Three Processes
description: atriumd, atrium-server and atrium-session — who runs as what, who spawns whom, and why the privilege sits where it does.
---

Atrium is three programs, split so that privilege, network exposure and
user code never share a process.

| Process | Identity | Started by | Role |
|---|---|---|---|
| `atriumd` | SYSTEM | peinit (service `atriumd`) | Originates logons with authd, holds the session table, spawns the other two |
| `atrium-server` | SYSTEM with every privilege deleted | atriumd (fork) | The only network-facing process: TCP :8080, TLS-less HTTP, cookies, forwarding |
| `atrium-session` | The logged-on user | peinit (submitted job) | One per interactive session: serves the shell, holds session state, runs applications |

**atriumd** is deliberately the smallest of the three. It runs as
SYSTEM because originating a logon takes that today — `/run/logon.sock`
admits SYSTEM alone — and everything it does follows from holding that
position: it conducts the PGSS Logon conversation, keeps logon tokens
in its session table, submits session hosts to peinit, and relays the
login exchange for the server. It parses no HTTP and never installs a
token on anyone. If a feature appears to belong in atriumd, it belongs
in one of the other two.

**atrium-server** is forked by atriumd at startup with a copy of
atriumd's own token from which every privilege has been deleted
(`Token::restrict`): the same user SID, so nothing about the
filesystem changes, but nothing a compromised HTTP parser can spend.
It asks the kernel for SIGTERM on parent death, so it cannot outlive
atriumd. It holds exactly the routing view — cookie → session — and
never sees a token.

**atrium-session** is not a child of Atrium at all. On a successful
logon, atriumd submits it to peinit's jobs channel (PSPU §7) with the
freshly minted logon token attached as the job identity — so peinit,
the one process on the machine that installs primary tokens for
others, is its parent, and the job record, cgroup and output capture
come with that. The session host starts with no privilege and needs
none: it *is* the user.

The processes an application starts — an `exec` command, a terminal's
shell — are children of the session host, inside the user's logon
session and the job's cgroup.
