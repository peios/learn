---
title: "test.*"
description: "Every field the evman catalogue defines under test: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `test`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="test.rendezvous.action"></a>`test.rendezvous.action`

- **Type:** `str.enum`
- **Values:** `none` · `hold` · `fail`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

What a test rendezvous point is set to do to the next task that reaches it.
`hold` blocks every task that arrives until the point is cleared. `fail`
makes the next arriving task's step fail with a chosen error, once, then
reverts to `none`, which leaves tasks unaffected.

**Carried by:**

No event carries this field yet.

## <a id="test.rendezvous.name"></a>`test.rendezvous.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The test rendezvous point a record concerns, one of `copy-up-begin`,
`copy-up-publish`, `rename-provider` and `link-install`. Rendezvous points
exist only in a kernel built with test hooks and booted with
`stratafs.test_hooks=1`, and let a conformance test hold an operation open
mid-flight or make one internal step fail. A production system never
records one.

**Carried by:**

No event carries this field yet.

## <a id="test.rendezvous.waiters"></a>`test.rendezvous.waiters`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The number of tasks blocked at a test rendezvous point, at the moment of
the record. A test polls it to know its target has arrived before acting
on the held state. Non-zero only while the point is set to `hold`.

**Carried by:**

No event carries this field yet.

*Generated from `stratafs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
