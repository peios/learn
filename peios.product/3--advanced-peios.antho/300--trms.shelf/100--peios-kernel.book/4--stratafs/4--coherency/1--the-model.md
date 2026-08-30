---
title: The Coherency Model
description: Strata change underneath stratafs without telling it — what can change a resolution, and the guarantee that survives it.
---

Every stratum of a mount may be modified at any time by an agent that
does not know stratafs exists. stratafs observes such changes without
being told of them.

## No coordination [*coherency.no-notification-protocol]

There is no notification machinery anywhere in the filesystem — no
`fsnotify` registration, no `inotify`, nothing a stratum's filesystem
is expected to report. No writer announces a change, quiesces, or
participates in any protocol. Every resolution is performed from
scratch by re-walking the stratum path string, so nothing has to be
told anything.

## What can change a resolution [*coherency.resolution-depends-on-names-not-contents]

A resolution depends only on which names each participating stratum
directory holds and what type each entry has. It does not depend on the
contents of any file.

A change to an object's **contents** therefore requires no action at
all. stratafs inodes carry no address-space operations; there is no
second page cache, and every data operation is forwarded to a backing
file opened on the provider. A change to that object is observed
through the mount immediately and by construction, because there is
nothing to invalidate.

A change to the **structure** of a participating stratum directory — an
entry created, removed, renamed, or replaced by one of another type —
may change which stratum provides a name. §4.4.2 covers how that is
handled, which is by not caching anything.

## The guarantee [*coherency.structural-change-visible-to-next-resolution]

A structural change in a stratum becomes visible to any resolution
begun after the stratum's own filesystem exposes that change to an
ordinary lookup. stratafs adds no delay of its own: there is no
timeout, no jiffies comparison, no generation counter, and no
resolution cache to serve a stale answer from.

It cannot anticipate a change the underlying filesystem is not yet
reporting. A network filesystem holding an attribute cache does not
show a change to stratafs any sooner than to any other caller, and
nothing claims otherwise.

Resolutions already completed are not revisited. Every regular-file
open is detached onto a descriptor-private dentry and inode holding
their own reference to the provider, and I/O runs against the file
opened at that time, so later masking or removal in any stratum cannot
reach that descriptor. It is not re-pointed and it does not fail. A
process holding a configuration file open across a package upgrade
continues to read the file it opened.

The one exception is copy-up, which §4.4.3 covers: a descriptor whose
own write caused a copy-up keeps its inode while that inode's backing
object becomes the copy.

## Live strata [*coherency.stratum-replaceable-while-mounted]

Because resolutions are made against current state, and because a
stratum is a path rather than a directory object (§4.2.1), a stratum's
directory may be replaced wholesale — by a package transaction, by a
reconciler, by an administrator — while the mount is live, with no
remount and no interruption to callers. That is the requirement the
filesystem exists to satisfy, and §4.4.2 is the whole of its cost.
