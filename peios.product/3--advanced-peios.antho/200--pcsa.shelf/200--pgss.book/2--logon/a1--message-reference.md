---
title: Message Reference
description: Every message type by number and socket, the protocol constants, and the field limits.
---

## Messages

### On `/run/logon.sock`

| `msg_type` | Message | Direction | Defined in |
|---|---|---|---|
| `0x0001` | `LogonStart` | client → authority | §2.7 |
| `0x0002` | `CredentialResponse` | client → authority | §2.8 |
| `0x8001` | `CredentialRequest` | authority → client | §2.8 |
| `0x8002` | `AccessGranted` | authority → client | §2.9 |
| `0x8003` | `AccessDenied` | authority → client | §2.10 |

### On `/run/ident.sock`

| `msg_type` | Message | Direction | Defined in |
|---|---|---|---|
| `0x0010` | `Lookup` | client → authority | §2.16 |
| `0x0011` | `Enumerate` | client → authority | §2.17 |
| `0x8010` | `LookupReply` | authority → client | §2.16 |
| `0x8011` | `EnumerateReply` | authority → client | §2.17 |

The high bit marks a message sent by the authority (§2.6). The two
ranges are disjoint, and a message of one range MUST be refused on the
other socket (§2.14).

## Protocol constants

| Constant | Value | Defined in |
|---|---|---|
| Logon socket path | `/run/logon.sock` | §2.5 |
| Identity socket path | `/run/ident.sock` | §2.14 |
| Magic | `PGSL` (`50 47 53 4c`) | §2.6 |
| Version | `1` | §2.6 |
| Header size | 12 bytes | §2.6 |
| Maximum message size | 65536 bytes | §2.6 |

## Field limits

| Field | Maximum | Defined in |
|---|---|---|
| `identifier` | 1024 bytes | §2.7 |
| `tty` | 128 bytes | §2.7 |
| `remote_host` | 256 bytes | §2.7 |
| `supported_credential_types` | 32 entries | §2.7 |
| `messages` | 8 entries | §2.8 |
| `prompts` | 16 entries | §2.8 |
| `answers` | 16 entries | §2.8 |
| `text` | 512 bytes | §2.8 |
| `credential_name` | 128 bytes | §2.8 |
| `data` | 32768 bytes | §2.8 |
| `home` | 4096 bytes | §2.9 |
| `shell` | 4096 bytes | §2.9 |
| `display_name` | 256 bytes | §2.9 |
| `reason` | 512 bytes | §2.10 |
| `name` (lookup key) | 256 bytes | §2.16 |
| `sid` | 68 bytes | §2.16 |
| `qualified_name` | 512 bytes | §2.16 |
| `withheld` | 32 entries | §2.16 |
| `values` | 32 entries | §2.16 |
| reference `name` | 512 bytes | §2.16 |
| `HOME`, `SHELL` | 4096 bytes | §2.16 |
| `DISPLAY_NAME` | 256 bytes | §2.16 |
| `GROUPS` | 128 entries | §2.16 |
| `MEMBERS` | 256 entries | §2.16 |
| `CLAIMS` | 64 entries | §2.16 |
| `of_name` | 256 bytes | §2.17 |
| `cursor`, `next` | 256 bytes | §2.17 |
| `entries` | 256 entries | §2.17 |
| `incomplete` | 32 entries | §2.17 |
| `incomplete` source name | 32 bytes | §2.17 |

The 68-byte SID maximum is a property of the SID encoding rather than of
this chapter: an eight-byte prelude plus the fifteen sub-authorities the
one-byte count admits. It is specified in PCDS.

An encoder MUST refuse to produce a field exceeding its maximum; a
decoder MUST reject one it receives (§2.6).
