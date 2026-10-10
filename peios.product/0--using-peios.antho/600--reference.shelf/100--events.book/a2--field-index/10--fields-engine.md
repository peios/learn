---
title: "engine.*"
description: "Every field the evman catalogue defines under engine: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `engine`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="engine.abi-version"></a>`engine.abi-version`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The version of the NTFE device interface the running kernel implements.
The interface is experimental and carries no stability promise, so a tool
reading the device checks this before trusting anything else.

**Carried by:**

No event carries this field yet.

## <a id="engine.enforcing"></a>`engine.enforcing`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Whether NTFE enforces anything at all: true when at least one rules layer
has a published forest. False from boot until the first generation
ingests, and whenever no layer has policy, in which case every traversal
is waved through.

**Carried by:**

No event carries this field yet.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
