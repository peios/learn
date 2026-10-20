---
title: Formats and Constants
type: reference
description: Find the specification or owning implementation for a binary layout, access right, or numeric constant.
---

Use the reference owned by the interface you are implementing. Shared data
structures are specified in Peios Core Data Structures (PCDS). Kernel system
calls and object layouts are documented beside the kernel's exported headers.
A service's protocol belongs to that service's contract.

## Shared structures

| Structure | Reference |
|---|---|
| Security identifier (SID), including its binary representation and well-known values | [PCDS SIDs](~specifications/pcds/sid/binary-format) |
| Globally unique identifier (GUID) | [PCDS GUIDs](~specifications/pcds/guid/binary-format) |
| Locally unique identifier (LUID) | [PCDS LUIDs](~specifications/pcds/luid/binary-format) |
| Self-relative security descriptor and its control flags | [SD Structure](~specifications/pcds/security-descriptor/structure) |
| Access control list (ACL) header and entries | [ACL Format](~specifications/pcds/security-descriptor/acl-format) |
| Access mask and generic-right interpretation | [Access Masks](~specifications/pcds/security-descriptor/access-masks) |
| Access control entry (ACE) types and bodies | [ACE Types](~specifications/pcds/security-descriptor/ace-types) |
| Inheritance and propagation flags | [Inheritance](~specifications/pcds/security-descriptor/inheritance) |
| Claims, resource attributes, and conditional expressions | [Security Descriptors](~specifications/pcds/security-descriptor/claim-attribute-format) |

PCDS describes the representation. The kernel's [descriptor and ACE
semantics](~kernel/userspace/native/kacs/descriptor-and-ace-semantics) and
[MS-DTYP compatibility notes](~kernel/userspace/native/kacs/ms-dtyp-compatibility-and-divergences)
explain implementation behavior. A representable ACE type does not by itself
establish that the evaluator acts on that type.

## Kernel interfaces

| Interface | Reference |
|---|---|
| Token creation, sessions, query classes, group attributes, and impersonation levels | [Token and Session ABI](~kernel/userspace/native/kacs/generated-token-and-session-abi) |
| Access checks, descriptors, central policies, and security-information flags | [Access-Check and Descriptor ABI](~kernel/userspace/native/kacs/generated-access-check-and-descriptor-abi) |
| File rights, create dispositions, and mount templates | [File and Mount ABI](~kernel/userspace/native/kacs/generated-file-and-mount-abi) |
| Process rights, process security blocks, and mitigations | [Process and PSB ABI](~kernel/userspace/native/kacs/generated-process-and-psb-abi) |
| Registry rights and key security | [Key and Security ABI](~kernel/userspace/native/lcs/generated-key-and-security-abi) |
| Registry watch records | [Watch ABI](~kernel/userspace/native/lcs/generated-watch-abi) |
| Event-ring records and constants | [KMES ABI](~kernel/userspace/native/kmes/generated-abi-tables) |

The generated tables retain exact exported spellings, field widths, and
limits. Consult their semantic companion pages for behavior that a compiler
cannot measure. The [naming
map](~kernel/userspace/native/kacs/abi-status-and-naming-differences) connects
specification names to header names; do not invent a constant by changing its
prefix.

Object-specific access bits are not interchangeable. A file, token, process,
registry key, and service can assign different meanings to the same bit.
Use the object's generic mapping and aggregate masks rather than copying a
mask from another interface.

## Privileges and service rights

The kernel's [privilege
catalog](~kernel/internals/kacs/privileges/privilege-catalogue) describes what
privileges enforce. Assignment and restriction remain separate questions:
[authd policy](~peios/authentication/granting-access) supplies grants,
while [peinit privilege
restriction](~peios/peinit/service-identity/privilege-restriction) removes
unrequested privileges using the names supported by that build.

Service-control rights belong to [Peinit's
constants](~peios/peinit/constants-and-paths) and [service access
model](~peios/services-and-jobs/who-can-manage-a-service). Do not substitute a
Windows service-access table for Peinit's values.

## Decode the actual format

There is no universal length-prefix convention across these interfaces.
Token input has a fixed header and structured variable sections. Session
input uses fields of different widths. Central access policy input has its
own version and rule structure; its ACL payloads are ACLs, while an
applies-to expression uses conditional-expression bytecode.

Choose a decoder for the documented version, validate lengths and counts,
and use its stated limits. A stale count of fields or query classes in a
secondary summary is not a format contract. Prefer the supported SDK encoder
when it provides the required operation.

## Events and packages

The [Peios System-to-Kernel
Protocols](~specifications/pspk) define shared kernel protocol contracts.
Use the emitting component's `evman` catalog for individual event payloads;
a name and a binary envelope do not define every event field.

Package and repository contracts are in [Peios System-to-Userspace
Protocols](~specifications/pspu). Match the documented package format to the
tool consuming it; a package format transition does not make an older
container readable by a newer tool automatically.
