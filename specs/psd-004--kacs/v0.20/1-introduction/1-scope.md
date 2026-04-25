---
title: Scope
---

This specification defines the Kernel Access Control Subsystem (KACS) for the Peios operating system. KACS is a Linux Security Module (LSM) within the Peios Kernel Module (PKM) that provides identity-based access control in the Linux kernel.

KACS is the sole identity-based authorization mechanism for managed objects in Peios. All identity-based authorization decisions -- file opens, registry reads, IPC connections, signal delivery, token operations -- pass through a single evaluation function, AccessCheck.

This specification covers:

- Security Identifiers (SIDs) -- the principal identification format
- Tokens -- per-thread identity objects carrying SIDs, groups, privileges, and integrity levels
- The Process Security Block (PSB) -- per-process security properties independent of identity
- Security Descriptors (SDs) -- per-object security policy structures containing access control lists
- Privileges -- system-wide rights carried on tokens
- AccessCheck -- the complete authorization evaluation algorithm
- Impersonation -- per-thread identity substitution with level controls
- Process Integrity Protection (PIP) -- process-level isolation based on binary trust
- File Enforcement (FACS) -- the file access control implementation mapping SDs to VFS operations
- The Linux credential model under KACS -- credential projection, DAC neutralization, and UID semantics

This specification does not cover:

- Authentication (authd)
- The principal store or directory services
- The registry subsystem (loregd)
- Service management (peinit)
- The Job Forwarding Subsystem (JFS)
- The event and audit subsystem (KMES -- specified separately)
- Network-level delegation and Kerberos integration
- Container integration
