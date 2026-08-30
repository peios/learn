---
title: Patterns and Descriptors
description: Access is defined on named patterns each carrying a descriptor — matching, resolution, storage, and the first-boot defaults.
---

Access is defined on **named patterns**, each standing for a category of
observability data and each carrying a descriptor. The three data types
have independent pattern namespaces:

| Namespace | Patterns match |
|---|---|
| Events | event type |
| Logs | log origin |
| Metrics | metric name |

## Matching

A pattern matches by **dot-delimited prefix**. The pattern `kacs` matches
the exact string `kacs` and any string beginning `kacs.` — and matches
neither `kacs_extended` nor `kacsfoo`, because the dot is the hierarchy
separator and not a mere character.

`*` is the wildcard default and matches everything.

Ingestion constrains origins and metric names to the identifier grammar
(PSPU §3.7, §3.10), which is what keeps a producer from choosing a name
containing the wildcard or a registry path separator — a name that would
otherwise match a rule its producer was never meant to satisfy, or store
its descriptor somewhere other than where the administrator who wrote it
believes.

## Resolution

For a concrete identifier, eventd resolves the applicable descriptor by
walking up the hierarchy:

1. Look for an exact match on the full identifier, `kacs.access_denied`.
2. Remove the last dot-separated component and look again, `kacs`.
3. Repeat.
4. Fall back to the wildcard, `*`.

The first match wins; a more specific pattern overrides a less specific
one.

## Storage

Descriptors are registry values under the eventd security subtree:

```text
Machine\System\eventd\Security\Events\*
Machine\System\eventd\Security\Events\kacs
Machine\System\eventd\Security\Events\kacs.access_denied
Machine\System\eventd\Security\Logs\*
Machine\System\eventd\Security\Logs\loregd
Machine\System\eventd\Security\Metrics\*
Machine\System\eventd\Security\Metrics\cpu
Machine\System\eventd\Security\Admin
```

Each type's wildcard default is **load-bearing**. If a default is
missing, eventd denies access to all data of that type: resolution that
reaches the end of the hierarchy without a match is a denial, not a
grant (PSPU §3.28).

Storing them in the registry rather than in eventd's own databases means
the registry's access control protects them, and an administrator edits
them with the ordinary registry tools rather than through eventd.

## Defaults on first boot

eventd creates the three wildcard keys and administrative descriptor if
they do not exist:

| Key | Default |
|---|---|
| `…\Security\Events\*` | SYSTEM and Administrators: `EVENTD_READ` on all fields. |
| `…\Security\Logs\*` | SYSTEM, Administrators and Authenticated Users: `EVENTD_READ` on all fields. |
| `…\Security\Metrics\*` | SYSTEM, Administrators and Authenticated Users: `EVENTD_READ` on all fields. |
| `…\Security\Admin` | SYSTEM and Administrators: `EVENTD_ADMINISTER`. |

The asymmetry reflects sensitivity. Events include security audit data
and are restricted to administrators; logs and metrics are operational
data and are readable by any authenticated user. An administrator can
tighten either.

## Conditional ACEs

Descriptors on eventd security objects may carry conditional ACEs, and
KACS evaluates them as it would anywhere.

eventd passes **no eventd-specific local claims** to AccessCheck:
`local_claims_ptr` is null and `local_claims_len` is zero. Conditions
referencing token claims that KACS itself supplies still evaluate;
conditions referencing eventd-local claims observe them as absent.

A stable set of eventd-local claims — the event's type, the log's
origin, the time of day — is a plausible later addition, and defining
one is a commitment to keep those claim names meaningful thereafter.

## The administrative descriptor

`INDEX` (PSPU §3.23) is checked against
`Machine\System\eventd\Security\Admin`, with `EVENTD_ADMINISTER` as the
desired access. Its default grants SYSTEM and Administrators.

eventd refuses `INDEX` outright if no administrative descriptor exists,
by the same fail-closed rule as the read path. Keeping it in the
registry means the registry's own descriptor protects the policy and a
recreated `eventd-meta.db` cannot reset it (§3.5).
