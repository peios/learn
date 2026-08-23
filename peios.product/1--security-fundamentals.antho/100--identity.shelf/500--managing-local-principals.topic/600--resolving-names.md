---
title: Resolving names
type: concept
description: How a name, a SID or a POSIX identifier becomes a principal — why only the authority can answer, the search order, and why "unavailable" is not "not found".
related:
  - peios/managing-local-principals/overview
  - peios/managing-local-principals/the-local-store
  - peios/linux-compatibility/name-service-switch
  - peios/identity/sids
  - peios/privileges/assigning-privileges
---

Every program that prints a name for a file's owner is asking the same question: *who is this?* On Peios that question goes to `authd`, over a socket of its own:

```
/run/ident.sock
```

Separate from `/run/logon.sock`, but the same standard — [PGSS §2](~peios/logon/scope-and-roles) defines both. What separates them is who calls: a handful of things ever originate a logon, where **every process on the system** resolves names. A filesystem walk is millions of lookups, and it must not be able to fill the queue an administrator needs in order to sign in.

## Why the authority, and only the authority

A principal source counts POSIX identifiers **relative** to a range it is never told the base of. `authd` adds the base — so `jack`, stored by `lpsd` as 1000, signs in as uid 1001000.

That arithmetic exists in exactly one place, and only that place can run it backwards. **No source can answer "who is uid 1001000", because no source knows what 1001000 means.** It is not that the authority is a convenient place to put this; it is the only party that can do it at all.

The same holds for names. A bare name may exist in more than one source, and which one wins is a property of the machine rather than of any source in it.

## One answer, systemwide

Whatever asks — a Peios tool, a Linux program through [`getpwnam`](~peios/linux-compatibility/name-service-switch), a future graphical console — the question goes to the same place and gets the same answer.

There is deliberately no way to arrange otherwise. glibc's identity databases are patched to reach the authority and nothing else, there is no `/etc/passwd` behind them, and PAM does not exist on Peios at all. Every route by which another system lets identity come from somewhere the authority cannot see has been closed rather than configured.

That is worth more than it sounds. If two components resolved names separately they could disagree, and a program acting on one principal's behalf while its access is checked against another is a confused-deputy bug rather than a cosmetic inconsistency. It also means a name resolves identically at a logon and at an `ls -l`, because the same code answers both.

## The search order

A name nobody qualified is resolved by asking sources **in a configured order**, stopping at the first that answers.

The order is a value on each source's allowlist entry:

```
Machine\Software\Authd\Sources\lpsd
    SearchOrder    REG_DWORD    1000
```

Lower is consulted first. Sources that share a value are ordered by name. A source that sets nothing resolves at 1000, which leaves room to place a new source either side of the ones already there without renumbering them.

It is deliberately explicit. Resolving in the order sources happened to register would let a slow disk change which principal a name refers to.

> [!NOTE]
> A machine with one source has nothing to order, and can ignore this entirely.

## Bare in, qualified out

You may look a principal up by a bare name. What comes back always carries the **SID** as well as the name.

So a tool can always tell which principal it got, compare two answers for identity, and record something unambiguous in a log. Ambiguity is permitted in what you ask; it is not permitted in what the authority answers.

### Reserved characters

A principal or group name may not contain `@`, `\`, `/`, `:` or `,`, may not begin or end with a space, and must be printable ASCII.

Each of those is a separator somewhere a name ends up — a path, a `passwd` record, a `group` member list — and the damage is done by whatever reads it later, so it cannot be prevented at the point of display. `@` and `\` are reserved for qualified names (`jack@local`), which do not exist yet: reserving them now is what stops an account literally called `jack@local` colliding with the syntax the day it arrives.

The ASCII restriction defers confusables and normalisation rather than getting them wrong. `jack` spelled with a Cyrillic `а` renders identically and is a different principal, and the same name in NFC and NFD is two byte sequences a comparison calls two people. Relaxing this later is safe; tightening it later would mean renaming accounts.

## Absent is not the same as missing

Three answers, and the difference between the last two is the one worth knowing:

| Answer | Means |
|---|---|
| **Found** | Here is the principal. |
| **Not found** | Every source that could have answered was asked, and there is no such principal. |
| **Unavailable** | A source that could have answered did not. |

**A source that is configured and not running does not simply drop out of the order.** If `lpsd` has crashed, `jack` resolves to *unavailable* — not to a directory's `jack` further down the order, which would be a different principal with a different SID, and every security descriptor granting the local one would stop applying to the person signing in under that name.

It also matters because *not found* is safe to remember and *unavailable* is not. A cache told "no such user" during an outage would keep saying so long after the outage ended.

> [!TIP]
> If names stop resolving and start reporting temporary failures, look for a principal source that is not running. `authd` logs which one it was waiting for.

## Groups you cannot list

Ask who is in a local group and you get its members. Ask who is in `Everyone` and you get nothing — and that is the correct answer rather than a limitation.

Membership comes in three kinds:

**Recorded.** Local groups, and `BUILTIN\Administrators`. A source holds the edges, so it can list them. (Note that being well-known has nothing to do with it — `Administrators` is well-known and perfectly enumerable.)

**Stapled.** `Everyone`, `Authenticated Users`. Nothing records who is in them; `authd` adds them to every token it mints. Membership is a rule, not data, so there is no list to produce.

**Session-scoped.** `Interactive`, `Network`, `Batch`, `Service`. These are not properties of an account at all, but of a *logon*: `jack` is in `Interactive` at the console and not in it over the network. No static answer exists even in principle, which is why they have no POSIX group id either.

The asymmetry that falls out is the useful one. *Which groups is this principal in* is cheap and always works. *Who is in this group* is best-effort, and a source is entitled to decline it — listing a directory group can mean listing an entire organisation.

## Every lookup is live

There is no cache yet. Each lookup is a fresh round trip to the source that holds the answer.

That is a deliberate first step rather than an oversight: a cache is invisible on both sides of the wire, so adding one later changes nothing about how any of this behaves. What it means today is that listing a very large directory is slower than it will be.

Sources already declare what a cache will need — whether they can push a change notification, and how long an answer may be held — so the contract is in place before the thing that uses it.

## Where to go next

For how Linux programs reach this resolution through `getpwnam` and friends, read [Name service switch](~peios/linux-compatibility/name-service-switch).

For where the local principals being resolved actually live, read [The local store](~peios/managing-local-principals/the-local-store).
