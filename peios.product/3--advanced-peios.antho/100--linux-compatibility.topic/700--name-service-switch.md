---
title: Identity for POSIX programs
type: concept
description: How getpwnam and friends reach Peios principals — no nsswitch.conf entry, no /etc/passwd, no PAM, and nothing resolves before authd is running.
related:
  - peios/linux-compatibility/overview
  - peios/networking/name-resolution
  - peios/linux-compatibility/credential-projection
  - peios/linux-compatibility/setuid-and-uid0
  - peios/managing-local-principals/resolving-names
  - peios/managing-local-principals/overview
---

A Linux program calls `getpwuid` and has never heard of a token. Between that call and the authority sits one shared object:

```
/usr/lib/libnss_peios.so.2
```

It asks `authd` over `/run/ident.sock` and renders the answer as a `struct passwd`.

## There is nothing to configure

On other systems `/etc/nsswitch.conf` decides where identity comes from. On Peios it does not, for `passwd`, `group`, `shadow` or `initgroups`. glibc is patched so those four reach the authority and nothing else, whatever any file says.

That is not tidiness. **A second search order the authority cannot see is a second answer to the question *who is `jack`***, and a program acting on one principal's behalf while its access is checked against another is a confused-deputy bug rather than a cosmetic inconsistency. The authority resolves a name across the principal sources it is configured to have, in a configured order, applying domain and numeric confinement — none of which `nsswitch.conf` can express, and all of which a line in it would bypass.

It also closes an extension point Peios does not want. Naming a module in `nsswitch.conf` injects a shared object into **every address space on the system**. That is the in-process-plugin pattern this design rejects everywhere else it appears. Adding a source of identity to a Peios machine means [writing a principal source](~peios/managing-local-principals/overview) — a separate process the authority confines, which cannot mint.

`hosts` is fixed the same way, for the same reason, to a different module: `libnss_peios_net.so.2`, which forwards to `resolvd`, the stub resolver. A `files dns` line would be a second resolver with none of resolvd's routing — and a second answer to *which address is `git.corp`*. There is no `/etc/hosts`; static names live in the registry and resolvd answers them at every door. See [name resolution](~peios/networking/name-resolution). `services`, `networks` and the rest are untouched.

## There is no `/etc/passwd`

No `files` entry, and nothing behind the authority to fall back to.

There is no `root` to hold there. **uid 0 is where the SYSTEM token projects**, not an account — nothing on the system looks for a principal called `root`, and `peinit` projects SYSTEM itself without resolving anything. A flat file of accounts would be a second identity store with none of the confinement the real one has, holding entries for principals that do not exist.

`shadow` and `gshadow` return nothing, always. A Peios verifier lives in its source's store and cannot be read out at all, so there is no entry to return and never will be.

**PAM does not exist on Peios.** There is no `libpam`, no `/etc/pam.d`, and no stack to configure. Authentication goes through [PGSS Logon](~peios/logon/scope-and-roles), where a client collects what it is asked for and an authority decides — and the module-stacking model PAM is built on is the same one the paragraph above rejects.

## Before the authority, nothing resolves

Anything running before `authd` — `peinit`, an initramfs — gets numbers rather than names.

That is the correct answer rather than a gap. Identity comes from the authority; until it exists there is none to have, and a file that answered anyway would be answering for principals nobody had vouched for.

> [!NOTE]
> A program that treats an unresolved uid as a fatal error will fail early in boot. Displaying the number is the expected behaviour.

## One call, one round trip

The module holds itself to a rule: **each libc call costs exactly one request.**

- `getpwuid` asks for the six fields a `passwd` record needs, together.
- `getgrnam` asks for the group's members *with their names already resolved*, so filling `gr_mem` costs nothing further. A reply of bare identifiers would have turned one call into one per member.
- `initgroups` asks about the principal, which is the direction sources actually store memberships — it never walks a group's membership to get there.

It opens a connection per call rather than holding one. A shared object cannot see its process fork, and a connection inherited by a child that then interleaves requests on it with its parent is a well-known way for a name resolver to hand back somebody else's answer. Connecting to a Unix socket is cheap; the caching that would be cheaper belongs in the authority, where every process shares it and something can tell it when it goes stale.

## What the return values mean

| Result | glibc status | Effect |
|---|---|---|
| The principal exists | `SUCCESS` | The record is returned. |
| No such principal | `NOTFOUND` | The caller sees no such user. |
| A source did not answer | `TRYAGAIN` (`EAGAIN`) | The caller retries. **Not** an absence. |
| `authd` is not reachable | `UNAVAIL` | Nothing is behind it; the lookup fails. |

The third row is the one that matters. A source that could have answered and did not is *not* the same as an account that does not exist, and reporting it as one would let an outage be remembered as a fact — the account comes back when the source does, but a cached "no such user" would not.

## What POSIX cannot express

The rendering is one-directional and lossy, and each loss is a property of `struct passwd` rather than of anything underneath it.

**No claims.** A principal's claims feed conditional ACEs and have no field in a `passwd` record. Peios-native tools see them; `getpwnam` does not.

**No domain.** A `uid_t` is a number. Which source and which domain it came from is recoverable — the ranges are laid out so it is — but nothing in the record carries it.

**Empty member lists.** `gr_mem` for `Everyone` is empty, because nothing records who is in `Everyone`; the authority adds it to every token it mints. Inventing a list of this machine's principals would be a wrong answer rather than a partial one. See [resolving names](~peios/managing-local-principals/resolving-names) for the three kinds of membership and which of them can be listed.

**Unnumbered groups are skipped.** `Interactive` and its siblings have no POSIX group id, because membership in them is a property of a session rather than of an account. They are omitted from a supplementary group list rather than rendered as `nobody`, which would grant whatever `nobody` can reach.

## `getent` and the whole list

`getent passwd` works, and pages through every source in turn.

A source is never *required* to enumerate — a directory able to answer any single question may be quite unable to answer all of them — so a listing can legitimately be partial. The authority records which sources did not contribute; a Peios-native tool can show that, though `getent` itself has nowhere to put it.

> [!TIP]
> A short `getent passwd` on a machine with a directory source is worth checking against `authd`'s log before concluding an account is missing.
