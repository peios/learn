---
title: The clock command
type: reference
description: Every verb of the clock command, what each field of its output means, and what its exit statuses tell a script.
related:
  - peios/time/overview
  - peios/time/configuring-sources
---

`clock` reads over timed's socket and prints. It **writes nothing** —
time policy is registry configuration, and `reg` is how a registry value is
set, so there is no second permission model to keep in step with the
first. The one verb that acts is `reload`.

It is called `clock` and not `time` because `time` is a shell keyword:
`time status` would run `status` and report how long it took.

## Verbs

| Command | Reads | Acts |
|---|---|---|
| `clock status` | socket | — |
| `clock sources` | socket | — |
| `clock reload` | — | asks timed to re-read `Machine\System\Time` |

`status` is the default, so bare `clock` is `clock status`.

## Status

```
$ clock status
generation   118
state        synchronised
following    1.time.peios.org (stratum 3)
offset       -412.0us
frequency    -12.750 ppm
jitter       +180.3us
accuracy     within 31.4ms
  root delay      28.2ms
  root dispersion 4.10ms
sources      4 configured, 3 contributing
updates      118 (last 22s ago)
stepped      +2.1d in total since start
floor        1788142329 (the build timestamp; the clock is never set below it)
```

**state** is the field to read first:

| State | Meaning |
|---|---|
| `synchronised` | Normal. |
| `settling` | Being steered, but the frequency estimate is still converging. Usual for the first few minutes after boot. |
| `spike` | A large offset has appeared and is being timed to see whether it is real. The clock is deliberately untouched meanwhile. |
| `unsynchronised` | Nothing is believed and the clock is free-running. |

**accuracy** is the honest bound: how wrong this machine's time might be,
with every uncertainty between here and the reference clock added up. It
is the number a Kerberos deployment cares about, and the number to check
before blaming a clock skew on something else.

**frequency** is what the crystal is doing, in parts per million, and it is
persistent — it is written to `/var/state/timed/drift` and read back at the
next boot. Tens of ppm is an ordinary machine. Approaching ±500 means the
hardware is at the edge of what the discipline can correct.

**stepped** is non-zero after a boot on a machine whose clock was wrong,
which is normal. It growing *later* is not, and means something is
repeatedly moving the clock.

**floor** is the build timestamp. If the machine's clock reads exactly
this, nothing has told it the real time yet and it is sitting on the floor
so that TLS can work — see [the overview](~peios/time/overview).

## Sources

```
$ clock sources
  source                   state        auth   str reach     offset     delay     last
* 1.time.peios.org         system-peer  nts      2   377   -0.918ms   22.7ms       44s
+ 0.time.peios.org         candidate    nts      3   377   -1.204ms   14.2ms       31s
- 3.time.peios.org         outlier      nts      2   377   +8.221ms   61.0ms       58s
x 2.time.peios.org         falseticker  nts      2   377   +4.102s    18.1ms       12s

* system peer  + candidate  - outlier  x falseticker  ? unusable
```

| Mark | State | Meaning |
|---|---|---|
| `*` | `system-peer` | Chosen. The machine takes its stratum and root figures from this one. |
| `+` | `candidate` | Agrees with the majority and contributes to the combined answer. |
| `-` | `outlier` | Agrees, but too noisy to be worth including. |
| `x` | `falseticker` | **Disagrees with the majority.** Go and look at this one. |
| `?` | `unusable` | Answering, but saying it is not synchronised itself. |
| ` ` | `unreachable` | Not answering. |

**auth** is `nts` or `none`. `none` means anyone on the path can forge that
source's replies.

**reach** is the last eight polls as an octal bitmask, newest in the low
bit — the classic NTP display. `377` is eight for eight; `376` means the
poll before last was missed; `0` means nothing for eight polls, at which
point the source's stored measurements are discarded rather than left to
vote with stale numbers.

**last** is how long ago the source answered. It exceeding the poll
interval by much is the first sign of trouble.

A source that is not contributing prints a note underneath saying why.

## Exit statuses

| Status | Meaning |
|---|---|
| `0` | Done. |
| `2` | Asked about something that is not there — no sources are configured. |
| `1` | It went wrong: timed is unreachable, or refused. |
| `64` | The command line was not understood. |

The separation of `2` from `1` is what lets a script tell "this machine has
no time sources" from "I could not find out".

## When reload is refused

```
$ clock reload
clock: not permitted
```

`reload` needs the control right on timed's control object. Reading does
not: what time the machine thinks it is, and how well it knows, is not a
secret, and a program deciding whether the clock is trustworthy enough to
validate a certificate should not need a privilege to find out.

The descriptor is `Machine\System\Time ControlSecurity`; by default SYSTEM
and Administrators may control, and everybody may query.
