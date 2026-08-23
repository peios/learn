---
title: Naming rules
type: reference
description: "The precise rules for names in UD: object-name validity, the pinned caseless folding, DN composition and RFC 4514 escaping, native paths, definition-name grammar, wire names, and the reserved descriptor x."
related:
  - universal-directory/concepts/objects-and-identity
  - universal-directory/concepts/modifying-the-schema
  - universal-directory/reference/base-schema
---

## Object names

An object's bare name must be:

- non-empty and at most 255 bytes,
- free of control characters,
- free of `/` (the native path separator),
- without leading or trailing whitespace.

Everything else — spaces, Unicode, `=`, `,` — is legal; DN composition escapes what needs escaping. These rules are deliberately strict: loosening a validity rule later is safe, tightening one is a data migration.

## Caseless comparison (pinned)

Sibling uniqueness, attribute-name lookup, path resolution, and `caseless`-matched value sets all compare under **Unicode canonical caseless matching** (Unicode §3.13): two strings are equal iff

```
NFD(casefold(NFD(a))) == NFD(casefold(NFD(b)))
```

So `Jack` = `jack`, `STRASSE` = `Straße` (ß case-folds to `ss`), and composed `é` = decomposed `e +  ́`. Stored spellings are always preserved; the folding governs comparison only. This function is pinned: changing it once data persists would shift uniqueness invariants underneath stored data.

## Distinguished names

DNs compose leaf-first from typed components: `CN=Jack,OU=Sales`. The component type is the object's class's `dnPrefix`; the value is the bare name escaped per **RFC 4514** — a backslash before any of `" + , ; < > \` anywhere, before a leading space or `#`, and before a trailing space. The root object contributes nothing; its DN is the empty string.

## Native paths

The untyped address form: `/` followed by bare names joined with `/`, root-first — `/Sales/Jack`, resolving case-insensitively. The root's path is `/`. Because `/` is banned in names, paths are unambiguous.

## Definition names and wire names

Schema definition names (attributes, facets, classes, extensions) follow a stricter grammar than object names: **a letter followed by letters or digits** — camelCase by convention, and **no hyphens**, because the hyphen is the namespace separator. **Namespace names** additionally allow **dots** between segments (each segment a letter followed by letters or digits): `Acme` and reverse-DNS `com.acme.tools` are both legal, and reverse-DNS is the convention for anything redistributable — it makes accidental collisions between vendors nearly impossible. A namespaced definition's **wire name** is `Namespace-name` (`Acme-badgeColor`, `com.acme.tools-badgeColor`) — the single hyphen is unambiguous because neither side may contain one. Base definitions are unprefixed, and that unprefixed space is [reserved forever](~universal-directory/concepts/modifying-the-schema).

The namespace names `gip` and `ud` (caselessly) are **permanently reserved**: they are GIP's service namespaces (`gip/relay`, `ud/drs`), and service names share the schema's namespace universe.

`dnPrefix` values follow RFC 4512 keystring grammar (a letter, then letters, digits, or hyphens).

## CNF display names

When replication merges two live siblings whose names fold equal, the earliest placement claim keeps the name and the later one *displays* as `<stored name> CNF:<guid>` (laddering ` (2)`, ` (3)`… past pathological collisions). This is a derived view, not a rename: the stored name is untouched, the CNF form resolves in paths, and an ordinary rename dissolves it.

## The reserved descriptor `x`

The name `x` (caselessly) is **permanently reserved** and can never be defined as an attribute, facet, class, extension, or namespace name. UD reserves it as its untyped-lookup descriptor so that no schema element can ever collide with that use.
