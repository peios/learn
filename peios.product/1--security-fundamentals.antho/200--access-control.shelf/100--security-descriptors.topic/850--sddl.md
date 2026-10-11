---
title: SDDL
type: concept
description: The text form of a security descriptor — the section grammar, the ACE fields, and the complete tables of type, flag, rights and SID codes Peios accepts.
related:
  - peios/security-descriptors/overview
  - peios/security-descriptors/acls-and-aces
  - peios/security-descriptors/conditional-aces
  - peios/security-descriptors/inheritance
  - peios/security-descriptors/the-sacl
  - peios/identity/well-known-principals
  - peios/files-and-directories/sd
---

A security descriptor is a binary structure, but almost nobody writes one by
hand. SDDL — the Security Descriptor Definition Language — is its text form: a
single line that names an owner, a group, and the two access control lists.

You meet it wherever a descriptor has to be written down rather than computed:

- `sd set` and `sd show --sddl`
- `mount`'s `--synth-sddl`, which supplies the template descriptor for a
  filesystem that has no native descriptor storage
- registry seeds, which carry descriptors for the keys they create
- peinit service definitions, whose `ControlSecurity` and `ServiceSecurity`
  values are descriptors

This article is the canonical list of the codes Peios accepts. The concepts
behind them — what a DACL is, how inheritance propagates, what the SACL carries
— have their own articles, linked at the end.

## The shape of a descriptor string

Four optional sections, each introduced by a letter and a colon:

```
O:<sid>G:<sid>D:<acl>S:<acl>
```

| Section | Contents |
| --- | --- |
| `O:` | The owner SID. |
| `G:` | The primary group SID. |
| `D:` | The discretionary ACL — who may do what. |
| `S:` | The system ACL — auditing, the integrity label, policy references. |

A section you omit is absent from the descriptor rather than empty, and the
formatter emits the sections in the order above regardless of the order you
wrote them. A section may appear only once; a repeat is an error rather than an
override.

One case is easy to write by accident. A bare `D:` with no ACEs after it is a
**NULL DACL**, which grants everyone everything — not an empty DACL, which
grants nobody anything. `D:` and `D:(A;;GA;;;WD)` are close together on the
keyboard and very far apart in effect.

## ACL flags

An ACL body may open with one or more flags, in any order, before the first
`(`:

| Flag | Meaning |
| --- | --- |
| `P` | Protected. The ACL does not inherit from its parent. |
| `AI` | Auto-inherited. The ACL was produced by inheritance propagation. |
| `AR` | Auto-inherit required. Requests that propagation be applied. |

So `D:PAI(A;;GA;;;SY)` is a protected, auto-inherited DACL with one ACE.

## An ACE

Each ACE is a parenthesised list of six semicolon-separated fields, or seven
when the ACE carries a payload:

```
(type;flags;rights;object_guid;inherit_object_guid;account_sid)
(type;flags;rights;object_guid;inherit_object_guid;account_sid;payload)
```

The two GUID fields apply only to object ACEs and are left empty otherwise —
supplying one on a non-object ACE is an error rather than a value that is
quietly discarded. The seventh field carries the condition expression on a
callback ACE, or the claim on a resource-attribute ACE.

Reading a real one:

```
O:SYG:SYD:(A;OICI;GA;;;SY)
```

Owner SYSTEM, group SYSTEM, and a DACL with one ACE: allow (`A`), inherited by
both containers and objects (`OI` `CI`), all access (`GA`), no object GUIDs, to
SYSTEM (`SY`). That is the descriptor Peios seeds `/run` with at boot.

## ACE types

| Code | ACE type |
| --- | --- |
| `A` | Access allowed |
| `D` | Access denied |
| `AU` | System audit |
| `OA` | Access allowed, object |
| `OD` | Access denied, object |
| `OU` | System audit, object |
| `XA` | Access allowed, callback — carries a condition |
| `XD` | Access denied, callback — carries a condition |
| `XU` | System audit, callback — carries a condition |
| `ZA` | Access allowed, callback object |
| `ZD` | Access denied, callback object |
| `ZU` | System audit, callback object |
| `AL` | System alarm — continuous auditing |
| `OL` | System alarm, object |
| `XL` | System alarm, callback — carries a condition |
| `ZL` | System alarm, callback object |
| `ML` | Mandatory label — the integrity level |
| `TL` | Process trust label |
| `RA` | Resource attribute — carries a claim |
| `SP` | Scoped policy identifier |
| `FL` | Access filter — carries a condition |

The callback types are how a [conditional ACE](~peios/security-descriptors/conditional-aces)
is spelled: `XA` is an allow ACE with an expression in its seventh field.

`XL` and `ZL` are Peios' own. Windows names no callback alarm, so a string
holding one does not read on Windows.

The formatter fails on any other ACE type, such as a compound ACE (`0x04`) or an
unallocated value. It does not leave the entry out, because a string without it
would describe a descriptor other than the one held.

## ACE flags

| Code | Meaning |
| --- | --- |
| `CI` | Container inherit — child containers receive it. |
| `OI` | Object inherit — child objects receive it. |
| `NP` | No propagate — children receive it, grandchildren do not. |
| `IO` | Inherit only — it does not apply to the object carrying it. |
| `ID` | Inherited — this ACE arrived by propagation. |
| `SA` | Audit successful access. |
| `FA` | Audit failed access. |

`SA` and `FA` are meaningful only on an audit ACE in the SACL.

## Access rights

Generic rights, mapped to concrete rights by the object class:

| Code | Right |
| --- | --- |
| `GA` | Generic all |
| `GR` | Generic read |
| `GW` | Generic write |
| `GX` | Generic execute |

Standard rights, which mean the same thing on every object class:

| Code | Right |
| --- | --- |
| `SD` | Delete |
| `RC` | Read control — read the descriptor |
| `WD` | Write DACL |
| `WO` | Write owner |

File composites:

| Code | Mask | Right |
| --- | --- | --- |
| `FA` | `0x001F01FF` | All file access |
| `FR` | `0x00120089` | File read |
| `FW` | `0x00120116` | File write |
| `FX` | `0x001200A0` | File execute |

Registry-key composites:

| Code | Mask | Right |
| --- | --- | --- |
| `KA` | `0x000F003F` | All key access |
| `KR` | `0x00020019` | Key read |
| `KW` | `0x00020006` | Key write |
| `KX` | `0x00020019` | Key execute |

Directory-object rights, for object ACEs:

| Code | Right |
| --- | --- |
| `CC` | Create child |
| `DC` | Delete child |
| `LC` | List children |
| `SW` | Self write |
| `RP` | Read property |
| `WP` | Write property |
| `DT` | Delete tree |
| `LO` | List object |
| `CR` | Control access |

Mandatory-label policy bits, valid on an `ML` ACE:

| Code | Policy |
| --- | --- |
| `NW` | No write up |
| `NR` | No read up |
| `NX` | No execute up |

A rights field may also be a hexadecimal mask, written `0x` followed by the
value. It consumes the rest of the field, so it can only come last — but it may
follow letter codes rather than replacing them. `FRFX0x6` grants file read, file
execute, and the two bits `0x6` names, which is how you reach a right that has
no two-letter code without giving up the ones that do:

```
(A;;FRFX0x6;;;WD)
```

`FILE_ADD_FILE` and `FILE_ADD_SUBDIRECTORY` are the usual reason to need it.
Writing the whole mask as `0x1200af` is equally correct and tells a reader
nothing.

## SID codes

An account field takes either a full `S-1-…` SID or one of these aliases.

Principals and logon types:

| Code | SID | Principal |
| --- | --- | --- |
| `WD` | `S-1-1-0` | Everyone |
| `AN` | `S-1-5-7` | Anonymous |
| `IU` | `S-1-5-4` | Interactive |
| `NU` | `S-1-5-2` | Network logon |
| `SU` | `S-1-5-6` | Service |
| `RC` | `S-1-5-12` | Restricted code |
| `WR` | `S-1-5-33` | Write-restricted code |
| `PS` | `S-1-5-10` | Principal self |
| `ED` | `S-1-5-9` | Enterprise domain controllers |
| `AU` | `S-1-5-11` | Authenticated Users |
| `SY` | `S-1-5-18` | Local System |
| `LS` | `S-1-5-19` | Local Service |
| `NS` | `S-1-5-20` | Network Service |
| `AC` | `S-1-15-2-1` | All application packages |

Inheritance placeholders:

| Code | SID | Principal |
| --- | --- | --- |
| `CO` | `S-1-3-0` | Creator Owner |
| `CG` | `S-1-3-1` | Creator Group |
| `OW` | `S-1-3-4` | Owner rights |

Integrity levels:

| Code | SID | Principal |
| --- | --- | --- |
| `LW` | `S-1-16-4096` | Low integrity |
| `ME` | `S-1-16-8192` | Medium integrity |
| `MP` | `S-1-16-8448` | Medium-plus integrity |
| `HI` | `S-1-16-12288` | High integrity |
| `SI` | `S-1-16-16384` | System integrity |

The BUILTIN groups, `S-1-5-32-*`. These are absolute despite the name: the RIDs
are fixed, not allocated per machine.

| Code | SID | Principal |
| --- | --- | --- |
| `BA` | `S-1-5-32-544` | Administrators |
| `BU` | `S-1-5-32-545` | Users |
| `BG` | `S-1-5-32-546` | Guests |
| `PU` | `S-1-5-32-547` | Power users |
| `AO` | `S-1-5-32-548` | Account operators |
| `SO` | `S-1-5-32-549` | Server operators |
| `PO` | `S-1-5-32-550` | Printer operators |
| `BO` | `S-1-5-32-551` | Backup operators |
| `RE` | `S-1-5-32-552` | Replicator |
| `RU` | `S-1-5-32-554` | Pre-Windows 2000 compatible access |
| `RD` | `S-1-5-32-555` | Remote desktop users |
| `NO` | `S-1-5-32-556` | Network configuration operators |
| `MU` | `S-1-5-32-558` | Performance monitor users |
| `LU` | `S-1-5-32-559` | Performance log users |
| `IS` | `S-1-5-32-568` | IIS users |
| `CY` | `S-1-5-32-569` | Cryptographic operators |
| `ER` | `S-1-5-32-573` | Event log readers |
| `CD` | `S-1-5-32-574` | Certificate service DCOM access |
| `RA` | `S-1-5-32-575` | RDS remote access servers |
| `ES` | `S-1-5-32-576` | RDS endpoint servers |
| `MS` | `S-1-5-32-577` | RDS management servers |
| `HA` | `S-1-5-32-578` | Hyper-V administrators |
| `AA` | `S-1-5-32-579` | Access control assistance operators |
| `RM` | `S-1-5-32-580` | Remote management users |

`SU` is worth knowing about: it is the group every token minted for a service
logon carries, so it is how you grant something to services as a class rather
than naming each one. Membership follows from how a process was started rather
than from which account it runs as, so an ordinary user process cannot acquire
it.

`CO` is the one you reach for most often after that. An inheritable ACE naming
Creator Owner is rewritten to the new object's owner when a child is created,
which is how a container grants each principal rights over what it makes there
without granting anything over what anyone else makes.

Two SIDs you might expect have no alias and must be written in full: the null
SID `S-1-0-0`, and the protected-process integrity level `S-1-16-20480`.

## The same two letters mean different things in different fields

The code tables overlap, and a code is interpreted by the field it appears in
rather than by its spelling. The collisions that catch people out:

| Code | As a right | As an account | Elsewhere |
| --- | --- | --- | --- |
| `WD` | Write DACL | Everyone | |
| `RC` | Read control | Restricted code | |
| `AU` | | Authenticated Users | ACE type: system audit |
| `RA` | | RDS remote access servers | ACE type: resource attribute |
| `FA` | All file access | | ACE flag: audit failed access |
| `SD` | Delete | | |

So in `(A;FA;FA;;;WD)` the first `FA` is an ACE flag, the second is a rights
mask, and `WD` is Everyone rather than write-DACL. Each is unambiguous in
place, but none of them reads that way at a glance.

## Not everything that parses is emitted

Reading a descriptor and formatting it again does not always return the string
you started with, and this is deliberate rather than a defect.

The directory-object rights (`CC` through `CR`) and the mandatory-label bits
(`NW`, `NR`, `NX`) occupy the same low bit positions as one another. Which of
them a bit means depends on the object class and the ACE type. The ACE type
settles it for a mandatory label, so an `ML` entry's mask comes back as `NW`,
`NR` and `NX`. Elsewhere the formatter would have to guess, so it accepts the
directory-object codes when parsing and emits none of them, falling back to a
hexadecimal mask. `KX` is dropped for a related
reason: it shares a mask with `KR`, so only one of the two can ever come back.

The formatter also prefers composites to their components, emitting `FA` rather
than the eight codes that add up to it.

## Domain- and machine-relative aliases

The codes `DA`, `DG`, `DU`, `DD`, `DC`, `SA`, `EA`, `RO`, `CA`, `PA`, `CN`,
`AP`, `KA`, `EK` and `RS` name principals relative to a domain — domain admins,
domain users, and so on — and `LA` and `LG` name the local administrator and
guest accounts relative to a machine. Peios recognises them so that it can
reject them with a message that says what is wrong, and it cannot resolve them:
there is no domain or machine SID for them to be relative to. Write the SID you
mean instead.

`RU` reads like one of these and is not: it is BUILTIN\\Pre-Windows 2000
Compatible Access, `S-1-5-32-554`, and resolves like any other BUILTIN group.

## Reading a descriptor

`sd show` normally renders its selected view for a person to read. Its
rights column uses a shorthand of its own — a lone `f` is all file access
(`0x001F01FF`), not the single bit `0xF`. To format the queried owner, group,
DACL and integrity-label subset as SDDL:

```
sd show --sddl /usr/bin/login
```

The command does not query the full SACL. Formatting cannot recover audit
ACEs or other components absent from the query: matching strings are not
proof of full descriptor equality, and this output is not a complete backup
to replay with `sd set`. See [`sd show` inspection limits](~peios/files-and-directories/sd#sd-show).

## Where to go next

- [Security descriptors](~peios/security-descriptors/overview) — what the parts
  of a descriptor do.
- [ACLs and ACEs](~peios/security-descriptors/acls-and-aces) — how the entries
  you have just learned to spell are evaluated.
- [Inheritance](~peios/security-descriptors/inheritance) — what `CI`, `OI`,
  `NP`, `IO` and `ID` do to a tree.
- [Conditional ACEs](~peios/security-descriptors/conditional-aces) — the
  expression language behind the callback types.
- [The sd command](~peios/files-and-directories/sd) — reading and writing
  descriptors on real objects.
