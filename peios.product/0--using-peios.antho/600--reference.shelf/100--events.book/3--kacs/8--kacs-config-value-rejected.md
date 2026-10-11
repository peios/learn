---
title: "kacs.config.value.rejected"
description: "The record that KACS read one of its registry-held tables, rejected it, and carried on with what it had."
---

- **Event type:** `kacs.config.value.rejected`
- **Defined in:** `kacs.evman`
- **Tier:** essential
- **Gating:** none — every rejected table is recorded
- **Cardinality:** once per rejected read of the key

The record that KACS read one of its registry-held tables, rejected it, and
carried on with what it had. Today that is the port reservation table under
`Machine\System\Network\TcpIp\PortReservations`, read whenever the key
changes.

The table is validated whole and is **reject-or-keep, never merge**: one bad
value refuses all of them, and whatever was in force before — the last good
table from the registry, or the compiled-in fallback — stays in force. That
makes this the only place the divergence is visible: the registry shows what
an administrator wrote, and this record shows that KACS is not using it. The
same reject-or-keep rule as `kmes.config.value.rejected` and
`lcs.config.value.rejected`, for a table rather than a single value.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`config.key.path`](~peios/events/field-index/fields-config#config.key.path) | `str` | required | The registry key the reported value lives under, in canonical form. |
| [`config.name`](~peios/events/field-index/fields-config#config.name) | `str` | optional | The value at fault, by its registry name: a selector such as `tcp:80`, or `@` for the default reservation. Absent when no single value is at fault. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | `empty`: the key has no values. `too-large`: the table exceeds the kernel's bound. `malformed`: the serialised table broke, which is the kernel's fault rather than a value's. `bad-selector`: a value's name does not parse as a selector. `bad-descriptor`: a value's data is not a self-relative security descriptor. `duplicate-default`: the default reservation is given twice. `missing-default`: there is no default reservation. `overlap`: two selectors of the same width cover a port, so the most specific is ambiguous.<br><br>Values here (open set): `empty` · `too-large` · `malformed` · `bad-selector` · `bad-descriptor` · `duplicate-default` · `missing-default` · `overlap`. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | required | The error the operation failed with, as a negative errno. |
| [`policy.previous-retained`](~peios/events/field-index/fields-policy#policy.previous-retained) | `bool` | required | Always true: a rejected table leaves the one in force in place. |
| [`policy.fallback`](~peios/events/field-index/fields-policy#policy.fallback) | `bool` | required | Whether what stays in force is the compiled-in fallback, because no table from the registry was ever accepted this boot. The fallback lets SYSTEM alone bind a port, so a rejected first table leaves every service that binds a port without one. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
