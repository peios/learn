---
title: Limits and abuse controls
type: reference
description: Wispist v1 storage, document, request, pagination, subscription, change-retention, idempotency, and rate-limit defaults.
related:
  - wispist/reference/wispist-json
  - wispist/problems/quota-exceeded
  - wispist/problems/rate-limited
  - wispist/problems/request-too-large
---

Wispist applies hard resource limits and bounded rate buckets before expensive work. A release may lower collection limits but cannot raise installation policy.

## Resource defaults

| Resource | Default |
| --- | ---: |
| Collections per release | 32 |
| Documents per collection | 1,000 |
| Document JSON | 32 KiB |
| Live document data per site | 10 MiB |
| Draft document data per site | 5 MiB |
| List page | 100; maximum 250 |
| Collections per SSE stream | 8 |
| SSE streams per site and client | 6 |
| SSE streams per site | 100 |
| Pending events per stream | 128 |
| Request envelope allowance | document limit plus 4 KiB |
| Live idempotency records per namespace | 10,000 |
| Retained changes per namespace | 10,000 |
| Change age | 7 days |
| Idempotency retention | at least 24 hours |

The document-data quota counts compact document JSON, not release files. Change and idempotency tables are separately bounded.

## Initial Wispdeck rate buckets

| Bucket | Sustained | Burst |
| --- | ---: | ---: |
| Reads per site and client | 600/minute | 100 |
| Mutations per site and client | 60/minute | 20 |
| Mutations across one site | 300/minute | 60 |
| Generated-ID creates across one site | 10,000/day | 100 |
| All Wispist requests | 6,000/minute | 1,000 |

Client keys come from Wispdeck's trusted-proxy-aware address resolution. Untrusted forwarding headers are ignored.

Buckets use bounded memory and expire after inactivity. Concurrent streams use counters rather than token rates. A rejected request returns [rate limited](~wispist/problems/rate-limited) with `Retry-After`.

Rate limits are availability controls, not authorization. A public `shared` collection remains publicly writable below the rate allowance.
