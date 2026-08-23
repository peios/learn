---
title: process.h — Process security
description: Complete reference for <peios/process.h> — setting process mitigation controls on the process security block (PSB).
related:
  - peios/sdk-tokens/token-h-tokens-and-sessions
  - peios/process-mitigations/overview
---

`<peios/process.h>` is the process-security surface of KACS. Today it is a small module with a single job: turning on **process mitigations** — the hardening controls that live on a process's security block (PSB). More process-security surface will land here as it appears; for now, this is the mitigation control.

The mitigation bits are the `KACS_MIT_*` flags from `<pkm/psb.h>` (`KACS_MIT_WXP` through `KACS_MIT_SML`, with `KACS_MIT_ALL` as the mask of all valid bits). `KACS_MIT_CFI` is a legacy alias that expands to `KACS_MIT_CFIF | KACS_MIT_CFIB`. The full catalogue and semantics are in the Peios Kernel TRM §3.3, the Process Security Block.

## Setting mitigations

```c
int peios_process_set_mitigations(int pidfd, uint32_t mitigations);
```

Turns on the mitigation bits named in `mitigations` (a mask of `KACS_MIT_*`). Returns `0` on success, or `-1` with `errno`.

Three properties define how this call behaves, and each matters:

- **It is one-way.** Mitigation bits can only be *set*, never cleared. Once a protection is on, it stays on for the life of the process. This is deliberate — a mitigation you could turn off is a mitigation an attacker could turn off — so treat each call as a permanent, additive commitment.
- **It targets a process by pidfd.** `pidfd == -1` targets the **calling** process, which is the common case: a program hardens itself early in startup. Targeting *another* process requires `PROCESS_SET_INFORMATION` on it **plus** PIP dominance over it — you cannot harden (or interfere with) a process you don't already dominate.
- **It is activation-backed and fails closed.** If a requested protection cannot actually be activated, the call **fails without mutating anything** — you never end up believing a mitigation is on when it isn't. Either every requested bit is activated and the call succeeds, or nothing changes and it returns `-1`.

```c
/* Harden the current process: enforce W^X and shadow-stack, refuse to
   proceed if either can't be activated. */
if (peios_process_set_mitigations(-1, KACS_MIT_WXP | KACS_MIT_SML) != 0) {
    perror("set_mitigations");
    /* nothing was changed; decide whether to continue unhardened or abort */
}
```

Because the call is all-or-nothing, request the bits you require together and check the result once: a success means the whole set is active, a failure means none of *this call's* bits were applied (bits set by earlier successful calls remain on).

## See also

- **[`<peios/token.h>`](~peios/sdk-tokens/token-h-tokens-and-sessions)** — PIP dominance is determined by the subject's token; process targeting other than self depends on it.
- **[Process mitigations](~peios/process-mitigations/overview)** — the operator-side account of each mitigation and what it defends against.
