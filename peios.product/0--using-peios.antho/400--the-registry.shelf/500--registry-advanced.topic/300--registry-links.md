---
title: Registry links
type: how-to
description: Inspect a registry link without following it, distinguish its stored target from the key it reaches, and understand privileged creation and layered targets.
related:
  - peios/registry-concepts/keys-values-and-types
  - peios/registry-layers/layers
  - peios/registry-security/access-control
  - peios/registry-concepts/overview
---

A registry link redirects a key path to another key. A normal open follows
it, so an inspection may show the target's values rather than the link's
own stored target. Check which object you are operating on before changing
or deleting a link.

## Inspect the link without following it

For a suspected link at `KEY`, use:

```sh
reg info KEY --no-follow
reg get KEY @ --no-follow
```

Replace `KEY` with the actual path. The first shows the key's metadata,
including its link flag; the second reads its unnamed target value.
Add `-L` to the value read to see the winning target's layer and sequence.
Omitting `--no-follow` follows the link by default.

These are inspection commands. Do not assume an option documented for
`get` and `info` is available on every mutating subcommand. Check the
[`reg` command reference](~peios/registry-tools/reg#symlinks) before changing
a link itself.

## What makes a key a link

A link has both a fixed link flag set at creation and an unnamed default
value of type `REG_LINK` containing an absolute registry target path.
A `REG_LINK` value alone does not turn an ordinary key into a link.

This is the exception to the registry's ordinary opaque-data behavior:
LCS reads the target during path resolution. The handle returned by a
normal open refers to the resolved target.

## Creating a link is privileged

The command form is `reg link KEY TARGET`. Creation requires
`KEY_CREATE_SUB_KEY` and `KEY_CREATE_LINK` on the parent, plus either
`SeTcbPrivilege` or Administrator membership, in addition to applicable
layer rights.
Use it only when redirecting that namespace is intended.

Targets are followed literally. `CurrentUser` is not expanded inside a
link target, so do not use it expecting a caller-specific user redirect.
Resolution has a hop limit; cycles fail rather than loop indefinitely.

## Layers can redirect a link

The default target value is layered. A higher-precedence or later
same-precedence write can change where the link resolves. Removing that
entry lets the next winner determine the target; it need not be the
historical target you expected.

A winning default value whose type is not `REG_LINK` can make resolution
through the still-flagged link fail. Inspect the link with `--no-follow`
and check the target's winning layer before attempting a repair. Verify
both the stored target and the intended resolved key after recovery.

## Where to go next

- [Layer selection](~peios/registry-layers/layers)
- [Deletion, including recursive tools that do not follow links](~peios/registry-layers/deleting-keys-and-values)
- [LCS symlink implementation](~peios/lcs/the-data-model/symlinks) and
  [ABI](~peios/lcs/lcs-abi) for programmatic link handling
