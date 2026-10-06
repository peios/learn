---
title: The administrative socket
type: reference
description: The socket lps talks to lpsd over — where it is, who may use it, and what decides that — and the self socket on which any principal reads their own account and sets their display name. Useful if you are writing tooling against them or diagnosing a refusal.
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

`lps` and [Principals Manager](~peios/managing-local-principals/principals-manager) are its clients. If you are writing tooling against it, or diagnosing why a command was refused, this page is what you need.

## Who may use it

Two ways to satisfy the check, and `lpsd` reads the connecting process's **token** to decide:

- membership of `BUILTIN\Administrators`, **enabled**; or
- being `LocalSystem`.

`LocalSystem` is admitted deliberately rather than as a convenience. At first boot there is no administrator yet — that is the problem the bootstrap service exists to solve, and it runs as `LocalSystem`.

The word *enabled* is load-bearing. A group that is present in a token but marked deny-only contributes to denials and grants nothing, so `lpsd` requires the enabled attribute. A deliberately restricted token that merely mentions `Administrators` does not qualify.

## What decides, and what does not

**The peer's token decides.** `lpsd` asks the kernel who is on the other end of the connection. Nothing in any message contributes to that answer, and nothing a client sends could.

**The socket's KACS descriptor admits the same callers.** `lpsd` stamps one on the socket when it creates it, admitting `LocalSystem` and `BUILTIN\Administrators`, so anyone else is refused at `connect` rather than after sending a request. Its runtime directory, `/run/lpsd`, is `peinit`'s, provisioned before `lpsd` starts.

That descriptor is load-bearing, not decoration: `/run` is seeded with a descriptor admitting `LocalSystem` alone, and everything created under it inherits that. Without `lpsd` stamping its own, an administrator running `lps` would be refused by KACS before a byte was exchanged.

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

## What is recorded

Every request that changes the store is recorded as an event, after the change is durable, or as the failure `lps` was told:

| Request | Event |
|---|---|
| `add` | `lpsd.account.created` |
| `remove` | `lpsd.account.deleted` |
| Any other change to an account: `enable`, `disable`, `password`, `set`, `claim set`, `claim remove`, `rename`, `logon-types`, `key add`, `key remove`, `policy` | `lpsd.account.modified`, with `operation.name` saying which |
| `group create` / `group delete` | `lpsd.group.created` / `lpsd.group.deleted` |
| `group add` / `group remove` (membership) | `lpsd.group.member.added` / `lpsd.group.member.removed` |

Each record names the administrator who asked as `subject.token.sid`, and the account and group as `object.account.sid` and `object.group.sid`, never by name. A deleted account or group is named by the SID it had, read before it went. A failure carries `outcome.reason`: `not-found`, `exists`, `invalid`, `internal`, or `not-saved` for a change that could not be written and so was rolled back. A request that changes nothing, such as enabling an account that is already enabled, is not recorded. All of these events are essential, so the emission policy cannot switch them off.

Two changes have no event yet: renaming a group and changing its description.

A caller refused because it is not an administrator is **not** recorded. The admin socket decides that from the peer's token, as above, not by a KACS access check, so no `kacs.audit.access.checked` record is written either. The socket's own descriptor is a KACS check, at `connect`, and is audited only if it has a SACL.

## The protocol itself

The wire protocol is `PLPS`, sharing its codec and header layout with PGSS Logon ([PGSS §2](~peios/logon/scope-and-roles)) and PSI ([PSPU §2](~peios/principal-source-interface/scope-and-roles)). It is specified in [PSPU §10](~peios/local-principal-administration/scope-and-roles): every request, its reply, and how a request is refused.

If you are writing tooling in Rust, the `libauthd-client` crate in the authd repository speaks it, as `lps` and Principals Manager do, and reports a refusal with `lpsd`'s reason. A program that only needs to *read* principals should ask the identity socket instead, which anyone may use: see [Resolving names](~peios/managing-local-principals/resolving-names). A program reading or changing the account of the person running it uses the self socket, below.

## The self socket

`lpsd` listens on a second socket:

```
/run/lpsd/self.sock
```

It is for every principal rather than for administrators. Any authenticated principal may connect, and it answers two requests, both about the caller and nobody else: show me my account (name, display name, credential policy, whether a password is set, and SSH keys), and set my display name. There is no field in either request for naming another account. `lpsd` reads whose account it is from the connecting process's token, as it does on the admin socket, and a caller whose account `lpsd` does not hold, such as `LocalSystem`, is told so.

Its descriptor admits `LocalSystem` and `BUILTIN\Administrators` fully, and **Authenticated Users** (every principal that signed in) with only what a connection needs.

Because everyone can reach it, `lpsd` never waits on a connection there. Each one gets five seconds from connecting to the end of its answer, a request may be at most 4 KiB, and `lpsd` holds at most 32 such connections at once and 4 from any one user. A program that connects and says nothing holds up nobody else's sign-in.

A changed display name is saved before the answer, and `lpsd` tells `authd` at once, so name lookups show the new name straight away. The change is recorded as `lpsd.account.modified`, with `operation.name` `set-display-name`, naming the principal as both who asked and the account changed.

Changing a password or an SSH key is not done here, because it asks for the current password: see [Changing your own keys](~peios/managing-local-principals/lps-command#changing-your-own-keys). In Rust, `libauthd-client`'s `own` module speaks the self socket and its `credential` module holds the password and key conversations. The protocol is [PSPU §10.11](~peios/local-principal-administration/the-self-socket).

## See also

- [The `lps` command](~peios/managing-local-principals/lps-command) — the client this socket serves.
- [Managing local principals](~peios/managing-local-principals/overview) — the authority/source split behind the design.
