---
title: Registration
description: The first message on every connection — the source's name, domain, capabilities, TTL, batch limit and the identifier range it is granted.
---

A connection opens with registration. Nothing else may precede it.

## Register

`msg_type` = `0x8001`. Source to authority, on conversation `0`.

| Field | Encoding | Limit |
|---|---|---|
| `source_name` | string | 32 bytes |
| `domain` | length-framed bytes (SID) | 68 bytes |
| `capabilities` | `u32` | §2.B |
| `entry_ttl` | `u32` | seconds |
| `max_batch` | `u32` | 64 |

### source_name

What the source calls itself. Bounded at 32 bytes because it becomes the
authentication-package name on every session the source authenticates —
so a token's provenance answers *which source vouched for this?* rather
than merely *the authority minted it*.

The name is a **claim**. It MUST be cross-checked against the identity
the authority established for itself (§2.9), and it MUST NOT be used for
anything else. A mismatch MUST be refused rather than quietly corrected:
a service registering under another's name is worth failing on, not
normalising.

### domain

The SID namespace this source is authoritative for (§2.10).

### capabilities

What the source can do beyond authenticating.

| Bit | Name | Meaning |
|---|---|---|
| 0 | `QUERIES` | Answers `Query` (§2.15). |
| 1 | `ENUMERATES` | Answers `EnumerateSource` (§2.16). |
| 2 | `MEMBERS` | Can produce a group's membership. |
| 3 | `PUSHES_CHANGES` | Sends `Changed` (§2.17). |

An authority MUST NOT send a message a source did not declare it
answers, and MUST NOT set a field bit gating a capability the source did
not declare. A source declaring nothing authenticates and does nothing
else, which is what a source predating these fields is saying by
omission — and is the only reading that keeps such a source working.

A source that declares no `QUERIES` cannot be asked about its principals
outside a logon, so they are unresolvable through PGSS Logon's identity
channel: they can sign in and will appear as bare numbers everywhere
else. That is a coherent configuration and this chapter permits it, but
it is almost never what an administrator intended, and an authority
SHOULD report it where one will see it — as it reports a source
registering with no identifier range.

This is a declaration of capability, not of willingness. A source
declaring `QUERIES` may still answer `Refused` to any particular
question (§2.15); a source declaring `ENUMERATES` may still refuse a
cursor it can no longer honour (§2.16).

### entry_ttl

How long, in seconds, the authority may hold an answer from this source
before asking again.

**Zero means do not cache.** A source declaring neither
`PUSHES_CHANGES` nor a non-zero `entry_ttl` has said its answers must
not be held at all, and an authority MUST honour that — see §2.17, where
the reasoning for reading silence that way is set out.

`entry_ttl` and `PUSHES_CHANGES` are not exclusive, and a source
declaring the second SHOULD declare a non-zero first as well. See §2.17:
the TTL is the backstop against a notification that was never sent.

### max_batch

The largest number of keys the source will accept in one `Query`
(§2.15). Zero means one.

An authority MUST NOT exceed it, and MUST NOT send more than 64 keys
whatever the source declared: an encoder MUST NOT declare more, and a
decoder MUST read a larger declaration as 64.

A source MUST still validate what it receives. The field is a hint the
authority is required to respect, not a guarantee about what will
arrive.

## Registered

`msg_type` = `0x0001`. Authority to source, on conversation `0`.

| Field | Encoding |
|---|---|
| `unix_id_base` | `u32` |
| `unix_id_count` | `u32` |

Load-bearing beyond its contents. A source SHOULD report itself ready
only once it has received this, so that anything ordered after the
source finds a system that can actually authenticate rather than merely
a process that exists (§2.3).

### unix_id_base, unix_id_count

The POSIX identifier range the authority has assigned this source
(§2.20). A base of **0** means no range was assigned, and every
principal the source asserts will project as unmapped.

**Informational.** A source counts within its range and asserts relative
identifiers; the authority applies the base. A source MUST NOT apply it
— see §2.20, where the reasoning is set out in full.

It is sent so that a source's administration tools can show an operator
the identifier a principal will really project to, rather than the
relative number the source stores. Without it that arithmetic falls to
the operator.

An authority that predates these fields sends neither, and a source MUST
read their absence as *no range assigned* — which is what such an
authority means, since it has no ranges to assign.

## Rules

1. A connection MUST open with `Register` on conversation `0`. An
   authority MUST refuse any connection that opens otherwise.
2. An authority MUST bound the time it waits for the opening `Register`,
   and close the connection on expiry. A peer that connects and says
   nothing MUST NOT be able to hold resources indefinitely.
3. An authority MUST NOT admit two sources under one name at the same
   time.
4. An authority MUST send `Registered` only after the source is
   routable, so that a logon racing the acknowledgement cannot find a
   source that is registered but not yet reachable.
5. A source MUST NOT send any other message before receiving
   `Registered`.
6. An authority SHOULD report, where an administrator will see it, that
   a source registered with no identifier range — its principals will
   all project as unmapped, and the cause is a configuration omission
   rather than anything the source did.
