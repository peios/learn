---
title: Boot Authority
type: concept
description: Follow authority from kernel bootstrap through the temporary root and the service graph.
---

The kernel must establish an initial identity before an identity service can
run. It constructs SYSTEM and Anonymous bootstrap tokens directly. SYSTEM
provides the initial authority; Anonymous represents a minimal identity for
anonymous impersonation. They are not accounts loaded from a user database.
Their exact fields and lifetime belong to the
[kernel bootstrap reference](~kernel/internals/kacs/tokens/token-lifecycle).

Prelude runs as PID 1 in the initramfs. It prepares kernel filesystems and
runs image-supplied hooks that make the real root available. When it hands
off, the same process number executes the real-root init, normally Peinit.
The programs perform different jobs; a successful handoff does not establish
that every later service or security policy is ready.

Peinit prepares the system's foundational state, starts the registry, then
loads and supervises the service graph. SYSTEM platform tokens and
authd-issued
service identities use separate launch paths. The child receives its intended
token before its service executable runs. User sign-in is an authd
conversation
followed by the requesting session launcher's work, not a universal Peinit
sign-in procedure.

## Distinct trust decisions

An initramfs archive is a build artifact, not intrinsically authenticated or
immutable runtime memory. Its contents become privileged boot code. Record
which image, kernel, hooks, drivers, and signatures are deployed; a successful
archive build does not prove firmware Secure Boot enforcement.

The token inherited through early boot gives authority. Executable signing
establishes PIP at exec. A SYSTEM identity alone does not prove TCB signing,
and signing alone does not give SYSTEM identity. Service management requires
both the relevant authority and sufficient process trust.

Policy caches, mount policies, descriptors, and process mitigations are
separate responsibilities. Neither authd readiness nor reaching the service
graph proves that a CAAP or TLP loader populated kernel policy. The maintained
Peinit path does not install those global policies or add a per-service
mitigation mask.

## Follow a boot failure to its owner

- Before real-root handoff, use
  [Prelude's boot diagnosis](~peios/initramfs-boot/debugging-initramfs-boot).
- For service dependencies, readiness, and recovery, use
  [Peinit boot modes](~peios/services-and-jobs/boot-and-boot-modes).
- For identity-source readiness and sign-in failures, use the accounts and
  sign-in guides. Transport availability does not prove every source loaded.
- For executable trust, check the kernel verifier and the running process's
  PSB. Inspect replacement processes separately after a restart.

A privileged recovery shell belongs to the failed stage and its deployment
policy. Do not assume every critical service failure opens a sign-in shell or
that exiting a failure shell resumes the failed operation.
