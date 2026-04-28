---
title: Networked IPC
type: concept
description: Cross-domain IPC on Peios — NIPCd, the CONNECT handshake, Kerberos-backed identity propagation, and the two-SD access-control model that makes a remote socket look local.
related:
  - peios/IPC/unix-domain-sockets
  - peios/IPC/peer-credentials
  - peios/identity/primary-vs-impersonation-tokens
  - peios/access-control/file-security-descriptors
---

A Unix-domain socket terminates inside the kernel: bytes go from one local socket buffer to another, never touching a network stack. **Networked IPC (NIPC)** preserves the local-socket programming model while routing the connection across a domain. A client on machine-A connects to a socket "on machine-B" through a per-host NIPC daemon; the server on machine-B accepts what looks like an ordinary local connection from a peer with a real, locally-meaningful identity. Neither end has to think about networking, authentication handshakes, or token marshalling — that's NIPCd's job.

The effect is the same shape as Windows MSRPC over named pipes: `\\.\pipe\foo` is a local resource, `\\machine\pipe\foo` is the same resource on another host, and Kerberos delegation makes the remote call appear to the server as if a local user invoked it. NIPC is the Peios analogue of that pattern, generalised over arbitrary Unix-domain sockets.

## The model

Every host with NIPC enabled runs **NIPCd**, a small daemon owning two endpoints:

- A local `AF_UNIX` listener at `/run/nipc/nipc.sock`.
- A network listener (typically TLS-protected) reachable from peer machines in the domain.

A client opens `/run/nipc/nipc.sock` like any local socket and sends a `CONNECT` request:

```
CONNECT /run/dns/dns.sock@machine-b.lan.local
```

NIPCd-A authenticates the calling thread (via `SO_PEERTOKEN`), establishes a Kerberos-backed channel to NIPCd-B, hands off identity, and waits for the server-side accept. From the client's point of view, once `CONNECT` succeeds, the local socket is the connection — it can be used with `read`, `write`, `sendmsg`, `recvmsg` exactly as if it were a local Unix-domain socket pair. From the server's point of view, an ordinary local `accept()` returns a connected fd whose peer credentials, peer SID, and peer token reflect the client's identity as projected on machine-B.

The byte-stream after the handshake is verbatim: NIPC does not interpose, frame, or transform application traffic. It is a routed pipe, not a protocol gateway.

## The CONNECT verb

The verb is intentionally minimal:

```
CONNECT <remote-socket-path>@<host>
```

`<remote-socket-path>` is the absolute filesystem path of the destination socket on the remote host. `<host>` is a domain DNS name resolvable to a NIPCd peer.

Pathname sockets only — abstract-namespace sockets are not addressable over NIPC because they have no SD (see [Unix Domain Sockets](unix-domain-sockets)) and the security model below requires one. A future revision may add an explicit registry of nameable abstract endpoints; the current surface omits it.

## Identity propagation

The interesting question is how the remote server ends up with a meaningful local identity for the caller without trusting machine-A's NIPCd to assert arbitrary identities.

The answer is Kerberos. NIPCd-A:

1. Captures the calling thread's effective token via `SO_PEERTOKEN` on the local connection.
2. Asks **authd** for a service ticket to `nipc/machine-b.lan.local` issued in the caller's name. authd consults the KDC and returns a ticket bundling a PAC with the caller's full token data (SIDs, claims, integrity, privileges).
3. Sends the ticket to NIPCd-B as part of the cross-machine handshake.

NIPCd-B:

1. Validates the ticket against its own keytab. The KDC's signature on the PAC is the load-bearing trust step — NIPCd-B trusts the KDC, not NIPCd-A.
2. Extracts the PAC and constructs an impersonation-class token reflecting the caller's identity, mapped through machine-B's local projection (UIDs/GIDs assigned by authd's local view).
3. Spawns a connection-handling thread, sets the freshly-minted token as that thread's impersonation token, and `connect()`s to the requested local socket.

The server on machine-B accepts that connection. From its perspective:

- `SO_PEERCRED` returns machine-B's projected UID/GID for the caller.
- `SO_PEERSEC` returns the caller's user SID as an SDDL string.
- `SO_PEERTOKEN` returns a token derived from the impersonation token NIPCd-B is currently holding.

The server cannot tell — and does not need to tell — that the peer is a NIPCd thread rather than an ordinary local process. That is the whole point.

This is **identity propagation, not credential delegation.** NIPCd-A does not forward the caller's TGT, and NIPCd-B does not gain the ability to act as the caller against arbitrary services. The ticket is for the NIPC service on machine-B specifically, and the impersonation token NIPCd-B mints is local to machine-B, scoped to the lifetime of the routed connection.

## Access control

The security envelope is two ordinary SD checks, both performed against tokens the kernels involved already trust:

**Local: nipc.sock on machine-A.** The caller must have connect-equivalent rights on `/run/nipc/nipc.sock` according to its SD, the same way any other Unix-socket gate works. This is the "may this principal use NIPC at all" question, and it's a normal pathname-socket SD check.

**Remote: the destination socket on machine-B.** When NIPCd-B's worker thread (now impersonating the caller) `connect()`s to `/run/dns/dns.sock`, the kernel performs the standard pathname-socket SD check against the impersonated token. If the caller has connect rights on the destination socket, the connect succeeds; if not, it fails with `EACCES` and NIPCd-B propagates the failure back to the caller as a handshake error.

That is the entire authorisation surface. **NIPC routes; it does not elevate.** A caller who has no rights on a destination socket gains no rights by going through NIPC. Conversely, a caller who has rights on a destination socket — under whatever SD that socket carries on machine-B — can reach it through NIPC subject only to the additional gate at `nipc.sock`.

The SD on the destination socket carries the full authorisation policy. Services that should be unreachable across the domain need only restrict their socket SD; no NIPC-specific configuration is required to keep them local.

## Chaining

NIPC connections compose. A service on machine-A may receive a NIPC connection from a caller, and from inside that connection-handler thread (now impersonating the caller) initiate a further NIPC connection to a third machine. The caller's identity propagates each hop, gated independently at every `nipc.sock` and every destination socket along the way:

```
client@A → NIPCd-A → NIPCd-B → service-on-B
                                  ↓
                              NIPCd-B → NIPCd-C → service-on-C
```

This is the natural consequence of impersonation tokens being first-class. It is also the natural way distributed administrative tools work in an AD-substrate world: a management console invokes service X on machine-B, which in turn talks to service Y on machine-C, and the user's identity is preserved end-to-end. Each hop is an independent SD check, so the policy surface is the union of the SDs along the path — no single gate can grant access the destinations themselves don't permit.

The corollary is also worth being explicit about: a caller's effective reach over NIPC is everywhere their identity has rights to. NIPC is the mechanism, not the policy. Restricting reach is done by restricting the SDs on the sockets that matter.

## What you don't get

Three intentional gaps follow from the model.

**No file-descriptor passing.** `SCM_RIGHTS` on a NIPC connection is rejected. A remote fd has no meaning on the receiving machine — its kernel object lives on the sending host. Forwarding fds via virtual handles that proxy operations back over the network is conceivable but not in scope; native Peios services do not rely on `SCM_RIGHTS` for cross-machine workflows.

**No transparent reconnect.** A network partition that breaks a NIPC connection produces the same behaviour as a local-IPC peer crash: the socket returns `EPIPE` / `ECONNRESET` on the next operation, and reconnection is the application's responsibility. This matches local-IPC semantics exactly and prevents subtle "the socket is alive but stale" failure modes.

**Latency is not local.** A NIPC `read` is a network round-trip, not a memory copy. Code written for local IPC microsecond latencies will not magically remain responsive when redirected through NIPC. The cost is opted into at `CONNECT` time — anything that can return latency-sensitive results synchronously is by definition not a NIPC use case.

These gaps are the price of preserving the local-socket programming model. Within them, NIPC is functionally equivalent to local IPC.

## Comparison

| Property | Local Unix socket | NIPC | Windows MSRPC over SMB pipe |
|---|---|---|---|
| Address form | Pathname or abstract | `path@host` | `\\host\pipe\name` |
| Identity surface | Peer's local token | Caller's token reprojected on receiver | Caller's TGS-reprojected token on receiver |
| Auth mechanism | Kernel-attested via socket | Kerberos service ticket + PAC | Kerberos service ticket + PAC |
| FD passing | Yes (`SCM_RIGHTS`) | No | No |
| Failure mode | Peer crash → `EPIPE` | Partition or peer crash → `EPIPE` | Partition or peer crash → RPC error |
| Latency | Memory copy | Network round-trip | Network round-trip |

The strong analogy with MSRPC over SMB pipes is intentional. NIPC is the Unix-domain-socket-flavoured version of the same federation-friendly pattern, expressed in the primitives Peios already has rather than adopting SMB.

## See also

- [Unix domain sockets](unix-domain-sockets) — the local primitive that NIPC extends across the domain.
- [Peer credentials](peer-credentials) — `SO_PEERCRED`, `SO_PEERSEC`, `SO_PEERTOKEN` — what the server sees on a NIPC connection.
- [Primary vs impersonation tokens](../identity/primary-vs-impersonation-tokens) — the kind of token NIPCd mints on the receiving side.
- [File security descriptors](../access-control/file-security-descriptors) — the SD model that gates both `nipc.sock` and the destination socket.
