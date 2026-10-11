---
title: "evaluation.*"
description: "Every field the evman catalogue defines under evaluation: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `evaluation`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="evaluation.flags"></a>`evaluation.flags`

- **Type:** `uint.flags`
- **Values:** `0x1 backstop` · `0x2 fail-closed` · `0x4 reject-degraded` · `0x8 rejudged` · `0x10 identity-unresolved`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

How an evaluation reached its result. `backstop` means no rule yielded and
the compiled-in DROP answered. `fail-closed` means evaluation could not
finish, usually for want of atomic memory, and the packet was dropped
regardless of policy. `reject-degraded` means a REJECT went out as a DROP
because no answer could be built or sent. `rejudged` means a flow's cached
verdict was stale, by generation or by time, and was judged again.
`identity-unresolved` means an endpoint could not be attributed.

**Carried by:**

No event carries this field yet.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
