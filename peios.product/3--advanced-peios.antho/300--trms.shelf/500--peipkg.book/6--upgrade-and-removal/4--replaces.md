---
title: Replaces
description: Supersession after a rename — the guard on a replaces-triggered upgrade, and how it interacts with removal.
---

A `replaces` relation expresses supersession: this package takes over
from that one, typically after a rename.

An upgrade triggered by a `replaces` follows the ordinary upgrade
procedure with the replaced package treated as the currently installed
version, even though its name differs. The database record for the
replaced package is removed and a record for the replacing package is
created. From the system's point of view the replaced package is
uninstalled and the replacing one installed; the file diff ensures no
payload file is spuriously removed during the transition.

## The guard

A `replaces` declared by a package from a lower-priority repository,
targeting a package installed from a higher-priority one, requires
explicit operator confirmation before it is applied (§3.7). A general
`--yes` does not satisfy it.

The guard compares repository priorities. For a package whose
originating repository has since been removed, there is no priority to
compare and the guard does not fire.

## Removal interaction

A package cannot be uninstalled while another installed package's
`replaces` targets it, unless that package is being removed in the same
transaction.
