---
title: Message Reference
description: Every PLPS message by number, which reply answers which request, the protocol constants and the field limits.
---

## Messages

| `msg_type` | Message | Direction | Answered with | Defined in |
|---|---|---|---|---|
| `0x0001` | `List` | client → store daemon | `Principals` | §10.5 |
| `0x0002` | `Show` | client → store daemon | `Principal` | §10.5 |
| `0x0003` | `Domain` | client → store daemon | `DomainIs` | §10.5 |
| `0x0004` | `Add` | client → store daemon | `Created` | §10.5 |
| `0x0005` | `Remove` | client → store daemon | `Done` | §10.5 |
| `0x0006` | `SetEnabled` | client → store daemon | `Done` | §10.5 |
| `0x0007` | `SetPassword` | client → store daemon | `Done` | §10.5 |
| `0x0008` | `GroupAdd` | client → store daemon | `Done` | §10.6 |
| `0x0009` | `GroupRemove` | client → store daemon | `Done` | §10.6 |
| `0x000a` | `GroupList` | client → store daemon | `Groups` | §10.6 |
| `0x000b` | `GroupCreate` | client → store daemon | `Created` | §10.6 |
| `0x000c` | `GroupDelete` | client → store daemon | `Done` | §10.6 |
| `0x000d` | `SetProfile` | client → store daemon | `Done` | §10.5 |
| `0x000e` | `SetPrimaryGroup` | client → store daemon | `Done` | §10.6 |
| `0x000f` | `SetClaim` | client → store daemon | `Done` | §10.7 |
| `0x0010` | `RemoveClaim` | client → store daemon | `Done` | §10.7 |
| `0x0011` | `KeyList` | client → store daemon | `Keys` | §10.8 |
| `0x0012` | `KeyAdd` | client → store daemon | `Done` | §10.8 |
| `0x0013` | `KeyRemove` | client → store daemon | `Done` | §10.8 |
| `0x0014` | `CredentialPolicy` | client → store daemon | `Done` | §10.8 |
| `0x0015` | `Rename` | client → store daemon | `Done` | §10.5 |
| `0x0016` | `SetLogonTypes` | client → store daemon | `Done` | §10.5 |
| `0x0017` | `GroupRename` | client → store daemon | `Done` | §10.6 |
| `0x0018` | `GroupDescribe` | client → store daemon | `Done` | §10.6 |
| `0x8001` | `Principals` | store daemon → client | | §10.5 |
| `0x8002` | `Principal` | store daemon → client | | §10.5 |
| `0x8003` | `DomainIs` | store daemon → client | | §10.5 |
| `0x8004` | `Created` | store daemon → client | | §10.9 |
| `0x8005` | `Done` | store daemon → client | | §10.9 |
| `0x8006` | `Failed` | store daemon → client | | §10.9 |
| `0x8007` | `Groups` | store daemon → client | | §10.6 |
| `0x8008` | `Keys` | store daemon → client | | §10.8 |

Any request may be answered with `Failed` instead.

## Protocol constants

| Constant | Value | Defined in |
|---|---|---|
| Socket path | `/run/lpsd/admin.sock` on Peios | §10.3 |
| Magic | `PLPS` (`50 4c 50 53`) | §10.4 |
| Version | `1` | §10.4 |
| Header size | 12 bytes | §10.4 |
| Maximum message size | 2,097,152 bytes | §10.4 |
| Requests a connection | 1 | §10.3 |

## Field limits

| Field | Limit |
|---|---|
| A principal's or group's name | 256 bytes |
| A password | 4096 bytes, never empty |
| `home`, `shell` | 4096 bytes |
| `display_name` | 256 bytes |
| A group's `description` | 1024 bytes |
| A principal's listed groups | 128 |
| Principals in `Principals` | 4096 |
| Groups in `Groups` | 4096 |
| A SID | 68 bytes |
| Claims on a principal | 64 |
| A claim's name | 255 bytes |
| A claim's values | 64 |
| A string or octet claim value | 1024 bytes |
| SSH keys on a principal | 32 |
| An SSH public key | 16384 bytes |
| A key's label | 128 bytes |
| A key's fingerprint | 128 bytes |
| A refusal's `reason` | 512 bytes |

## Enumerations

| Enumeration | Defined in |
|---|---|
| Failure | §10.9 |
| Credential policy | §10.8 |
| Logon types | PGSS §2.16, carried as PSI carries them (§2.13) |
| Claim value types and flags | PCDS §5.9, closed as on PSI (§2.A) |
