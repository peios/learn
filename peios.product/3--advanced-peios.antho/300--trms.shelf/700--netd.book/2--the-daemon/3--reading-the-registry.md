---
title: Reading the registry
description: What netd reads from Machine\System\Network, how values are lowered before anything interprets them, the depth limit, and what a registry change causes.
---

netd reads its configuration from `Machine\System\Network`, whole, every
time it reads it.

## What is read [*config.what-is-read]

| Value or key | Used for |
|---|---|
| `Hostname` (`REG_SZ`) | the machine's name (§8.4). An empty string counts as unset. |
| `ControlSecurity` (`REG_BINARY`) | the control object's descriptor (§9.1). An empty value counts as unset. |
| `Duid` (`REG_SZ`) | the machine's DHCP unique identifier, as hex (§5.7). A value that is not hex is ignored with a warning. |
| `Rules\Interface\` and everything under it | the interface layer (§3.2) |
| `Profiles\` and everything under it | the profiles (§3.1) |

Nothing else under the key is configuration to netd. `Interfaces\` and
`Networks\` are read only for the values netd shares with the operator
(§5.7, §7.2), at the moment it needs them.

A missing `Machine\System\Network` means no configuration: no hostname,
no rules (so the backstop ignores every interface), no profiles.

## Lowering [*config.lowering]

Every value in the two trees is lowered to one of four shapes before
anything interprets it:

| Registry type | Lowered to |
|---|---|
| `REG_DWORD` (4 bytes) | an integer |
| `REG_QWORD` (8 bytes) | an integer |
| `REG_SZ`, `REG_EXPAND_SZ` | a string, cut at the first NUL; *other* if not UTF-8 |
| `REG_MULTI_SZ` | a list of strings, empty items dropped, invalid UTF-8 items dropped |
| anything else, or a DWORD or QWORD of the wrong length | *other* |

The rule builder refuses an *other* by name (§3.2), and the profile
parser refuses it as a value of the wrong shape (§3.1), so an unusable
value is never silently dropped. The default (unnamed) value of a key is
skipped in both trees.

Values and subkeys are sorted by name, so two readings of an unchanged
tree compare equal.

A tree is read at most 16 levels deep. Below that the read stops with a
warning, and whatever lies there is not part of the configuration.
`pnp-core` refuses rule nesting deeper than 12 anyway (PKM §6.5), so the
limit matters only to a pathological profile tree.
[*config.tree-read-sixteen-deep]

## A registry change [*config.registry-change]

The watch is armed on the whole `Machine\System\Network` subtree. On any
event, netd reads the whole configuration again and compares it with
what it holds:

- If anything differs, the control object is rebuilt from
  `ControlSecurity`. If the rules or the profiles differ, a new
  generation is built (§3.2), and taken or refused.
- Whatever differs, a full pass follows.

netd's own writes to `Interfaces\` and `Networks\` come back through the
same watch. They cause a reload that finds nothing changed, and a pass
that plans nothing.

A failed read of the watch's events re-arms the watch.

There is no reload command: a write is noticed within the time it takes
the watch to deliver and a pass to run.
