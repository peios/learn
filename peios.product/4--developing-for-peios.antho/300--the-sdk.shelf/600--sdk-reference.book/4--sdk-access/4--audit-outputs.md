---
title: Audit outputs
description: The audit struct a check can fill in — continuous audit masks, staging mismatch, and what each field means.
---

```c
struct peios_access_audit {
    uint32_t continuous_audit;   /* OR of matching alarm masks */
    int      staging_mismatch;   /* 1 if the staged CAAP result differs */
};
```

When you pass a non-`NULL` `audit`, the check reports:

- `continuous_audit` — the OR of the alarm masks of any `SYSTEM_AUDIT` ACEs that matched, i.e. what a continuous-audit consumer would log for this access.
- `staging_mismatch` — `1` if evaluating the *staged* central access policy would have produced a different result than the active one. This is the signal you watch when rolling out a [central access policy](~peios/central-access-policies/overview) change: a non-zero value means the pending policy would decide this access differently.
