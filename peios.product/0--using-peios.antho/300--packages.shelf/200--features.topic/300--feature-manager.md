---
title: Feature Manager
type: how-to
description: Turn features on and off on the desktop with Feature Manager, which runs feat as you — what each card shows, what each button does, an interrupted feature, and what you may change.
related:
  - peios/features/overview
  - peios/features/using-feat
  - peios/package-management/package-manager
---

**Feature Manager** is the desktop's window on
[features](~peios/features/overview). Open it from the launcher (type
`feature`). It has no authority of its own: it runs `feat` as you, so what
you may change is exactly what you could with the command.

## The cards

Each feature on this machine is a card: its title and name, its state, and
what it says it does. The state is one of:

| State | Means |
|---|---|
| **Not Installed** | Nothing it sets up is in place. |
| **Installed, Off** | What it sets up is in place, but not in use. |
| **On** | It is set up and in use. |
| **Interrupted** | One of its scripts didn't finish. The card says which, and what each way on does. |
| **Definition Missing** | Its package was removed while it was set up. What it set up is still in place; installing the package again lets it be turned off or removed. |

A feature comes in a package: one installed with
[Package Manager](~peios/package-management/package-manager) appears here.

## The buttons

| Button | Does | The command |
|---|---|---|
| **Turn On** | On a feature that isn't installed, installs it and turns it on. On one that is, turns it on. | `feat add`, `feat enable` |
| **Install Only** | Installs it without turning it on. | `feat install` |
| **Turn Off** | Turns it off, leaving it installed. | `feat disable` |
| **Remove…** | Asks first, then turns it off if it is on and removes it. The feature stays available to install again; its package isn't removed. | `feat remove` |
| **Try Again** | On an interrupted feature, runs the step that didn't finish again. | the same command again |

While a change is being made, its card shows which script is running and
the last thing it said. Once it is done, the line along the bottom says so.

If a script fails, the card says which, shows everything the script said,
and offers **Try Again**. The feature is left interrupted until it is
tried again or taken the other way.

A change is made to the end even if you close the window: the window stays
until then, saying so, and then closes.

## What you may do

Whether you may change a feature is asked of the system, by `feat`. As
shipped, only Administrators may. Anyone else sees every feature and its
state, with the reason said once at the top, and no buttons.

Being allowed to change a feature's state doesn't make every script able
to do its work: a script that needs more than you have fails, and says so
on the card.

## Where to go next

- [Using feat](~peios/features/using-feat), the same from a terminal, and
  for a program of your own.
- [Writing a feature](~peios/writing-features/writing-a-feature).
