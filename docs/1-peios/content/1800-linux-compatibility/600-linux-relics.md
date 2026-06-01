---
title: Linux relics
type: concept
description: Some Linux features survive on Peios for compatibility but are superseded and outside Peios's recommended surface. They still work as they do on Linux; Peios does not document them in depth. This page lists them, with the privilege each needs and where to look instead.
related:
  - peios/linux-compatibility/overview
---

A handful of Linux features are **relics**: they still exist and still work the way
they do on Linux — so software depending on them keeps running — but they have been
superseded and are not part of how anything is meant to be done on Peios. Peios does
not document them in depth. For the mechanics of the underlying Linux feature, the
authoritative source is third-party Linux documentation (the relevant `man` pages
and the kernel's own docs). Where Peios has a native replacement for what the relic
was used for, this page points to it — that, not the relic, is the path to take.

A feature belongs here only if it is genuinely superseded, has no role in Peios's
future, and gives essentially no reason to reach for it. This is a short list by
design, not a place to park anything inconvenient to document.

## Process accounting (`acct`)

`acct()` is BSD process accounting. Called with a filename it turns on system-wide
accounting, appending a fixed binary record for every process as it terminates —
resource usage, timing, exit status, and a few behaviour flags; called with no
argument it turns accounting off. Enabling or disabling it requires
**`SeTcbPrivilege`** (the privilege Linux's `CAP_SYS_PACCT` maps to). For the record
format and per-field detail, see the Linux `acct(2)` and `acct(5)` documentation.

On Peios you almost certainly want **eventd and KMES** instead: process lifecycle is
already an event stream there, keyed on each process's GUID and carrying its real
identity, exit status, and resource usage — structured and queryable, where `acct`
produces an opaque append-only file built around the Linux UID model. See the eventd
and KMES material for the native way to account for what processes do.
