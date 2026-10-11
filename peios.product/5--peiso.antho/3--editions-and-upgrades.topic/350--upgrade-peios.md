---
title: Upgrade Peios
type: how-to
description: Move a machine to the next release on the desktop with Upgrade Peios, which runs upgrade-peios as you — the check, the plan, when the release's settings apply, and what you may do.
related:
  - peios/peiso/editions-and-upgrades/upgrading-peios
  - peios/package-management/package-manager
---

**Upgrade Peios** is the desktop's window on
[`upgrade-peios`](~peios/peiso/editions-and-upgrades/upgrading-peios).
Open it from the launcher (type `upgrade`). It has no authority of its
own: it runs `upgrade-peios --driven` as you, with the same package and
seed operations. Driven mode handles an explicit cancellation separately:
a `cancelled` result stops before release seeds are staged or applied.
Do not apply the [ordinary CLI's declined-prompt warning](~peios/peiso/editions-and-upgrades/upgrading-peios)
to that driven cancellation result.

## The release

At the top is the release installed on this machine, as its name (Peios 2026.8
Experimental) and its edition package with that package's version. Beside
it, once Upgrade Peios has looked: **Up to Date**, a newer release
**Available**, or **Not Checked** when the look was refused.

## Looking for a newer release

Upgrade Peios looks as it opens, and again with **Check Now** or **Check
Again**. A look refreshes the repositories this machine trusts, updating
cached metadata, then previews the package plan without applying it or
staging or applying release seeds.

It refreshes only repositories already trusted: a repository set up but
never confirmed is confirmed in
[Package Manager](~peios/package-management/package-manager), under
Repositories, never as a side effect of looking.

When a newer release is offered, the page shows every change upgrading
makes — the edition package and whatever of its release comes with it —
with what it downloads and takes once installed.

## Upgrading

**Apply Its Settings at the Next Restart** chooses when the release's
settings (its registry seeds: which services run, which policies apply) take
effect. Off, as it starts, they are applied as soon as the release is
installed. On, they wait for the next restart; use it when a setting would
change something under the people signed in now.

**Upgrade to …** makes the upgrade. The changes it makes are the ones just
shown; if they differ by the time it starts, because a repository changed in
between, the new changes are shown and asked about again. Anything peipkg
needs your specific approval for, such as a package moving back to an older
version, is asked on its own, as in Package Manager.

The page then shows how far it has got: downloading and checking, putting
the release in place, recording it, then gathering and applying the
release's settings. Once the upgrade is approved it is made to the end even
if you close the window, which stays, saying so, until it is done.

The upgrade doesn't restart the machine. Its displayed release and
completed package/seed steps do not establish which kernel or service
binaries are running. Follow the [outcome checks](~peios/peiso/editions-and-upgrades/upgrading-peios#check-the-outcome),
and follow the [activation inspection checklist](~peios/peiso/editions-and-upgrades/upgrading-peios#check-what-an-update-has-activated)
before relying on a kernel update.

## When something stops it

- **A repository's information is out of date**, and refreshing it brought
  nothing newer. **Continue Anyway** carries on with what this machine
  already has, as `--allow-stale` does, and is recorded. Upgrade Peios
  remembers it until you close it.
- **A repository isn't trusted yet.** Confirm it, or remove it, in Package
  Manager.
- **Another change is being made.** **Try Again** once it has finished.
- **The release's settings couldn't all be applied.** The release is
  installed; its settings wait for the next restart, which tries them
  again.

## Settings waiting for the next restart

When some of the release's settings are waiting for the next restart —
left by an upgrade made that way, or by one that stopped part-way — the
page says so, with **Apply Now** to apply them at once, as
`upgrade-peios --seeds-only` does.

## What you may do

Whether you may upgrade is asked of the system, by `upgrade-peios`. As
shipped, only Administrators may. Anyone else sees the release, with the
reason said once, and nothing to press.

Software other than Peios itself is updated in Package Manager, which holds
the edition back and points here.

The driven invocation is established by
[gxwi-upgrade-peios `f40e8d8b`](https://github.com/peios/gxwi-upgrade-peios/blob/f40e8d8bdc7a5a1b40e3a83227dc70fdf53c6725/src/tool.rs#L162-L206).
The [release updater's source scope](~peios/peiso/editions-and-upgrades/upgrading-peios#source-and-release-scope)
also applies; a source revision is not proof of the version in an installed image.
