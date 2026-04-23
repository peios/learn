---
title: Scope
---

This specification defines peinit, the init system for the Peios
operating system. peinit is PID 1 -- a single-threaded Rust process
responsible for service lifecycle management from boot to shutdown.

peinit is the sole service manager in Peios. All supervised process
execution -- service starts, stops, restarts, health monitoring, and
ad-hoc job submission -- passes through peinit. Services are
identity-aware: each service process runs with a KACS token that
determines its access rights, and each service object carries a
Security Descriptor that controls who may manage it.

This specification covers:

- The boot sequence -- two-phase bootstrap (hardcoded Phase 1,
  registry-driven Phase 2), boot modes (Full, Safe, Recovery), and
  the escalation path between them
- The service model -- definition schema, registry layout,
  configuration generations, service types, triggers, and the
  Disabled flag
- Service identity -- token materialisation for SYSTEM and
  authd-minted identities, per-service SIDs, privilege restriction
- Services as securable objects -- ServiceSecurity descriptors,
  access rights, and peinit's own control security descriptor
- The pre-exec sequence -- the exact operations between "peinit
  decides to start service X" and "the service binary is running"
- The service state machine -- states, transitions, transition
  causes, restart semantics, reload semantics, and invariants
- Dependencies -- Requires, Wants, BindsTo, and Conflicts
  relationships, graph validation, parallel start, failure
  propagation, conflict resolution, and shutdown ordering
- Jobs -- supervised process execution as first-class objects,
  lifecycle, types, ad-hoc jobs, and the JFS consumption protocol
- Operations -- queued state machine actions, lifecycle, conflict
  resolution, dependency propagation, and retention
- Timers -- calendar expressions, evaluation, persistence, jitter,
  and clock behaviour
- Shutdown -- triggers, the graceful shutdown sequence, signal
  handling, and global timeout enforcement
- The control interface -- control socket wire protocol, peer
  authentication, the command set, wait semantics, and the notify
  socket
- Service output handling -- stdout/stderr wiring, pre-eventd
  buffering, flood protection, eventd handoff, and console output
- The security model -- trust boundaries, peinit's privilege
  requirements, service identity security, control socket security,
  notify socket security, and the attack surface

This specification does not cover:

- KACS (covered by the KACS v0.20 specification)
- LCS (covered by the LCS v0.21 specification)
- registryd internals (storage engine, schema, caching)
- authd (authentication, token minting, identity source routing)
- lpsd (local principal store)
- eventd (event storage, indexing, query API)
- JFS kernel internals (token capture, privilege validation, the
  char device implementation)
- Specific registry key schemas defined by other subsystems
- Admin tooling (peiosctl, peinit-analyze)
- The role system and package management
- FACS (File Access Control via Security Descriptors)
- Network-level service management (future remote SCM)
