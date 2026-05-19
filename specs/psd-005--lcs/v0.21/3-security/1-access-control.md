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

KEY_READ, KEY_WRITE, and KEY_ALL_ACCESS are concrete registry
convenience masks. LCS also accepts the raw KACS generic access
bits GENERIC_READ, GENERIC_WRITE, GENERIC_EXECUTE, and GENERIC_ALL
in caller-supplied desired_access and in registry SD ACE masks.
Those raw generic bits are mapped through the registry GenericMapping
before AccessCheck according to PSD-004 §10.10. GENERIC_EXECUTE maps
to 0 because registry keys have no execute right.

### Access mask validation

LCS validates caller-supplied desired_access before path resolution
or AccessCheck. The valid caller mask is:

- the six specific registry rights listed above;
- DELETE, READ_CONTROL, WRITE_DAC, and WRITE_OWNER;
- ACCESS_SYSTEM_SECURITY;
- MAXIMUM_ALLOWED;
- GENERIC_READ, GENERIC_WRITE, GENERIC_EXECUTE, and GENERIC_ALL.

If desired_access is 0, LCS MUST fail with EINVAL. If desired_access
contains any bit outside the valid caller mask, LCS MUST fail with
EINVAL. MAXIMUM_ALLOWED MAY be used alone or combined with specific,
standard, system, or raw generic rights, following PSD-004 §10.2.

Registry keys do not support SYNCHRONIZE in v0.21. A caller request
containing SYNCHRONIZE is therefore an unknown-bit request and fails
with EINVAL.

LCS also validates registry SDs returned by sources before using
them for AccessCheck. ACE masks MAY contain registry concrete rights
and raw KACS generic bits. ACE masks MUST NOT contain
MAXIMUM_ALLOWED. After generic mapping, an ACE mask MUST be a subset
of concrete registry rights plus ACCESS_SYSTEM_SECURITY. A source SD
that violates these rules is malformed source data: LCS fails the
operation closed with EIO and emits the source-validation audit event
defined in §3.1.

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

For v0.21, the LCS kernel audit pipeline is KMES (PSD-003). KMES is
an in-kernel PKM facility and must be initialised before LCS can
emit audit events. LCS audit emission is synchronous at the audit
point.

For a key-open SACL audit, LCS evaluates AccessCheck, determines the
access decision and granted mask, emits the KMES audit event, and
only then publishes the resulting key fd to userspace. If KMES event
emission fails, LCS fails the open with EIO and does not return a key
fd. The AccessCheck decision itself is not changed, but the audited
operation is not completed without the required audit record.

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

## LCS audit events

LCS emits the following KMES audit events.

| Event | When emitted | Required fields |
|---|---|---|
| LCS_KEY_OPEN_AUDIT | A key open has a matching SACL audit ACE. | caller token summary, key GUID, requested access, granted access, decision, SACL match flags |
| LCS_BACKUP_START | Before REG_IOC_BACKUP starts reading subtree data. | caller token summary, key GUID, output fd number |
| LCS_BACKUP_COMPLETE | After REG_IOC_BACKUP completes or fails after start. | caller token summary, key GUID, result errno |
| LCS_RESTORE_START | Before REG_IOC_RESTORE starts modifying source state. | caller token summary, key GUID, input fd number |
| LCS_RESTORE_COMPLETE | After REG_IOC_RESTORE completes or fails after start. | caller token summary, key GUID, result errno |
| LCS_SOURCE_VALIDATION_FAILURE | LCS rejects malformed source data. | source slot identifier, hive name if known, request ID if known, operation code if known, key GUID if known, validation class |
| LCS_SELF_CONFIG_INVALID | LCS rejects an invalid self-configuration value. | configuration path, expected type/range, received type, received value summary, retained value summary |

`caller token summary` is a KMES-safe summary of the effective token
used for the operation. It must include enough identity information
to correlate the event with the caller without exposing unbounded
token internals in the event record.

For v0.21, every LCS audit payload MUST be a single msgpack map with
string keys. Map order is not semantically significant, but kernel
emitters SHOULD encode fields in the table order below for stable
diagnostics. GUID fields are 16-byte Microsoft GUID binary values.
SID fields are binary KACS SID encodings.

The `caller` field used below is itself a msgpack map with the
following bounded fields:

| Field | Type | Description |
|---|---|---|
| `effective_token_guid` | `bin(16)` | GUID of the effective token captured for the operation. |
| `true_token_guid` | `bin(16)` | GUID of the process primary token captured for the operation. |
| `process_guid` | `bin(16)` | GUID of the calling process. |
| `user_sid` | `bin` | User SID from the effective token. |
| `authentication_id` | `uint64` | Effective token authentication ID. |
| `token_id` | `uint64` | Effective token ID. |
| `token_type` | `uint32` | KACS token type value. |
| `impersonation_level` | `uint32` | KACS impersonation level value, or 0 for primary tokens. |
| `integrity_level` | `uint32` | Effective token integrity level. |

The caller summary MUST NOT include group lists, privilege arrays,
claims, default DACLs, or other unbounded token internals.

`LCS_KEY_OPEN_AUDIT` payload:

| Field | Type | Description |
|---|---|---|
| `caller` | map | Caller token summary. |
| `key_guid` | `bin(16)` | Open target key GUID. |
| `requested_access` | `uint32` | Caller requested access after registry generic mapping rules are applied. |
| `granted_access` | `uint32` | Granted mask computed by AccessCheck; 0 on denied opens. |
| `decision` | string | Either `allowed` or `denied`. |
| `sacl_match_flags` | `uint32` | Non-zero bitmask of matching SACL audit classes. Bit 0 (`0x1`) means success-audit match. Bit 1 (`0x2`) means failure-audit match. All other bits are reserved and MUST NOT be set. |

Backup and restore start/complete payloads:

| Event | Fields |
|---|---|
| `LCS_BACKUP_START` | `caller` map, `key_guid` `bin(16)`, `fd` `int32` output fd number. |
| `LCS_BACKUP_COMPLETE` | `caller` map, `key_guid` `bin(16)`, `result_errno` `uint32`, where 0 means success and non-zero values are Linux errno numbers. |
| `LCS_RESTORE_START` | `caller` map, `key_guid` `bin(16)`, `fd` `int32` input fd number. |
| `LCS_RESTORE_COMPLETE` | `caller` map, `key_guid` `bin(16)`, `result_errno` `uint32`, where 0 means success and non-zero values are Linux errno numbers. |

`LCS_SOURCE_VALIDATION_FAILURE` payload:

| Field | Type | Description |
|---|---|---|
| `source_slot` | `uint32` | LCS source slot identifier. |
| `hive_name` | string or nil | Hive name if known. |
| `request_id` | `uint64` or nil | RSI request ID if known. |
| `op_code` | `uint16` or nil | RSI operation code if known. |
| `key_guid` | `bin(16)` or nil | Key GUID associated with the failed validation if known. |
| `validation_class` | string | One of `malformed_security_descriptor`, `future_sequence_number`, `duplicate_winning_sequence_tie`, or `malformed_layer_metadata_security_descriptor`. |

`LCS_SELF_CONFIG_INVALID` payload:

| Field | Type | Description |
|---|---|---|
| `configuration_parent_path` | string | Parent key path containing the invalid configuration value. |
| `configuration_name` | string | Configuration value name. |
| `expected_type` | `uint32` | Expected registry value type. |
| `expected_min` | `uint32` | Minimum accepted value for numeric ranges. |
| `expected_max` | `uint32` | Maximum accepted value for numeric ranges. |
| `received_kind` | string | One of `missing`, `wrong_type`, or `dword_out_of_range`. |
| `received_type` | `uint32` or nil | Actual registry type for `wrong_type`, otherwise nil. |
| `received_u32` | `uint32` or nil | Actual numeric value for `dword_out_of_range`, otherwise nil. |
| `retained_value` | `uint32` | Previous known-good value retained by LCS. |

Audit emission failure policy:

- For LCS_KEY_OPEN_AUDIT, failure to emit returns EIO and the key fd
  is not published.
- For LCS_BACKUP_START and LCS_RESTORE_START, failure to emit returns
  EIO and the backup or restore does not start.
- For LCS_BACKUP_COMPLETE and LCS_RESTORE_COMPLETE, the operation has
  already completed or failed. LCS attempts emission; if emission
  fails, it does not alter the already determined result.
- For LCS_SOURCE_VALIDATION_FAILURE, the triggering operation already
  fails with EIO. LCS attempts emission; if emission fails, the
  operation still returns EIO.
- For LCS_SELF_CONFIG_INVALID, the invalid value is ignored and the
  previous known-good value is retained. LCS attempts emission; if
  emission fails, the retained configuration remains in force.
