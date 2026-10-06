---
title: "machinery.*"
description: "Every field the evman catalogue defines under machinery: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `machinery`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="machinery.collision.name"></a>`machinery.collision.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The other name in a hash collision: a second tag or stream name whose hash
equals that of the name the record carries. NTFE refuses a generation in
which this happens, so that a hash stays a single identity while the policy
runs.

**Carried by:**

No event carries this field yet.

## <a id="machinery.hash"></a>`machinery.hash`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The FNV-1a-64 hash by which the tag and counter stores know a tag name or a
counter stream name. Tags and streams are hashed by the same function into
separate namespaces, so one hash can name both a tag and a stream: read it
with the record's event type. A hash maps to a name only within the
generation that published it.

**Carried by:**

No event carries this field yet.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
