---
title: The claim Command
description: Listing providers and granting a role by hand, addressed by role, with the grants that are refused.
---

`peipkg claim` inspects and changes holders independently of install.

| Form | Effect |
|---|---|
| `peipkg claim <role>` | Report the role's holder, its materialised claim paths, and the installed eligible providers |
| `peipkg claim <role> grant <package>` | Make the named package the holder, repointing every claim link |
| `peipkg claim <role> revoke` | Revoke the current grant, removing the links and leaving the role unheld |

The bare form lists every installed eligible provider, including the
current holder.

A grant to a package that is not installed, and a grant to a package
that is installed but not an eligible provider, each fail with their own
error.

A revoke on a role that is not held is an error rather than a no-op.

A grant or revoke prompts for confirmation, satisfied by `--yes`, and
executes within a transaction that rolls back on failure like any other.

## Addressed by role

A role is addressed by name, never by path. Because a role has one
holder across all of its slots and paths, granting it moves every one of
its claim paths together.

> [!NOTE]
> Addressing by name rather than by path keeps a multi-path,
> multi-slot role coherent: one command moves the whole role, however
> many files it materialises. A path-addressed form would invite a role
> being half-moved.
