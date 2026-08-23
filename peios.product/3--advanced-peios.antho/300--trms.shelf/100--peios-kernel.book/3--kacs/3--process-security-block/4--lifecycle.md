---
title: PSB Lifecycle
description: What the PSB does across fork, exec and CLONE_THREAD, and how it feeds AccessCheck.
---

## Fork

The child receives a copy of the parent's PSB with a single exception:
`process_guid` is not copied, and the child is given a new
kernel-generated one. Everything else — the PIP fields, the
mitigations, and any active restrictions — is inherited, so a
Protected process's children start Protected and PIP propagates across
fork.

The child also receives a new default process descriptor. Its owner is
the forking thread's **primary** token's user SID, not the
impersonation token's, even when the thread is impersonating at the
time. The DACL follows the default template.

## Exec

The PIP fields are reset at exec from the new binary's cryptographic
signature. A Protected parent that execs an unsigned binary loses PIP
protection: protection follows the binary, not the lineage.

The mitigation flags — `lsv`, `wxp`, `tlp`, `cfif`, `cfib`, `pie`,
`sml`, `ui_access` — are not reset. They persist across exec
unchanged, so a mitigation set between fork and exec survives whatever
binary is subsequently loaded. `no_child_process` persists in the same
way: a process restricted from creating children stays restricted no
matter what it execs.

`process_guid` is not reset either, because it identifies the process
— the scheduling entity — rather than the binary.

The process descriptor is not reset. Exec preserves it unchanged. It
was initialised at fork from the forking thread's primary token and
reflects the process creation context, or a later explicit management
context, rather than the binary being executed. Primary token
installation and the other explicit process-descriptor mutation paths
replace or modify it only under their own rules (§3.2.3).

## Clone with CLONE_THREAD

Threads share the process's PSB. Thread creation is unaffected by
`no_child_process`, which blocks new processes only.

## Relationship to AccessCheck

The PSB is not an input to AccessCheck in the general case. AccessCheck
takes a token and a descriptor and evaluates access; most PSB fields
are invisible to it.

PIP is the exception. The pipeline includes a PIP enforcement step
reading `pip_type` and `pip_trust`, which come from the PSB rather
than from any token: the enforcement layer extracts them and passes
them to AccessCheck as explicit parameters.

The asymmetry between MIC and PIP follows from that. **MIC** uses the
effective token, so impersonation changes how it evaluates — which is
safe because the integrity ceiling on impersonation (§3.5.2) prevents
escalation. **PIP** uses the PSB, so impersonation cannot change how
it evaluates — necessary because there is no impersonation gate
constraining the PIP dimensions, making the PSB the only safe source.

The process mitigations and `no_child_process` do not interact with
AccessCheck at all. Each is enforced at its own enforcement point,
independently of the access control pipeline.
