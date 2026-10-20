---
title: The Self Socket
description: How any principal reads their own account from the store daemon and sets their own display name — a second socket whose requests never name anybody, and how the daemon serves it without letting a caller stall it.
---

The admin socket (§10.3) is for administrators, and every request on it
names the principal it is about. A principal also needs to see their own
account — what they are called, what they sign in with, which SSH keys
they have — and to set what they are called, without being an
administrator. The **self socket** serves that: any authenticated
principal may connect to it, and no request on it names anybody.

Changing a credential is not here. A display name is not a credential,
so setting it asks for no proof; a password or an SSH key is one, so
changing either goes through PGSS Logon, where the principal's current
password is asked for (PGSS §2.20 and PGSS §2.23).

## The socket

The store daemon listens on a second Unix stream socket. On Peios it is
`/run/lpsd/self.sock`.

Its descriptor MUST admit every authenticated principal to connect. On
Peios it is `D:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;0x100082;;;AU)`: SYSTEM and
Administrators with full access, and Authenticated Users with exactly
what a connect needs (`FILE_WRITE_DATA`, `READ_ATTRIBUTES` and
`SYNCHRONIZE`), the mask Peios grants them on `/run/logon.sock`.
The store daemon sets it when it creates the socket and reads it back;
the socket's directory admits nobody the socket is for, so a socket that
inherited it would be closed to everyone it exists to serve.

## The subject is the peer

The subject of every request is the **user of the connected peer's
token**, read by the store daemon from the connection when it accepts
it. No request carries a name, a SID or any other way to point at a
principal, and the store daemon MUST NOT answer about, or change, any
principal but that one.

A peer whose user the store does not hold — `SYSTEM`, a service
identity, a principal another source holds — is refused with `NotFound`
and a reason saying so. It is never shown, or allowed to change,
somebody else's account.

## Framing

Messages are PLPS's (§10.4): the same header, magic, encoding and
`Failed` and `Done` replies (§10.9). The requests are in a range of
their own, `0x0040` upward, with their reply at `0x8040`. Each socket
MUST refuse the other's requests with `Invalid`: the self socket is not
a second way to administer the store, and the admin socket does not
answer about its caller.

A request on the self socket MUST NOT exceed **4096 bytes**. The store
daemon MUST refuse, from its header and without reading the body, one
that declares more, answering `Invalid`. Replies are bounded by PLPS's
ceiling as on the admin socket.

## One request a connection, never served blocking

Each connection carries one exchange, as on the admin socket (§10.3).

The admin socket admits only administrators, so a store daemon MAY
serve it a connection at a time. The self socket admits everyone, and a
store daemon that also answers PSI (§2) MUST NOT let a connection on it
delay anything else: a principal who connected and sent nothing would
otherwise stall every sign-in behind them. A store daemon MUST serve the
self socket without blocking on any one connection, MUST bound how long
a connection may remain open from accept to the last byte of its reply,
and MUST bound the connections open at once and the connections any one
user, by the token's user SID, holds. A caller over a bound is refused,
with `Failed` where that will not block, and the connection closed.

On Peios lpsd holds each connection non-blocking in a table its poll
loop drives, and drops one at **5 seconds** after accept. It holds at
most **32** at once and **4** from any one user.

## ShowSelf

`msg_type` = `0x0040`. Empty body. Answered with `Self`.

## Self

`msg_type` = `0x8040`. The caller's own account.

| Field | Encoding |
|---|---|
| `name` | string, 256 bytes |
| `sid` | byte string, 68 bytes |
| `display_name` | string, 256 bytes; empty when unset |
| `enabled` | boolean |
| `policy` | `u8`: the credential policy (§10.8) |
| `has_password` | boolean: whether the account has a password at all |
| `keys` | array of at most 32 length-framed keys |

A key:

| Field | Encoding |
|---|---|
| `id` | byte string, 16 bytes: as `Keys` gives it (§10.8) |
| `fingerprint` | string, 128 bytes: as `ssh-keygen -l` writes one |
| `algorithm` | string, 64 bytes: the key's type, such as `ssh-ed25519` |
| `label` | string, 128 bytes |
| `created` | `u64`: seconds since the Unix epoch |

`has_password` is separate from `policy` because a policy can name a
password the account has not got, and a principal adding or removing a
key must prove a password (PGSS §2.23). A client SHOULD offer key
changes only where the account has one.

This is what `Show` and `KeyList` give an administrator about the same
principal, less what is the administrator's to manage. Nothing in it is
a verifier, a key's private half or anything a credential could be
recomputed from.

## SetDisplayName

`msg_type` = `0x0041`. Answered with `Done`.

| Field | Encoding |
|---|---|
| `display_name` | string, 256 bytes; empty clears it |

The store daemon MUST validate it exactly as it validates `SetProfile`'s
`display_name` (§10.5), refusing what that refuses with `Invalid`. It
MUST refuse with `Denied` a principal that is disabled: a session that
outlived its account's disabling is not a way to change the account.

The change is applied as any other (§10.9): made durable before `Done`,
undone and answered `Internal` if it cannot be saved, and announced to
the authority as PSI's `Changed` (§2.17) so that its identity channel
answers with the new name at once. A request that changes nothing — the
name is already that — MAY be answered `Done` without writing.

## Conformance

**A store daemon serving the self socket** admits every authenticated
principal to connect to it; answers every request about the peer's
token's user and nobody else, and refuses a peer it does not hold with
`NotFound`; refuses the admin socket's requests with `Invalid`, and a
request over 4096 bytes from its header; never blocks on one connection,
and bounds each connection's time, the connections open, and each user's
connections; validates `SetDisplayName` as `SetProfile`, refuses it for
a disabled principal, and makes, undoes and announces it as §10.9
requires.

**A client of the self socket** names nobody, since there is no field
to; opens a connection for each request; treats a `connect` refused for
permission as `Denied`; and changes credentials through PGSS Logon, not
here.
