---
title: Terminology
---

Terms defined in PSD-004 (token, primary token, impersonation token,
logon session, `auth_id`, SID, RID, security descriptor (SD), DACL,
privilege, integrity level, logon SID, `SeTcbPrivilege`,
`SeCreateTokenPrivilege`) are used here with the same meaning and are
not redefined. Terms defined in PSD-006 (hive, registry source) and
PSD-007 (the SYSTEM bootstrap token, the boot handoff) are likewise
used as defined.

This specification defines the following terms.

- **authd** — the authentication broker daemon (§2.1).
- **lpsd** — the Local Principal Store daemon; the reference principal
  source (§2.1, §3).
- **adpsd** — the (deferred) domain principal source that fronts Active
  Directory; named only where it constrains source-neutral contracts.
- **Principal source** (or **source**) — a process that authoritatively
  verifies credentials for, and resolves the identity of, some set of
  principals. lpsd and adpsd are sources. A source occupies a fixed
  structural role behind authd's router.
- **Source registry** — the directory of source sockets under which each
  source registers itself so authd can discover and connect to it
  (§6.1).
- **Broker** — authd, in its role as the privileged intermediary that
  applies policy and mints tokens. "The broker" and "authd" are
  interchangeable.
- **Resolved principal** — the PAC-shaped record a source returns to
  authd on successful verification: the principal's SID, its
  namespace-expanded group SIDs, its source-native claims, and its
  account state (§4).
- **Credential** — material a caller presents to prove identity (for
  this version, a password). A **transient credential** is the material
  in flight during a logon; a **verifier** is the stored value a source
  checks it against (for this version, an argon2id hash).
- **Logon** — a single authentication event. A successful logon creates
  exactly one logon session and at least one token.
- **Source-transparent operation** — an operation that MUST behave
  identically regardless of which source backs the principal
  (authentication, ChangePassword, self-service). Source-transparent
  operations pass through authd (§2.2).
- **Source-shaped operation** — an operation whose form legitimately
  differs between sources (account and group administration, policy).
  Source-shaped operations go directly to a source (§2.2).
- **Domain object** — the single lpsd record holding the machine SID,
  the RID counter, and the password/lockout policy (§3.1).
- **Policy phase** — the stage in which authd, after a source verifies a
  principal, applies system policy (group merge, privilege assignment,
  logon-rights gate, integrity level, token shaping) before minting
  (§5.2).
