---
title: Modifying the schema
type: how-to
description: How UD's schema is extended at runtime — namespaces as OUs, definitions born whole and immutable, the unused-delete rule, and class extensions — with a complete worked example.
related:
  - universal-directory/concepts/the-schema-model
  - universal-directory/reference/naming-rules
  - universal-directory/reference/json-api
---

UD's schema is writable at runtime. The rules are designed so that a directory can be extended for decades without accumulating the classic schema scar tissue: colliding names, orphaned definitions that can never be removed, and third-party leftovers polluting the core forever.

## Namespaces

All new definitions live in a **namespace**: a `schemaNamespace` OU created directly under `/Configuration/Schema`.

The flat set of unprefixed base definitions is **reserved forever**. Even the local organisation extends the schema through its own namespace — `/Configuration/Schema/Homelab/`, `/Configuration/Schema/Acme/`. Namespaces hold definitions only; they cannot nest.

Namespace names may be dotted, and **reverse-DNS (`com.acme.tools`) is the convention for anything redistributable**, which makes vendor collisions structurally unlikely rather than merely hoped against. Short names remain fine for org-internal extensions. `gip` and `ud` are permanently reserved, being GIP's service namespaces.

A namespaced definition's **wire name** is `Namespace-name`. A facet `badging` in the `Acme` namespace is addressed everywhere — API, console, attribute lookups — as `Acme-badging`. The hyphen is *structural*: it is the namespace separator, which is exactly why native definition names may not contain one. See [naming rules](~universal-directory/reference/naming-rules). Collisions between namespaces are therefore structurally impossible, not conventionally unlikely.

## Definitions are born whole, then frozen

A definition is created **complete, in one atomic call** — object and attributes together. The API's create accepts an `attributes` map; the console's create modal generates a field per attribute of the chosen class. The engine fills in `lifecycle: active` and `system: false` itself.

Every schema write then passes a **trial recompile** of the whole schema. An attribute definition missing its `syntax`, an extension whose target is not a class, a dangling facet reference — any incoherence rejects the write atomically, with the compiler's message, as if it never happened.

Once created, a definition is **immutable and immovable**: no attribute edits, no renames, no moves. Add and delete are the only verbs. To fix a definition, delete it and recreate it.

The recreated definition is a **new definition with a new GUID**, so anything that referenced the old one dangles visibly rather than silently rebinding. This is the *no-resurrection guarantee*: a deleted definition's name can be reused, but its identity can never be impersonated.

## The unused-delete rule

A definition can be deleted only when **provably unused**.

| Kind | Blocked while… |
|---|---|
| attribute | any object holds values for it, any value uses it as a meta key, any attribute lists it in `legalMeta`, or any facet references it |
| facet | any class composes it, any extension grafts it, or any object has it attached |
| class | any instance exists — including restorable soft-deleted ones; shredded skeletons do not count — or any extension targets it |
| class extension | any instance of the target class holds values in attributes the extension *exclusively* provides |

Refusals **enumerate their blockers by name**: `attribute still has values on: /Sales/Jack`, `facet is used by class Acme-badgeHolder`. Teardown is a matter of reading the error.

Two shapes of teardown work:

- **Dependency order** — clear values, remove the extension, then the facet, then the attribute, then the namespace.
- **Wholesale** — deleting a namespace takes its entire contents down in one atomic subtree delete, and usage *between the dying definitions themselves does not count*. Only usage from outside the namespace blocks.

Definition deletion is the same [soft delete](~universal-directory/concepts/objects-and-identity) as everywhere else. A deleted definition sits restorably in the morgue — restoring it recompiles the schema and revives its wire name, refused if the name has been retaken — then hardens to a skeleton when the restore window closes. Values stored under a definition die at *its* shred: data whose meaning can never return is not kept.

## Class extensions

A **class extension** grafts facets onto a class its author does not own. It is the mechanism for "our app needs a tracking number on every user" without touching the `user` class.

An extension is a definition of class `classExtension`, living in the *extender's* namespace, declaring a `targetClass` and the `facets` to add. From the moment it exists, every instance of the target class carries those facets in its surface. Delete the extension and the surface shrinks back — refused, per the table above, while instances still hold values only the extension legitimises.

The target class object is never modified. The extension is entirely the extender's property, living in their namespace, removable with their namespace.

## Worked example: badges for users

The full flow, as API calls. The console can do all of this through the create modal.

First the namespace:

```
POST /api/objects/{schema-ou}/children
{ "name": "Acme", "class": "schemaNamespace" }
```

An attribute, born whole:

```
POST /api/objects/{acme}/children
{ "name": "badgeColor", "class": "attributeDefinition", "attributes": {
    "syntax":       [{ "value": "string" }],
    "singleValued": [{ "value": "true" }],
    "matching":     [{ "value": "caseless" }]
} }
```

A facet carrying it, then an extension grafting that facet onto `user`. Reference values are GUIDs; the console lets you type `/paths` instead:

```
POST /api/objects/{acme}/children
{ "name": "badging", "class": "facetDefinition", "attributes": {
    "attributes": [{ "value": "{badgeColor-guid}" }]
} }

POST /api/objects/{acme}/children
{ "name": "userBadging", "class": "classExtension", "attributes": {
    "targetClass": [{ "value": "{user-class-guid}" }],
    "facets":      [{ "value": "{badging-guid}" }]
} }
```

Every user in the directory now reports `Acme-badging` among its facets, and accepts:

```
PUT /api/objects/{some-user}/attributes/Acme-badgeColor
{ "values": [{ "value": "red" }] }
```
