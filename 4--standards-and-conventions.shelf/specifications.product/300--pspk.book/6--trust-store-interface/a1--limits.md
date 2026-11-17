---
title: Limits
description: The size and count limits of the Trust Store Interface in one
  table, covering the store image, the store's three sets, the seen
  certificates, and the notification queue.
---

| Limit | Value | Defined in |
|---|---|---|
| Size of the store image | 64 MiB | §6.3 |
| Top-levels in the store | 4096 | §6.5 |
| Revocations in the store | 1,048,576 | §6.5 |
| Distrust entries in the store | 65,536 | §6.5 |
| Seen certificates recorded | 65,536 | §6.5 |
| Notifications queued | 1024 | §6.6 |

An image over its size limit is malformed as a whole (§6.3). An object
that would take a set past its limit is refused with `ENOSPC` when
added (§6.5), and skipped when it is an entry of the image (§6.3). A
certificate that would take the record of seen certificates past its
limit is not recorded, and the kernel queues an Overflow (§6.6).
