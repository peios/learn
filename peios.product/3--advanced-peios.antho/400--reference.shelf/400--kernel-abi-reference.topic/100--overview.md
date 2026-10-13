---
title: Kernel ABI reference
type: reference
description: Where the KACS, LCS and NTFE kernel ABIs are documented — syscall numbers, ioctls, structure layouts, and constants, generated from uapi.
related:
  - peios/advanced-peios/wire-formats-reference/overview
  - peios/debugging-the-kernel/overview
  - peios/advanced-peios/constants-and-catalogs/overview
---

The kernel ABI is documented in the **Peios Kernel TRM**, in four appendices generated from `uapi/pkm/`:

| Appendix | Covers |
|---|---|
| §2.A, KMES ABI Reference | Event syscalls, ring and event header layouts, configuration structures, and trace controls |
| §3.A, KACS ABI Reference | Syscall numbers, ioctls, structure layouts, token query classes, and the KACS constants |
| §5.A, LCS ABI Reference | The registry ABI — syscalls, ioctls, structure layouts, and the watch record header offsets |
| §6.A, NTFE ABI Reference | The packet engine's `/dev/peios-ntfe` ABI — ioctls, the verdict event and status layouts, the counter record, and the seat, layer, verdict and flag constants |

Two more appendices sit alongside them: §3.B lists where the KACS evaluator departs from MS-DTYP, and §3.C lists the audit events KACS emits.

## Names

Those appendices use the names `uapi/pkm/` declares. A reader arriving with the name PCDS uses — which is MS-DTYP's — will find the mapping in §3.A's own divergence table. Impersonation levels, create dispositions, group attribute flags and `SECURITY_INFORMATION` flags all differ between the two vocabularies. See Conventions §6.5 for why neither is being renamed.

## Checking generated appendices

The PKM repository's `tools/gen-kmes-abi.py`, `gen-kacs-abi.py`, `gen-lcs-abi.py` and
`gen-ntfe-abi.py` derive these appendices from that checkout's sources.
`gen-stratafs-constants.py` checks the StrataFS constants appendix in the
same way. Run a generator with `--check` to detect stale output without
writing it; omit `--check` to regenerate.

By default, the companion documentation is a sibling `learn/` checkout.
For a named documentation worktree, select it explicitly:

```sh
PKM_LEARN_ROOT=/path/to/docs-worktree python3 tools/gen-kacs-abi.py --check
PKM_LEARN_ROOT=/path/to/docs-worktree git push
```

All five generators and the PKM pre-push appendix checks use this setting.
Kernel inputs always come from the checkout containing the generator,
regardless of its directory name or the command's working directory.
An invalid explicit documentation path fails; a standalone kernel checkout
without a sibling `learn/` or an override skips documentation checks.
Missing or stale appendices in a selected documentation checkout fail
`--check`.

## Related

- Byte-level layouts by structure: [Wire formats reference](~peios/advanced-peios/wire-formats-reference/overview).
- Numeric constants by kind: [Constants and catalogs](~peios/advanced-peios/constants-and-catalogs/overview).
- The tracepoints the kernel exposes: [Kernel tracepoints](~peios/debugging-the-kernel/kernel-tracepoints).
