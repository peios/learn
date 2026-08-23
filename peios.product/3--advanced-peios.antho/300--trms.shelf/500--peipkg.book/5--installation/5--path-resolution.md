---
title: Path Resolution
description: How an install path is computed and used, what the final component is protected against, and what is not protected.
---

An install path is computed by joining the payload-relative path to the
installation root, and then used as an ordinary path.

## What is protected

The **final component** of every operation is symlink-safe. A staged
file is created with exclusive-create semantics, so it cannot land on an
existing file. A pre-existing entry at a destination is detected without
following it, and is displaced by a rename, which does not follow a
symlink at either end. A symlink already sitting at an install path is
therefore renamed aside rather than written through.

## What is not

**Ancestor components are resolved by the kernel afresh, following
symlinks, on every call.** peipkg holds no directory descriptor across
an operation and re-walks each path string at each step.

Two consequences follow.

**A symlink ancestor redirects a write, with no race involved.** The
format's rules permit a package to ship a symlink whose target resolves
into a permitted destination, and permit a *different* package to ship a
file whose path descends through that symlink's location — each entry
validates in isolation. When the second package installs, the ancestor
symlink is followed, and the file lands where the symlink points rather
than where the archive said. The path recorded in the database is the
archive's path, so the collision constraint of §5.3 compares the wrong
name and does not fire.

**The window between check and commit is the whole transaction.** The
check for a pre-existing entry runs while the transaction's intent is
being journalled; the rename that acts on it runs in the apply phase,
after every package in the transaction has been downloaded, decompressed
and staged. Nothing is re-validated at commit, and no descriptor pins
the directory in between.

> [!NOTE]
> The format's symlink-target rules are the first layer of the defence
> described in PSPU §5.26, and component-wise resolution against a
> pinned parent descriptor is the second. Only the first is in place.
> The second is what PSPU §5.26 requires of a conforming consumer, and
> what closes the two cases above.
