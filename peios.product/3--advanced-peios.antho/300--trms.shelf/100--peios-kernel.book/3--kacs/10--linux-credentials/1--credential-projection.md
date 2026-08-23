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
credentials are set to match. The token's user SID maps to a UID
through the directory's `uidNumber` attribute, defaulting to 65534 —
nobody — where none is set. The primary group SID maps to a GID the
same way, with the same fallback. Group SIDs map to supplementary GIDs
wherever `gidNumber` attributes exist. There is no algorithmic
mapping anywhere in this: every value is looked up or defaulted.

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
authd allocates `uidNumber` and `gidNumber` from a single unified
counter across all principal types, so every SID projects to a unique
number whichever Linux namespace it lands in.
