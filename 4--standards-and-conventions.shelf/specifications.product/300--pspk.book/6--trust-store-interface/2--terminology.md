---
title: Terminology
description: The terms this chapter adds, covering store, store image,
  generation, and seen certificate, with everything else delegated to
  PGSS Signed Objects.
---

**Store.** The trust store as the kernel holds it: a set of top-levels,
a set of revocations, and a set of distrust entries.

**Store image.** A file holding the whole store, which the kernel reads
once at boot (§6.3).

**Generation.** A number the kernel raises by one each time the store
changes. A store keeper uses it to tell whether what it last read is
still what the kernel holds.

**Seen certificate.** A certificate the kernel has verified as part of
a chain since boot, with a record of its use (§6.5).

Terms defined in PGSS §7.2 (object, root, top-level, intermediary,
leaf, bundle, warrant, trust store, enabled, revocation, distrust,
object hash, and key hash) are used with the same meaning and are not
redefined.
