---
title: What Are Security Identifiers (SIDs)
type: concept
order: 20
description: How Security Identifiers uniquely and permanently identify every user, group, service, and machine on Peios.
---

Every security principal on Peios — every user, group, service, and machine — is identified by a **Security Identifier (SID)**. A SID is a unique value that is assigned once and never reused. If a user account is deleted and a new one is created with the same name, the new account gets a different SID.

This immutability is the foundation of the security model. Tokens, security descriptors, and access control lists all reference principals by SID, not by name. A principal's name is a display label — the SID is the real identity.

## SID format

A SID is written as a string of numbers separated by hyphens:

```
S-1-5-21-3623811015-3361044348-30300820-1013
```

Each part has a meaning:

| Part | Meaning |
|---|---|
| `S` | Indicates this is a SID |
| `1` | The SID specification version (always 1) |
| `5` | The **identifier authority** — who issued this SID. `5` means the NT Authority, which covers most principals |
| `21-3623811015-3361044348-30300820` | **Sub-authorities** — these narrow down the domain. The `21` prefix followed by three numbers identifies a specific domain |
| `1013` | The **Relative Identifier (RID)** — the unique identifier of this principal within its domain |

Not all SIDs are this long. Some are short and fixed:

```
S-1-5-18          (three components)
S-1-5-32-544      (four components)
```

The number of sub-authorities varies depending on the type of principal.

## Well-known SIDs

Some SIDs have fixed, universal meaning across every Peios installation. These are called **well-known SIDs**.

| SID | Name | Meaning |
|---|---|---|
| `S-1-5-18` | SYSTEM | The operating system itself. Highest-privilege identity on the machine |
| `S-1-5-19` | Local Service | A built-in identity for services that need minimal local access |
| `S-1-5-20` | Network Service | A built-in identity for services that need network access |
| `S-1-5-32-544` | Administrators | The built-in administrators group |
| `S-1-5-32-545` | Users | The built-in users group |
| `S-1-1-0` | Everyone | Matches every authenticated principal |
| `S-1-5-11` | Authenticated Users | All users who have authenticated (excludes anonymous) |

These SIDs are the same on every machine and in every domain. You will see them in security descriptors, default access rules, and system configuration throughout Peios.

## Domain SIDs

In a domain environment, every principal's SID shares a common **domain prefix**. The final number — the **RID** — distinguishes individual principals within that domain.

For example, if the domain SID is `S-1-5-21-3623811015-3361044348-30300820`:

| SID | RID | Principal |
|---|---|---|
| `...30300820-500` | 500 | The domain Administrator account |
| `...30300820-512` | 512 | The Domain Admins group |
| `...30300820-1013` | 1013 | A regular user account |

When you see two SIDs that share the same prefix, you know they belong to the same domain. The RID tells you which principal within that domain.

Some RIDs below 1000 are reserved for well-known domain principals (Administrator is always 500, Domain Admins is always 512). RIDs for regular accounts start at 1000 and are assigned sequentially.

## Why SIDs matter

SIDs are the stable anchor for all security decisions. Because access rules reference SIDs:

- **Renaming a principal doesn't break access.** A user whose account is renamed keeps the same SID, so all their existing permissions continue to work.
- **Deleting and recreating isn't the same as renaming.** A new account gets a new SID, even if it has the same name. It has no access to the old account's resources unless explicitly granted.
- **SIDs travel across the network.** In a domain, SIDs are carried inside authentication tokens (via Kerberos). A file server evaluates the same SIDs regardless of which machine the user logged in from.
