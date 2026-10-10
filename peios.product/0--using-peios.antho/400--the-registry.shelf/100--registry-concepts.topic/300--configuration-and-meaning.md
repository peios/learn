---
title: Change a setting and verify it
type: how-to
description: Look up a setting, record its current state, make a typed change, and distinguish registry read-back from consumer acceptance.
related:
  - peios/registry-concepts/keys-values-and-types
  - peios/registry-administration/regman
  - peios/registry-concepts/watches
  - peios/registry-administration/bootstrap-and-self-configuration
  - peios/auditing/overview
  - peios/registry-concepts/overview
---

A registry write changes stored configuration. The program that reads it
still decides whether it is valid and when to use it. Treat a change as
finished only after checking both the stored result and the consumer.

## 1. Look up the setting

```sh
regman 'Machine\System\KMES' BufferCapacity
```

Read the expected **Type**, **Default**, **Valid** range and **Applies**
field. In this example, the documented type is `REG_QWORD`; the value is a
power-of-two buffer capacity and applies live. Other settings may apply
only on service restart or reboot.

`regman` reads package documentation, not the live registry. If it has no
entry, find the owning component's documentation before changing the
value. An undocumented setting is not evidence that any type or value is safe.

## 2. Inspect and prepare recovery

```sh
reg ls Machine/System/KMES -l
reg get Machine/System/KMES BufferCapacity -L
```

Record the effective value, type and winning layer. `-L` shows only the
winner, not every shadowed entry. If the setting is absent, record that
fact too; writing the documented default is not the same as leaving it unset.

Choose the layer to write into, check [permissions](~peios/registry-security/access-control),
and decide how you will recover. Use a [backup](~peios/registry-administration/backup-and-restore)
when you need the subtree's permissions and layered entries retained.
A JSON export is useful for review but is not an equivalent backup.

## 3. Make the smallest intended change

For example, after deciding an 8 MiB buffer is appropriate for this machine:

```sh
reg set Machine/System/KMES BufferCapacity qword:8388608 --layer base
reg get Machine/System/KMES BufferCapacity -L
```

The type is explicit and the destination is explicit. A higher-precedence
layer can still win, so read-back may show a different value. See
[Layers](~peios/registry-layers/layers) before rewriting the setting repeatedly.

For a guarded update, `reg set --expected-seq N` can reject a concurrent
change with exit status `6`. The check is against the destination layer's
entry: use the sequence from `reg get -L` only when that winning entry is
in the layer you intend to write. If it is not, the effective sequence is
not a sequence for your target layer. See [`reg`](~peios/registry-tools/reg#reg-set-key-value-data)
and the [transaction notes](~peios/registry-advanced/transactions).

## 4. Verify that the consumer accepted it

1. Confirm the effective value and type with `reg` or Registry Editor.
2. Follow **Applies**: allow the live consumer to process the change, or
   arrange its documented restart or reboot if required.
3. Inspect that component's status and relevant events. A watch notification
   or a successful `reg set` is not an acceptance acknowledgement.
4. Test the behavior the setting was intended to change.

Use the [event and audit guides](~peios/auditing/overview) for reading
records. Do not treat silence in the log alone as proof of acceptance.

## If the stored value is rejected

Consumers validate their configuration. Under **reject-or-keep**, a
rejected setting remains stored while the consumer keeps its last
known-good value and logs the rejection. It does not clamp or silently
repair the invalid value.

Check the event for the rejected value and the retained value. Correct the
type or data according to the component's manual, then repeat both checks.
The consumer's documented fallback matters: for example,
[SdDefaults](~peios/registry-security/default-security-descriptors) uses a
compiled descriptor when an override is invalid.

## Registry settings follow the same check

LCS reads its own settings under `Machine\System\Registry`. It validates
changes before using them and logs rejections. Deleting one of these
values does not necessarily reset the running parameter: the documented
LCS behavior is to retain the last active value when a parameter is
missing. See [Registry startup and configuration](~peios/registry-administration/bootstrap-and-self-configuration).

## If the write fails or times out

A write can fail because of access, input, capacity or source errors.
Use the [`reg` exit-status reference](~peios/registry-tools/reg#exit-status)
to distinguish them. After a timeout or source failure, read the affected
state before retrying: a dispatched write or commit may still have succeeded.

## Recover deliberately

- For an isolated edit, restore the intended value in the intended layer
  and verify the consumer again.
- To withdraw a layer's entry, use [per-layer deletion](~peios/registry-layers/deleting-keys-and-values).
- To remove a bundle of configuration, review [layer recovery](~peios/registry-layers/what-layers-are-for).
- To replace a damaged subtree from a snapshot, follow
  [backup and restore](~peios/registry-administration/backup-and-restore).

Removing configuration does not reverse changes to a key's security
descriptor or undo effects already performed by a consumer.
