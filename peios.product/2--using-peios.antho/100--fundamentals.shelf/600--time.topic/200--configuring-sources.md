---
title: Configuring time sources
type: how-to
description: Point a machine at your own time servers, decide what it may believe, and understand what turning authentication off actually costs.
related:
  - peios/time/overview
  - peios/time/the-clock-command
  - peios/registry-administration/regman
---

Everything about where a machine gets its time is under
`Machine\System\Time`. There is no configuration file, and `clock` writes
nothing — `reg` is how it is changed, so the key's own security descriptor
is the only gate.

## Naming your own servers

```
$ reg set Machine/System/Time Servers multi:'dc01.corp.example' \
                                            'dc02.corp.example' \
                                            'ntp3.corp.example'
$ clock reload
```

Each entry is a host, optionally `host:port`, optionally followed by
option words:

| Option | Meaning |
|---|---|
| `prefer` | Lead with this one when several agree. |
| `unauthenticated` (or `noauth`) | This source speaks plain NTP, not NTS. |

`prefer` breaks ties and nothing more. A preferred source that disagrees
with the majority is still discarded — a preference is a statement about
which server to lean on, not a licence to be wrong.

A misspelled option is an error and the entry is ignored with a warning in
the log, rather than silently doing nothing. `clock sources` will show the
entry missing.

> [!IMPORTANT]
> **Name at least three.** One source is believed because there is nothing
> to check it against. Two that disagree cannot be told apart, and the
> machine will report itself unsynchronised rather than pick one. Three is
> where a wrong server starts being outvoted instead of believed.

### Precedence is first match, not merge

```
Servers  →  the domain  →  DHCP, if enabled  →  the shipped fallback set
```

The first of those that names anything is the *whole* list. Setting
`Servers` does not add to the fallback set, it replaces it — a machine
told exactly which servers to use should not also be quietly talking to
somebody else's.

To go back to the shipped default, delete the value:

```
$ reg del Machine/System/Time Servers
$ clock reload
```

## Turning authentication off

`AllowUnauthenticated` is `0` by default: a source must prove who it is or
it is not used.

```
$ reg set Machine/System/Time AllowUnauthenticated dword:1
$ reg set Machine/System/Time Servers multi:'ntp.lan unauthenticated'
$ clock reload
```

Both are needed. The per-source word says which sources are plain, and the
machine-wide value says whether that is permitted at all — so setting
`AllowUnauthenticated` back to `0` really does turn everything off, rather
than leaving per-source exceptions behind.

What you give up is worth being clear about. Without NTS, the only thing
standing between you and a forged reply is that the server must echo the
exact 64 bits timed put in its request — a random number, so an attacker
who cannot *see* the request cannot guess it. An attacker who can see it
can forge freely and move your clock wherever they like.

The reason to think twice is that a wrong clock is not a self-contained
problem: certificate validity, Kerberos, and the ordering of your logs all
rest on it.

Reasonable uses: an isolated network with its own stratum-1 appliance; a
lab; a machine behind a firewall that blocks port 4460 where you control
the path anyway.

## DHCP time servers

`UseFromDHCP` is `0` by default, as on Windows.

```
$ reg set Machine/System/Time UseFromDHCP dword:1
```

They are used only when `Servers` is absent, and only without
authentication. Off by default because on a network you do not control the
DHCP server's idea of the time is the attacker's idea of the time — and
turning this on is a statement that you trust every network this machine
will ever join. That is a reasonable statement for a machine that only
ever attaches to one you run.

## Poll intervals

```
MinPoll   default 6    64 seconds
MaxPoll   default 10   about 17 minutes
```

Both are powers of two seconds, and both are clamped to the range 4 to 17.
timed lengthens the interval towards `MaxPoll` while the clock is being
held steadily and shortens it when the offset starts moving.

There is rarely a reason to change either. Lowering `MinPoll` makes
recovery from a disturbance faster and costs the servers more traffic; a
long interval measures the crystal's *rate* better than a short one
measures its phase, and it is the rate estimate that holds the clock right
between polls anyway.

The floor of 4 is not negotiable. A configuration error must not be able
to turn a machine into a nuisance at somebody else's public server.

## Doing it from a domain

Every value here is an ordinary registry write, so distributing time
policy to a fleet is an ordinary policy push. There is no separate
mechanism and nothing timed-specific to learn.

## When something is wrong

```
$ clock sources
  source                   state        auth   str reach     offset     delay     last
* 0.time.peios.org         system-peer  nts      3   377   -1.204ms   14.2ms       31s
+ 1.time.peios.org         candidate    nts      2   377   -0.918ms   22.7ms       44s
x 2.time.peios.org         falseticker  nts      2   377   +4.102s    18.1ms       12s
  3.time.peios.org         unreachable  nts     16     0       +0ns       0ns         -
    NTS-KE failed: connecting to 192.0.2.9:4460: Connection refused
```

- `falseticker` — this server disagrees with the others. It is the one to
  go and look at, and the single most useful thing a time client can tell
  you.
- `unreachable` — no reply for eight polls. The note says why.
- `reach` is the last eight polls in octal: `377` is eight for eight, and
  anything else says how recently one was missed.
