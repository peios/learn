---
title: PSB Lifecycle
order: 4
---

## Fork (clone without CLONE_THREAD)

The child receives a copy of the parent's PSB. PIP fields, mitigations, and any active restrictions are inherited. A Protected process's children start as Protected -- PIP protection propagates across fork.

The child receives a new default process SD. The owner is the forking thread's effective token's user SID. The DACL follows the default template.

## Exec

PIP fields (`pip_type`, `pip_trust`) are reset based on the new binary's cryptographic signature. A Protected parent that execs an unsigned binary loses PIP protection -- protection follows the binary, not the lineage.

Mitigation flags (`lsv`, `wxp`, `tlp`, `cfif`, `cfib`, `pie`, `sml`, `ui_access`) are NOT reset by exec. They persist across exec unchanged. A mitigation set between fork and exec survives regardless of what binary is loaded.

The `no_child_process` flag persists across exec. A process that has been restricted from creating children remains restricted regardless of what binary it loads.

The process SD is NOT reset by exec. The SD was set at fork time and persists. The SD reflects the process's creation context, not the binary it is running.

## Clone with CLONE_THREAD

Threads share the process's PSB. Thread creation is not affected by `no_child_process` -- only new processes (fork/clone without CLONE_THREAD) are blocked.

## Relationship to AccessCheck

The PSB is NOT an input to AccessCheck in the general case. AccessCheck takes a token (identity) and an SD (policy) and evaluates access. Most PSB fields are invisible to the access control pipeline.

The exception is PIP. The AccessCheck pipeline includes a PIP enforcement step that reads `pip_type` and `pip_trust`. These come from the PSB, not from any token. The enforcement layer extracts PIP values from the PSB and passes them as explicit parameters to AccessCheck.

This means:

- **MIC** (integrity level) uses the **effective token** -- impersonation changes how MIC evaluates. This is safe because the integrity ceiling on impersonation prevents escalation.
- **PIP** (process protection) uses the **PSB** -- impersonation MUST NOT change how PIP evaluates. There is no impersonation gate that constrains PIP dimensions, so the PSB is the only safe source.

Process mitigations (`lsv`, `wxp`, `tlp`, `cfi`) and `no_child_process` do not interact with AccessCheck. They are enforced at their respective enforcement points independently of the access control pipeline.
