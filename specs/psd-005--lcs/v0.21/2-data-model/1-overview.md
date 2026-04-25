---
title: Overview
---

The registry data model has six entities: hives, keys, path entries,
values, layers, and sources. This section defines each entity, its
fields, its constraints, and its relationships to other entities.

## Semantic core

Six rules define the entire registry model. Every section that follows
is a consequence of these rules. If a design decision conflicts with
one of them, the decision is wrong.

1. **Names are layered.** A key's presence at a path is per-layer.
   Different layers can name different keys at the same path. Layer
   resolution determines which is visible. Removing a layer removes
   its names.

2. **Values are layered.** Every value write is tagged with a layer.
   The effective value is the highest-precedence entry. Removing a
   layer removes its entries and the next layer's values surface.
   Tombstones can actively mask lower layers.

3. **Key identity is not layered.** A key's GUID, Security
   Descriptor, volatile flag, symlink flag, and last write time
   belong to the key itself, not to any layer. These properties are
   direct mutations on the object. They are never automatically
   reverted.

4. **Security is key-bound, not layer-bound.** SD modifications are
   permanent changes to the key object. Removing a layer does NOT
   revert SD changes that were made while the layer existed. Security
   policy is operational state, not configuration overlay.

5. **Handles are capabilities granted at open.** An open key fd
   carries a granted access mask computed once at open time via
   AccessCheck. Subsequent operations check the mask, not the SD.
   SD changes do not affect existing handles. Handle lifetime is
   independent of path lifetime.

6. **Sources persist, the kernel decides meaning.** Sources are
   storage backends. They store path entries, key records, and value
   entries. They return all layer data on request. They do not
   evaluate access, resolve layers, dispatch watches, or interpret
   paths. LCS does all of that.

## Property matrix

| Property | Layered? | Resolved how | Survives layer deletion? | Visible to watchers as |
|---|---|---|---|---|
| Path existence | Yes | Highest precedence, then highest sequence number | No | SUBKEY_CREATED / SUBKEY_DELETED |
| Values | Yes | Highest precedence, then highest sequence number | No | VALUE_SET / VALUE_DELETED |
| Value tombstones | Yes | Masks lower precedence | No | Writing: VALUE_DELETED. Removing: VALUE_SET if lower layer surfaces, otherwise no event. |
| Blanket tombstones | Yes | Masks all lower-precedence values on key | No | Writing: VALUE_DELETED per masked value. Removing: VALUE_SET per surfaced value. |
| Key hiding (HIDDEN) | Yes | Masks lower precedence | No | Writing: SUBKEY_DELETED. Removing: SUBKEY_CREATED if lower layer surfaces, otherwise no event. |
| Key GUID | No | Direct on key object | Yes | N/A (identity, not state) |
| Security Descriptor | No | Direct on key object | Yes | SD_CHANGED |
| Volatile flag | No | Direct on key object | Yes | N/A (set at creation) |
| Symlink flag | No | Direct on key object | Yes | N/A (set at creation) |
| Last write time | No | Direct on key object | Yes | N/A (informational) |
| Watch binding | N/A | Object-bound (GUID), not path-bound | Watch stays on original object | N/A |

## Invariants

The following invariants hold at all times. Violations are
implementation bugs.

1. **Two-level hierarchy.** The registry is keys and values. Keys
   are containers. Values are named, typed data within keys. This
   is a hard constraint from registry.pol compatibility.

2. **Security at key level.** Values inherit their key's access
   control. There is no per-value SD.

3. **Single authority.** LCS is the sole registry authority. All
   access control, path resolution, watch delivery, and layer
   resolution happens in the kernel. Sources are storage backends.

4. **Identity capture at syscall boundary.** The kernel captures the
   calling thread's token (including impersonation tokens) at the
   syscall boundary. Sources never see caller identity.

5. **Fd-based access.** Every open key is an fd. Access is checked
   once at open time and cached on the fd.

6. **Hive isolation.** Each hive is backed by exactly one source.
   A source may back multiple hives. Transactions are hive-scoped.

7. **Volatile parent, volatile children.** Children of volatile keys
   MUST be volatile. A non-volatile key MUST NOT be created under a
   volatile parent.

8. **Symlinks are privileged.** Symlink creation requires
   KEY_CREATE_LINK on the parent and SeTcbPrivilege or Administrator group
   membership.

9. **Case-preserving, case-insensitive.** All path and value name
   comparisons are case-insensitive. Stored names preserve original
   case. Non-negotiable for registry.pol compatibility.

10. **Global sequence counter.** LCS maintains a single monotonic
    sequence counter across all sources. Every mutation (path entry
    creation, value write, key hiding) is assigned a sequence number
    from this counter. The counter provides deterministic tiebreaking
    within a precedence tier.
