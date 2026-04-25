---
title: Terminology
---

The following terms are used throughout this specification with the precise meanings defined here.

**KACS** (Kernel Access Control Subsystem): The access control subsystem within PKM. Implements per-thread tokens, Security Descriptors, AccessCheck, privileges, and impersonation. KACS is the sole identity-based authorization engine for managed objects.

**PKM** (Peios Kernel Module): The single compiled-in kernel module containing all Peios kernel extensions. KACS is one of the subsystems within PKM.

**Token**: A per-thread identity object maintained by KACS in the kernel's credential structure. Contains: a user SID, group SIDs, a privilege bitmask, an integrity level, an impersonation level, and metadata. Tokens are immutable in their identity fields (SIDs, type, integrity level) and atomically adjustable in their policy fields (privileges enabled, groups enabled, default owner/group/DACL). Every thread has a token; there are no NULL tokens.

**Primary token**: The token that defines a process's baseline identity. Inherited by child processes on fork. Stored via `task->real_cred`.

**Impersonation token**: A temporary, per-thread token that overrides the primary token for access control decisions. Stored via `task->cred`. Only affects the thread that set it.

**SID** (Security Identifier): A unique, hierarchical principal identifier. Format: `S-1-{authority}-{sub1}-{sub2}-...`. SIDs identify users, groups, services, machines, and well-known principals. SIDs are binary-compatible with Windows SIDs.

**Security Descriptor (SD)**: A binary structure defining the security policy for a protected object. Contains: an owner SID, a primary group SID, a DACL, and optionally a SACL. SDs use the self-relative binary format defined in MS-DTYP section 2.4.6, ensuring compatibility with Active Directory and Samba environments.

**ACL** (Access Control List): An ordered list of ACEs. Two kinds exist: the DACL (controls access) and the SACL (controls audit, mandatory integrity, resource attributes, and central access policy references).

**DACL** (Discretionary Access Control List): The ACL that defines access rules. An empty DACL denies all access. A NULL DACL (absent) grants all access.

**SACL** (System Access Control List): The ACL that defines system-level policy -- audit rules, mandatory integrity labels, resource attributes, and scoped policy references. Modifying the SACL requires ACCESS_SYSTEM_SECURITY.

**ACE** (Access Control Entry): A single rule within an ACL. Contains: a type discriminator, flags, an access mask, a SID, and optionally GUIDs (for object ACEs) or application data (for conditional and resource attribute ACEs). Types include: access allowed/denied (basic and callback/conditional), object ACEs (with property/property-set GUIDs), audit/alarm ACEs, mandatory integrity labels, resource attributes, scoped policy IDs, and process trust labels.

**AccessCheck**: The complete authorization evaluation function. Takes a token (subject), a Security Descriptor (object policy), and a desired access mask. Returns the set of granted rights or denial.

**Access mask**: A 32-bit bitmask representing requested or granted access rights. Divided into: object-specific rights (bits 0--15), standard rights (bits 16--20), special rights (bits 24--25), and generic rights (bits 28--31).

**Privilege**: A system-wide right carried on a token that gates specific operations. Some privileges influence AccessCheck; others gate standalone operations.

**Impersonation level**: Controls how far a token's identity can travel. Four levels: Anonymous, Identification, Impersonation, Delegation.

**Integrity level**: A vertical trust classification on tokens and objects. Five levels forming a strict total order: Untrusted < Low < Medium < High < System.

**MIC** (Mandatory Integrity Control): A mandatory access constraint evaluated before the DACL. Blocks write access (and optionally read/execute) when the caller's integrity level is below the object's mandatory label.

**PIP** (Process Integrity Protection): A 2D trust model (type x trust level) that protects objects and processes from access by insufficiently trusted processes. Unlike MIC, PIP revokes privilege-granted rights.

**PSB** (Process Security Block): A per-process security structure carrying PIP identity, process mitigations, and process restrictions. The PSB is never affected by impersonation.

**FACS** (File Access Control Shim): The KACS subsystem that replaces Linux DAC with SD-based evaluation on files. Enforces the handle model: AccessCheck runs at open time, the granted mask is cached on the file descriptor, and subsequent operations check the cached mask (with limited exceptions documented in the use-time semantics, e.g., v0.20 `execveat` uses live AccessCheck).

**Principal**: A user, group, service, or machine -- an entity that can be identified. Principals exist in a directory; tokens are runtime snapshots of principal identity.

**Object type**: The category of a protected resource. Each object type defines a GenericMapping table that translates generic access rights to object-specific rights.

**TCB** (Trusted Computing Base): The set of components whose correct behaviour is necessary for system security. In Peios: the Linux kernel, PKM, and core trusted userspace daemons (peinit, authd, loregd).

**LSM** (Linux Security Module): The kernel framework that KACS builds on. LSM provides hook points throughout the kernel where security modules interpose access control decisions.

**LogonSession**: A kernel object representing a single authentication event. Contains: session ID, logon type, user SID, authentication package, logon time, and a logon SID. Tokens reference their LogonSession by ID.
