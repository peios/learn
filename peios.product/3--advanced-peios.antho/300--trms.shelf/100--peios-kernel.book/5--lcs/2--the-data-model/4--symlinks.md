---
title: Symlinks
description: The two load-bearing mechanisms behind a symlink key — the structural flag and the target value — plus resolution, depth and opening the link itself.
---

A symlink key uses two mechanisms, and both are load-bearing.

The **symlink flag** on the key record marks the key's structural type.
It is set at creation by `REG_OPTION_CREATE_LINK` and is immutable
afterwards — `RSI_WRITE_KEY` can update only the descriptor and the
last write time, so there is no operation that could change it.

The **default value, of type `REG_LINK`,** supplies the target path. It
is an ordinary layered value, which means a higher-precedence layer can
redirect a symlink by writing a different `REG_LINK` default value, and
removing that layer restores the original target.

The flag marks identity; the value provides the target.

## Resolution

LCS follows symlinks during path resolution and the fd it returns
refers to the resolved target — its GUID, its position in the tree, its
ancestor chain — not to the link.

The target is resolved by issuing a separate `RSI_QUERY_VALUES` for the
key's default value (the empty name) and applying ordinary layer
resolution to the result, so the target participates in the layer
system exactly as any other value does.

If the effective default value is missing, or is not of type
`REG_LINK`, resolution fails with `EINVAL`. LCS does **not** validate
the type at write time: a layer that writes a `REG_SZ` default value
over a symlink's target breaks resolution at the next open, and
removing that layer fixes it. The offending value stays in the
registry; a failed resolution writes nothing.

## The target path

The `REG_LINK` payload is a length-delimited UTF-8 registry path. No
trailing null is required or permitted — the length delimits it, and a
null byte inside that length is rejected like any other. Forward
slashes are handled as separators as everywhere else.

The target is validated with exactly the same rules as a syscall path:
UTF-8, no null bytes, per-component and total length, no empty
components, no trailing separator, maximum depth. The only difference
is that a syscall path arrives null-terminated and has its terminator
stripped first.

A target is always interpreted as absolute — its first component is
routed as a hive name. There is no check that rejects a relative-looking
target as malformed. A target of `Sub\Key` is not an error; it is a
request for a hive named `Sub`, and it yields `ENOENT` unless such a
hive happens to be registered, in which case it resolves there.

`CurrentUser\` rewriting is not applied (§5.2.1), so a target beginning
with `CurrentUser\` routes as a hive of that name and cannot be
registered, and therefore always fails. Ordinary hive routing does
apply, private hives included, for the resolving thread.

## Depth

Symlink resolution is bounded by `SymlinkDepthLimit`, default 16,
configurable from 1 to 64. Exceeding it is `ELOOP`.

Two paths in the walk use the compiled-in default rather than the
configured value, so a `SymlinkDepthLimit` other than 16 is not honoured
everywhere.

## Opening the link itself

`REG_OPEN_LINK` on `reg_open_key` opens the symlink key rather than
following it, which is how a symlink is managed at all — deleted,
retargeted, inspected.

It applies to the **final path component only**. A symlink encountered
part-way along a path is followed whether or not the flag is set. The
access check follows the same rule: with `REG_OPEN_LINK` the check is
against the link, otherwise against the target.

## Creation

Creating a symlink needs all of:

- `KEY_CREATE_SUB_KEY` on the parent, as for any key;
- `KEY_CREATE_LINK` on the parent;
- either an enabled `SeTcbPrivilege` or membership of Administrators.

The last is a genuine disjunction — either satisfies it — and the
privilege branch marks the privilege used. Failing it is `EPERM`.
