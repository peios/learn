---
title: Layers
---

A layer is a named collection of registry writes that can be managed
as a unit. Layers have precedence: higher-precedence layers override
lower ones. Layers are the mechanism for role management, Group
Policy, and configuration revert.

## Fields

| Field | Type | Mutable | Description |
|---|---|---|---|
| Name | string | No | Unique layer identifier (e.g., "role-jellyfin", "gpo-security-baseline"). Human-readable and meaningful by construction. The identity -- not a GUID, not an integer. Layer names are **case-sensitive** (binary comparison). They are code-generated identifiers, not user-facing paths. Maximum length is MaxPathComponentLength (default 255 characters). |
| Precedence | uint32 | Yes | Determines override order. Higher precedence wins. Default is 0 (role-level). Changes are picked up by LCS via the self-watch mechanism. |
| Enabled | boolean | Yes | Disabled layers are globally invisible during resolution unless attached to a thread's credentials (see Private Layers). Default: enabled. |
| Owner | SID | No | The principal that created the layer. Informational -- access control is on the layer's registry keys, not on this field. |

## The base layer

The base layer (named "base") is a kernel-reserved implicit layer.
It exists unconditionally -- LCS hardcodes its existence even if no
persisted layer metadata has been loaded yet.

The base layer:

- MUST NOT be deleted.
- MUST NOT be disabled.
- MUST NOT have its precedence changed.
- Has precedence 0.

Persisted metadata in `Machine\System\Registry\Layers\base\` MAY
describe the base layer but MUST NOT contradict its existence or
properties. LCS MUST ignore self-watch SUBKEY_DELETED events for
the base layer -- if a higher-precedence HIDDEN entry masks the
base layer's metadata key, LCS MUST NOT process this as a layer
deletion. The base layer's existence is hardcoded and cannot be
overridden by layer mechanics.

When a write does not specify a layer, it targets the base layer.
This is the default for all manual admin operations and system
initialisation.

Role layers also have precedence 0. Within the same precedence
tier, the most recent write wins (highest sequence number). Group
Policy layers have precedence > 0 and override both base and role
layers.

## Layer metadata storage

Layer metadata is stored in the registry itself, under
`Machine\System\Registry\Layers\<LayerName>\`. Each layer's
metadata is a set of values under its key:

- `Precedence` (REG_DWORD)
- `Enabled` (REG_DWORD, 0 or 1)
- `Owner` (REG_BINARY, SID)

LCS watches this subtree and maintains an in-memory cache of the
layer table.

### Circularity

Layer metadata lives in the registry, which is itself layered. This
is intentionally circular but safe. LCS resolves the circularity as
follows:

- LCS always uses its **currently cached** layer table when
  resolving values -- including when resolving layer metadata values.
- When a write to the layer metadata subtree commits, the watch
  fires and LCS re-reads the affected layer metadata using the
  current cache.
- LCS updates the cache with the new values.

There is no recursion risk. LCS reads, caches, and uses the cached
table for all subsequent resolution until the next watch event. The
layer table is never re-resolved mid-operation.

A high-precedence layer (e.g., Group Policy) can override another
layer's precedence -- this is useful and intentional. The cached
layer table picks up the change on the next watch event.

Modifying layer metadata requires SeTcbPrivilege, which limits the
circularity surface to highly privileged callers.

## Layer metadata is global

LCS maintains one authoritative layer table. When additional sources
register, LCS provides them with the current layer list. Each source
stores layer *entries* (path entries and value writes tagged with
layer names) for its own hives. Layer *metadata* (precedence,
enabled state, owner) is global and lives in one place.

## Access control

### Layer lifecycle

| Operation | Requirement |
|---|---|
| Create layer at precedence 0 | KEY_CREATE_SUB_KEY on `Machine\System\Registry\Layers\` |
| Create layer at precedence > 0 | KEY_CREATE_SUB_KEY on `Machine\System\Registry\Layers\` AND SeTcbPrivilege |
| Write into a layer | KEY_SET_VALUE on the layer's metadata key |
| Modify layer metadata | KEY_SET_VALUE on the layer's metadata key. Changing precedence to > 0 additionally requires SeTcbPrivilege. |
| Delete layer | DELETE on the layer's metadata key fd |

SeTcbPrivilege is required specifically for operations that establish or
elevate a layer's precedence above 0. This is a defense-in-depth
measure: compromise of the Layers\ key SD alone cannot create
high-precedence layers without also holding SeTcbPrivilege.

**Enforcement.** LCS maintains a set of layer metadata key GUIDs,
populated by the internal self-watch on
`Machine\System\Registry\Layers\`. This set is updated when layer
metadata keys are created or deleted. The GUID set and the
corresponding SD cache entry MUST be populated atomically within
the self-watch callback, before the creating syscall returns to
userspace. This eliminates any window where a layer exists in the
table but has no cached SD or is absent from the GUID set. If the
SD for a newly created layer metadata key cannot be read (source
error), the layer MUST NOT be added to the table and the creation
syscall MUST fail with EIO.

SeTcbPrivilege for precedence > 0 is enforced inline at
REG_IOC_SET_VALUE time:

1. On every REG_IOC_SET_VALUE, LCS checks whether the target key
   GUID is in the layer metadata key set.
2. If yes, and the value name matches "Precedence"
   (case-insensitive, using the same Unicode Simple Case Folding
   as all other value name comparisons), and the data represents
   a value > 0, LCS checks the caller's token for SeTcbPrivilege.
3. If SeTcbPrivilege is not held, the ioctl returns EPERM without
   contacting the source.

This is a synchronous check at ioctl time — no deferred
validation, no privilege state recording. The caller's token is
available at the syscall boundary.

All other layer operations (writes into a layer, deletion, metadata
modification within the same precedence tier) are controlled
exclusively by the SD on the layer's metadata key.

### Layer lifecycle mechanism

Layers are created and deleted by writing to and deleting keys
under `Machine\System\Registry\Layers\`. There is no dedicated
"create layer" or "delete layer" syscall. LCS watches this subtree
via the self-watch mechanism:

- **Creation:** A key is created at
  `Machine\System\Registry\Layers\<name>\` with Precedence,
  Enabled, and Owner values. Layer creation SHOULD be performed
  within a transaction so all metadata values are present when
  the self-watch fires at commit time. If LCS reads the metadata
  key and finds missing values, it uses defaults: Precedence=0,
  Enabled=true. LCS adds the layer to the in-memory table.

- **Deletion:** The key at
  `Machine\System\Registry\Layers\<name>\` is deleted. The
  self-watch fires a SUBKEY_DELETED event. LCS removes the layer
  from the in-memory table and sends RSI_DELETE_LAYER to all
  registered sources. Sources purge all entries tagged with that
  layer name. LCS determines which keys and values changed
  effective state and dispatches watch events.

Access control on layer lifecycle operations is enforced by the
SDs on the layer metadata keys. Deleting a layer metadata key
requires DELETE right on that key's fd.

### Writing into a layer

Every mutating operation that targets a layer (value writes,
deletions, tombstones, key hides, blanket tombstones) requires
**layer write authorization**: the caller's token MUST have
KEY_SET_VALUE on the layer's metadata key at
`Machine\System\Registry\Layers\<layer_name>\`.

This check is in addition to the fd's granted access mask on the
target key. Both checks MUST pass.

LCS caches layer metadata SDs alongside the layer table. The cache
is invalidated via the self-watch mechanism on the
`Machine\System\Registry\Layers\` subtree.

The layer metadata key's SD determines who can write into that
layer. By default, the base layer's metadata key inherits from the
Machine hive root (SYSTEM and Administrators: KEY_ALL_ACCESS). GP
layers receive restrictive SDs set by the GP client at creation.
Role layers receive SDs set by the role installer.

This prevents both vertical escalation (unprivileged process
writing to a GP layer) and lateral movement (one role's service
writing into another role's layer).

## Layer count cap

The total number of distinct layers in the in-memory layer table
is bounded by MaxTotalLayers (default 1024). Creating a layer when
the table is full returns ENOSPC. This prevents unbounded kernel
memory consumption from layer creation.

## Per-value layer cap

A maximum number of layers MAY write to the same (key GUID, value
name) pair. The default cap is 128. This is a per-value cap, not a
global layer count limit. It prevents amplification attacks where
every read must resolve an excessive number of entries.

**Enforcement.** The cap is checked by LCS at REG_IOC_SET_VALUE
time, before contacting the source. LCS queries the source for
the current entry count at (key GUID, value name) across all
layers. If adding a new layer entry would exceed
MaxLayersPerValue, the write is rejected with ENOSPC. This check
is not performed for writes that replace an existing entry in the
same layer (which do not increase the layer count).

The cap is configurable via the self-configuration mechanism. See
§11.4 for the full parameter table.

## Private layers

A private layer is a disabled layer attached to a specific thread's
credentials. Private layers are globally invisible during normal
resolution but included when resolving on behalf of a thread whose
credentials carry the layer.

Private layers enable:

- **Per-session configuration overrides.** A user opens an
  application with experimental settings without affecting other
  sessions.
- **Testing.** Inject test configuration without modifying the
  shared registry.
- **Sandboxing.** A container sees a different view of the registry
  without a separate hive.

### Credential attachment

A thread's credentials MAY carry a set of private layer names. When
LCS resolves a value or path entry for that thread, disabled layers
whose names appear in the thread's credential set are treated as
enabled for the duration of that resolution.

The mechanism for attaching private layers to credentials depends on
KACS token extensions not yet specified. LCS defines the resolution
behaviour; KACS defines the credential model.

**Security constraint on KACS.** When KACS implements credential
attachment for private layers, it MUST verify at attachment time
that the attaching token holds sufficient privilege for the named
layer's precedence. Specifically: attaching a layer with precedence
> 0 MUST require SeTcbPrivilege. Without this constraint, an unprivileged
process could attach an existing high-precedence disabled layer to
its own credentials, gaining the ability to see (and potentially
influence) GP-level configuration.

### Resolution interaction

Private layers participate in the normal precedence ordering. A
disabled layer with precedence 5 attached to a thread's credentials
is resolved at precedence 5, competing with other enabled layers
at the same or different precedence levels.

### Scope

Private layers are per-thread, not per-process. Different threads
in the same process MAY have different private layer sets via
different impersonation tokens. The maximum number of private
layers per token is bounded by MaxPrivateLayersPerToken (default
16). Exceeding this limit at credential attachment time is an
error.
