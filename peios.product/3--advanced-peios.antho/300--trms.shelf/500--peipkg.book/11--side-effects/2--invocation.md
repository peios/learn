---
title: Invocation
description: Each side effect maps to one fixed command, and the three properties that keep a package from influencing how it runs.
---

Each side effect maps to one fixed command.

| Identifier | Invoked as |
|---|---|
| `ldconfig` | `/bin/ldconfig`, no arguments |
| `depmod` | `/bin/depmod -a` |
| `man-db` | `/bin/mandb -q` |

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

`depmod -a` acts on the *running* kernel, since no release is named.

A transaction installing modules for a kernel release other than the one
currently booted — which is the normal case during a kernel update, and
always the case during an image build — rebuilds the running kernel's
dependency cache and leaves the installed release's unbuilt, so those
modules are unloadable until something rebuilds it.

A package shipping modules for two releases gets one invocation, for
neither of them necessarily.

## The root

The tools invoked are the **host's**, at the host's absolute paths, with
no root argument.

An operation against an alternate installation root therefore rebuilds
the host's caches rather than the target's — once per participating
root, in a cross-root transaction, and never for the root whose contents
changed.

`peipkg-compose` runs no side effects at all, so a composed root's
caches are never built by the composer either.
