---
title: The local store
type: concept
description: What lpsd keeps on disk — the machine's domain SID, its principals, and the argon2id verifiers that stand in for their passwords — and why it is one file.
related:
  - peios/managing-local-principals/overview
  - peios/managing-local-principals/creating-accounts
  - peios/identity/sids
  - peios/security-descriptors/overview
---

`lpsd` keeps everything it knows in one file:

```
/var/state/lpsd/principals
```

It is read once at startup and held in memory. It changes only when an administrator changes it.

## What is in it

**The machine's domain SID.** Every local principal is numbered under it, and it is generated — from the kernel's random number generator — the first time `lpsd` runs on a machine that has no store.

That last point matters more than it sounds. Two machines built from the same image do **not** share a domain, so the security descriptors written on one do not grant access to the other's users. An image cannot ship a domain, because the domain does not exist until first boot.

The domain is always of the form `S-1-5-21-A-B-C`. That shape is structural — the store holds three numbers under a fixed prefix, so it cannot express a domain of any other kind. It cannot claim `S-1-5-32` (BUILTIN) or any well-known namespace, whatever is written into it.

**The principals.** For each: a relative identifier (RID), a Unix ID, the canonical spelling of the name, whether the account is enabled, a password verifier, the groups it belongs to, which of them is primary, a home directory, a shell, a display name, and any claims.

A principal's SID is the domain plus their RID. `jack` with RID 1000 in domain `S-1-5-21-A-B-C` is `S-1-5-21-A-B-C-1000`.

**RIDs start at 1000 and are never reused.** Not even after an account is deleted. That is deliberate and it is the property that makes deletion safe to offer at all: a reissued RID would give a new person the SID of an old one, silently inheriting every access the descriptors on this machine still grant them. It is the one identity mistake that cannot be undone by fixing the account afterwards.

**The local groups.** A group created here is an object: a RID from the same counter, a name, and a Unix ID. Sharing the counter with principals is what stops a group ever colliding with a user's SID.

Well-known groups — `BUILTIN\Administrators`, `Everyone`, `Authenticated Users` — are **not** stored. Their SIDs are the same on every Peios machine, so a stored copy could only ever drift from the real one, and provisioning would freeze whatever the table said that day. `lpsd` resolves their names from a table in its own code.

## Unix IDs

Linux programs call `getuid` and `getgroups` and have never heard of a token, so every token carries POSIX numbers alongside the SIDs. Those numbers begin here.

**A principal's Unix ID is their RID**, and a group's is its RID. One object, one number — so a uid in a log tells you the RID without a lookup.

The numbers stored here are **relative**. `lpsd` knows nothing about where its range sits: `authd` adds a base from the registry before the number reaches a token, so `jack` with RID 1000 stores 1000 and signs in as uid **1001000** when the base is 1,000,000.

That indirection is not bookkeeping. It is what stops a principal source reaching uid 0 or another source's numbers — `authd` reserves everything below the sources' ranges for its own, and refuses a relative number that runs past the end of a range rather than wrapping it. A source can only ever express numbers inside the range it was given.

It also means moving a range is a registry edit rather than a rewrite: nothing stored here was ever absolute.

`lps list` and `lps show` display the **effective** number, with the base already added, because that is the one an operator will see everywhere else.

The same indirection is why `getpwuid` has to reach `authd` rather than `lpsd`: the arithmetic that made a number absolute happened in `authd`, and only `authd` can run it backwards. See [resolving names](~peios/managing-local-principals/resolving-names).

> [!NOTE]
> A `-` where a uid should be means `authd` has assigned this machine no range at all, and every principal here will sign in as `nobody`. The `UnixIDBase` value on this source is missing or unusable.

## Profiles and claims

The **profile** — home directory, shell, display name — is not identity. No security descriptor names a home directory and no token carries one. It is stored here because this is where an administrator sets it, and it travels to `login` on the logon reply so a session can start without a second lookup.

**Claims** are named, typed attributes that conditional ACEs read: a descriptor can grant access to *anyone whose Department is Engineering* without naming principals individually. They are fixed on a token when it is minted, so a claim set now takes effect at the principal's next sign-in.

## What is not in it

**Passwords.** What is stored is a **verifier** — an argon2id hash — and a verifier is deliberately not password-equivalent. You cannot authenticate with it, and it cannot be used to answer a challenge.

That is the property that makes stealing the store meaningfully weaker than knowing the passwords. It is also why Peios does not use challenge-response schemes: those require storing something a response can be recomputed from, which is exactly what this avoids.

Each verifier carries the cost parameters it was created with, so raising them applies to passwords set afterwards while existing accounts keep working.

**Well-known group definitions.** The store defines the groups *this machine* creates, and records memberships of everything else as SIDs. `BUILTIN\Administrators` exists on every Peios machine whether or not this store mentions it; `lpsd` only records that `jack` is in it.

**Privileges and integrity levels.** What a principal may *do* is not stored here at all. `authd` decides it, from local policy keyed on the SIDs a token ends up carrying — a registry key rather than this file, so that it stays readable by an administrator and this file can stay readable by nobody. A principal source says who someone is; it has no way to say how much this machine trusts them. See [assigning privileges](~peios/privileges/assigning-privileges).

## The descriptor

The store file is owned by `LocalSystem` and its DACL grants `LocalSystem` and nothing else — not even `BUILTIN\Administrators`.

That is narrower than almost anything else on the system, and it is on purpose. This is the machine's password material, and the list of principals entitled to read it should be as close to empty as the system permits. An administrator who genuinely needs the file can take ownership, which is an act that leaves a trail; a read granted by the DACL does not.

It is also why `lps` talks to `lpsd` over a socket rather than editing the file. A tool that wrote the file would need that descriptor widened to whatever the tool runs as, undoing the one thing it exists to do.

## A file, not a database

The store is serialised whole and replaced atomically: written to a temporary file, flushed, then renamed over the old one.

A few hundred principals, rewritten when an administrator changes an account, is not a workload that needs a write-ahead log. And because the swap is a rename, a reader sees the old file or the new one and there is no third outcome — which means there is no recovery code, and code that does not exist cannot be wrong.

The file carries a checksum. Not to catch a half-written file, which atomic replacement makes impossible, but because a corrupted store that decoded *short* would present as an account quietly no longer existing.

## Missing versus corrupt

These are treated as opposite outcomes, and the distinction is the most important behaviour in this page.

**No store at all** means an unprovisioned machine. `lpsd` generates a domain, writes an empty store, and carries on.

**A store that will not read** is fatal. `lpsd` refuses to start.

Collapsing the two — "cannot read it, so make a new one" — would turn a flipped bit into every account on the machine silently ceasing to exist, and then reappearing under a *new domain* with different SIDs, orphaning every security descriptor that named them. Refusing to start is loud, reversible, and leaves the evidence intact.

If `lpsd` reports that the store is corrupt, do not delete it. Take a copy first: it is the only record of your machine's identity.
