---
title: AccessGranted
description: The terminal success message — the token passed as a file descriptor and never named, the session id, and the profile that comes with it.
---

`msg_type` = `0x8002`. Authority to client. One of the two terminal
messages; nothing follows it.

| Field | Encoding |
|---|---|
| `session_id` | `u64` |
| `profile` | length-framed structure, optional |

**Ancillary data: the token, as one file descriptor via `SCM_RIGHTS`.**

## The descriptor

The token MUST be transferred as a file descriptor attached to this
message. It MUST NOT be named, and there MUST be no path, handle, or
identifier by which another process could reach it.

Possession of the conversation is what confers the token. There is no
window in which a minted token exists under a name something else could
open, and no lookup that could be raced or guessed.

A client MUST read the descriptor from the ancillary data of this
message. An `AccessGranted` arriving without one is a protocol violation
and MUST be treated as a failed logon — a client MUST NOT proceed as
though a logon succeeded when it holds no token.

## session_id

The logon session the token belongs to. The client MAY record it, MAY
report it, and needs it to relate this logon to the kernel's session
records.

It is informational to the protocol. The token is the thing that confers
authority; the session identifier merely names the session the token
already belongs to.

## profile

Where the session starts, and what to call the principal. A
length-framed structure, so it can grow without displacing anything
appended to `AccessGranted` after it.

| Field | Encoding | Limit |
|---|---|---|
| `home` | string | 4096 |
| `shell` | string | 4096 |
| `display_name` | string | 256 |

`profile` is an optional trailing field. **Every field may be empty**,
and an empty field means *the authority did not say*. An authority that
knows nothing about home directories is conforming, and so is one that
omits the whole structure — a client MUST treat an absent `profile`
exactly as it treats one whose fields are all empty.

A client MUST have a fallback for each field and MUST NOT treat an empty
value as an error.

`home` and `shell`, when non-empty, MUST be absolute paths. A client
MUST NOT execute a relative `shell` or resolve a relative `home` against
its own working directory. An authority with no value for a field MUST
leave it empty rather than invent one.

### Why this is on the terminal message

Nothing here is an access-control input. No ACL names a home directory,
and the token carries none of these fields — so this is not identity,
and an authority that got it wrong would produce an inconvenient session
rather than an unsafe one.

It is here because the authority has just read these values in order to
decide the logon, and a caller that needs them in order to *start a
session* would otherwise have to ask a second time. A logon originator
cannot `chdir` or `exec` without them.

### What this is not

It is not a directory lookup, and it MUST NOT be treated as one. It
answers for exactly one principal — the one who just authenticated — at
exactly one moment. It cannot answer for anybody else, it cannot answer
for a principal who never logged on, and nothing in this protocol says
what it means an instant later.

Resolving arbitrary principals to home directories or shells is §2.16's,
and a client that caches these values as though they had come from there
has misread them.

### display_name

A human's name for a human to read.

It is deliberately **not** a GECOS field. GECOS is a comma-separated
`/etc/passwd` artefact carrying a name, an office, and two telephone
numbers in one string; a protocol that carried one would oblige every
client to parse it apart, and would tie this chapter to a file format it
has nothing to do with.

An implementation that must produce a GECOS field renders it *from*
this, not the other way round.

> [!NOTE]
> A client is not obliged to *use* any of this. Falling back to a fixed
> shell, or ignoring `display_name` entirely, is conforming. The fields
> exist so that a client which wants them does not need a second
> protocol.

## What the client does next

Installs the token, if that is what it wanted. The authority is not
involved and MUST NOT be told (§2.1).

A client that decides not to install the token MUST close the
descriptor. A logon session whose token is never installed still exists
as far as the kernel is concerned.

A client SHOULD NOT fail a logon because a `home` it was given does not
exist. The principal has authenticated and holds a token; refusing to
start their session over a missing directory turns a cosmetic problem
into being locked out. Starting elsewhere and saying so is the better
failure.
