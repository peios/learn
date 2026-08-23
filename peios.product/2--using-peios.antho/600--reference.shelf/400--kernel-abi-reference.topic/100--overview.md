---
title: Kernel ABI reference
type: reference
description: Where the KACS and LCS kernel ABIs are documented — syscall numbers, ioctls, structure layouts, and constants, generated from uapi.
related:
  - peios/wire-formats-reference/overview
  - peios/debugging-the-kernel/overview
  - peios/constants-and-catalogs/overview
---

The kernel ABI is documented in the **Peios Kernel TRM**, in two appendices generated from `uapi/pkm/`:

| Appendix | Covers |
|---|---|
| §3.A, KACS ABI Reference | Syscall numbers, ioctls, structure layouts, token query classes, and the KACS constants |
| §5.A, LCS ABI Reference | The registry ABI — syscalls, ioctls, structure layouts, and the watch record header offsets |

Two more appendices sit alongside them: §3.B lists where the KACS evaluator departs from MS-DTYP, and §3.C lists the audit events KACS emits.

## Names

Those appendices use the names `uapi/pkm/` declares. A reader arriving with the name PCDS uses — which is MS-DTYP's — will find the mapping in §3.A's own divergence table. Impersonation levels, create dispositions, group attribute flags and `SECURITY_INFORMATION` flags all differ between the two vocabularies. See Conventions §6.5 for why neither is being renamed.

## Related

- Byte-level layouts by structure: [Wire formats reference](~peios/wire-formats-reference/overview).
- Numeric constants by kind: [Constants and catalogs](~peios/constants-and-catalogs/overview).
- The tracepoints the kernel exposes: [Kernel tracepoints](~peios/debugging-the-kernel/kernel-tracepoints).
