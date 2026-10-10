---
title: Features
type: concept
description: Decide whether you need a package or a feature change, inspect lifecycle state, recover an interrupted step, and remove setup before its package.
related:
  - peios/features/using-feat
  - peios/features/feature-manager
  - peios/package-management/overview
  - peios/writing-features/writing-a-feature
---

Installing a package makes its files available. A **feature** performs
additional setup, such as defining a service or changing a setting, through
scripts you explicitly run. Installing its package does not run those scripts
or turn the feature on. Package-manager maintenance steps are a separate,
[closed set](~peios/peipkg/side-effects/the-recognised-set), not feature scripts.

Start with `feat list` and `feat info <name>` to see what is available, its
state and what it says it will change. Use [Using feat](~peios/features/using-feat)
for the commands, or open [Feature Manager](~peios/features/feature-manager)
from the launcher by typing `feature`.

| What you want | Tool |
|---|---|
| Install or remove the files that supply a feature | `peipkg` or Package Manager |
| Set up a feature without turning it on | `feat install <name>` |
| Set it up and turn it on | `feat add <name>` |
| Turn it off but keep its setup | `feat disable <name>` |
| Undo its setup before removing its package | `feat remove <name>` |

## What a feature can do

A feature's scripts run **as whoever asked**, with no authority of their
own. `feat` grants nothing: a script can do exactly what the person
running it could do by hand. An Administrator's request can define a
service; the same request from someone else is refused by the system, at
whatever step needs the authority.

## Its lifecycle

A feature is in one of three settled states, and moves between them a step
at a time:

| State | Means |
|---|---|
| **Not installed** | Nothing it would set up is in place. |
| **Installed** | Its install script has run: what it sets up is in place, but not in use. |
| **On** (enabled) | Its enable script has run as well: what it set up is in use. |

**Turning on** a feature that isn't installed installs it first. **Removing**
one that is on turns it off first. Each step runs one script: `install.sh`,
`enable.sh`, `disable.sh` or `uninstall.sh`. A feature that has nothing to do
at a step ships no script for it, and the step only records the new state.

What a feature's own words say about when it takes effect matters: dynamic
boot's services, for example, start at the next boot after it is turned on.

## Interrupted

Before each step's script runs, the step is recorded as begun; once the
script succeeds, the new state is recorded. A script that fails or is
stopped therefore leaves the feature **interrupted** — installing, turning
on, turning off or removing — rather than claiming a state it never
reached.

An interrupted feature is fixed by asking again: running the same step
reruns its script from the start, which every feature's scripts are written
to allow. Or it can be taken the other way: an interrupted turn-on can be
turned off, an interrupted install removed.

## Where its state is kept

Changing a feature requires write access to its registry state. As shipped,
Administrators can change it and everyone can read it. Use `feat` or Feature
Manager rather than editing numeric state to make a failed step look complete:
the scripts' work may still be unfinished.

The [client reference](~peios/peipkg/the-tools/feat-client-interface#where-its-state-is-kept)
keeps the definition path, registry key and complete numeric state mapping.

## When its package is removed

Removing the package that brought a feature takes its scripts away, but
not what they set up, since package removal does not run the feature's
teardown scripts. The registry
still holds the feature's state, and both `feat list` and Feature Manager
show it as having no definition. Installing the package again brings the
scripts back, so the feature can be turned off or removed properly.

Remove a feature before removing its package. Verify the feature's state
with `feat list` or `feat info <name>` after the removal. If its definition
is already missing, install the supplying package again, inspect the feature,
then use `feat remove <name>` while the scripts are available. Package `undo`
or `recover` is not a substitute for running the feature's teardown scripts.

## Features in an image

An image can install or turn on features as it is built, with
[`[[feature]]`](~peios/peiso/building-images/customising-an-image#features)
in its spec. They are set up at
the image's first boot, before its services start.

## Where to go next

- [Using feat](~peios/features/using-feat), the command.
- [Feature Manager](~peios/features/feature-manager), the window.
- [Writing a feature](~peios/writing-features/writing-a-feature), to ship one
  with your own package.
