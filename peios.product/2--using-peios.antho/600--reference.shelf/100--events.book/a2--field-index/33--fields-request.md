---
title: "request.*"
description: "Every field the evman catalogue defines under request: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `request`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="request.deferred-effect"></a>`request.deferred-effect`

- **Type:** `str.enum`
- **Values:** `restore-commit` · `key-mutation`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The kind of kernel-side work attached to a source request, to be applied
when the source's reply arrives rather than when the caller returns.
`restore-commit` completes a registry restore; `key-mutation` publishes
the effects of a key write, such as watch notifications and generation
updates. Absent when the request carries no deferred work.

Deferred work is what makes a late reply consequential. When the caller
has already given up (`request.waiter-detached`), the effect is still
applied, so a change the caller was told had failed can land afterwards.

**Carried by:**

No event carries this field yet.

## <a id="request.id"></a>`request.id`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The identifier of the source request this record concerns, for joining a
record to the exchange that produced it. A pure correlation key.

**Carried by:**

- [`lcs.source.response.rejected`](~peios/events/lcs/lcs-source-response-rejected)

## <a id="request.op-code"></a>`request.op-code`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The source-protocol operation code of the request this record concerns.
Identifies which kind of exchange returned unusable data.

**Carried by:**

- [`lcs.source.response.rejected`](~peios/events/lcs/lcs-source-response-rejected)

## <a id="request.op-code-expected"></a>`request.op-code-expected`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The source-protocol operation code the kernel expected a response to carry,
recorded where the source answered with a different one. Read it beside
`request.op-code`, which holds the code that actually arrived; the
disagreement between the two is the finding.

A response code is the request code with the high bit `0x8000` set, so an
expected code of `0x8021` answers a request of `0x0021` (`RSI_SET_VALUE`).

**Carried by:**

No event carries this field yet.

## <a id="request.status"></a>`request.status`

- **Type:** `str.enum`
- **Values:** `ok` · `not-found` · `already-exists` · `storage-error` · `not-empty` · `too-large` · `txn-busy` · `invalid` · `cas-failed` · `txn-not-supported`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The RSI status code a registry source returned for a request, named from
the `RSI_*` status constants with the prefix removed. The kernel maps each
status to an errno before the caller sees it, and the errno loses the
source's own account: `storage-error` and a response the kernel could not
use at all both reach the caller as `EIO`, and only this field says which
it was.

A status code outside this list is never carried here. It is rejected as
malformed source data and recorded on `lcs.source.response.rejected` with
the reason `unknown-rsi-status-code`.

**Carried by:**

No event carries this field yet.

## <a id="request.timed-out"></a>`request.timed-out`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

Whether a request's wait for the source's reply ran out before the reply
arrived. The deadline is the configured request timeout. A timed-out
request is not cancelled at the source: its reply may still arrive, and
any deferred effect attached to it may still be applied.

**Carried by:**

No event carries this field yet.

## <a id="request.waited"></a>`request.waited`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

Whether the kernel blocked waiting for the source's reply to a request.
False for a request dispatched without a waiter, whose outcome no caller
will see directly.

**Carried by:**

No event carries this field yet.

## <a id="request.waiter-detached"></a>`request.waiter-detached`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

Whether the caller that issued a request had stopped waiting by the time
the source's reply arrived. True means the operation had already reported
failure to userspace, typically a timeout, so any effect the reply carries
lands after the caller was told it did not. This is the entry condition for
the kernel's late-effect replay.

**Carried by:**

No event carries this field yet.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
