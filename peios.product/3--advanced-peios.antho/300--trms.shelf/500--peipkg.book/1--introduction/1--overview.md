---
title: Overview
description: What peipkg is — the program that fetches, verifies and installs software — what is unusual about it, and the shape of an operation.
---

peipkg is the package manager of Peios: the program that fetches
software from a repository, verifies it, and installs it onto a system.
It is the consumer side of the package format and repository protocol
(PSPU §5), and it is one of several programs built around that format.

## What it does

peipkg maintains a picture of what is installed, resolves what a
requested change implies, and applies that change as a single
transaction that either lands completely or does not land at all. Around
that core sit the parts that make the core trustworthy: a per-repository
trust state, a verification pipeline that runs to completion before any
byte reaches its destination, and a journal that survives a power cut
mid-write.

## What is unusual about it

**It holds no identity.** peipkg is not a daemon and has no service
principal. It runs as whoever invoked it, and every file it creates or
replaces is checked by the kernel against that caller's token. There is
no standing privileged process to compromise, and the blast radius of a
malicious package is exactly the authority of the person who installed
it. The consequence runs both ways: peipkg cannot let a low-authority
operator install something they could not have written by hand, and it
does not need to be trusted to keep its own hands clean.

**Packages carry no permissions.** Every entry in a package is mode
`0777`, owned by uid 0, with no extended attributes. That is honest
signalling rather than laxity: a mode bit in a package would imply a
contract the kernel does not consult. What access control an installed
file ends up with is decided at install time, from the parent
directory's inheritable descriptor or from an explicit override the
package declares and the operator approves.

**There are no install scripts.** A package cannot ship code that runs
at install time. It can declare that one of three standard maintenance
operations is required, from a closed enumerated set, and peipkg invokes
that operation itself, from a fixed absolute path, with a cleared
environment. Everything a package might otherwise want a script for —
registering a service, seeding registry state — belongs to the
higher-level artifacts that compose packages.

**Installation targets a named root, not a path.** The default root is
the system root, but a system may define others — an initramfs image is
the motivating case — and a package's dependency closure flows into the
root the package occupies unless a dependency names a different one. A
package never names a filesystem location; it names a root, and where
that root lives is the installing system's business.

**Several packages may contend for one filesystem name.** A *role* is a
virtual name that more than one installed package can provide, with at
most one *holding* it. The holder's file answers the contended path
through a symlink peipkg owns. Two registry daemons can be installed at
once; only one is `/usr/bin/registryd`.

## The shape of an operation

Every install, upgrade, and uninstall follows the same arc. peipkg
acquires an exclusive lock, resolves the request against the installed
set and the configured repositories' indexes, presents the resulting
plan for confirmation, fetches and fully verifies every package the plan
names, stages each file beside its destination, journals its intent,
renames everything into place, commits the database, and only then runs
any side effects.

The database commit is the single durability boundary. Before it, a
crash rolls the whole transaction back from the journal's record of
where each displaced file was moved to. After it, the transaction
happened and there is only cleanup left. There is no state in which a
transaction is half committed.
