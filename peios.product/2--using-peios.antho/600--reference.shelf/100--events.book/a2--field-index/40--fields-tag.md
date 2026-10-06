---
title: "tag.*"
description: "Every field the evman catalogue defines under tag: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `tag`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="tag.amount"></a>`tag.amount`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The amount a tag operation applied: the value a `set` wrote, or the amount
an `add` added. Both default to 1 when the rule names none. Absent for
`clear`.

**Carried by:**

No event carries this field yet.

## <a id="tag.name"></a>`tag.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The name of a flow tag, as the policy author wrote it. **Not emitted
today**: the tag store is passed only the tag's hash, `machinery.hash`, and
the name lives in the published policy. A hash names the same tag only
within one generation.

**Carried by:**

No event carries this field yet.

## <a id="tag.operation"></a>`tag.operation`

- **Type:** `str.enum`
- **Values:** `set` · `clear` · `add`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Which operation a `TAG` action applied to a flow tag. `clear` removes the
tag so that it reads as absent; clearing an absent tag does nothing.

**Carried by:**

No event carries this field yet.

## <a id="tag.value"></a>`tag.value`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The value a flow tag holds. An `add` that would overflow leaves it at the
largest representable value, where it stays.

**Carried by:**

No event carries this field yet.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
