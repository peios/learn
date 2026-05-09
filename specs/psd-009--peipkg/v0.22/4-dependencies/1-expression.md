---
title: Expression
---

A package's relationships to other packages are expressed in
five fields of the manifest:

- `dependencies`: packages that MUST be installed for this
  package to function.
- `optional_dependencies`: packages that enhance functionality
  but are not required.
- `conflicts`: packages that MUST NOT be installed alongside
  this one.
- `provides`: virtual names this package satisfies on behalf
  of dependencies declared elsewhere.
- `replaces`: packages this one supersedes (typically used
  for renames).

This section defines the schema and syntax of entries in
these fields.

## Dependency object

A single entry in `dependencies` or `optional_dependencies`
has the form:

```json
{
  "name": "<package or virtual name>",
  "constraint": "<version constraint>",
  "arch": "<arch qualifier>"
}
```

| Field | Type | Description |
|---|---|---|
| `name` | string | The depended-on package name or a virtual name (§4.1.4). MUST conform to §2.1. |
| `constraint` | string | OPTIONAL. A version constraint per §2.2.8. If absent, any version satisfies. |
| `arch` | string | OPTIONAL. An architecture qualifier (§4.1.3). Default: `any`. |

A dependency object MUST contain at least the `name` field.
Other fields are optional.

> [!INFORMATIVE]
> A bare-name dependency (`{ "name": "libssl" }`) is satisfied
> by any installed package matching the name. A dependency
> with a constraint (`{ "name": "libssl", "constraint": ">=
> 3.0" }`) requires both the name match and the version
> constraint to be satisfied.

## Conflict object

A single entry in `conflicts` has the form:

```json
{
  "name": "<package name>",
  "constraint": "<version constraint>",
  "arch": "<arch qualifier>"
}
```

Field semantics are identical to the dependency object,
except that the entry expresses incompatibility rather than
requirement: a package with a conflicts entry MUST NOT be
installed simultaneously with any package matching that
entry.

A conflict whose `constraint` is absent expresses
incompatibility with any version of the named package.

## Architecture qualifier

The `arch` field on a dependency or conflict entry restricts
the qualified package's architecture.

In this version of the specification, the only valid value
is `any`, which is the default. `any` means: the qualified
package's architecture MUST equal the depending package's
architecture or be `noarch`.

> [!INFORMATIVE]
> Future versions of this specification may permit explicit
> architecture identifiers in the `arch` field to support
> multi-architecture systems (§2.3.5). The reservation in
> v0.22 ensures forward-compatible parsing.

A dependency or conflict entry whose `arch` value is anything
other than `any` MUST be rejected by a v0.22-conformant
implementation.

## Provides

A single entry in `provides` has the form:

```json
{
  "name": "<virtual name>",
  "version": "<version string>"
}
```

| Field | Type | Description |
|---|---|---|
| `name` | string | The virtual name being provided. MUST conform to §2.1. |
| `version` | string | OPTIONAL. A version string per §2.2 expressing the version of the virtual capability provided. If absent, the entry provides any version of the virtual name. |

A virtual name in the namespace of real package names MAY be
provided. When a real package name and a virtual name
collide, both are valid satisfiers of dependencies on that
name.

A `provides.version` SHOULD reflect the providing package's
actual functional compatibility level. A `provides.version`
greater than the providing package's own `version` SHOULD
generate an operator warning at install time, since
inflated provides-versions can be used to defeat
constraint-based dependency resolution.

> [!INFORMATIVE]
> Example: a package `postfix` may provide
> `{ "name": "smtp-server", "version": "3.0" }`. A
> dependency `{ "name": "smtp-server", "constraint": ">=
> 2.0" }` is satisfied by `postfix` (or by any other
> package that provides `smtp-server` at a satisfying
> version).

The provides relation does not transitively flow: providing
`smtp-server` does not provide whatever `smtp-server` itself
provides.

## Replaces

A single entry in `replaces` has the form:

```json
{
  "name": "<package name>",
  "constraint": "<version constraint>"
}
```

| Field | Type | Description |
|---|---|---|
| `name` | string | The package name this package supersedes. MUST conform to §2.1. |
| `constraint` | string | OPTIONAL. A version constraint per §2.2.8. If absent, this package replaces any version of the named package. |

A replaces entry expresses that this package supersedes the
named package. During upgrade, the replaced package is
removed and this package is installed in its place. Files
owned by the replaced package that no longer exist in this
package are removed; files that exist in both are updated.

> [!INFORMATIVE]
> Replaces is the mechanism for handling package renames.
> If `nginx-core` is renamed to `nginx`, the new `nginx`
> package declares `{ "name": "nginx-core" }` in its
> `replaces` array. Existing systems with `nginx-core`
> installed will, on upgrade, transition to `nginx`
> seamlessly.

A replaces entry does not imply a conflict. A package MAY
replace and conflict with the same target, but typically a
replaces entry is sufficient on its own to express the
succession.

## Constraint syntax

Version constraints in `constraint` fields use the operators
defined in §2.2.8:

```
=  >  >=  <  <=  !=
```

Multiple constraints on the same dependency are combined
with logical AND, separated by commas:

```
">= 3.0, < 4.0"
```

Whitespace around operators and commas is OPTIONAL and is
ignored.

A bare version string with no operator is equivalent to `=`:

```
"1.26.2-3"   ≡   "= 1.26.2-3"
```

A constraint string MUST parse as one or more operator-and-
version expressions separated by commas. A constraint that
does not parse is INVALID.

## Field constraints

Each of the five fields (`dependencies`, `optional_dependencies`,
`conflicts`, `provides`, `replaces`) is an array of objects
matching the appropriate schema above.

Fields MAY be empty arrays. Fields MAY be omitted from the
manifest; an omitted field is equivalent to an empty array.

Within a single field, entries MUST be sorted lexicographically
by `name`. Two entries in the same field MUST NOT have
identical `name` values; if a package has multiple constraints
on the same target, they MUST be combined into a single
entry's `constraint` string.
