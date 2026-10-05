---
title: Features
type: concept
description: What a feature is — set-up beyond the files a package installs, done by the feature's own scripts as you — how its state is kept, what it means when one is left interrupted, and where to manage them.
related:
  - peios/features/using-feat
  - peios/features/feature-manager
  - peios/package-management/overview
  - peios/writing-features/writing-a-feature
---

A package only puts files in place. Installing one never runs anything, so
it can never change what this machine does beyond the files it delivers.
Some software needs more than files, though: a service defined in the
registry, a setting changed, something made that the files rely on. A
**feature** is how that is done. Each one is a small set of scripts that
set something up, turn it on, turn it off and take it away again.

Features are deliberately plain and few. A package brings a feature's
scripts with it; nothing runs them until someone asks, with the `feat`
command or with [Feature Manager](~peios/features/feature-manager).

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

A feature's definition is read-only, in `/libexec/features/<name>/`. Its
state is the registry's, under `Machine\System\Features\<name>`, in the value
`State`:

| `State` | Means |
|---|---|
| 0 | Not installed |
| 1 | Installing (interrupted, if nothing is running) |
| 5 | Installed |
| 6 | Turning on |
| 10 | On |
| 9 | Turning off |
| 4 | Removing |

Changing a feature needs write access there. As shipped, only Administrators
have it; everyone can read it, so anyone can see what is set up.

## When its package is removed

Removing the package that brought a feature takes its scripts away, but
not what they set up, since removing a package runs nothing. The registry
still holds the feature's state, and both `feat list` and Feature Manager
show it as having no definition. Installing the package again brings the
scripts back, so the feature can be turned off or removed properly.

Remove a feature before removing its package.

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
