---
title: Modified Files
description: A file whose content no longer matches the hash recorded at install — where the check runs, and what checking costs.
---

A file whose on-disk content no longer matches the hash recorded at
install has been modified since installation — by a person, by a
program, or by corruption.

## Where the check runs

peipkg compares recorded hashes against disk in two places.

`peipkg verify` does it on demand, across every recorded file, and
reports what differs.

An upgrade does it for configuration files, to decide whether to
preserve an operator's edit (§6.2).

An uninstall does not. Every owned path is renamed aside regardless of
whether its content matches what was installed, and the operator is not
told that something they customised is being removed.

> [!NOTE]
> A modified file at removal time is either a customisation that removal
> destroys, or an unauthorised modification of a system file. Both are
> worth surfacing, and both currently pass silently.

## The cost of checking

Hashing every installed file at uninstall is expensive: a large package
on slow storage takes seconds. The workable shape is to restrict the
check to paths where customisation is expected — configuration, and
locations policy names — and skip it for binaries and libraries, with
the operator able to authorise removal, skip the file, or abort.
