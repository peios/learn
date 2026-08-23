---
title: What Is Shared with PGSS Logon
description: A checklist of exactly what PSI shares with PGSS Logon unchanged, what it adds, and what it changes.
---

PSI is a superset of PGSS Logon (§2.5). This appendix consolidates
exactly what is shared, what is added, and what differs — as a checklist
for an implementer building both, and as the list to re-examine whenever
either specification changes.

## Shared unchanged

| Element | PGSS | Note |
|---|---|---|
| `LogonStart` body | §2.7 | Nested whole inside `Authenticate`, never inlined (§2.7) |
| `CredentialRequest` body | §2.8 | Byte-for-byte identical |
| `CredentialResponse` body | §2.8 | Byte-for-byte identical |
| `profile` body | §2.9 | Nested inside `Assertion`, relayed onward unchanged (§2.13) |
| Denial codes | §2.B | Reused by `Refusal` (§2.13) |
| Lookup result body, `present` onward | §2.16 | Nested inside a `QueryResult` entry (§2.15) |
| Field bitmask | §2.B | Carried unchanged by `Query` (§2.15) |
| Object kinds | §2.B | Carried unchanged by a key entry (§2.15) |
| Lookup outcomes | §2.B | A source may send three of the five (§2.B) |
| Header layout, first 12 bytes | §2.6 | Same fields at the same offsets |
| Byte order, string encoding, length framing | §2.6 | See §2.7 |
| Extensibility rules | §2.6 | Append-only; new enum value is breaking |
| Credential-handling obligations | §2.12 | Bind sources too (§2.21) |
| Name rules | §2.15 | Bind what a source asserts (§2.13) |

An implementation that reimplements any of these rather than sharing one
definition has taken on the job of keeping two copies in step. The
sharing is the point: a translation layer between two byte-identical
formats is a place for them to drift.

## Added by PSI

| Element | Defined in |
|---|---|
| `conversation` header field | §2.7 |
| `Register` / `Registered` | §2.8 |
| `Authenticate`, wrapping `LogonStart` plus `originator` | §2.11 |
| `Assertion` | §2.13 |
| `Abandon` | §2.14 |
| Domain claim and its checks | §2.10 |
| POSIX identifiers, and the ranges that confine them | §2.13, §2.20 |
| Claims carried from a source | §2.13 |
| `Query` / `QueryResult`, and batching | §2.15 |
| `EnumerateSource` / `EnumerateResult`, and cursors | §2.16 |
| `Changed`, and the cache contract | §2.17 |
| Source capabilities, TTL and batch limit | §2.8 |
| Relative key types, where PGSS Logon's are absolute | §2.15, §2.B |
| Identity, membership and numeric scope | §2.18 to §2.20 |

## Differs

| | PGSS Logon | PSI |
|---|---|---|
| Magic | `PGSL` | `PPSI` |
| Header | 12 bytes | 20 bytes |
| Maximum message | 65536 | 81920 |
| Conversations per connection | one | many |
| Connection lifetime | one logon | the source's lifetime |
| High bit of `msg_type` | authority → client | source → authority |
| Success terminal | `AccessGranted` + token fd | `Assertion` — no session, no token |
| Socket path | normative | the implementation's choice |
| Key type `3` | absolute POSIX identifier | relative identifier |

The success terminal is what makes minting structurally impossible for a
source (§2.4); the socket path is normative in PGSS because it is a
conformance bar and not here because PSI is not one (§2.1).

The message ceiling is the row most likely to catch an implementer out,
because the larger number is the one that does *not* bind a reply — see
§2.A.

## When either specification changes

A field appended to `LogonStart`, `CredentialRequest`,
`CredentialResponse` or `profile` in PGSS appears here automatically,
because the bodies are shared. That is the intended behaviour and needs
no change to this chapter.

The profile is the one shared body that travels in the *opposite*
direction to the others: the interrogation bodies pass from the
authority outward to the client, while the profile originates at the
source and is relayed outward through the authority. It is shared for
the same reason regardless — one definition, so the value a source
states and the value a client reads cannot drift apart.

A new `Denial` value, a new `CredentialType`, or any change to the
header's first twelve bytes is a **breaking change to both** and requires a
coordinated version bump. An implementer maintaining both MUST NOT bump
one alone.
