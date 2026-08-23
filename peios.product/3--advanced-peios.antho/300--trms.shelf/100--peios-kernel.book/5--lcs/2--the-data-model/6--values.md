---
title: Values
description: A named, typed datum inside a key — one name with many layer entries, the type set, REG_TOMBSTONE, naming and size.
---

A value is a named, typed datum inside a key. Values hold the
configuration data; keys hold values.

| Field | Description |
|---|---|
| Key GUID | The key this value belongs to. |
| Name | The value's name; the empty string is the default value. Case-preserving, compared case-insensitively. |
| Type | A registry value type. |
| Data | An opaque byte array, up to `MaxValueSize` (default 1 MB). |
| Layer | The layer this entry belongs to. Every write is tagged. |
| Sequence | Assigned by LCS at write time, for tiebreaking within a precedence tier. |

A key holds many values with distinct names, and at most one unnamed
one.

## One name, many entries

A single `(key GUID, value name)` pair can have several entries in the
source — one per layer that has written to it. The source stores them
all and returns them all; LCS resolves the effective value at read
time (§5.3.6).

That is the mechanism that makes layer deletion revert configuration
automatically. Delete the layer, its entries go, and the
next-highest-precedence entry becomes effective. Nothing has to be
recomputed or rewritten.

## Types

The full Windows type set is supported, for `registry.pol` fidelity:
`REG_NONE`, `REG_SZ`, `REG_EXPAND_SZ`, `REG_BINARY`, `REG_DWORD`,
`REG_DWORD_BIG_ENDIAN`, `REG_LINK`, `REG_MULTI_SZ`,
`REG_RESOURCE_LIST`, `REG_FULL_RESOURCE_DESCRIPTOR`,
`REG_RESOURCE_REQUIREMENTS_LIST` and `REG_QWORD`, numbered 0 to 11.
Values are in §5.A.

LCS stores the type tag and returns it on read but does not interpret
the data. The single exception is `REG_LINK` read as a symlink key's
default value, which triggers target resolution (§5.2.4).

The three hardware-resource types, 8 to 10, describe device resource
assignments in the Windows `HKLM\HARDWARE` hive, which the Windows
kernel rebuilds at every boot. Peios has no equivalent: hardware
enumeration belongs to the Linux device model, sysfs and `/proc/iomem`,
not to the registry. LCS accepts these tags only so a value carrying
one round-trips without loss. They have no semantics, LCS never
produces one, and for every operation they behave as `REG_BINARY`.
Rejecting a faithfully-copied value would break the fidelity guarantee
that is the reason the registry exists.

Type tags are validated at every write boundary, before sequence
allocation, transaction enlistment or source dispatch. An unknown code
is `EINVAL`.

## `REG_TOMBSTONE`

One further type, `REG_TOMBSTONE` (`0xFFFF`), is internal. It is never
returned to a caller reading a value — a caller whose effective entry
is a tombstone gets `ENOENT`, which is exactly what a tombstone means.

There is no separate tombstone flag in the `REG_IOC_SET_VALUE`
argument. Writing type `REG_TOMBSTONE` **is** the explicit tombstone
operation, and it must carry zero-length data; non-empty tombstone data
is `EINVAL`, again before sequence allocation, enlistment or dispatch.

## Naming

Value names use the same case rules as key names: Unicode Simple Case
Folding, case-preserving, case-insensitive.

They differ in one respect. **Backslash and forward slash are permitted
in a value name.** Value names are not hierarchical, so a separator has
no meaning in one. Only the null byte is forbidden, and invalid UTF-8 is
rejected. The empty string is reserved for the default value.

That difference is why watch event path components are length-prefixed
rather than joined by a separator (§5.6.2) — a value name can contain
the separator.

## Size

`MaxValueSize` defaults to 1 MB and is configurable from 4 KB to 64 MB
(§5.10.3). Value data is opaque bytes and is not subject to the UTF-8
validation that applies to every string in the interface.
