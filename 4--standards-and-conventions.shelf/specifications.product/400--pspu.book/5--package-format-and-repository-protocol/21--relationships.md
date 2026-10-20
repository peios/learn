---
title: Relationships
description: The five manifest fields expressing what a package needs, conflicts with, provides and replaces — with their constraints.
---

A package expresses its relationships to other packages in five manifest
fields:

- `dependencies` — packages that must be installed for this one to
  function
- `optional_dependencies` — packages that enhance functionality but are
  not required
- `conflicts` — packages that must not be installed alongside this one
- `provides` — virtual names this package satisfies on behalf of
  dependencies declared elsewhere
- `replaces` — packages this one supersedes

## Dependency entries

An entry in `dependencies` or `optional_dependencies`:

```json
{
  "name": "<package or virtual name>",
  "constraint": "<version constraint>",
  "arch": "<arch qualifier>",
  "root": "<root reference>",
  "claims": { "<slot>": { "path": "<absolute path>" } }
}
```

| Field | Required | Description |
|---|---|---|
| `name` | yes | The depended-on package name (§5.3) or virtual name (§5.4). |
| `constraint` | no | A version constraint per §5.7. Absent means any version satisfies. |
| `arch` | no | An architecture qualifier. Default `any`. |
| `root` | no | A root reference (§5.19) naming the root this dependency is placed and satisfied in. Absent means the same root as the depending package. |
| `claims` | no | Claim paths this dependency expects a holder to materialise (§5.23). |

`root`, when present, MUST be a syntactically valid named root
reference — never a filesystem path. An entry whose `root` is not one is
invalid.

## Conflict entries

An entry in `conflicts` has the same shape as a dependency entry, minus
`root` and `claims`, and expresses incompatibility rather than
requirement: a package MUST NOT be installed simultaneously with any
package matching the entry. A conflict whose `constraint` is absent
expresses incompatibility with any version of the named package.

## The architecture qualifier

`arch` restricts the qualified package's architecture. In this version
the only valid value is `any`, which is the default. Any other value
MUST be rejected.

`any` means: the qualified package's architecture MUST equal the
depending package's **effective architecture**, or be `noarch`.

A depending package's effective architecture is its own architecture
when arch-specific, and the system's primary architecture (§5.8) when
the depending package is `noarch`. A `noarch` label describes an
architecture-independent payload, not an architecture-independent
resolution context: a `noarch` package's dependencies on arch-specific
packages — a script on its interpreter, a meta-package on native tools —
resolve against the concrete system being assembled, exactly as a native
package's do.

> [!NOTE]
> A future version may permit explicit architecture identifiers here, to
> support multi-architecture systems. Reserving the field now is what
> makes such an extension parse compatibly.

## Provides entries

```json
{
  "name": "<virtual name>",
  "version": "<version string>",
  "claims": { "<slot>": { "target": "<absolute path>",
                          "path": "<absolute path>" } }
}
```

| Field | Required | Description |
|---|---|---|
| `name` | yes | The virtual name provided, conforming to §5.4. |
| `version` | no | The version of the capability provided. Parsed revision-relaxed (§5.7), because a provides version is a capability level rather than a packaging iteration. Absent means any version of the name is provided. |
| `claims` | no | Filesystem targets this package materialises when it holds the named role (§5.23). |

A virtual name that collides with a real package name MAY be provided;
both are then valid satisfiers of a dependency on that name.

`provides.version` SHOULD reflect the providing package's actual
functional compatibility level. A `provides.version` greater than the
providing package's own `version` MUST generate an operator warning at
install time, because an inflated provides-version defeats
constraint-based resolution.

> [!NOTE]
> The attack the warning exists for is concrete: a package at version
> `1.0-1` declaring `provides: [{name: libfoo, version: "5.0"}]`
> satisfies a dependency on `libfoo >= 4.0` and gets installed in place
> of a real `libfoo` — most easily when the real one is absent from the
> candidate set, which is precisely the shadowing case.

The provides relation does not flow transitively: providing
`smtp-server` does not provide whatever `smtp-server` itself provides.

## Replaces entries

```json
{
  "name": "<package name>",
  "constraint": "<version constraint>"
}
```

`name` is required and MUST conform to the package-name grammar (§5.3).
`constraint` is optional; absent means this package replaces any version
of the named one.

A replaces entry expresses supersession. During upgrade the replaced
package is removed and this one installed in its place: files owned by
the replaced package that no longer exist in this one are removed, and
files existing in both are updated.

A replaces entry does not imply a conflict. A package MAY both replace
and conflict with the same target, but a replaces entry is typically
sufficient on its own.

> [!NOTE]
> Replaces is the rename mechanism. When `nginx-core` becomes `nginx`,
> the new `nginx` declares `{ "name": "nginx-core" }` in `replaces`, and
> existing systems transition on their next upgrade.

## Field constraints

Each of the five fields is an array of objects matching the appropriate
schema. `dependencies` and `conflicts` MUST be present, and MAY be
empty. The other three MAY be omitted, which is equivalent to an empty
array.

Within a single field, entries MUST be sorted lexicographically by
`name`, and two entries MUST NOT carry identical `name` values. A
package with several constraints on one target MUST combine them into
that entry's single `constraint` string.

## What satisfies a dependency

A dependency is **satisfied** by a candidate package when all of the
following hold:

1. The candidate's name equals the dependency's `name`, **or** the
   candidate has a `provides` entry whose name equals it.
2. If the dependency carries a `constraint`, the version satisfies it —
   the candidate's own version when matched by name, and the matching
   `provides` entry's version when matched through `provides`.
3. The candidate's architecture satisfies the `arch` qualifier.
4. The candidate is installed, or is being installed, in the
   dependency's root (§5.19).

A conflict is **triggered** by a candidate when the same conditions hold
with respect to a `conflicts` entry.

A `claims` field has no effect on satisfaction. A dependency on a role
is satisfied by any installed eligible provider regardless of which one
currently holds the role; claims govern which installed file owns a
contended filesystem name, nothing more (§5.23).
