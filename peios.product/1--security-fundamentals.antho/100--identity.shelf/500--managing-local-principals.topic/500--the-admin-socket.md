---
title: The administrative socket
type: reference
description: The socket lps talks to lpsd over — where it is, who may use it, and what decides that. Useful if you are writing tooling against it or diagnosing a refusal.
related:
  - peios/managing-local-principals/lps-command
  - peios/managing-local-principals/overview
  - peios/security-descriptors/overview
  - peios/tokens/overview
---

`lpsd` listens on:

```
/run/lpsd/admin.sock
```

`lps` is its only client today. If you are writing tooling against it, or diagnosing why a command was refused, this page is what you need.

## Who may use it

Two ways to satisfy the check, and `lpsd` reads the connecting process's **token** to decide:

- membership of `BUILTIN\Administrators`, **enabled**; or
- being `LocalSystem`.

`LocalSystem` is admitted deliberately rather than as a convenience. At first boot there is no administrator yet — that is the problem the bootstrap service exists to solve, and it runs as `LocalSystem`.

The word *enabled* is load-bearing. A group that is present in a token but marked deny-only contributes to denials and grants nothing, so `lpsd` requires the enabled attribute. A deliberately restricted token that merely mentions `Administrators` does not qualify.

## What decides, and what does not

**The peer's token decides.** `lpsd` asks the kernel who is on the other end of the connection. Nothing in any message contributes to that answer, and nothing a client sends could.

**A KACS descriptor is defence in depth.** `lpsd` stamps one on its runtime directory and socket, admitting `LocalSystem` and `BUILTIN\Administrators`.

That descriptor is load-bearing in a way worth knowing about: `/run` is seeded with a descriptor admitting `LocalSystem` alone, and everything created under it inherits that. Without `lpsd` stamping its own, an administrator running `lps` would be refused by KACS before a byte was exchanged.

**The Unix mode decides nothing.** KACS grants every managed process the capabilities that override the DAC check, so file modes do not gate anything on Peios. The socket's mode is permissive to say so rather than to imply a control that is not operating.

> [!TIP]
> If you see `permission denied` from `lps`, it is a KACS refusal, not a Unix one. Check the descriptor on `/run/lpsd/admin.sock` with `sd show`, and check your token's groups with `token`.

## Shape of the protocol

One request per connection: `lps` connects, sends one request, reads one answer, and disconnects. There is no session and no state carried between commands.

That is partly the shape of the tool — a command does one thing and exits — and partly a bound on a real hazard. `lpsd` serves administrative requests on the same thread as logons, so a client that connected and then said nothing would stall every logon behind it. One request under a deadline bounds that.

The authorization check happens **before** anything is read, so an unauthorised connection costs a token read and a refusal rather than the full timeout. An open socket cannot be used to stall logons.

## Durability

A change is applied in memory, **written to disk, and only then reported as done**. If the write fails the change is rolled back and the command reports failure.

So a command that reports success has persisted. A command that reports failure changed nothing — not "possibly changed something", but nothing: `lpsd` keeps a snapshot and restores it.

## The protocol itself

The wire protocol is `PLPS`, sharing its codec and header layout with PGSS Logon ([PGSS §2](~peios/logon/scope-and-roles)) and PSI ([PSPU §2](~peios/principal-source-interface/scope-and-roles)). It is not itself specified, because unlike those two it is one daemon's administrative interface rather than a contract anyone else implements.

If you are writing tooling, prefer driving `lps` and parsing its output over speaking the protocol directly. The command's surface is stable; the protocol's is not promised to be.

## See also

- [The `lps` command](~peios/managing-local-principals/lps-command) — the client this socket serves.
- [Managing local principals](~peios/managing-local-principals/overview) — the authority/source split behind the design.
