---
title: Keys
---

A key is a node in the registry hierarchy. Keys are containers --
they hold subkeys (forming a tree) and values (holding data). Keys
are analogous to filesystem inodes: they carry identity and
properties, while path entries carry naming.

## Fields

| Field | Type | Mutable | Layer-qualified | Description |
|---|---|---|---|---|
| GUID | GUID | No | No | Immutable identity assigned by LCS at creation. Persisted by the source. Never reused. |
| Name | string | No | No | The key's name component (not a full path). Case-preserving, compared case-insensitively. Informational -- the authoritative name is in the path entry. |
| Parent GUID | GUID | No | No | The GUID of the parent key. Null for hive root keys. |
| Security Descriptor | SD (binary) | Yes | No | KACS Security Descriptor controlling access. Computed by the kernel from parent inheritance at creation (see the SD Inheritance section of the KACS v0.20 specification). Modifiable at runtime via WRITE_DAC / WRITE_OWNER. SD changes are direct mutations on the key -- they are not reverted on layer deletion. |
| Last write time | timestamp | Yes | No | Updated by LCS when a value is written, deleted, or the SD is modified. Stored by the source. |
| Volatile | boolean | No | No | If true, the source stores this key in non-persistent storage only. Lost on reboot or hive unload. Children of volatile keys MUST also be volatile. Set at creation, immutable thereafter. |
| Symlink | boolean | No | No | If true, this key is a symbolic link. Set at creation via REG_OPTION_CREATE_LINK, immutable thereafter. See the Symlinks section below. |

No key property is layer-qualified. Properties belong to the key
object itself. To change a key's structural type (volatile, symlink)
through a layer, the layer hides the original key and creates a new
one at the same path -- the standard overlay pattern.

## Key identity

A key's identity is its GUID, not its path. Two keys at different
points in time at the same path are different objects with different
GUIDs. A path is a name that maps to an identity. The identity
persists independently of the name.

GUIDs are assigned by LCS (not by sources) and pushed to the source
at key creation via the RSI. The source persists them as primary keys
in its storage schema. After path-to-GUID resolution at open time,
all RSI operations use the GUID directly.

## Naming rules

The following characters are forbidden in key name components:

- `\` (backslash) -- path separator
- `/` (forward slash) -- normalised to backslash on input, therefore
  also a separator
- null (`\0`) -- string terminator

All other characters are permitted, including spaces and Unicode.
The kernel normalises forward slashes to backslashes on input; the
stored canonical form always uses backslashes.

Empty name components are forbidden. Paths containing consecutive
separators (`Machine\\System`) or trailing separators
(`Machine\System\`) are invalid.

## Symlinks

A symlink key uses two complementary mechanisms:

1. **The symlink flag** on the key record marks the key's structural
   type. Set at creation via REG_OPTION_CREATE_LINK. Immutable.

2. **The default value with type REG_LINK** provides the target path.
   The target is a regular layered value -- a higher-precedence layer
   can redirect a symlink by writing a different REG_LINK default
   value.

Both mechanisms are load-bearing. The flag marks identity; the value
provides the target. LCS follows symlinks during path resolution,
resolving the target path before completing the operation. The fd
references the resolved target, not the link.

**Target resolution.** If the symlink flag is set but the effective
default value is not type REG_LINK (e.g., a layer writes REG_SZ as
the default value), path resolution fails with EINVAL. LCS does not
validate the default value's type at write time -- the error occurs
at resolution time. Removing the offending layer restores the
original REG_LINK target.

**Recursion limit.** Symlink resolution is limited to a configurable
depth (default 16). Exceeding the limit produces ELOOP.

**Opening the link itself.** The REG_OPEN_LINK flag on reg_open_key
opens the symlink key rather than following it. This is required for
managing the symlink (deleting it, changing its target).

**Creation restriction.** Symlink creation requires KEY_CREATE_LINK
on the parent key and SeTcbPrivilege or Administrator group membership.

## Case comparison

Key name comparison uses Unicode Simple Case Folding
(CaseFolding.txt, status S and C entries, Unicode 16.0) -- a fixed
one-to-one codepoint mapping with no locale dependency. This
provides practical compatibility with Windows'
RtlCompareUnicodeString behaviour. The Unicode version is pinned
at 16.0 for v0.21. Future versions MAY adopt a newer Unicode
version; the upgrade is a deliberate decision, not an implicit
consequence of updating a library.

Unicode normalisation (NFC vs NFD) is explicitly not performed.
Two different Unicode representations of the same visual character
are different keys, matching Windows semantics.
