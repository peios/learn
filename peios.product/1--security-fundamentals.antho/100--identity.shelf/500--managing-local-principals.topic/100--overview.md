---
title: Managing local principals
type: concept
description: Where the accounts on a Peios machine live — the authority that mints tokens, the sources that hold identity, and lpsd, the one that owns the local store.
related:
  - peios/identity/overview
  - peios/logon-sessions/overview
  - peios/managing-local-principals/the-local-store
  - peios/managing-local-principals/creating-accounts
  - peios/managing-local-principals/lps-command
  - peios/managing-local-principals/resolving-names
---

Signing in on Peios involves three separate things, and it is worth being able to name them before you administer any of them.

**The authority** is the process that mints tokens. On a stock Peios system that is `authd`. It listens on `/run/logon.sock`, it holds the privilege to create tokens, and it is the only thing on the system that does. When you type a password at a login prompt, `login` is talking to `authd`.

**A principal source** is a process that knows who exists. It verifies credentials and answers the question "who is this?" — and nothing else. It cannot mint a token, cannot grant a privilege, and cannot create a session, because the protocol it speaks gives it no way to say any of those things.

**`lpsd`** is the local principal source: the one that holds this machine's own accounts. It is where `jack` lives, and it is what you are administering when you run `lps`.

## Why the split

It would be simpler to have one daemon that both checks passwords and mints tokens. The split exists because those two jobs have very different risk profiles.

Checking a credential means parsing input that came from outside — from a login prompt, a network connection, a smartcard reader. That is the code most likely to have a defect in it. Minting a token is the most privileged operation on the system.

Putting them in one process means a defect in the first becomes a compromise of the second. So `authd` mints and cannot verify; `lpsd` verifies and cannot mint. A completely compromised `lpsd` can lie about the accounts it holds, and that is the whole of what it can do — it cannot elevate anyone, cannot forge a token, and cannot claim identities that are not its to claim.

The division runs through what a source is even able to *say*. A source states **who someone is**: their SID, their memberships, their POSIX identifiers, where their session starts. It never states **how much this machine trusts them** — privileges and integrity levels are `authd`'s, decided from local policy, and there is no message with which a source could ask for one.

That local policy is a registry key, one record per principal, and it is where you go to change what an account may *do* as opposed to who it is: [assigning privileges](~peios/privileges/assigning-privileges).

## How they find each other

`lpsd` connects **to** `authd`, not the other way round. That keeps `authd` — the process holding the token-minting privilege — free of any reason to open an outbound connection to anything.

At boot, `lpsd` starts after `authd`, connects to `/run/psi.sock`, registers itself, and only then reports itself ready. That ordering means anything that starts after `lpsd` — `login`, a greeter, a remote access daemon — finds a system that can genuinely authenticate, rather than one where the processes merely exist.

If you see `lpsd` failing to start, the usual causes are that `authd` is not running, or that this machine's configuration does not permit `lpsd` to register. The second is deliberate: a source must be explicitly allowed to assert identity, and an unconfigured machine permits none.

## More than one source

`lpsd` is the only source on a stock machine, but nothing about the design assumes it is alone. A directory-backed source can register alongside it, holding domain accounts while `lpsd` holds local ones, and `authd` routes each logon to whichever source owns the name.

Each source declares the SID namespace it is authoritative for, and `authd` confines it there. That is what stops a directory deciding who administers your machine, and equally what stops a local source handing out domain identities.

The same confinement applies to **numbers**. A source is given a range of POSIX identifiers and counts inside it, and `authd` adds the base — so a source's principals land in its own range whatever the source sends, and the numbers below every range, uid 0 among them, belong to `authd` alone. `lpsd` starts at 1,000,000; a directory source would be given somewhere well clear of it.

That is why a uid on a Peios machine is larger than you might expect, and why moving a source's range is a configuration change rather than a migration: nothing a source stores was ever an absolute number.

## Seeing a principal, rather than a number

Signing in is one half. The other is that everything on the system can turn an identifier back into a name — `ls -l` showing an owner, `id` showing a group.

That goes to `authd` too, on a socket of its own, and for a reason worth knowing: a source counts its POSIX identifiers relative to a range it is never told the base of, so **only the authority can work out who a uid belongs to**. See [resolving names](~peios/managing-local-principals/resolving-names).

## Where to start

- [The local store](~peios/managing-local-principals/the-local-store) — what `lpsd` keeps, and where.
- [Resolving names](~peios/managing-local-principals/resolving-names) — how a name, a SID or a number becomes a principal.
- [Creating accounts](~peios/managing-local-principals/creating-accounts) — the first one, and every one after.
- [The `lps` command](~peios/managing-local-principals/lps-command) — the full reference.

The protocols themselves are specified rather than merely documented: [PGSS §2](~peios/logon/scope-and-roles) is Logon, and [PSPU §2](~peios/principal-source-interface/scope-and-roles) is PSI, the interface sources speak. Read those if you are writing a principal source of your own.
