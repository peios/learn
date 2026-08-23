---
title: Message Reference
description: Every PSI message by number and direction, the protocol constants, and the field limits — including the ceiling that actually binds a page.
---

## Messages

| `msg_type` | Message | Direction | Conversation | Defined in |
|---|---|---|---|---|
| `0x8001` | `Register` | source → authority | `0` | §2.8 |
| `0x0001` | `Registered` | authority → source | `0` | §2.8 |
| `0x0002` | `Authenticate` | authority → source | 1+ (opens) | §2.11 |
| `0x8002` | `CredentialRequest` | source → authority | 1+ | §2.12 |
| `0x0003` | `CredentialResponse` | authority → source | 1+ | §2.12 |
| `0x8003` | `Assertion` | source → authority | 1+ (terminal) | §2.13 |
| `0x8004` | `Refusal` | source → authority | 1+ (terminal) | §2.13 |
| `0x0004` | `Abandon` | authority → source | 1+ (terminal) | §2.14 |
| `0x0005` | `Query` | authority → source | 1+ (opens) | §2.15 |
| `0x8005` | `QueryResult` | source → authority | 1+ (terminal) | §2.15 |
| `0x0006` | `EnumerateSource` | authority → source | 1+ (opens) | §2.16 |
| `0x8006` | `EnumerateResult` | source → authority | 1+ (terminal) | §2.16 |
| `0x8007` | `Changed` | source → authority | `0` | §2.17 |

The high bit marks a message sent by **the source**, which is the
authority for its own principals (§2.7).

## Protocol constants

| Constant | Value | Defined in |
|---|---|---|
| Socket path | the implementation's choice | §2.6 |
| Magic | `PPSI` (`50 50 53 49`) | §2.7 |
| Version | `1` | §2.7 |
| Header size | 20 bytes | §2.7 |
| Maximum message size | 81920 bytes | §2.7 |
| Reserved conversation | `0` | §2.7 |

## Field limits

| Field | Maximum | Defined in |
|---|---|---|
| `source_name` | 32 bytes | §2.8 |
| `domain` | 68 bytes | §2.8 |
| `max_batch` | 64 | §2.8 |
| `originator` | 68 bytes | §2.11 |
| `user_sid` | 68 bytes | §2.13 |
| `canonical_name` | 256 bytes | §2.13 |
| `groups` | 128 entries, each SID 68 bytes | §2.13 |
| `primary_group` | 68 bytes | §2.13 |
| `claims` | 64 entries | §2.13 |
| claim `name` | 255 bytes | §2.13 |
| claim `values` | 64 per claim | §2.13 |
| claim string value | 1024 bytes | §2.13 |
| claim octet value | 1024 bytes | §2.13 |
| claim SID value | 68 bytes | §2.13 |
| `reason` | 512 bytes | §2.13 |
| `keys` | 64 entries | §2.15 |
| key `name` | 256 bytes | §2.15 |
| `results` | 64 entries | §2.15 |
| `withheld` | 32 entries | §2.15 |
| `values` | 32 entries | §2.15 |
| `entries` | 256 entries | §2.16 |
| `cursor`, `next` | 256 bytes | §2.16 |

68 bytes is the largest a SID can be: an eight-byte prelude plus fifteen
sub-authorities (§2.7).

A claim name is bounded at 255 **bytes** of UTF-8 while PCDS §5.9 bounds
it at 255 UTF-16 code units. A string's UTF-16 length never exceeds its
UTF-8 byte length, so the byte bound is the stricter of the two and
satisfies PCDS without transcoding to find out.

The claim limits are otherwise tighter than PCDS §5.9 permits — it
allows 1024 values per claim. These bound the work an authority does
decoding a message it has not yet decided to believe, and nothing needs
a thousand-valued claim from a principal source.

Fields inside a nested `LogonStart`, `CredentialRequest`,
`CredentialResponse` or profile keep PGSS Logon's limits (PGSS §2.A).

## The ceiling that actually binds a page

None of the entry counts above is the constraint on how much a source
may return. **An entry that fits a PSI message need not fit the PGSS
Logon message the authority must re-encode it into**: this chapter's
ceiling is 81920 bytes and PGSS Logon's is 65536, and a `QueryResult` or
`EnumerateResult` entry travels outward inside the smaller one.

A source MUST therefore bound a reply by the **smaller** of the two
ceilings, not by this one, and MUST page rather than fill a PSI message
it knows an authority cannot forward. A page that fits here and not
there is a page nobody can deliver, and the entry-count bounds do not
prevent one — 256 entries of a few hundred bytes each exceeds both.

The margin an implementation leaves for the authority's own framing is
its own choice; leaving none is a defect.
