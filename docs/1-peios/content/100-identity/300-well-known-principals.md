---
title: Well-known principals
type: concept
description: Peios ships with a fixed catalog of principals whose SIDs are defined by the system rather than allocated at runtime. This page is the catalog — what each well-known SID is, when it appears in an ACE, and which ones you will reach for in practice.
related:
  - peios/identity/sids
  - peios/security-descriptors/overview
  - peios/access-decisions/overview
---

A **well-known principal** is a principal whose SID is fixed by the system rather than allocated when an account is created. Some name a single specific entity (`SYSTEM`, `Anonymous`). Some name a category (`Everyone`, `Authenticated Users`). Some are placeholders that get rewritten during inheritance (`CREATOR OWNER`). All of them have the same purpose: they let you write ACEs that target a role without naming a specific user.

You will recognise the common ones almost immediately. The full catalog below exists so you can look up the less common ones the first time you see them in an audit log.

## How to read the catalog

Each well-known SID has a fixed numeric value, a conventional name, and a defined behaviour during access checks. Some of them are not real principals at all — they are placeholders or labels that the access check treats specially. Where that distinction matters, it is called out.

The catalog is organised by SID authority, because that is how the SIDs are structured and how you will tend to recognise them.

## Universal SIDs (`S-1-0`, `S-1-1`, `S-1-2`, `S-1-3`)

These authorities are defined globally — not tied to any specific machine or domain — and exist for cross-system meaning.

| SID | Name | Behaviour |
|---|---|---|
| `S-1-0-0` | Nobody | Matches nothing. Used to write an ACE that can never apply, usually as a deliberate placeholder. |
| `S-1-1-0` | Everyone | Matches every token, including Anonymous. The broadest possible grant. |
| `S-1-2-0` | Local | Matches any token created by a local logon (not a network logon). |
| `S-1-2-1` | Console Logon | Matches a token created by a physical or console session. |
| `S-1-3-0` | Creator Owner | Placeholder. Inheritable ACEs containing this SID are rewritten to the new object's owner SID when the child is created. Does not match anything at access-check time. |
| `S-1-3-1` | Creator Group | Placeholder. Same as Creator Owner but for the primary group. |
| `S-1-3-4` | Owner Rights | Special. When present in a DACL, it suppresses the implicit READ_CONTROL and WRITE_DAC grants that the owner would otherwise receive. See [Ownership and implicit rights](~peios/security-descriptors/ownership). |

The placeholder SIDs (`S-1-3-0` and `S-1-3-1`) are the trickiest. They never grant or deny anything at access-check time. Their job is to make inheritable ACEs portable across owners — you write an ACE that grants WRITE to Creator Owner, and when a child object is created, that ACE is rewritten to grant WRITE to whoever owns the child.

## NT Authority SIDs (`S-1-5`)

This is the largest group of well-known SIDs and where most of the principals you will use day-to-day live.

### Logon classifiers

| SID | Name | Behaviour |
|---|---|---|
| `S-1-5-2` | Network | Matches a token created by a network logon. |
| `S-1-5-4` | Interactive | Matches a token created by an interactive logon (console, RDP, SSH). |
| `S-1-5-6` | Service | Matches a token created for a service. |
| `S-1-5-7` | Anonymous | The user SID for tokens at the Anonymous impersonation level. |
| `S-1-5-11` | Authenticated Users | Matches every successfully authenticated token. Excludes Anonymous. |

The pair `S-1-1-0` (Everyone) and `S-1-5-11` (Authenticated Users) is the most common distinction worth getting right. Everyone includes Anonymous; Authenticated Users excludes it. Anything reachable by Anonymous is reachable by an unauthenticated network peer, which is almost never what you want.

### System actors

| SID | Name | Behaviour |
|---|---|---|
| `S-1-5-18` | Local System (SYSTEM) | The kernel and TCB services run as SYSTEM. The most privileged identity on the local machine. |
| `S-1-5-19` | Local Service | Built-in service account with reduced privileges. |
| `S-1-5-20` | Network Service | Built-in service account that can authenticate outward to remote machines. |

### Built-in aliases

The sub-authority `32` under NT Authority is the "BUILTIN" domain, which holds aliases for common administrative roles. The full alias list includes a few dozen entries; the ones you will see most often:

| SID | Name |
|---|---|
| `S-1-5-32-544` | BUILTIN\Administrators |
| `S-1-5-32-545` | BUILTIN\Users |
| `S-1-5-32-546` | BUILTIN\Guests |
| `S-1-5-32-551` | BUILTIN\Backup Operators |

### Logon sessions and domains

| Pattern | Meaning |
|---|---|
| `S-1-5-5-X-Y` | A specific logon session. `X` and `Y` are derived from the session's LUID. Always carried in the token of any thread belonging to that session. |
| `S-1-5-21-DA1-DA2-DA3-RID` | A principal in a specific domain. `DA1-DA2-DA3` identifies the domain; `RID` identifies the principal within it. |
| `S-1-5-21-DA1-DA2-DA3-500` | The Administrator account of that domain (RID 500 is reserved). |
| `S-1-5-21-DA1-DA2-DA3-512` | Domain Admins. |
| `S-1-5-21-DA1-DA2-DA3-513` | Domain Users. |
| `S-1-5-21-DA1-DA2-DA3-515` | Domain Computers — the machine accounts in the domain. |

The full set of reserved RIDs under `S-1-5-21-*` follows administrative convention. Domain-specific principals (your actual users) get RIDs allocated above 1000.

### Service SIDs

A SID derived from a service's name, used to grant a service ACL entries independent of the account it runs under.

| Pattern | Meaning |
|---|---|
| `S-1-5-80-h1-h2-h3-h4-h5` | A service SID. The five hash values come from the SHA-1 of the UTF-16LE uppercased service name, split into five little-endian 32-bit integers. |

Service SIDs let you say "grant the loregd service read access to this file" without saying "grant SYSTEM read access" or "grant a specific user read access" — both of which would be too broad.

## Mandatory integrity labels (`S-1-16`)

These are not principals. They are labels carried in a token's integrity level field and in an object's mandatory label ACE.

| SID | Level |
|---|---|
| `S-1-16-0` | Untrusted |
| `S-1-16-4096` | Low |
| `S-1-16-8192` | Medium |
| `S-1-16-12288` | High |
| `S-1-16-16384` | System |

Integrity levels are a vertical axis on top of identity. A user at Medium integrity and the same user at High integrity have the same SID but different integrity labels. See [Mandatory integrity control](~peios/access-decisions/mandatory-integrity-control) for how the levels interact with access checks.

## Process trust labels (`S-1-19`)

Like integrity labels, these are not principals. They label processes by signing trust for [Process integrity protection](~peios/process-integrity-protection/overview).

| Pattern | Meaning |
|---|---|
| `S-1-19-T-L` | PIP trust label. `T` is the PIP type (0 None, 512 Protected, 1024 Isolated). `L` is the trust level within that type. |

Common combinations:

| SID | Trust meaning |
|---|---|
| `S-1-19-0-0` | No PIP protection. Default for unsigned processes. |
| `S-1-19-512-1024` | Protected, Authenticode. Third-party signed binaries. |
| `S-1-19-512-2048` | Protected, App. Peios-distributed applications. |
| `S-1-19-512-4096` | Protected, Peios. Core Peios components. |
| `S-1-19-512-8192` | Protected, PeiosTcb. Trusted computing base. |

## Confinement and capability SIDs (`S-1-15`)

These are used by [Confinement](~peios/confinement/overview) to label sandboxed applications and the capabilities they have been granted.

### Confinement domains

| SID | Name |
|---|---|
| `S-1-15-2-1` | ALL_APPLICATION_PACKAGES — matches every confined application in normal confinement mode. |
| `S-1-15-2-2` | ALL_RESTRICTED_APPLICATION_PACKAGES — matches confined applications in both normal and strict modes. |

### Well-known capabilities

| SID | Capability |
|---|---|
| `S-1-15-3-1` | internetClient — outbound network. |
| `S-1-15-3-2` | internetClientServer — inbound and outbound network. |
| `S-1-15-3-3` | privateNetworkClientServer — LAN/private network. |
| `S-1-15-3-8` | enterpriseAuthentication — domain credential access. |
| `S-1-15-3-9` | sharedUserCertificates — certificate store access. |
| `S-1-15-3-10` | removableStorage — removable media access. |

### Derived capability SIDs

For application-defined capabilities beyond the well-known set, the SID is derived from the capability name:

| Pattern | Meaning |
|---|---|
| `S-1-15-3-h1-h2-h3-h4-h5-h6-h7-h8` | A derived capability SID. The eight values come from the SHA-256 of the capability name. The same name always produces the same SID. |

## Special placeholder SIDs

A few SIDs never appear as a real principal but are recognised by the access check.

| SID | Name | How it is used |
|---|---|---|
| `S-1-3-0` | Creator Owner | Substituted at inheritance time. |
| `S-1-3-1` | Creator Group | Substituted at inheritance time. |
| `S-1-3-4` | Owner Rights | Suppresses owner implicit rights when present in a DACL. |
| `S-1-5-10` | Principal Self | A placeholder for "the principal this object is about". The access check substitutes the caller-supplied `self_sid` parameter for this SID at evaluation time. Used in directory-style objects where an ACE says "the user can modify their own properties". |

These are the cases where a SID in an ACE does not literally mean "match a token whose user SID is this value". They are special-cased by the access check.

## Which ones to actually use

The catalog above is comprehensive. In practice, day-to-day administrative work touches a much smaller set:

- **`BUILTIN\Administrators`** and **`SYSTEM`** for default protective DACLs.
- **`Authenticated Users`** for "any logged-in user should be able to read this".
- **`Everyone`** only when you actually mean "including unauthenticated network peers".
- **`Creator Owner`** in inheritable ACEs that should follow the owner of a child object.
- **`Owner Rights`** when you want to suppress the owner's default grants on a sensitive object.
- Specific user/group SIDs allocated by the directory (the `S-1-5-21-...-RID` form) for everyone else.

The remaining well-known SIDs — service SIDs, capability SIDs, integrity labels, PIP labels — show up in specialised contexts that have their own topics in these docs.
