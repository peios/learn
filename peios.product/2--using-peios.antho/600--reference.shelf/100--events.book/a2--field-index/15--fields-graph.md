---
title: "graph.*"
description: "Every field the evman catalogue defines under graph: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `graph`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="graph.context"></a>`graph.context`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The graph execution context an event belongs to: one boot's start of its
service set, or one on-demand start of a service and everything it needs.
Records with the same context belong to one attempt to bring a set of
services up.

Numbered from 0 in the order peinit creates contexts. Not durable: the
numbering starts again when peinit does.

**Carried by:**

No event carries this field yet.

## <a id="graph.counts.added"></a>`graph.counts.added`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How many service definitions a configuration reload added: names that
had no definition before.

Meaningful only when the reload succeeded. peinit writes zero for every
count today when a reload fails, which reads as a reload that changed
nothing.

**Carried by:**

No event carries this field yet.

## <a id="graph.counts.discarded"></a>`graph.counts.discarded`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How many definitions a configuration reload withdrew and dropped at
once, because their services were not running. Meaningful only when the
reload succeeded, as for `graph.counts.added`.

**Carried by:**

No event carries this field yet.

## <a id="graph.counts.marked-removed"></a>`graph.counts.marked-removed`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How many definitions a configuration reload withdrew from services that
were still running. Such a service is left running, cannot be started
again, and is discarded once it stops. Meaningful only when the reload
succeeded, as for `graph.counts.added`.

**Carried by:**

No event carries this field yet.

## <a id="graph.counts.restored"></a>`graph.counts.restored`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How many definitions a configuration reload brought back after an
earlier reload had removed them while their services were still
running. Meaningful only when the reload succeeded, as for
`graph.counts.added`.

**Carried by:**

No event carries this field yet.

## <a id="graph.counts.undecodable"></a>`graph.counts.undecodable`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How many definitions a configuration reload found in the registry but
could not decode. Each such service is failed, or, if it was running,
left running with its definition marked removed. Not counted under
`graph.counts.marked-removed` or `graph.counts.discarded`, because the
key is still there. Meaningful only when the reload succeeded, as for
`graph.counts.added`.

**Carried by:**

No event carries this field yet.

## <a id="graph.counts.updated"></a>`graph.counts.updated`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How many existing service definitions a configuration reload changed.
Meaningful only when the reload succeeded, as for `graph.counts.added`.

**Carried by:**

No event carries this field yet.

## <a id="graph.phase"></a>`graph.phase`

- **Type:** `str.enum`
- **Values:** `boot` · `reload-config` · `phase2-boot`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

When the service graph was validated. The phase changes what a finding
did: at `boot`, the services it names are marked and the boot continues;
at `reload-config`, the whole reload is rejected and nothing is applied;
at `phase2-boot`, the boot plan itself could not be built.

**Carried by:**

No event carries this field yet.

## <a id="graph.role"></a>`graph.role`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The role no service fills. A role is a virtual name a service declares it
provides, such as `authn`, and other services depend on the role rather
than on a service name. The services that need it are in
`graph.services`.

**Carried by:**

No event carries this field yet.

## <a id="graph.services"></a>`graph.services`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The services a graph finding involves. For a dependency cycle, the
services in the cycle, in the order the cycle runs; for an unfilled role, the
services that need the role and cannot start; for a reload during the
boot window, the services whose definitions were deferred.

**Carried by:**

No event carries this field yet.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
