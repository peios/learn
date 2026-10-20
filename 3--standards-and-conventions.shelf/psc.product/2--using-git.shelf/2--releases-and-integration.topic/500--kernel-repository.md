---
title: Kernel Repository
type: reference
description: Preserving Linux ancestry and selecting exact Peios kernel
  revisions.
---

The kernel remains a separate Git repository with upstream Linux ancestry.
Panorama selects an exact retained kernel commit for each OS release.

Keep Peios kernel versions distinct from their upstream Linux base. Preserve
upstream tags such as `v7.0.9`, and use `peios/v<version>` for Peios kernel
release tags. Kernel maintenance fixes must also be selected and qualified in
the appropriate Panorama release; publishing a kernel commit alone does not
update an OS release.
