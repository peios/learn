---
title: Scope
---

This specification defines the Peios **authentication subsystem**: the
processes, data, and protocols that turn a principal's credentials into
a kernel token. It covers two daemons and the contracts between them:

- **authd** — the authentication broker. authd holds `SeTcbPrivilege`
  and `SeCreateTokenPrivilege`, owns the client-facing socket, routes
  requests to the appropriate principal source, applies system policy,
  and is the sole userspace caller of the kernel token- and
  session-minting syscalls. authd holds no accounts and no stored
  secrets.
- **lpsd** — the Local Principal Store. lpsd is the SQLite-backed
  database of local users, groups, and credentials for a standalone
  system. It is the reference **principal source** and the local
  analogue of a domain directory.

This specification covers:

- The component split between authd, lpsd, and future domain sources,
  and the boundary (the "seam") between a source and the broker (§2)
- The routing rule that decides whether an operation passes through
  authd or goes directly to a source (§2.2)
- lpsd's principal model: entities, the SID namespace, the user and
  group records, the credential model, and the storage design (§3)
- The resolved-principal contract a source returns to authd (§4)
- The end-to-end authentication (logon) flow, the policy phase authd
  applies, and the session/token mint (§5)
- The socket layout, the caller trust model, the request taxonomy, and
  the client wire protocol (§6)
- First-boot bootstrap, first-admin seeding, and account administration
  (§7)
- Features deferred to later versions (§8)

This specification does not cover:

- Tokens, sessions, SIDs, security descriptors, privileges, integrity
  levels, impersonation, and the access check — PSD-004 (KACS). This
  specification consumes those primitives; it does not redefine them.
- The registry, the RSI, and loregd — PSD-005 (LCS), PSD-006 (loregd).
  The registry is configuration storage, not identity storage.
- Boot orchestration, the SYSTEM-token handoff, and service supervision
  — PSD-007 (peinit). This specification defines authd's startup
  obligations but not how peinit launches or supervises it.
- The KMES event and audit pipeline — PSD-003 (KMES). This
  specification names the events it emits; it does not define KMES.
- **CAAP distribution.** authd's role in pushing central access policies
  into the kernel cache is deferred (§8) and is not specified here.
- Domain join, Active Directory integration, and Kerberos — deferred
  (§8). The domain principal source (adpsd) is described only where it
  constrains the source-neutral contracts.
