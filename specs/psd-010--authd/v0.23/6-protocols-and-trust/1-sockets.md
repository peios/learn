---
title: Sockets
---

The subsystem exposes three Unix-domain sockets. All three MUST be
`SOCK_SEQPACKET`: this is required for the kernel peer-token capture
(§6.2) — datagram and `socketpair` sockets yield no peer token — and it
provides message framing and `SCM_RIGHTS` fd passing.

| Socket | Owner / listener | Purpose | Connect access |
|---|---|---|---|
| `/run/authd.sock` | authd | Client door: Logon and source-transparent requests (§6.3) | Authenticated Users + SYSTEM/services |
| `/run/authd/sources/<source>.sock` | the source (e.g. lpsd → `…/lpsd.sock`) | Source interface: verify/resolve + forwarded self-service ChangePassword (§4, §5.1, §7.2) | authd only |
| `/run/lpsd.sock` | lpsd | Administration and setup-control interface (§7.1, §7.2) | Administrators + SYSTEM |

The connect-access column lists the allow-ACE SIDs; the exact security
descriptor for each socket — allow-ACEs by SID, deny by absence — and for
the `/run/authd/sources/` directory is given in §9. Sockets are created
so that access is governed by the SD, not by POSIX permission bits.

## The source registry

`/run/authd/sources/` is a **source registry**: each principal source
registers by creating its verify/resolve socket there. authd discovers
the available sources by enumerating this directory and connects to
each. A domain source registers as `/run/authd/sources/adpsd.sock`. Because
authd **connects out** to whatever sockets appear here and then trusts the
identities they resolve (§5.2), this channel MUST be protected in **both
directions**:

- The directory's own SD (defined in §9) MUST restrict entry creation to
  the specific trusted source identities (for v0.23, lpsd's SYSTEM service
  token carrying the per-service SID for `lpsd`), and socket creation MUST
  be exclusive so an impostor cannot pre-create or recreate a source's
  socket (e.g. in the window before the source starts or after it crashes).
- authd MUST authenticate every source it connects to: obtain the connected
  peer token with `kacs_open_peer_token`, verify it against the static
  source allowlist of §9 (the mirror of the source checking the peer is
  authd), and refuse any source socket whose peer token lacks the expected
  source identity.

Without the second control, a rogue process that won the race to create a
source socket would *become* a source — minting arbitrary identities and
harvesting every cleartext credential authd forwards (§6.2.5). The
verify/resolve sockets MUST also be connectable only by authd (per-request
peer-token check of §6.2). All of these are mandatory.

## Two-layer authorization

Access is enforced in two layers:

1. **The connect SD** on each socket (the table above) — coarse control
   over who may `connect()` at all.
2. **Per-request authorization** against the peer token (§6.2) — the
   fine-grained gate that actually decides each request (§6.3).

The per-request gate is the real enforcement; the connect SD is
defence-in-depth. In particular, the verify/resolve interface MUST
additionally check that the connected peer is authd, not rely on the
connect SD alone.
