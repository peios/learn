---
title: Well-Known SIDs Reference
type: how-to
order: 160
description: Reference table of well-known SIDs including universal, NT Authority, built-in, service, and confinement SIDs.
---

Well-known SIDs have fixed, universal meaning across every Peios installation and every domain. This page is a reference for the most commonly encountered ones.

## Universal well-known SIDs

| SID | Name | Meaning |
|---|---|---|
| `S-1-0-0` | Null | No identity. Used as a placeholder. |
| `S-1-1-0` | Everyone | Matches every principal, including anonymous |
| `S-1-1-7` | Anonymous | The anonymous identity — used when no authentication has occurred |
| `S-1-2-0` | Local | Any principal that has logged on locally |
| `S-1-2-1` | Console Logon | A principal that has logged on at the physical console |
| `S-1-3-0` | Creator Owner | Replaced with the creating principal's SID when inherited |
| `S-1-3-1` | Creator Group | Replaced with the creating principal's primary group SID when inherited |
| `S-1-3-4` | Owner Rights | Controls the owner's implicit rights on an object |

## NT Authority SIDs (S-1-5)

| SID | Name | Meaning |
|---|---|---|
| `S-1-5-2` | Network | A principal that authenticated over the network |
| `S-1-5-3` | Batch | A principal running as a batch job |
| `S-1-5-4` | Interactive | A principal that logged on interactively |
| `S-1-5-6` | Service | A principal running as a service |
| `S-1-5-7` | Anonymous Logon | An anonymous logon session |
| `S-1-5-9` | Enterprise Domain Controllers | All domain controllers in the enterprise |
| `S-1-5-11` | Authenticated Users | All principals that have authenticated (excludes anonymous) |
| `S-1-5-13` | Terminal Server Users | Principals that have logged on via terminal services |
| `S-1-5-15` | This Organization | Principals from the same organization |
| `S-1-5-18` | SYSTEM | The operating system itself — highest-privilege identity |
| `S-1-5-19` | Local Service | Built-in service account for services needing minimal local access |
| `S-1-5-20` | Network Service | Built-in service account for services needing network identity |

## Built-in domain SIDs (S-1-5-32)

| SID | Name | Meaning |
|---|---|---|
| `S-1-5-32-544` | Administrators | The built-in administrators group |
| `S-1-5-32-545` | Users | The built-in users group |
| `S-1-5-32-546` | Guests | The built-in guests group |
| `S-1-5-32-547` | Power Users | Legacy group — no special meaning on Peios |
| `S-1-5-32-548` | Account Operators | Can manage user accounts |
| `S-1-5-32-549` | Server Operators | Can manage domain servers |
| `S-1-5-32-550` | Print Operators | Can manage printers |
| `S-1-5-32-551` | Backup Operators | Can back up and restore files regardless of permissions |
| `S-1-5-32-552` | Replicators | Supports directory replication |

## Logon session SIDs (S-1-5-5)

| SID | Name | Meaning |
|---|---|---|
| `S-1-5-5-X-Y` | Logon SID | Unique to a specific logon session. Added to the token's groups at authentication. Can be used in ACEs to scope access to a single session. |

## Well-known domain RIDs

Within a domain (prefix `S-1-5-21-{domain}`), certain RIDs are reserved:

| RID | Name | Meaning |
|---|---|---|
| 500 | Administrator | The built-in domain administrator account |
| 501 | Guest | The built-in domain guest account |
| 502 | krbtgt | The Kerberos ticket-granting account |
| 512 | Domain Admins | The domain administrators group |
| 513 | Domain Users | All domain users |
| 514 | Domain Guests | All domain guests |
| 515 | Domain Computers | All domain-joined machines |
| 516 | Domain Controllers | All domain controllers |

RIDs below 1000 are reserved. Regular user and group accounts start at RID 1000.

## Service SIDs (S-1-5-80)

| SID | Name | Meaning |
|---|---|---|
| `S-1-5-80-{hash}` | Per-service SID | Unique to a specific service. Added to the service's token to distinguish it from other services running under the same account. |

## Confinement SIDs

| SID | Name | Meaning |
|---|---|---|
| `S-1-15-2-{hash}` | Confinement SID | Identifies a specific confined application |
| `S-1-15-2-1` | ALL_APPLICATION_PACKAGES | Matches all normal confined applications |
| `S-1-15-2-2` | ALL_RESTRICTED_APPLICATION_PACKAGES | Matches all confined applications including strictly confined |
| `S-1-15-3-{n}` | Capability SID | A declared capability for a confined application |

## Process Trust Label SIDs (S-1-19)

| SID | Name | Meaning |
|---|---|---|
| `S-1-19-0-0` | None / None | No PIP protection |
| `S-1-19-512-{trust}` | Protected / {trust} | Protected process (PPL equivalent) |
| `S-1-19-1024-{trust}` | Isolated / {trust} | Isolated process (PP equivalent) |
