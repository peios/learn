---
title: What is Universal Directory
type: concept
description: An orientation to Universal Directory — a self-hosted directory service in the X.500 and Active Directory lineage — covering what exists today, what does not, and the design decisions visible in its current behaviour.
related:
  - universal-directory/getting-started/running-udd
  - universal-directory/concepts/objects-and-identity
  - universal-directory/concepts/the-schema-model
  - universal-directory/concepts/replication
---

**Universal Directory (UD)** is Peios' directory service: a hierarchical tree of named objects — organisational units, users, groups, and whatever else the schema is extended to describe — in the lineage of X.500 and Active Directory, built self-hosted from the ground up.

UD is in **early development**. What exists today is a RAM-resident directory engine and its server, [`udd`](~universal-directory/getting-started/running-udd).

## What works today

- A **tree of objects** whose [identity is a GUID](~universal-directory/concepts/objects-and-identity). Distinguished names (`CN=Jack,OU=Sales`) and native paths (`/Sales/Jack`) are always *derived*, never stored.
- A **[self-hosted, compositional schema](~universal-directory/concepts/the-schema-model)**. Attributes, facets, and classes are themselves objects in the tree, browsable like everything else and [extensible at runtime](~universal-directory/concepts/modifying-the-schema) through namespaced definitions.
- A **[multi-master convergent replication engine](~universal-directory/concepts/replication)** with a three-stage deletion lifecycle, per-atom merge, and deterministic conflict repair — proven across in-process node fleets under simulated chaos.
- **[Durable persistence](~universal-directory/concepts/persistence)**. A restart recovers the directory from a snapshot-and-log footprint on disk, with acked-implies-durable semantics.
- A **[JSON API](~universal-directory/reference/json-api)** and an **[embedded debug console](~universal-directory/the-console/the-debug-console)** that expose everything the engine knows — per-value metadata, replication stamps, storage marks — in the browser.

## What does not work yet

Be equally clear about the gaps.

**There is no authentication or authorisation on the JSON API.** Anyone who can reach the port has full control of the directory. The listener binds to loopback.

**The GIP fabric is partially built.** GIP is UD's intra-domain network layer. Daemons discover the other machines in the directory, hold supervised QUIC link connections to them, and run authenticated end-to-end encrypted **service channels** over those links. The first real service is `ud/msgs` — machine-to-machine talk with honest delivery outcomes.

**Directory replication does not ride the fabric yet.** The replication engine still syncs only between in-process nodes. Wiring it to the network is the next arrival.

Treat `udd` as a development tool at this stage, not a deployable service.

## Design decisions you can see in today's behaviour

Even this early, a few load-bearing decisions shape everything UD does.

**Identity is not location.** Every object gets an immutable GUID at birth. Its DN and path are addresses computed on demand. Renaming or moving a container changes one object's record — every descendant's DN changes *logically*, for free, and references never notice, because references store GUIDs.

**The data model is X.500-shaped from day one.** DNs use real LDAP naming attributes (`CN=`, `OU=`), attribute and class names follow LDAP descriptor grammar, and DN values are escaped per RFC 4514. There is no bespoke model waiting for a compatibility layer to be bolted on.

**Names are caseless from birth.** `Jack` and `jack` cannot coexist as siblings. Case-insensitive but case-preserving uniqueness is baked into the tree's conflict detection rather than layered on later. See [naming rules](~universal-directory/reference/naming-rules) for the exact folding.

**Composition, not inheritance.** The schema has no class hierarchy at all. Classes are flat compositions of facets, and objects can gain facets individually or through class extensions. See [the schema model](~universal-directory/concepts/the-schema-model).

**Nothing is hidden.** The schema is ordinary objects under `/Configuration/Schema`. Engine-level bookkeeping like facet attachment is stored as an ordinary attribute. The console shows unset attributes, system flags, dangling references, and per-value metadata. Full observability is a feature, not a debug mode.

## Where to go next

To create a domain and start the daemon, read [Running udd](~universal-directory/getting-started/running-udd).

For the object model — GUID identity, derived addresses, and the deletion lifecycle — read [Objects and identity](~universal-directory/concepts/objects-and-identity).

For the schema, which is where UD differs most from what you may expect, read [The schema model](~universal-directory/concepts/the-schema-model).
