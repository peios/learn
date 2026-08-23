---
title: Hives and Routing
description: A hive is the first component of every path — the routing table that maps hive names to sources, and the two names the kernel knows itself.
---

A hive is a top-level namespace — the first component of every registry
path. LCS keeps a routing table mapping hive names to registered
sources, and that table is built entirely from what registers. There is
no static configuration.

| Field | Description |
|---|---|
| Name | The hive name, e.g. `Machine`, `Users`. Case-preserving, compared case-insensitively. |
| Root GUID | The GUID of the hive's root key, supplied by the source at registration. |
| Source | The source slot backing this hive. |
| Status | Active or Unavailable, tracking source connectivity. |

Status is a property of the source slot rather than of the individual
hive, which amounts to the same thing: a slot's hives are exactly one
source's, and they go Down together.

## Route identity

A hive route is identified by the pair **(case-folded name, scope)**,
where the scope is either the global namespace or one private scope
GUID. That pair must be unique across every registered source; a source
claiming one another source already holds is rejected.

The same name may appear in different scopes, which is precisely how a
private hive shadows a global one without colliding with it.

A hive is backed by exactly one source. A source may back many.

## Routing a path

LCS takes the first component of a path — everything before the first
separator — and looks it up. Registered and active routes to the
backing source. Not registered is `ENOENT`. Registered but Down is
`EIO`.

Before any source registers, the table is empty and every path yields
`ENOENT` (§5.10.1).

## `CurrentUser` is not a hive

`CurrentUser\` is a kernel-level alias. When a caller-supplied absolute
path starts with it, LCS reads the user SID from the calling thread's
effective token and rewrites the path to `Users\<SID>\...` before
routing. The rewritten path is re-checked against the total-length
limit, since a textual SID is longer than the alias it replaced.

Three constraints keep this safe.

It applies **only to the first component** of a path, and only to a
caller-supplied absolute one. It does **not** apply to symlink targets:
a target beginning with `CurrentUser\` is followed literally, routes as
a hive of that name, and finds nothing. Without that rule, a symlink
containing `CurrentUser\` would redirect a privileged service into the
service's own user hive — a confused deputy.

And `CurrentUser` cannot be registered as a hive name. LCS rejects the
registration with `EINVAL`, so the alias can never collide with a real
hive.

Symlink targets *are* subject to ordinary hive routing, private hives
included. A sandboxed process resolving a symlink sees the same
registry through it that it sees directly, which is the point of
sandboxing it.

## Two names the kernel knows

LCS is source-agnostic about routing but not entirely ignorant of
names. `Users` is compiled in as the target of `CurrentUser\`
rewriting. `Machine` is matched, case-insensitively and only for a
global hive, to decide when to run the bootstrap refresh that reads
LCS's own configuration (§5.10.2).

Neither is a routing decision — an unregistered `Machine` routes
nowhere like any other name — but the two names do exist in the kernel.

In practice loregd registers `Machine` and `Users` at boot. Other
sources may register other hives at any time.

## Names

Hive names follow the same rules as key name components: no backslash,
no forward slash, no null byte, valid UTF-8, non-empty, and no longer
than `MaxPathComponentLength`. They are case-preserving and compared
case-insensitively (§5.2.8).
