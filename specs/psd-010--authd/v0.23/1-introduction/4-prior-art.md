---
title: Prior Art
---

The Peios authentication subsystem is modelled on the Windows security
architecture, with deliberate divergences. This section records the
parity mapping and the divergences, and notes the standards adopted.

## Windows parity

| Peios | Windows analogue | Notes |
|---|---|---|
| authd | LSASS | Broker that loads authentication results and mints tokens. Holds the TCB privilege. |
| lpsd | the local SAM | The standalone account/credential store. |
| adpsd (deferred) | AD via `lsass` over Kerberos/NTLM | Domain principal source. |
| Resolved principal (§4) | the PAC (`PAC_LOGON_INFO` + claims) | Source-to-broker authorization identity. |
| Policy phase (§5.2) | LSASS token assembly + LSA policy | Privilege/rights assignment, integrity level, local-group merge. |
| Logon types | Windows logon types | Values are shared with PSD-004. |

The central structural decision — that the **source** owns credential
verification and namespace group expansion, while the **broker** owns
local/system policy and minting — is taken directly from Windows, where
even a domain logon's final token is assembled by the member machine's
LSASS layering local policy over the KDC-signed PAC. This boundary
(§2.2) is what keeps lpsd and a future AD source interchangeable.

## Deliberate divergences

- **Credential storage.** Windows stores the unsalted NT hash (MD4) and,
  on a DC, Kerberos keys. Peios stores neither for a member system.
  lpsd uses **argon2id** verifiers (§3.3). This is safe because the
  credential format never crosses the source/broker seam (§2.2): the
  broker is credential-agnostic, so the source is free to use a modern,
  memory-hard verifier without affecting interoperability.
- **Local store shape.** The Windows SAM and AD share the
  security-principal data model but not the directory machinery. lpsd
  adopts the **data model** (SIDs, RIDs, well-known principals,
  account-control flags, group semantics) but is a **flat, RID-keyed
  store**, not an LDAP/X.500 directory. It has no DIT, distinguished
  names, organisational units, schema engine, or replication (§3).
- **Source-to-broker contract.** The contract is **PAC-isomorphic**
  (§4): information-equivalent to the Windows PAC but a clean,
  versioned, signature-free format, because the source/broker hop is a
  trusted local IPC rather than an untrusted network hop. A domain
  source verifies a real PAC's signatures and then translates into this
  format.
- **Routing by transparency.** Windows routes account administration to
  the directory (SAMR/LDAP) and authentication to LSASS. Peios
  generalises this into an explicit rule (§2.2): operations that MUST be
  source-transparent pass through the broker; source-shaped operations
  go direct.

## Standards

- **RFC 2119** — normative keywords (§1.3).
- **argon2id** — the password verifier (§3.3), per the Argon2 password
  hashing specification; parameters are policy (§3.4).
- The KACS syscall and wire-format contracts of **PSD-004** — token,
  session, peer-token, and impersonation primitives. Where this
  specification and PSD-004 disagree, PSD-004 is correct.
