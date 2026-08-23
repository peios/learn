---
title: Credential Projection
description: Linux applications call getuid() and know nothing of tokens — how KACS projects a token onto Linux credentials, one way only.
---

KACS tokens are the sole identity-based authorization mechanism, and
Linux applications do not know tokens exist. They call `getuid()`,
`getgid()` and `getgroups()`, read `/proc/self/status`, and assume
those numbers determine their access. KACS projects token identity
onto standard Linux credentials so unmodified applications work.

When a token is installed on a process, the process's Linux
credentials are set to match. The numbers themselves are **already on
the token**: the user SID's projected uid, the primary group SID's
projected gid, and a projected supplementary gid per group SID are all
computed by authd when the token is minted, and KACS copies them.

**KACS never resolves a SID to a number itself.** It holds no directory
handle and consults nothing at install time — which is what makes
projection cheap enough to do on every credential change, and what
keeps a name-service outage from being able to change what a running
process may do.

How a SID becomes a number is therefore not KACS's rule to state, and
this chapter deliberately does not restate it. The authority is the
principal source interface's numeric scope (PSPU §2): identifiers are
**computed** — an authority grants a source a band `(base, count)` and
derives `base + r` from a relative identifier — rather than looked up
per principal, and a source's assertion outside its band is refused
rather than clamped.

`65534` does appear in KACS, but not as a "no attribute was set"
fallback: it is `ANONYMOUS_PROJECTED_ID`, what the projected-id
accessors return for the anonymous identity and for an invalid token
pointer. It is a sentinel for *no identity*, not a default for an
identity whose number could not be found.

The consequences are mostly convenient ones. No process runs as UID 0
unless it holds the SYSTEM token — enforced, not merely expected: a
token creation naming a projected UID of 0 with any user SID other
than `S-1-5-18` is rejected, and the projection path refuses it again
at install time. Home directories work naturally, because
`getpwuid(getuid())` returns the right answer when the UID is real and
consistent with NSS. And different services get different UIDs, which
is incidental defence in depth alongside KACS's own enforcement.

## Projection is one-way

Token state flows into credential fields and never the reverse. The
projected credentials are observational compatibility data; the token
is the authority. The `setuid` family restores the old credential
rather than deriving a token from it (§3.10.3).

Projection reflects **all** groups regardless of enabled state, so
adjusting groups never triggers recalculation.

Projected credentials reflect the **effective** token — the
impersonated one during impersonation, the primary one otherwise. When
a service thread impersonates a client and creates a file, the file is
owned by the client's projected UID, quota is charged to the client,
and audit attributes to the client.

The two accessors deliberately disagree during impersonation.
`current_fsuid()` reads the projected UID from the *effective*
credential, so it yields the client's UID; `getuid()` reads the
*primary* credential's UID, so it yields the service's. During
impersonation `getuid()` returns the service and `current_fsuid()`
returns the client, and that is the intended behaviour rather than an
inconsistency.

One caveat applies to a credential carrying no token at all — a blank
credential, or one created before KACS initialised. `current_fsuid()`
falls back to `cred->fsuid` in that case, and the capability
switchboard denies before consulting the ALLOW list (§3.10.2), so
Linux DAC becomes authoritative for such a task.

## Precomputed values

Every token carries precomputed projected UID and GID values,
calculated by authd at creation and stored on the token. KACS never
resolves a SID-to-UID mapping at runtime; the accessors are pure field
reads.

Because SIDs are one namespace while Linux UIDs and GIDs are two,
authd allocates from a **single unified counter** across all principal
types rather than a separate one per namespace, so every SID projects
to a unique number whichever Linux namespace it lands in. A user and a
group can never collide on a number, which is what lets one SID answer
both `getuid()` and `getgid()` questions without ambiguity.
