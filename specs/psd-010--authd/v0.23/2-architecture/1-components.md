---
title: Components
---

The authentication subsystem is built from a privileged **broker** and
one or more unprivileged **principal sources**.

## authd (the broker)

authd is the authentication broker. It is signed at TCB level and runs
PIP-protected. Its responsibilities are:

- Own the client-facing socket and accept logon and source-transparent
  requests (§6.1, §6.3).
- Route each request to the correct principal source (§2.2).
- Apply system policy after a source verifies a principal — group
  merge, privilege assignment, the logon-rights gate, integrity level,
  and token shaping (§5.2).
- Mint logon sessions and tokens via the KACS syscalls (§5.3).

authd MUST hold `SeTcbPrivilege` and `SeCreateTokenPrivilege`. authd
MUST be the only userspace process that calls `kacs_create_logon_session`,
`kacs_create_token`, and `kacs_destroy_empty_logon_session` in normal
operation. authd MUST NOT store accounts. authd MUST NOT persist
credential material, stored verifiers, or any reversible secret; any
transient credential it handles is subject to §6.2.5.

authd does own one persistent store: the **idmap** (§3.6) — the SID↔id
projection cache plus the authoritative id assignments for ephemeral,
non-directory SIDs (service SIDs, virtual and orphan identities). The
idmap holds neither accounts nor secrets, so the prohibitions above are
unaffected, and it is low-criticality (rebuildable from the sources).

## lpsd (the local principal source)

lpsd is the Local Principal Store: a SQLite-backed database of the
local users, groups, and credentials of a standalone system (§3). lpsd
is the **reference** principal source and the local analogue of a
domain directory.

lpsd MUST NOT mint tokens or sessions and does not require
`SeCreateTokenPrivilege` or `SeTcbPrivilege`. lpsd is, in the
token-minting sense, "just a database with a protocol." It is
nonetheless security-critical: it is the sole holder of the system's
password verifiers, and §3.5 and §6.1 constrain its protection
accordingly.

lpsd exposes two interfaces on two sockets (§6.1):

- a **source** interface, callable only by authd, carrying the
  source-transparent operations authd brokers: verify/resolve, which
  authenticates a principal and returns a resolved principal (§4), and the
  forwarded self-service ChangePassword (§7.2); and
- an **administration** interface, gated per-object by a KACS AccessCheck
  against each principal's (or the domain object's) security descriptor
  (§7.2), for the source-shaped account operations.

## Principal sources and the structural role

A principal source is any process that authoritatively verifies
credentials for, and resolves the identity of, a set of principals.
lpsd is one source; the deferred domain source **adpsd** is another,
occupying the same structural role behind the broker.

All sources MUST answer the same source-neutral contract: the
verify/resolve request and the resolved-principal response of §4. The
broker treats every source identically and MUST NOT branch its policy
or minting logic on which source answered. A source's *internal* design
(storage engine, credential format, namespace) is private to it and is
not constrained by this contract — only the resolved principal it
returns is.

> [!INFORMATIVE]
> This is what makes lpsd and a future AD source interchangeable, and
> it is why lpsd is free to use argon2id verifiers and a flat SQLite
> store while AD uses Kerberos keys and an LDAP directory: neither
> choice crosses the seam (§2.2).

## Built-in and well-known principals

Well-known principals (SYSTEM `S-1-5-18`, Anonymous `S-1-5-7`,
Everyone, Authenticated Users, LocalService, NetworkService, the
`S-1-5-32` BUILTIN aliases, and so on) are defined by PSD-004 and a
static catalogue. They are NOT stored in any source. authd resolves
them from the static catalogue, not by querying a source.
