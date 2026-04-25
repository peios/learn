---
title: Access Control
---

The registry's security model is a direct application of KACS. LCS
does not define its own access control mechanism -- it uses the same
AccessCheck, SDs, tokens, and SIDs that every other Peios subsystem
uses. This section describes how KACS primitives integrate with
registry operations.

## Access control flow

Every registry operation that opens a key follows the same path:

1. **Token capture.** The userspace thread makes a registry syscall.
   LCS captures the thread's effective token -- the impersonation
   token if one is set, otherwise the primary token. This is the
   same token capture KACS uses for all syscalls.

2. **Path resolution.** LCS walks the registry path via RSI Lookup
   operations, resolving through the layer stack. Symlinks are
   followed. No access checking occurs during the walk --
   intermediate keys are not checked. Only the final key matters.

3. **AccessCheck.** LCS calls the KACS AccessCheck function with:
   - The caller's token (captured in step 1)
   - The final key's SD (returned by the source in the Lookup
     response)
   - The desired access mask (from the syscall arguments)

   All requested rights MUST be granted or the open fails with
   EACCES. There is no partial grant -- the caller gets exactly
   what they asked for, or nothing.

   The special value MAXIMUM_ALLOWED requests whatever the SD
   grants. AccessCheck computes the full set of allowed rights and
   uses that as the granted mask.

4. **Granted mask storage.** The granted access mask is stored on
   the key fd. It does not change after open.

5. **Per-ioctl access check.** Each ioctl has a required access
   right. Before processing, LCS verifies that the fd's granted
   mask includes the required right. This is a bitmask check, not
   an AccessCheck re-evaluation. If the right is not present, EACCES
   is returned without contacting the source.

## Access rights

Registry access rights are bit positions within the desired_access
and granted_access uint32 masks. The values match the Windows
registry access rights for registry.pol and Samba compatibility.

### Specific rights (bits 0--15)

| Right | Value | Description |
|---|---|---|
| KEY_QUERY_VALUE | 0x0001 | Read values. |
| KEY_SET_VALUE | 0x0002 | Write and delete values. |
| KEY_CREATE_SUB_KEY | 0x0004 | Create child keys. |
| KEY_ENUMERATE_SUB_KEYS | 0x0008 | Enumerate child keys. |
| KEY_NOTIFY | 0x0010 | Subscribe to watches. |
| KEY_CREATE_LINK | 0x0020 | Create symlink keys. |

### Standard rights (bits 16--23)

| Right | Value | Description |
|---|---|---|
| DELETE | 0x00010000 | Delete the key. Hide the key. |
| READ_CONTROL | 0x00020000 | Read the SD and key metadata. |
| WRITE_DAC | 0x00040000 | Modify the DACL. |
| WRITE_OWNER | 0x00080000 | Change the owner SID. |

### System rights

| Right | Value | Description |
|---|---|---|
| ACCESS_SYSTEM_SECURITY | 0x01000000 | Read or modify the SACL. Gated by SeSecurityPrivilege (PSD-004 §7). |

### Generic-to-specific mapping

| Generic right | Maps to |
|---|---|
| KEY_READ | KEY_QUERY_VALUE \| KEY_ENUMERATE_SUB_KEYS \| KEY_NOTIFY \| READ_CONTROL |
| KEY_WRITE | KEY_SET_VALUE \| KEY_CREATE_SUB_KEY \| READ_CONTROL |
| KEY_ALL_ACCESS | All specific rights \| all standard rights |

These mappings are applied during AccessCheck. Callers MAY use
generic rights in desired_access. SDs MAY contain generic ACEs.
The mapping table is defined by LCS and registered with KACS.

## SD inheritance

When a key is created via reg_create_key, its initial SD is
computed from the parent key's SD using the KACS inheritance
algorithm (PSD-004 §3.6).

Registry-specific notes:

- Inheritance is **static** -- computed once at creation time.
  Changes to the parent's SD do not automatically propagate to
  existing children. Re-propagation is an explicit admin action
  (a client-side tree walk), not a kernel operation.

- **OBJECT_INHERIT_ACE is not relevant** for registry keys. All
  registry objects are containers (keys contain subkeys and values).
  Values are not independent security objects -- they inherit their
  key's access control. Only CONTAINER_INHERIT_ACE applies.

- If the parent has no inheritable ACEs, the child's DACL is set
  from the creating token's default DACL.

- LCS delegates the inheritance computation to KACS and passes the
  resulting SD to the source for storage. LCS does not implement
  its own inheritance logic.

## Hive root SDs

Hive root keys are the top of the inheritance chain -- they have
no parent to inherit from. Their SDs are set by the source at
first boot and serve as the seeds for all descendant key
permissions.

**Machine\\ root:**

| Principal | Rights | Inheritance |
|---|---|---|
| SYSTEM | KEY_ALL_ACCESS | Container-inherit |
| Administrators | KEY_ALL_ACCESS | Container-inherit |
| Authenticated Users | KEY_READ | Container-inherit |

**Users\\&lt;SID&gt;\\ root (per-user hive root):**

| Principal | Rights | Inheritance |
|---|---|---|
| &lt;User SID&gt; | KEY_ALL_ACCESS | Container-inherit |
| SYSTEM | KEY_ALL_ACCESS | Container-inherit |
| Administrators | KEY_ALL_ACCESS | Container-inherit |

These defaults match Windows HKLM and HKU semantics. Subsystems
that need tighter access (e.g., `Machine\Security\`) set explicit
SDs on their subtree roots at creation time, overriding the
inherited defaults.

These SDs are not hardcoded in LCS. They are set by the source
(loregd) when creating hive roots. LCS enforces whatever SD the
source stores.

## Registry-specific considerations

**No traverse checking.** LCS does not check access on intermediate
path components during path resolution. Only the final key's SD is
evaluated. This matches the Windows registry model. A process can
access `Machine\System\Services\Jellyfin` without needing any
access to `Machine\System\Services` or `Machine\System`.

**Symlink security.** Opening a symlink follows the target path.
LCS evaluates AccessCheck on the **target key**, not the symlink
key (unless REG_OPEN_LINK is specified). Symlink creation is
privileged (KEY_CREATE_LINK + SeTcbPrivilege or Administrator membership).

**Watch access.** Subscribing to watches requires KEY_NOTIFY on the
key fd. This prevents processes from monitoring keys they cannot
read. Subtree watches expose structural changes (key creation,
deletion) in descendants without per-descendant access checks --
the watcher learns that a descendant was created but cannot read
its values without opening it separately. This matches Windows
RegNotifyChangeKeyValue semantics. Structure visibility is
intentionally weaker than content visibility.

**SACL evaluation and audit.** When LCS performs AccessCheck at key
open time and the key's SD contains a SACL with matching audit
ACEs, LCS MUST emit audit events via the kernel audit pipeline.
SACL evaluation follows the KACS AccessCheck algorithm — the SACL
is evaluated alongside the DACL. Audit events include the caller's
token, the key GUID, the requested access, and the access decision.
Accessing or modifying the SACL itself requires
ACCESS_SYSTEM_SECURITY, which is gated by SeSecurityPrivilege (see
PSD-004 §7).

**SD changes and existing fds.** SD modifications take effect for
future opens. Existing fds retain their granted access mask from
open time (§2.1 semantic rule 5). The admin's recourse for revoking
access is to restart the service holding the fd.

**SD modification access rights:**

| Operation | Required right |
|---|---|
| Read owner, group, DACL | READ_CONTROL |
| Modify DACL | WRITE_DAC |
| Change owner | WRITE_OWNER |
| Read SACL | ACCESS_SYSTEM_SECURITY |
| Modify SACL | ACCESS_SYSTEM_SECURITY |

SD modifications are NOT layer-qualified. They are direct mutations
on the key object (§2.1 semantic rule 4). See §2.5 for the
distinction between layered data and non-layered properties.
