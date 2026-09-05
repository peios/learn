---
title: Symlinks
description: The two load-bearing mechanisms behind a symlink key — the structural flag and the target value — plus resolution, depth and opening the link itself.
---

A symlink key uses two mechanisms, and both are load-bearing.

The **symlink flag** on the key record marks the key's structural type.
It is set at creation by `REG_OPTION_CREATE_LINK` and is immutable
afterwards. [*symlink.flag.set-at-creation-and-immutable]

`RSI_WRITE_KEY` can update only the descriptor and the last write time,
so there is no operation that could change it. [*symlink.flag.rsi-write-key-cannot-change-it]

The **default value, of type `REG_LINK`,** supplies the target
path. [*symlink.target.is-the-reg-link-default-value]

It is an ordinary layered value, which means a higher-precedence layer
can redirect a symlink by writing a different `REG_LINK` default value,
and removing that layer restores the original target. [*symlink.target.layer-can-redirect-and-revert]

The flag marks identity; the value provides the target.

## Resolution

LCS follows symlinks during path resolution and the fd it returns
refers to the resolved target — its GUID, its position in the tree, its
ancestor chain — not to the link. [*symlink.resolution.fd-refers-to-the-target]

The target is resolved by issuing a separate `RSI_QUERY_VALUES` for the
key's default value (the empty name) and applying ordinary layer
resolution to the result, so the target participates in the layer
system exactly as any other value does. [*symlink.resolution.target-read-with-layer-resolution]

If the effective default value is missing, or is not of type
`REG_LINK`, resolution fails with `EINVAL`. [*symlink.resolution.missing-or-wrong-type-is-einval]

LCS does **not** validate the type at write time: a layer that writes a
`REG_SZ` default value over a symlink's target breaks resolution at the
next open, and removing that layer fixes it. [*symlink.resolution.target-type-not-validated-at-write-time]

The offending value stays in the registry; a failed resolution writes
nothing. [*symlink.resolution.failed-resolution-writes-nothing]

## The target path

The `REG_LINK` payload is a length-delimited UTF-8 registry path. No
trailing null is required or permitted — the length delimits it, and a
null byte inside that length is rejected like any
other. [*symlink.target-path.length-delimited-no-trailing-null] Forward
slashes are handled as separators as everywhere else.

The target is validated with exactly the same rules as a syscall path:
UTF-8, no null bytes, per-component and total length, no empty
components, no trailing separator, maximum depth. [*symlink.target-path.validated-like-a-syscall-path] The only difference
is that a syscall path arrives null-terminated and has its terminator
stripped first.

A target is always interpreted as absolute — its first component is
routed as a hive name. [*symlink.target-path.always-absolute]

There is no check that rejects a relative-looking target as malformed.
A target of `Sub\Key` is not an error; it is a request for a hive named
`Sub`, and it yields `ENOENT` unless such a hive happens to be
registered, in which case it resolves there. [*symlink.target-path.relative-looking-target-not-rejected]

`CurrentUser\` rewriting is not applied (§5.2.1), so a target beginning
with `CurrentUser\` routes as a hive of that name and cannot be
registered, and therefore always fails. Ordinary hive routing does
apply, private hives included, for the resolving thread.

## Depth

Symlink resolution is bounded by `SymlinkDepthLimit`, default 16,
configurable from 1 to 64. Exceeding it is `ELOOP`. [*symlink.depth.exceeding-the-limit-is-eloop]

Two paths in the walk use the compiled-in default rather than the
configured value, so a `SymlinkDepthLimit` other than 16 is not honoured
everywhere. [*symlink.depth.limit-not-honoured-on-two-paths]

## Opening the link itself

`REG_OPEN_LINK` on `reg_open_key` opens the symlink key rather than
following it, which is how a symlink is managed at all — deleted,
retargeted, inspected. [*symlink.open-link.opens-the-link-not-the-target]

It applies to the **final path component only**. A symlink encountered
part-way along a path is followed whether or not the flag is
set. [*symlink.open-link.final-component-only]

The access check follows the same rule: with `REG_OPEN_LINK` the check
is against the link, otherwise against the target. [*symlink.open-link.access-check-follows-the-flag]

## Creation

Creating a symlink needs all of:

- `KEY_CREATE_SUB_KEY` on the parent, as for any key; [*symlink.create.requires-key-create-sub-key]
- `KEY_CREATE_LINK` on the parent; [*symlink.create.requires-key-create-link]
- either an enabled `SeTcbPrivilege` or membership of Administrators. [*symlink.create.requires-setcbprivilege-or-administrators]

The last is a genuine disjunction — either satisfies it — and the
privilege branch marks the privilege used. [*symlink.create.privilege-branch-marks-privilege-used]

Failing it is `EPERM`. [*symlink.create.failure-is-eperm]
