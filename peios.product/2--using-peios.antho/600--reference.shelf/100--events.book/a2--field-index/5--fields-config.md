---
title: "config.*"
description: "Every field the evman catalogue defines under config: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `config`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="config.coalesced"></a>`config.coalesced`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether change notifications were coalesced before they were acted on.
Network policy coalesces and the registry and KMES do not, which is why
one registry edit produces different numbers of records from different
subsystems.

**Carried by:**

No event carries this field yet.

## <a id="config.counts.applied"></a>`config.counts.applied`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many settings in a configuration refresh were applied. One of four
counters read together, which between them account for every setting the
refresh saw.

**Carried by:**

- [`kmes.config.applied`](~peios/events/kmes/kmes-config-applied)

## <a id="config.counts.ignored-unknown"></a>`config.counts.ignored-unknown`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many registry values were ignored because their names match no
setting. A misspelt setting name lands here and nowhere else, so a non-zero
count is usually an administrator's typo.

**Carried by:**

- [`kmes.config.applied`](~peios/events/kmes/kmes-config-applied)

## <a id="config.counts.retained-invalid"></a>`config.counts.retained-invalid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many settings kept their previous value because the stored value was
rejected, of the wrong type or out of range.

**Carried by:**

- [`kmes.config.applied`](~peios/events/kmes/kmes-config-applied)

## <a id="config.counts.retained-missing"></a>`config.counts.retained-missing`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many settings kept their previous value because they were absent from
the registry.

**Carried by:**

- [`kmes.config.applied`](~peios/events/kmes/kmes-config-applied)

## <a id="config.expected.max"></a>`config.expected.max`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The largest value accepted for this setting.

**Carried by:**

- [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected)
- [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected)

## <a id="config.expected.min"></a>`config.expected.min`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The smallest value accepted for this setting.

**Carried by:**

- [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected)
- [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected)

## <a id="config.expected.type"></a>`config.expected.type`

- **Type:** `uint.enum`
- **Values:** `0 REG_NONE` · `1 REG_SZ` · `2 REG_EXPAND_SZ` · `3 REG_BINARY` · `4 REG_DWORD` · `5 REG_DWORD_BIG_ENDIAN` · `6 REG_LINK` · `7 REG_MULTI_SZ` · `8 REG_RESOURCE_LIST` · `9 REG_FULL_RESOURCE_DESCRIPTOR` · `10 REG_RESOURCE_REQUIREMENTS_LIST` · `11 REG_QWORD`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The registry type the value is required to have.

**Carried by:**

- [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected)
- [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected)

## <a id="config.key.path"></a>`config.key.path`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The registry key the reported value lives under, in canonical form.

**Carried by:**

- [`eventd.config.changed`](~peios/events/eventd/eventd-config-changed)
- [`kacs.config.value.rejected`](~peios/events/kacs/kacs-config-value-rejected)
- [`kmes.config.applied`](~peios/events/kmes/kmes-config-applied)
- [`kmes.config.refresh.failed`](~peios/events/kmes/kmes-config-refresh-failed)
- [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected)
- [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected)

## <a id="config.limit"></a>`config.limit`

- **Type:** `str.enum`
- **Values:** `request-timeout-ms` · `transaction-timeout-ms` · `notification-queue-size` · `symlink-depth-limit` · `max-value-size` · `max-key-depth` · `max-path-component-length` · `max-total-path-length` · `max-layers-per-value` · `max-bound-transactions-per-source` · `max-read-only-transactions-per-source` · `max-total-layers` · `max-registered-sources` · `max-hives-per-source` · `max-concurrent-rsi-requests` · `max-scope-guids-per-token` · `max-private-layers-per-token` · `max-subtree-watch-depth` · `max-transaction-watch-event-burst`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The kernel's internal identifier of a runtime limit, from the `LCS_LIM_*`
codes with the prefix removed and folded to lower case. A different
vocabulary from `config.name`: that is the name an administrator wrote in
the registry, and can be anything; this is the limit the kernel validated,
and a record can carry one without the other.

**Carried by:**

No event carries this field yet.

## <a id="config.name"></a>`config.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The name of the configuration value being reported on, within
`config.key.path`.

**Carried by:**

- [`eventd.config.changed`](~peios/events/eventd/eventd-config-changed)
- [`kacs.config.value.rejected`](~peios/events/kacs/kacs-config-value-rejected)
- [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected)
- [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected)
- [`netd.hostname.changed`](~peios/events/netd/netd-hostname-changed)
- [`peipkg.repository.reconfigured`](~peios/events/peipkg/peipkg-repository-reconfigured)

## <a id="config.received.kind"></a>`config.received.kind`

- **Type:** `str.enum`
- **Values:** `missing` · `wrong-type` · `out-of-range`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How the stored value failed validation. Three different administrative
mistakes with three different fixes: a value that was absent, one of the
wrong type, and one that was well-typed but outside the permitted range.

KMES and LCS reached this vocabulary independently and disagreed —
`u32_out_of_range` and `u64_out_of_range` against `dword_out_of_range` for
the same condition. The width was never information the reader needed,
since `config.expected.type` already carries it, so the three collapse to
one.

**Carried by:**

- [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected)
- [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected)

## <a id="config.received.text"></a>`config.received.text`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

A value supplied as text and rejected because it could not be parsed, as
the caller wrote it. Carried where there is no well-typed value for
`config.received.value` to hold.

**Carried by:**

No event carries this field yet.

## <a id="config.received.type"></a>`config.received.type`

- **Type:** `uint.enum`
- **Values:** `0 REG_NONE` · `1 REG_SZ` · `2 REG_EXPAND_SZ` · `3 REG_BINARY` · `4 REG_DWORD` · `5 REG_DWORD_BIG_ENDIAN` · `6 REG_LINK` · `7 REG_MULTI_SZ` · `8 REG_RESOURCE_LIST` · `9 REG_FULL_RESOURCE_DESCRIPTOR` · `10 REG_RESOURCE_REQUIREMENTS_LIST` · `11 REG_QWORD`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The registry type the value actually had. Present only when the failure was
the type itself.

**Carried by:**

- [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected)
- [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected)

## <a id="config.received.value"></a>`config.received.value`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The value that was stored and rejected. Present only when the value was
well-typed and out of range — there is nothing to report for a value that
was missing or of the wrong type entirely.

**Carried by:**

- [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected)
- [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected)

## <a id="config.root"></a>`config.root`

- **Type:** `str.enum`
- **Values:** `registry` · `kmes` · `layers` · `port-reservations` · `network`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which kernel-read configuration root the record concerns:
`Machine\System\Registry` for the registry's own limits,
`Machine\System\KMES`, the layer metadata under
`Machine\System\Registry\Layers`, the port reservations under
`Machine\System\Network\TcpIp\PortReservations`, and the network policy
under `Machine\System\Network`. Which subsystem's key, not which setting
within it.

**Carried by:**

No event carries this field yet.

## <a id="config.roots-present"></a>`config.roots-present`

- **Type:** `str.enum[]`
- **Values:** `registry` · `kmes` · `layers` · `port-reservations` · `network`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The configuration roots found present when the registry was bootstrapped,
from the same values as `config.root`. A root missing from the list is
running on compiled-in defaults, and the kernel watches the whole machine
hive for it to appear rather than watching the root itself.

**Carried by:**

No event carries this field yet.

## <a id="config.seed-file"></a>`config.seed-file`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The shipped registry seed file that was applied, from `/usr/share/regim/`.
Seed files are inert until an image names them, so this records which
defaults a machine was actually given.

**Carried by:**

No event carries this field yet.

## <a id="config.self-watch-mode"></a>`config.self-watch-mode`

- **Type:** `str.enum`
- **Values:** `disarmed` · `targeted` · `machine-root-fallback` · `mixed`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How precisely the kernel is watching its own configuration in the
registry. `targeted` means each kernel-read configuration key has its own
watch. `machine-root-fallback` means none of those keys could be watched,
so the kernel watches the whole `Machine` hive and re-reads everything on
any change beneath it. `mixed` means some keys are watched precisely and
the fallback covers the rest. `disarmed` means no watch is armed, so a
configuration change will not be noticed until the next bootstrap.

Anything other than `targeted` is a degraded mode, cheaper to tolerate
than to diagnose: configuration still loads, but from coarse rescans.

**Carried by:**

No event carries this field yet.

## <a id="config.text"></a>`config.text`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

A setting's value in force, where the value is not an integer: a string,
or the textual rendering of a value of another registry type. The registry
type is `config.type`.

**Carried by:**

- [`netd.hostname.changed`](~peios/events/netd/netd-hostname-changed)
- [`peipkg.repository.reconfigured`](~peios/events/peipkg/peipkg-repository-reconfigured)

## <a id="config.text-previous"></a>`config.text-previous`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The text value a change replaced, beside `config.text`.

**Carried by:**

- [`netd.hostname.changed`](~peios/events/netd/netd-hostname-changed)
- [`peipkg.repository.reconfigured`](~peios/events/peipkg/peipkg-repository-reconfigured)

## <a id="config.type"></a>`config.type`

- **Type:** `uint.enum`
- **Values:** `0 REG_NONE` · `1 REG_SZ` · `2 REG_EXPAND_SZ` · `3 REG_BINARY` · `4 REG_DWORD` · `5 REG_DWORD_BIG_ENDIAN` · `6 REG_LINK` · `7 REG_MULTI_SZ` · `8 REG_RESOURCE_LIST` · `9 REG_FULL_RESOURCE_DESCRIPTOR` · `10 REG_RESOURCE_REQUIREMENTS_LIST` · `11 REG_QWORD`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The registry type of the value now in force, as the number of its `REG_*`
constant. Absent when no value is in force. The same registry types, in the
same numbering, as `config.expected.type`.

**Carried by:**

- [`eventd.config.changed`](~peios/events/eventd/eventd-config-changed)

## <a id="config.type-previous"></a>`config.type-previous`

- **Type:** `uint.enum`
- **Values:** `0 REG_NONE` · `1 REG_SZ` · `2 REG_EXPAND_SZ` · `3 REG_BINARY` · `4 REG_DWORD` · `5 REG_DWORD_BIG_ENDIAN` · `6 REG_LINK` · `7 REG_MULTI_SZ` · `8 REG_RESOURCE_LIST` · `9 REG_FULL_RESOURCE_DESCRIPTOR` · `10 REG_RESOURCE_REQUIREMENTS_LIST` · `11 REG_QWORD`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The registry type of the value a change replaced. Absent when there was no
value before.

**Carried by:**

- [`eventd.config.changed`](~peios/events/eventd/eventd-config-changed)

## <a id="config.value"></a>`config.value`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The value in force after the event. On a rejection that is the last
known-good value, not a corrected version of what was stored:
configuration validation is reject-or-keep and never clamps.

**The registry and this field can legitimately disagree.** The registry
shows what was written; this shows what the subsystem is actually using.

**Carried by:**

- [`eventd.config.changed`](~peios/events/eventd/eventd-config-changed)
- [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected)
- [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected)
- [`peipkg.repository.reconfigured`](~peios/events/peipkg/peipkg-repository-reconfigured)

## <a id="config.value-previous"></a>`config.value-previous`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The value that was in force before the change. With `config.value`, the
before and after of a setting that took effect.

**Carried by:**

- [`eventd.config.changed`](~peios/events/eventd/eventd-config-changed)
- [`peipkg.repository.reconfigured`](~peios/events/peipkg/peipkg-repository-reconfigured)

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
