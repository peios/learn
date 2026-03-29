---
title: Well-Known SIDs
order: 2
---

The following SIDs have fixed values and well-defined meanings. An implementation MUST recognize these SIDs and apply the semantics described in this specification wherever they are referenced.

## Universal authorities

| SID | Name | Description |
|---|---|---|
| S-1-0-0 | Nobody | The null SID. No principal. |
| S-1-1-0 | Everyone | Matches all principals, including anonymous. |
| S-1-2-0 | Local | Principals that log on locally (physically). |
| S-1-2-1 | Console Logon | Principals that log on via the physical console. |

## Creator authorities

| SID | Name | Description |
|---|---|---|
| S-1-3-0 | Creator Owner | Placeholder in inheritable ACEs. Replaced with the creating principal's SID during inheritance. |
| S-1-3-1 | Creator Group | Placeholder in inheritable ACEs. Replaced with the creating principal's primary group SID during inheritance. |
| S-1-3-4 | Owner Rights | When present in a DACL, overrides the owner's implicit READ_CONTROL and WRITE_DAC grants. AccessCheck treats this SID as matching the object's owner. |

## NT Authority (S-1-5)

| SID | Name | Description |
|---|---|---|
| S-1-5-7 | Anonymous | The anonymous identity. Carried by tokens at Anonymous impersonation level. |
| S-1-5-10 | Principal Self | Placeholder in ACEs on directory objects. Matches the caller when the caller's identity corresponds to the object's associated principal. Resolved via the `self_sid` parameter to AccessCheck. |
| S-1-5-11 | Authenticated Users | All principals that have been authenticated (excludes Anonymous). |
| S-1-5-18 | Local System (SYSTEM) | The operating system's own identity. Highest privilege level. |
| S-1-5-19 | Local Service | A built-in service account with reduced privileges. |
| S-1-5-20 | Network Service | A built-in service account that can authenticate to remote services. |

## Logon SIDs

| SID | Name | Description |
|---|---|---|
| S-1-5-5-*X*-*Y* | Logon SID | A per-authentication-event SID generated at session creation. *X* and *Y* are unique values. Injected into the token's groups with SE_GROUP_LOGON_ID. |

## BUILTIN domain (S-1-5-32)

| SID | Name | Description |
|---|---|---|
| S-1-5-32-544 | BUILTIN\Administrators | The built-in administrators group. |
| S-1-5-32-545 | BUILTIN\Users | The built-in users group. |
| S-1-5-32-546 | BUILTIN\Guests | The built-in guests group. |
| S-1-5-32-551 | BUILTIN\Backup Operators | Members can bypass file security for backup and restore. |

> [!INFORMATIVE]
> Additional BUILTIN SIDs (S-1-5-32-547 through S-1-5-32-583) are defined by Active Directory. KACS does not assign special semantics to these SIDs -- they participate in normal ACE matching like any other group SID. Their meaning is an administrative convention, not a kernel enforcement property.

## Domain SIDs (S-1-5-21)

Domain-specific SIDs follow the pattern `S-1-5-21-{DA1}-{DA2}-{DA3}-{RID}`, where the three domain authority sub-authorities identify the domain and the RID identifies the principal within that domain.

| RID | Name | Description |
|---|---|---|
| 500 | Domain Administrator | The built-in administrator account. |
| 501 | Domain Guest | The built-in guest account. |
| 512 | Domain Admins | The domain administrators group. |
| 513 | Domain Users | The domain users group. |
| 514 | Domain Guests | The domain guests group. |
| 515 | Domain Computers | Computer accounts in the domain. |

> [!INFORMATIVE]
> Domain SIDs are assigned by the domain controller and replicated through Active Directory. KACS does not create or manage domain SIDs -- it evaluates them as opaque binary values during AccessCheck.

## Mandatory integrity labels (S-1-16)

| SID | Name | Numeric level | Description |
|---|---|---|---|
| S-1-16-0 | Untrusted | 0 | Lowest trust. Sandboxed or experimental code. |
| S-1-16-4096 | Low | 4096 | Reduced trust. Services handling untrusted input. |
| S-1-16-8192 | Medium | 8192 | Standard trust. Default for interactive sessions and most services. |
| S-1-16-12288 | High | 12288 | Elevated administrative sessions. |
| S-1-16-16384 | System | 16384 | The kernel, peinit, and TCB services. |

Integrity levels form a strict total order: System > High > Medium > Low > Untrusted. MIC compares the caller's level against the object's label using this ordering.

## Process trust labels (S-1-19)

| SID | Name | Description |
|---|---|---|
| S-1-19-0-0 | None / No trust | Default for unsigned processes. |
| S-1-19-512-1024 | Protected, Authenticode | Third-party signed binaries. |
| S-1-19-512-1536 | Protected, AntiMalware | Security tooling. |
| S-1-19-512-2048 | Protected, App | Peios-distributed applications. |
| S-1-19-512-4096 | Protected, Peios | Core Peios components. |
| S-1-19-512-8192 | Protected, PeiosTcb | Peios Trusted Computing Base. |
| S-1-19-1024-8192 | Isolated, PeiosTcb | Maximum isolation and trust. |

Trust labels encode two dimensions in the SID: the first sub-authority is the PIP type (0 = None, 512 = Protected, 1024 = Isolated), and the second is the trust level (higher = more trusted). Dominance requires both dimensions to be greater than or equal.

## Confinement SIDs (S-1-15)

| SID | Name | Description |
|---|---|---|
| S-1-15-2-*hash* | Confinement SID | Identifies a confined application. The sub-authorities are derived from the application identity. |
| S-1-15-2-1 | ALL_APPLICATION_PACKAGES | Matches all confined applications in normal confinement mode. |
| S-1-15-2-2 | ALL_RESTRICTED_APPLICATION_PACKAGES | Matches confined applications in strict confinement mode. |

## Capability SIDs (S-1-15-3)

| SID | Name | Description |
|---|---|---|
| S-1-15-3-1 | internetClient | Outbound internet access. |
| S-1-15-3-2 | internetClientServer | Inbound and outbound internet access. |
| S-1-15-3-3 | privateNetworkClientServer | LAN/private network access. |
| S-1-15-3-8 | enterpriseAuthentication | Domain credential access. |
| S-1-15-3-9 | sharedUserCertificates | Certificate store access. |
| S-1-15-3-10 | removableStorage | Removable media access. |

Capability SIDs 4--7 (picturesLibrary, videosLibrary, musicLibrary, documentsLibrary) are reserved. Their SID values MUST NOT be redefined.

Derived capabilities use 8 sub-authorities computed from the SHA-256 hash of the capability name: `S-1-15-3-{h0}-{h1}-{h2}-{h3}-{h4}-{h5}-{h6}-{h7}`. The same name always produces the same SID.

## Service SIDs

Service SIDs follow the pattern `SERVICE\{service_name}` (e.g., `SERVICE\jellyfin`, `SERVICE\loregd`) and are added as a group in the service's token. The token's primary user SID is the account the service runs as (typically SYSTEM, LocalService, or NetworkService); the service SID enables per-service access control -- a file's DACL can grant access to `SERVICE\jellyfin` specifically, rather than to the broad account the service runs under.

The SID value is derived from the service name using the same SHA-256 hash derivation as capability SIDs: `S-1-5-80-{h0}-{h1}-{h2}-{h3}-{h4}-{h5}-{h6}-{h7}`. The same service name always produces the same SID.
