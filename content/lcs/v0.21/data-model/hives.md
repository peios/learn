---
title: Hives
order: 2
---

A hive is a top-level namespace -- the first path component in every
registry path. LCS maintains a routing table mapping hive names to
registered sources.

## Fields

| Field | Type | Description |
|---|---|---|
| Name | string | Unique hive name (e.g., "Machine", "Users"). Case-insensitive. |
| Root GUID | GUID | The GUID of the hive's root key. Provided by the source at registration. |
| Source | fd reference | The char device fd of the source backing this hive. |
| Status | enum | Active or Unavailable. Tracks source connectivity. |

## Constraints

- A hive name MUST be unique across all registered sources. A source
  attempting to register a hive name already claimed by another source
  MUST be rejected.

- A hive is backed by exactly one source. A source MAY back multiple
  hives.

- `CurrentUser` is not a hive. It is a kernel-level alias. When a
  path begins with `CurrentUser\`, LCS extracts the calling thread's
  user SID from their token and rewrites the path to
  `Users\<SID>\<remainder>` before routing. This rewriting applies
  only to the initial caller-supplied path. Symlink targets
  encountered during path resolution are NOT subject to CurrentUser
  rewriting -- they are followed literally. This prevents a confused
  deputy attack where a symlink containing `CurrentUser\` redirects
  a privileged service into the service's own user hive. Symlink
  targets ARE subject to normal hive routing including private hive
  routing — if the resolving thread has a private hive that shadows
  the target's hive, the symlink resolves into the private hive.
  This is intentional: a sandboxed process should see a consistent
  view of the registry through symlinks.

- Hive names follow the same naming rules as key name components:
  no backslash, no forward slash, no null. Case-preserving,
  case-insensitive.

- The name "CurrentUser" (case-insensitive) MUST NOT be registered
  as a hive name. LCS MUST reject registration attempts with this
  name (EINVAL). CurrentUser is reserved as a kernel-level alias
  and must never collide with a real hive.

## Routing

When a registry syscall provides a path, LCS extracts the first
component (everything before the first backslash) and looks it up
in the routing table. If the hive is registered and active, the
request is routed to the backing source. If the hive is not
registered, the syscall fails with ENOENT. If the hive is
registered but the source is unavailable, the syscall fails with
EIO.

The routing table is updated when sources register or disconnect.
There is no static configuration -- hive routing is entirely
dynamic, driven by source registration.

## Private hives

A private hive is a hive registered with the RSI_HIVE_PRIVATE flag
and a scope GUID. Private hives are not globally visible -- they
are only accessible to threads whose credentials carry the matching
scope GUID.

### Routing with private hives

When routing a path, LCS checks private hives before global hives.
For each scope GUID in the calling thread's credentials (in order),
LCS checks whether a private hive with the path's hive name and
that scope GUID exists. If found, that hive is used. If no private
hive matches, the global routing table is checked.

Private hives can shadow global hives. A thread with a private
"Machine\" hive sees the private version, not the global one. This
enables complete registry isolation for sandboxing and containers.
The maximum number of scope GUIDs per token is bounded by
MaxScopeGUIDsPerToken (default 8).

### Credential attachment

A thread's credentials MAY carry an ordered set of scope GUIDs.
The mechanism for attaching scope GUIDs to credentials depends on
KACS token extensions not yet specified. LCS defines the routing
behaviour; KACS defines the credential model.

**Security constraint on KACS.** When KACS implements scope GUID
attachment, it MUST verify that the attaching principal is
authorised to join the scope. The specific authorization mechanism
(privilege check, scope creator approval, etc.) is a KACS design
decision. Without this constraint, any process could claim
membership in any scope, defeating private hive isolation.

### Scope lifecycle

A scope GUID is an opaque 128-bit identifier generated using a
cryptographically secure pseudorandom number generator. It has no
inherent lifecycle. It exists as long as at least one private hive or
credential references it. When the last private hive using a scope
GUID is unregistered and no credentials carry it, the scope is
implicitly gone. LCS does not track scope lifecycle -- it only
checks for scope GUID matches during routing.

## Default hives

LCS does not hardcode any hive names. The hive namespace is
determined entirely by which sources register and what names they
claim. In practice, loregd registers `Machine` and `Users` at boot.
Other sources MAY register additional hives at runtime.
