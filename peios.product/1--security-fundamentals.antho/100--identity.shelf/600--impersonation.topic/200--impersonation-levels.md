---
title: Impersonation levels
type: concept
description: The four impersonation levels — Anonymous, Identification, Impersonation, Delegation — what each permits, and the pitfalls each one produces.
related:
  - peios/impersonation/overview
  - peios/impersonation/the-two-gates
  - peios/impersonation/peer-tokens
---

Every token carries an **impersonation level** — one of four values, ordered from least to most permissive. On an impersonation token it is the answer to "how much may a server do with this identity?". On a primary token it is the ceiling on everything derived from that process's identity. Each level admits all the operations of the levels below it and additionally allows specific extra things.

There is one rule worth pinning before the catalog: **the level is set by the client, not the server.** A client sets `KACS_SO_IMPERSONATION_LEVEL` on the socket (`setsockopt` under the `SOL_KACS` level, or `peios_socket_set_impersonation_level`) before `connect()` to declare the maximum level a server may use. The kernel records the level on the socket. When the server later impersonates the peer, the level cannot exceed what the client set. A server cannot ask for a higher level; it can only end up at the level the client granted or lower.

## The four levels

The numeric values are also catalogued in [Other constants](~peios/constants-and-catalogs/other-constants).

| Value | Name | What a server may do |
|---|---|---|
| 0 | **Anonymous** | Nothing identity-related. The impersonation token has the Anonymous SID as its user; the server learns nothing about the actual client. |
| 1 | **Identification** | Inspect the client's identity. The server may read the client's SIDs, groups, integrity level, and privileges — but the token must not be used for AccessCheck. Any access check using an Identification-level token is denied immediately, no matter what the DACL says. |
| 2 | **Impersonation** | Act as the client for all local operations. This is the default and the level most server-to-client code paths assume. |
| 3 | **Delegation** | Identical to Impersonation locally, plus the client's credentials may be forwarded to a remote machine over Kerberos. The kernel only records that Delegation was granted; the actual forwarding is authd's responsibility. |

The default — what a socket carries if the client never sets a level — is **Impersonation**. This default exists because the vast majority of clients want their server to be able to act on their behalf; making the no-action case the conservative one would push every client into boilerplate.

## Anonymous

The least useful level, and not as common as you might expect. An Anonymous impersonation token has:

- A user SID of `S-1-5-7` (the well-known Anonymous SID).
- The Everyone group, but **not** Authenticated Users.
- Untrusted integrity.
- No privileges.

A server impersonating an Anonymous client effectively has no identity at all. It can act, but every access check is evaluated as Anonymous — which usually fails because almost every interesting object's DACL grants nothing to Everyone-but-not-Authenticated-Users.

You will mostly see Anonymous in two cases:

- **A client explicitly opted out of identity disclosure.** Some protocols want the server to act on a request without knowing who issued it. The client sets its socket's level to Anonymous; the server impersonates and gets Anonymous.
- **A connection that was never authenticated.** A network peer that connected without going through any auth step is, from the server's point of view, Anonymous. The token reflects this honestly.

## Identification

The most misleading level. Identification gives the server enough of the client's token to **inspect** identity but explicitly forbids using it for access decisions. AccessCheck with an Identification-level token returns ACCESS_DENIED immediately, before reading the DACL.

The intended use is for servers that need to know who is asking — for audit logging, for routing decisions, for displaying a username — without actually wanting to act as them. A web server that logs which user made each request but always reads files as itself wants Identification.

The pitfall: a server that thinks it is doing Impersonation but the client set the level to Identification finds every file open returning ACCESS_DENIED for reasons that look nothing like an identity problem. The DACL is fine; the user has rights to the file; the server's primary identity has rights to the file. Yet every access fails. The cause is almost always that the client connected at Identification level and the server is supposed to be inspecting, not acting.

The fix is at the client end. If your server has to act on behalf of the user, the client must connect at Impersonation level (or accept the default — which is already Impersonation).

There is one specific construction that always produces an Identification-level token: `KACS_IOC_GET_LINKED_TOKEN` called without `SeTcbPrivilege` returns an Identification-level clone of the partner token. The clone is for inspection only — it cannot be installed and would fail every access check if it were. See [Elevation and linked tokens](~peios/security-fundamentals/tokens/elevation).

## Impersonation

The level you will use almost all of the time. An Impersonation-level token can act as the client for any local operation:

- Open files as the client.
- Read and modify registry keys as the client.
- Connect to other local services as the client (and have those services impersonate the same client — see "Identity cascading" in [Peer tokens and capture](~peios/impersonation/peer-tokens)).
- Be the subject of any AccessCheck call.

What an Impersonation-level token cannot do is cross the machine boundary with the client's identity. If the impersonating service makes a network request that requires authentication, that request goes out using the service's credentials, not the client's. The client's identity stays on this machine.

That last point is the dividing line between Impersonation and Delegation.

## Delegation

Delegation extends Impersonation to remote calls. A server at Delegation level can act as the client locally and forward the client's identity to a remote machine over Kerberos. The remote service receives a token that represents the original client, not the intermediary.

The mechanism is entirely in authd. KACS records that the impersonation token was granted Delegation; the kernel does nothing further. When the impersonating server makes an outbound network request, authd consults the token's level. If it sees Delegation, authd performs the Kerberos credential forwarding (constrained or unconstrained, depending on the domain policy). If it sees only Impersonation, authd authenticates the outbound request as the server's own identity.

The split — KACS records the flag, authd acts on it — keeps the kernel out of the Kerberos business. It also means Delegation is meaningful only on domain-joined machines where authd has Kerberos configured. On a standalone machine, Delegation is recorded but has no effect, since there are no remote services to forward to.

## What sets the level

Three things determine the level a server actually ends up with:

1. **The client's request**, set on the socket with the `KACS_SO_IMPERSONATION_LEVEL` socket option (`peios_socket_set_impersonation_level`) — usually before connect, though it can change at any time and bounds every capture made from then on. Default is Impersonation if the client says nothing.
2. **The two-gate model**, applied at impersonation time: the identity gate and the integrity ceiling. Either can cause the granted level to be silently downgraded. See [The two-gate model](~peios/impersonation/the-two-gates).
3. **The transport.** Datagram and socketpair sockets capture nothing at connect, so identity on them travels per message (`KACS_SO_PASS_TOKEN` or a `KACS_SCM_TOKEN` cmsg); pipes carry no identity at all, and a server on a pipe must obtain a token some other way and use the explicit-fd ioctl. See [Peer tokens and capture](~peios/impersonation/peer-tokens).

The first sets the maximum. The second can lower it. The third is about the mechanism for getting the token at all.

There is a fourth input that usually never shows, because it starts at the top: **the client's own token**. The level is a ratchet. A logon token from authd starts at Delegation, and every step identity takes — a capture at connect, a `KACS_SO_PASS_TOKEN` send, a `KACS_IOC_DUPLICATE` in either direction — produces something at or below its source. A process running on a primary that was made from an Impersonation-level token can set Delegation on every socket it opens and still conveys Impersonation. Nothing short of a fresh `CreateToken` (`SeCreateTokenPrivilege`) goes back up, which is what makes the client's original choice hold across any number of services and process launches.

## Inspecting the granted level

A server that has just impersonated can read its own effective token to check what level it actually got. Reading the `impersonation_level` field of the effective token (via `KACS_IOC_QUERY` on the thread's token fd) returns the level in effect.

This is worth doing at runtime if your code branches on level. The "client asked for Impersonation, but the integrity ceiling silently downgraded to Identification" case is silent by design — the impersonation call succeeds and the work proceeds, but every access check on the downgraded token will fail. Code that wants to detect the downgrade before doing access-requiring work should query the level first and skip work for which the level is insufficient.

## Where to go next

For how the kernel decides the level a server actually ends up with — and why the downgrade is silent — read [The two-gate model](~peios/impersonation/the-two-gates).

For how a server gets hold of a client's identity in the first place, read [Peer tokens and capture](~peios/impersonation/peer-tokens).
