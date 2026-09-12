---
title: Invocation
description: Each side effect maps to one fixed command, and the three properties that keep a package from influencing how it runs.
---

Each side effect maps to one fixed command, shaped by the installation
root the transaction acted on.

| Identifier | Host root (`/`) | Alternate root |
|---|---|---|
| `depmod` | `/libexec/depmod -a <release>`, once per affected kernel release | `/libexec/depmod -b <root> -m /usr/lib/modules -a <release>`, once per affected release |
| `man-db` | `/bin/mandb -q` | Not invoked; the operation report says so |

## Hardening

Three properties make invocation safe against a package trying to
influence it.

**A fixed absolute path.** The set is closed, so peipkg knows each
tool's location and never searches a path variable. A package cannot
shadow the intended tool, and because the location is a root-level
runtime view, populating the writable stratum behind it needs separate
local-administrator authority that a package does not have.

**A cleared environment.** Each tool runs with exactly `LC_ALL=C` and
`PATH=/bin`. Nothing is inherited from the invoking context, which
closes the environment-injection route.

**Standard input closed.** Each tool runs with its input attached to the
null device.

Output is captured and length-capped, so a runaway tool cannot flood the
operation report.

## The kernel release

`depmod` names the release it indexes, and runs once per release whose
module set the transaction changed. The releases come from the
transaction's own file lists — every staged package's payload and every
removal's ownership rows, under `usr/lib/modules/<release>/` — rather
than from the running kernel, so installing modules for a kernel other
than the one booted (the normal case during a kernel update, and always
the case in an image build) indexes the release that changed. A package
shipping modules for two releases gets two invocations; a release split
across two packages gets one.

A transaction that declares `depmod` but neither installs nor removes a
kernel module runs nothing and reports a warning, rather than falling
back to indexing the running kernel.

## The root

The tools invoked are always the **host's** binaries, at the host's
fixed absolute paths, and each is directed at the root the transaction
acted on. For the host root the bare forms in the table run. For an
alternate root — a named root, an initramfs image, a mounted target —
each root of a cross-root transaction schedules its own side effects
against itself.

`depmod` is given the root with `-b` and the module directory beneath it
with `-m /usr/lib/modules`. The second argument is what makes the first
work: kmod's default module directory is `/lib/modules`, which on a
running Peios is the runtime view of `/usr/lib/modules`, but an
alternate root is storage with no views mounted over it, so without `-m`
the tool would look under `<root>/lib/modules` and index nothing.

`man-db` is not run against an alternate root. The man index is a cache
that the reading system's own man-db configuration locates and keys, and
the host's `mandb` cannot be pointed at another root's configuration.
The operation report carries one warning naming the effect and the root;
page lookup in that root falls back to a filesystem scan until that
system's own next `man-db` side effect rebuilds the index.

`peipkg-compose` runs no side effects at all, so a composed root's
caches are never built by the composer either.
