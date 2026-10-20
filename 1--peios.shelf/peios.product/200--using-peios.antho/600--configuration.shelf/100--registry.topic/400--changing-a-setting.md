---
title: Changing a Registry Setting
type: how-to
description: Verify a setting's documentation, stored value, and consuming component as separate steps.
related:
  - peios/registry/finding-a-setting
  - peios/registry/reg
  - peios/registry/changing-registry-values
---

A registry write changes stored configuration. Its consumer still decides
whether the data is valid and when to apply it. Verify both storage and
behavior before treating an edit as complete.

## Before you start

Find the owning component and confirm that the value is configuration rather
than a reported fact. You need access to the exact key and the destination
layer. Keep a working route to the machine if the change affects access.

Read the setting's registry manual. Record its type, valid range, default,
and application timing. `regman` reads installed documentation, not live
state. A missing manual entry is not permission to try arbitrary values.

## Inspect, change, and verify

1. Inspect the setting and its manual. For example, these commands read
   the kernel event-buffer setting without changing it:

   ```sh
   regman 'Machine\System\KMES' BufferCapacity
   reg ls Machine/System/KMES -l
   reg get Machine/System/KMES BufferCapacity -L
   ```

2. Record the current type, effective value, winning layer, and sequence.
   If the value is absent, record that instead. `-L` shows the winning
   entry; it does not enumerate every entry hidden beneath it.
3. Prepare recovery appropriate to the change. A JSON export is useful for
   review but does not preserve everything an opaque registry backup does.
   Include permissions and layer definitions when recovery depends on them.
4. Write the intended value with an explicit type and destination layer.
   For example, only after confirming that an 8 MiB event buffer is the
   intended configuration:

   ```sh
   reg set Machine/System/KMES BufferCapacity qword:8388608 --layer base
   reg get Machine/System/KMES BufferCapacity -L
   ```

5. Check the effective value and type. Follow the manual's application
   point: a live change, service restart, or reboot. Inspect the consumer's
   state and events, then test the behavior the change was intended to alter.

The desktop equivalent is [Changing Registry
Values](~peios/registry/changing-registry-values). It still requires the
same choice of layer and separate consumer check.

## Interpret a different result

A higher-precedence layer can keep a successful write from becoming the
winner. At equal precedence, write order chooses the effective entry. Do not
repeat base-layer writes to try to override stronger policy.

A conditional write checks the destination layer's entry. A sequence reported
for a winner in another layer is not a version of the entry you intend to
change. Read `reg(1)` before using `--expected-seq` in automation.

A watch notification reports a registry change, not consumer acceptance.
Some consumers reject invalid configuration and keep their last valid state;
others have a documented compiled fallback. Read the component's rule and
rejection diagnostic. Do not assume every component repairs, clamps, or
resets a value in the same way.

## Recover and check again

After a timeout or source failure, read back inspectable state before
retrying.
A dispatched write or commit can have succeeded despite a lost reply.

Restore the intended entry in its intended layer, or withdraw that layer's
entry through the supported tool. Deletion can reveal a different winner
rather than select a compiled default. Removing a layer does not restore a
key's previous security descriptor or undo actions a service already took.

Repeat both the stored-state check and the consumer check after recovery.
If storage is unavailable, start with [registry storage
failure diagnosis](~peios/registry/diagnosing-failures) instead of
editing backing databases.

## When two readers see different state

Compare effective thread credentials before comparing registry results.
A private hive can shadow the global hive, and a privately attached layer
can remain active when disabled globally. Impersonating threads in one
process need not share a view. An administrator's global read or backup
therefore need not describe a sandbox's private configuration.

The kernel defines [private hive routing](~kernel/internals/lcs/data-model/private-hives)
and [private layer attachment](~kernel/internals/lcs/layers/private-layers).
The workload's isolation mechanism controls these attachments; `reg` does
not manage them. Limits on scopes and layers can also reject an operation
without a key-permission failure.
