---
title: The schema model
type: concept
description: UD's compositional schema — globally defined attributes, facets as the unit of composition, nominal classes with no inheritance, per-instance attached facets, class extensions, and typed per-value metadata.
related:
  - universal-directory/concepts/modifying-the-schema
  - universal-directory/reference/base-schema
  - universal-directory/concepts/objects-and-identity
---

UD's schema is **compositional**. There is no class inheritance anywhere in the model, and never will be. The schema is built from three layers, each referencing the one below by GUID, with flat set-union as the only combining operation.

## The three layers

**Attributes are defined globally.** One definition per attribute — `surname`, `member`, `expiry` — carrying:

- its **syntax**: `string`, `integer`, `boolean`, `timestamp`, `reference`, `endpoint`, or `publicKey`;
- whether it is **single- or multi-valued**;
- its **matching rule**, `caseless` or `exact`, governing value comparison and set uniqueness;
- the **meta-attributes its values may carry** (`legalMeta`, below);
- an **aliases** slot recording alternative wire names.

Facets *reference* attributes; they never define them. So two facets that both want `description` agree by construction, because there is only one `description`.

**A facet is a named set of attribute references** — the smallest unit of composition. `securityPrincipal` carries `sid`; `person` carries `givenName`, `surname`, `email`; `membership` carries `member`. Each reference in a facet can be flagged **required**, shown in the console as `*`. Facets cannot include other facets: composition is flat, so it is order-free and collision-free.

**A class is a named set of facet references plus nominal properties.** `user` is `described` + `person` + `securityPrincipal`, plus a `dnPrefix` of `CN` supplying its DN component type.

Classes carry **zero attributes directly** — a class needing unique attributes gets its own facet. A class is *nominal*: an object **is** a `user`, queryably and permanently, since [class is immutable at birth](~universal-directory/concepts/objects-and-identity), but its attribute surface comes entirely from facets.

## An object's surface

Which attributes an object may hold — its **surface** — is the union of three facet sets:

1. its **class's facets**;
2. facets grafted onto its class by **class extensions**, covered in [modifying the schema](~universal-directory/concepts/modifying-the-schema);
3. its own **attached facets** — facets added to this one instance.

Setting an attribute outside the surface is refused. The console renders the entire surface, set and unset attributes alike, grouped by the facet that provides them, so the surface is always visible rather than discovered by trial and error.

**Attached facets** are ordinary data: the engine-level `attachedFacets` attribute holds facet references on the object itself. Attaching a facet immediately widens the surface. Detaching is refused while any attribute *only that facet* provides still holds values — clear the values first, explicitly. Nothing is ever silently destroyed.

## Values and per-value metadata

Attributes are **natively multi-valued**: an attribute holds an ordered set of values, unique under the attribute's matching rule.

Each value can carry **metadata**: a generic map of meta-attribute name to values, with nothing hardcoded. Which meta keys are legal on which attribute is itself schema data — an attribute's `legalMeta` lists other *attribute definitions*, so meta values are typed and validated by the same machinery as everything else.

Two invariants hold:

**Meta never forks identity.** The value itself is the set key. `member` cannot contain the same GUID twice with different metadata; changing a value's meta is an update to that value, not a new value.

**Meta is validated, not yet interpreted.** The canonical example — a group membership with an expiry — is expressible today and fully validated: `member` permits the `expiry` meta key, a timestamp. Engine *semantics* for expiry, filtering expired values at read, are not yet active.

## Self-hosting

The schema is not a config file. It is **objects in the directory**, flat under `/Configuration/Schema`, one per attribute, facet, and class, browsable and inspectable through the same console and API as everything else. `CN=surname,OU=Schema,OU=Configuration` is a real DN.

The recursion grounds out cleanly: `attributeDefinition`, `facetDefinition`, and `classDefinition` are themselves classes, composed of facets like `attributeSchema` — and `classDefinition` is an instance of itself. The engine works from a cache compiled off these objects, but the objects are the truth.

The complete contents of the base schema — 26 attributes, 11 facets, 11 classes — are tabulated in the [base schema reference](~universal-directory/reference/base-schema).
