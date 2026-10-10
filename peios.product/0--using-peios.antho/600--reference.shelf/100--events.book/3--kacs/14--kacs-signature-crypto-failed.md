---
title: "kacs.signature.crypto.failed"
description: "The record that the machinery for verifying signed executables cannot run."
---

- **Event type:** `kacs.signature.crypto.failed`
- **Defined in:** `kacs.evman`
- **Tier:** essential
- **Gating:** none — recorded whenever the signature machinery cannot run
- **Cardinality:** one record per occurrence

The record that the machinery for verifying signed executables cannot run.
From then on **every signed executable is refused**: a signature that cannot
be verified fails the exec rather than passing as unsigned.

Recorded at boot when the probe for the ML-DSA-65 transform fails. KACS
cannot refuse to start over it — a security module that fails to
initialise boots with no protection at all, which is worse — so it reports
instead, and the refusal happens at each exec. Without this record, the
condition would show only as every process running without an integrity
label.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`signature.crypto-stage`](~peios/events/field-index/fields-signature#signature.crypto-stage) | `str.enum` | required | Always `boot-probe` today. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | required | The error the operation failed with, as a negative errno. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
