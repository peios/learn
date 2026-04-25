---
title: Terminology
---

This section defines terms used throughout the specification. Terms
defined inline in later sections (activation generation, boot
generation, transition cause, cgroup generation, etc.) are not
duplicated here.

- **PKM** (Peios Kernel Module): The single compiled-in kernel
  module containing all Peios kernel extensions. PKM is the
  boundary between Peios kernel code and the upstream Linux
  kernel.

- **KACS** (Kernel-based Access Control System): The access control
  subsystem within PKM. Implements per-thread tokens, Security
  Descriptors, and AccessCheck. peinit depends on KACS for service
  identity (token installation on child processes), control
  interface authentication (peer token retrieval and AccessCheck),
  and service object access control (ServiceSecurity descriptors).
  Specified separately in PSD-004.

- **LCS** (Layered Configuration Subsystem): The configuration
  subsystem within PKM, peer to KACS. Implements the kernel-side
  registry: syscall dispatch, hive routing, access control
  enforcement, layer resolution, watch dispatch, and transaction
  coordination. peinit reads service definitions and configuration
  from the registry via LCS syscalls. Specified separately in the
  PSD-005.

- **Registry**: The user-facing configuration system provided by
  LCS and its sources working together. peinit reads service
  definitions from `Machine\System\Services\`, boot configuration
  from `Machine\System\Boot\`, and its own operational parameters
  from `Machine\System\Init\`. When precision matters, use "LCS"
  for the kernel subsystem and the relevant source name for the
  userspace component.

- **registryd**: The userspace registry source daemon. peinit
  starts registryd during Phase 1 boot using a compiled-in service
  definition. registryd implements the Registry Source Interface
  for persistent hives. peinit treats registryd as an opaque
  dependency -- it does not interact with registryd's storage
  internals. In Recovery mode, the administrator interacts directly
  with the registryd implementation (loregd) via diagnostic
  command-line flags. See §2.3.

- **Token**: A per-thread identity object maintained by KACS.
  Contains a user SID, group SIDs, a privilege bitmask, an
  integrity level, and metadata. peinit requests tokens from authd
  for service processes and installs them before exec. For SYSTEM
  services, peinit clones its own token. Tokens are the sole
  identity mechanism -- peinit never sets Linux UIDs, GIDs, or
  capabilities on service processes.

- **SID** (Security Identifier): A unique principal identifier
  (e.g., `S-1-5-18` for SYSTEM, `S-1-5-32-544` for
  Administrators). SIDs appear in tokens (as identity), in
  Security Descriptors (as access rules), and in registry paths
  (`Users\<SID>\`).

- **Security Descriptor** (SD): A KACS structure controlling
  access to a securable object. Contains a DACL (who can access,
  and how) and optionally a SACL (audit policy). peinit uses SDs
  in two contexts: ServiceSecurity descriptors control who may
  manage a service via the control interface, and peinit's own
  control SD controls who may perform system-level operations
  (shutdown, reload-config).

- **AccessCheck**: The KACS kernel function that evaluates a
  caller's token against an object's SD to produce an access
  decision. peinit calls AccessCheck to authorize every control
  interface command. Single code path for all access control
  decisions across all Peios subsystems.

- **Privilege**: A granular system-wide right carried on a token.
  Privileges are checked by name and enforced by KACS. peinit
  uses RequiredPrivileges to restrict service tokens -- privileges
  not in the list are removed before exec.

- **Impersonation**: A thread temporarily assuming a different
  identity. The thread's effective token changes; its primary
  token is preserved. peinit uses impersonation indirectly --
  KACS captures client identity on control socket connections,
  and peinit evaluates that identity via AccessCheck.

- **SYSTEM**: The highest-privilege built-in identity (`S-1-5-18`).
  peinit runs as SYSTEM for the lifetime of the system. Platform
  services (registryd, authd, lpsd, eventd) also run as SYSTEM.
  SYSTEM carries all defined privileges.

- **authd**: The central identity authority. Handles
  authentication, token minting, logon session creation, and
  identity source routing. peinit requests service tokens from
  authd for non-SYSTEM services. authd automatically adds a
  per-service SID to each minted token.

- **lpsd** (Local Principal Store): The local identity database.
  Users, groups, SID allocation, password hashes. One of
  potentially many identity sources that authd routes to.

- **eventd**: The logging and audit daemon. Drains the kernel
  audit ring buffer, captures service logs, stores events, and
  serves the query API. peinit forwards service stdout/stderr to
  eventd and emits structured lifecycle events. eventd is
  ErrorControl=Critical -- its failure triggers a reboot.
  Observability is a foundational guarantee in Peios, not an
  optional layer.

- **Service**: A named, supervised unit of execution managed by
  peinit. A service has a definition (registry schema), a runtime
  state (state machine), and optionally a running process. Services
  are securable objects -- each carries a Security Descriptor
  controlling who may manage it.

- **Job**: A single supervised process execution. Every time peinit
  forks a process -- starting a service, running a hook, executing
  a health check, or handling an ad-hoc run request -- the
  execution is a job with a GUID, lifecycle tracking, and log
  correlation. Jobs are the observable unit of "what actually ran."

- **Operation**: A first-class object representing a requested
  state machine action on a service. Control commands (start,
  stop, restart, reload, reset) create operations that are
  validated, queued, and executed. Operations provide conflict
  resolution for concurrent commands and observable lifecycle
  tracking via GUIDs.

- **JFS** (Job Forwarding Subsystem): A kernel subsystem within
  PKM that provides a secure bridge for ad-hoc job submission.
  JFS captures the caller's effective KACS token and delivers it
  to peinit via `/dev/jfs`. peinit consumes JFS requests from
  its event loop. JFS kernel internals are outside the scope of
  this specification.

- **KMES** (Kernel Mediated Event Subsystem): The kernel-side
  observability component within PKM. Manages the kernel ring
  buffer, trusted metadata stamping, and event persistence across
  reboots. KMES ensures audit data survives eventd restarts and
  system reboots.

- **TCB** (Trusted Computing Base): The set of components whose
  correct behaviour is necessary for the system's security
  guarantees. In peinit's context, the TCB comprises the kernel,
  KACS, LCS, KMES, peinit, registryd, authd, lpsd, and eventd.
  A compromise of any TCB component compromises the entire system.

- **sd_notify**: A datagram-based readiness and health signalling
  protocol. Services send structured messages (e.g., `READY=1`,
  `WATCHDOG=1`) to peinit via a Unix datagram socket whose path
  is provided in the `NOTIFY_SOCKET` environment variable. Sender
  authentication uses kernel-attested PID matching.

- **pidfd**: A file descriptor referring to a specific process,
  obtained atomically at fork time via `clone3(CLONE_PIDFD)`.
  pidfds eliminate PID reuse races and provide race-free process
  supervision. peinit tracks every managed process via a pidfd.

- **cgroup**: A Linux kernel mechanism for grouping processes.
  peinit uses cgroups v2 exclusively, for process tracking and
  clean kill. Every service runs in its own cgroup tree under
  `/sys/fs/cgroup/peinit/`. peinit does not use cgroups for
  resource accounting or limits.

- **Phase 1**: The hardcoded bootstrap phase. peinit remounts
  root read-write, mounts virtual filesystems, sets the system
  clock, starts registryd, and performs infrastructure setup
  (control socket, JFS device, loopback interface). No registry
  access occurs during Phase 1.

- **Phase 2**: The registry-driven boot phase. With registryd
  running, peinit reads service definitions from the registry
  and starts all boot-triggered services in dependency order.

- **Mount pseudo-service**: A synthetic Oneshot service generated
  by peinit from mount entries in `Machine\System\Boot\Mounts\`.
  Named `mount:<mountpoint>` (e.g., `mount:/data`). Behaves as a
  Oneshot with RemainAfterExit -- the mount completes, the
  pseudo-service stays in Completed, and dependents can start.
  Participates in the dependency graph like any other service.

- **ErrorControl**: A per-service policy that determines peinit's
  response when a service fails irrecoverably. Normal (default):
  service remains in Failed state. Critical: peinit syncs
  filesystems and reboots.
