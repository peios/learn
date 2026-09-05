---
title: Access Rights
description: Registry rights at their Windows bit positions — the convenience masks, generic mapping, and validation of what a caller asks and a source returns.
---

Registry rights occupy the Windows bit positions, so a Security
Descriptor carrying registry ACEs is binary-compatible with one written
by Windows tooling. [*right.windows-bit-positions] That is a `registry.pol` and Samba requirement, not
an aesthetic choice.

The values are in §5.A. In summary: six specific rights in bits 0–5
(`KEY_QUERY_VALUE`, `KEY_SET_VALUE`, `KEY_CREATE_SUB_KEY`,
`KEY_ENUMERATE_SUB_KEYS`, `KEY_NOTIFY`, `KEY_CREATE_LINK`), the four
standard rights `DELETE`, `READ_CONTROL`, `WRITE_DAC` and
`WRITE_OWNER`, and `ACCESS_SYSTEM_SECURITY` for the SACL, which is
itself gated by `SeSecurityPrivilege`.

There is no execute right on a key. [*right.no-execute-right]

## Convenience masks and generic mapping

`KEY_READ`, `KEY_WRITE` and `KEY_ALL_ACCESS` are concrete masks, not
generic bits — they are unions of the rights above and are usable
directly. [*right.convenience-masks-are-concrete]

Separately, LCS accepts the raw KACS generic bits `GENERIC_READ`,
`GENERIC_WRITE`, `GENERIC_EXECUTE` and `GENERIC_ALL` in a caller's
`desired_access` and in ACE masks in a Security Descriptor. Those are
mapped through the registry generic mapping before AccessCheck sees
them. [*right.generic-bits-accepted-and-mapped]

`GENERIC_READ` maps to `KEY_READ`, `GENERIC_WRITE` to
`KEY_WRITE`, `GENERIC_ALL` to `KEY_ALL_ACCESS`, and **`GENERIC_EXECUTE`
maps to zero**, because there is nothing to execute. [*right.generic-mapping]

## Validating what a caller asks for

`desired_access` is validated before path resolution or AccessCheck. [*right.desired-access-validated-first]

- Zero is `EINVAL`. A caller must ask for something. [*right.zero-desired-access-is-einval]
- Any bit outside the valid caller mask is `EINVAL`. [*right.unknown-desired-access-bit-is-einval]
- `MAXIMUM_ALLOWED` may appear alone or combined with anything else. [*right.maximum-allowed-may-combine]
- `SYNCHRONIZE` (`0x00100000`) is not a registry right, so it is an
  unknown bit and fails `EINVAL`. [*right.synchronize-is-not-a-registry-right]

The valid caller mask is a single constant, `REG_VALID_DESIRED_ACCESS_MASK`
(§5.A): the six specific rights, the four standard rights,
`ACCESS_SYSTEM_SECURITY`, `MAXIMUM_ALLOWED` and the four generic bits. [*right.valid-desired-access-mask-contents]

## Validating what a source returns

Source-supplied Security Descriptors are validated too, because a
source is trusted for its data but not for its arithmetic (§5.8.4).

An ACE mask may contain concrete registry rights and raw generic bits.
It **may not** contain `MAXIMUM_ALLOWED` — that is a request, not a
grant, and it is meaningless in an ACE. [*right.ace-mask-rejects-maximum-allowed]

After generic mapping, an ACE
mask must be a subset of the concrete registry rights plus
`ACCESS_SYSTEM_SECURITY`. [*right.ace-mask-subset-after-mapping]

A descriptor that breaks either rule is malformed source data: the
operation fails closed with `EIO` and an
`LCS_SOURCE_VALIDATION_FAILURE` audit event is emitted (§5.4.4). [*right.malformed-descriptor-is-eio]

Two further constants, `REG_VALID_MAPPED_ACCESS_MASK` and
`REG_VALID_ACE_ACCESS_MASK`, express those two bounds.

## Which right each operation needs

| Operation | Required |
|---|---|
| `REG_IOC_QUERY_VALUE`, `QUERY_VALUES_BATCH`, `ENUM_VALUES` | `KEY_QUERY_VALUE` [*right.query-value] |
| `REG_IOC_SET_VALUE`, `DELETE_VALUE`, `BLANKET_TOMBSTONE`, `FLUSH` | `KEY_SET_VALUE` [*right.set-value] |
| `REG_IOC_ENUM_SUBKEYS` | `KEY_ENUMERATE_SUB_KEYS` [*right.enum-subkeys] |
| `REG_IOC_QUERY_KEY_INFO` | `READ_CONTROL` [*right.query-key-info] |
| `REG_IOC_DELETE_KEY`, `HIDE_KEY` | `DELETE` [*right.delete-key] |
| `REG_IOC_NOTIFY` | `KEY_NOTIFY` [*right.notify] |
| `REG_IOC_GET_SECURITY` | `READ_CONTROL` for owner, group and DACL; `ACCESS_SYSTEM_SECURITY` for the SACL [*right.get-security] |
| `REG_IOC_SET_SECURITY` | `WRITE_OWNER` for owner **or group**; `WRITE_DAC` for the DACL; `ACCESS_SYSTEM_SECURITY` for the SACL [*right.set-security] |
| `REG_IOC_BACKUP` | `SeBackupPrivilege`, no per-key check |
| `REG_IOC_RESTORE` | `SeRestorePrivilege`, no per-key check |
| creating a key | `KEY_CREATE_SUB_KEY` on the parent [*right.create-key] |
| creating a symlink key | `KEY_CREATE_SUB_KEY` and `KEY_CREATE_LINK` on the parent, plus `SeTcbPrivilege` or Administrators |

Where a `REG_IOC_SET_SECURITY` or `GET_SECURITY` request names several
components, every right those components imply must be present before
the source is contacted. [*right.security-info-needs-every-implied-right]

`REG_IOC_FLUSH` requires `KEY_SET_VALUE` because a flush is only
meaningful to a caller that wrote something and wants it durable.
Requiring a write right stops an unprivileged reader using flush as a
disk-I/O amplifier.

## Enumeration exposes names, not contents

`REG_IOC_ENUM_SUBKEYS` performs no per-child access check. Every
visible child is returned, whatever the caller's access to it. The
caller learns names, and must open each child separately — with a real
AccessCheck — to read anything. [*right.enum-subkeys-no-per-child-check]

Subtree watches work the same way: a watcher is told a descendant was
created without a check on that descendant. [*right.subtree-watch-no-per-descendant-check] Structure visibility is
deliberately weaker than content visibility, matching
`RegNotifyChangeKeyValue` and `RegEnumKeyEx`.
