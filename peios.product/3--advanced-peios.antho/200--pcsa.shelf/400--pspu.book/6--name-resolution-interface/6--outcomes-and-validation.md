---
title: Outcomes and Validation
description: The three outcomes and why no door may merge two of them; the validation state every answer carries from the first version.
---

## Outcomes

| Outcome | Meaning | Cached |
|---|---|---|
| `found` | An answer. Includes a name that exists with no records of the asked type — an empty `records` with `found` is NODATA, and is not absence. | Yes, by TTL |
| `notfound` | The name does not exist, authoritatively (NXDOMAIN, or a single label with no domain to apply, or `.local`). | Yes, briefly (§6.7) |
| `unavailable` | Nothing that could have answered did: every server timed out, refused, or failed; or no server exists to ask. | Never |

The third row is the one that carries the weight. A resolver MUST NOT
report `unavailable` as `notfound`, at any door, and MUST NOT cache it:
a source that could have answered and did not is not the same as a name
that does not exist, and recording it as one would let an outage be
remembered as a fact. Each door renders the distinction in its own
terms (§6.8, §6.10).

A resolver MUST answer `notfound` locally, without a query, for a
single-label name with no applicable search domain and for any name
under `.local` (§6.7).

## Validation

Every `answer` and `addresses` reply carries `validation`:

| Value | Meaning |
|---|---|
| `unvalidated` | The resolver did not attempt DNSSEC validation. |
| `secure` | Validated, with a chain of trust to a configured anchor. |
| `insecure` | Validated as provably unsigned. |
| `bogus` | Validation failed. |

This version of the interface defines no validating resolver, and a
resolver that does not validate MUST report `unvalidated` for every
answer from the network. The field exists now so that a client is
written against it from the start: when validation arrives, the change
is a value, not a field, and a client that wanted only `secure` answers
needs nothing new.

A resolver MUST NOT set the `AD` bit on a stub-door reply (§6.8) unless
its own validation produced `secure`. An upstream's `AD` is an assertion
by a plaintext peer and MUST NOT be forwarded as one.
