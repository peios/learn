---
title: Emission Policy
description: How the kernel decides which of its own event types are switched on — the generated type table, the cached enabled mask, the walk of Machine\Generic\Events, the watch that keeps it current, and the tier defaults it runs on until the registry can be read.
---

An event type that is switched off is never written. PGSS §6.9 defines
the policy: a tree of keys under `Machine\Generic\Events`, one per
event-type segment, any of which may hold an `Enabled` `REG_DWORD` of
0 or 1, where the deepest value on a type's path decides and the
type's tier decides when there is none. This section is how the kernel
applies that policy to the event types it writes itself. Userspace
components apply it to their own types through libpeios, peios-rs and
libp-go; KMES does not enforce the policy on what userspace emits.

## The kernel's event types

The kernel writes a closed set of event types, fixed when it is built.
They are generated from the kernel's own evman fragments
(`pkm/evman/*.evman`) by `tools/gen-kmes-event-table.py` into a C
header and a matching Rust module, each type with an id, its type
string and its tier. The generator has a `--check` mode, so a type
cannot change tier in its fragment without the kernel's table
following. [*policy.closed-kernel-type-table]

The policy is cached as a 64-bit mask with one bit per kernel type:
bit *i* set means type *i* is switched on. A walk of the registry
computes a whole new mask and publishes it with a single store, and an
emitter reads it with a single load, so a decision is a load and a bit
test and no lock is taken on any emission path. A mask is never
published half-computed. [*policy.mask-one-bit-per-type]

An emitter asks before it builds a payload, with
`pkm_kmes_event_enabled(id)`, and Rust emitters through the generated
module's `enabled()`. An `essential` type's tier is a compile-time
constant, so the check for it folds to *on* when the emitter is
compiled and never reads the mask: no policy can switch an essential
type off, whatever the tree holds. [*policy.essential-never-consults]
The policy and an event type's own gating — a SACL, an alarm mask, a
`REPORT` level — combine by AND, the policy first because it is the
cheaper of the two.

Every kernel emitter makes the check, and makes it first: before it
resolves the subject, looks up a path, sizes the payload or allocates
anything. A type that is switched off therefore costs one check and
nothing else, and the emitter carries on as though the record had been
written. Each emitter names its type with the generated table's string
rather than one of its own, so the type written and the type the policy
decided on cannot drift apart.

> [!NOTE]
> `kacs.impersonation.reverted` is the kernel's one `verbose` type, so on
> a machine whose policy says nothing about it, it is not written. An
> administrator who wants each revert recorded sets `Enabled` to 1 on
> `Machine\Generic\Events\kacs\impersonation\reverted`, or on a key
> above it.

## Before the policy can be read

From the moment PKM initialises until a registry source for the
`Machine` hive has registered and the first walk has finished, the
mask holds the tier defaults: every `essential` and `standard` type on,
every `verbose` and `debug` type off. That is PGSS §6.9's rule for an
emitter that cannot read the policy, and the kernel writes events from
long before any source exists, so it is the policy the kernel runs on
for the whole of early boot. No event is ever held back to wait for
the registry. [*policy.early-boot-tier-defaults]

A `verbose` type the registry switches on is therefore not written
before the walk, and a `standard` type the registry switches off is. A
boot-time event that must be written whatever the policy says has the
`essential` tier and nothing else.

If `Machine\Generic\Events` does not exist, no `Enabled` value can be
found anywhere and the tier decides for every type: the kernel
publishes the tier defaults. A bootstrap refresh that finds the key
gone after it existed does the same, so deleting the key undoes the
policy it held. [*policy.absent-key-is-tier-defaults]

## The walk

One walk resolves every kernel type at once. It reads `Enabled` on
`Machine\Generic\Events` itself, then descends the trie of the kernel
types' segments — `kacs`, `kacs\audit`, `kacs\audit\access` and so on
— looking up only the keys some kernel type's path passes through.
Each key that exists costs one `RSI_LOOKUP` and one `RSI_QUERY_VALUES`.
[*policy.walk-follows-kernel-types]

A key that does not exist ends the walk down that path, and nothing
beneath it is asked for: an empty `Events` key costs one query and one
lookup per root. A key that is a link is not followed and ends the
walk the same way. [*policy.missing-key-ends-walk]

Only an `Enabled` value that is a `REG_DWORD` holding 0 or 1 is a
setting. A value of another type, of the wrong length, or holding any
other number is ignored as though it were absent, and the setting
found above it stands. Nothing reports the ignored value. Value names
compare ignoring case, as the registry does.
[*policy.enabled-dword-only]

From what it read the walk computes the mask by PGSS §6.9's procedure:
for each type, the `Enabled` on the deepest existing key on its path
decides; with none, the tier decides; an essential type is on. The
mask is then published. [*policy.resolution] [*policy.walk-publishes]

A walk that fails — the source does not answer in time, or answers
with something malformed — publishes nothing. The mask in force stays,
whether that is the tier defaults or the last mask a walk computed,
and a `kmes.config.refresh.failed` record names
`Machine\Generic\Events` and the error. [*policy.failed-walk-keeps-mask]

## Noticing a change

At bootstrap, after the KMES, layer, port reservation and network
policy keys, LCS discovers `Machine\Generic\Events` and walks it. If
it exists it gets an internal watch of its own; if not, the machine
root fallback watch stays armed (LCS §5.10.4), and creating the key —
`Generic` and `Events` two levels below `Machine`, with or without
`Generic` already there — re-runs the bootstrap, which then walks it
and watches it. [*policy.discovered-at-bootstrap]

The watch covers the whole subtree at any depth, but it passes on only
what can change a kernel type: a change on `Events` itself, a change
beneath one of the kernel's five roots (`kacs`, `kmes`, `lcs`, `ntfe`,
`stratafs`), and among value changes only those to a value named
`Enabled`. A vendor writing under `Events\org\…`, which PGSS §6.9
lets an emitter ignore, costs the kernel nothing.
[*policy.watch-filtered-to-kernel-roots]

What the watch passes on is coalesced. The first change of a burst
schedules one re-walk 50 ms later; changes that arrive before it runs
join it rather than postponing it, and a change that arrives while a
walk is running schedules the next one. **A change to the policy
applies within about 50 ms plus one walk** of the write that made it —
or, when a walk is already in progress, after that walk and one more —
however busy the tree is, which is inside PGSS §6.9's one second.
[*policy.change-applies-within-50ms-plus-one-walk]

A change is not retroactive. An event already written stays written,
and a decision made before the walk publishes stays made.

## The shipped seed

The kernel package ships a registry seed, `event-policy.reg` in
`/usr/share/regim/`, that creates `Machine\Generic\Events` and sets no
`Enabled` anywhere: with nothing set, the tiers decide, which is the
policy a machine ships with. The key is there so the policy has a home
for an administrator to write beneath. Like every seed it is inert
until an image names it in `[registry] autoapply`, and until then
every emitter decides by tier just the same. [*policy.seed-creates-key-without-enabled]

The seed gives the key the SACL PGSS §6.9 asks for, one that audits
writes: `S:(AL;CI;0x10002;;;WD)`, a `SYSTEM_ALARM` ACE for Everyone,
inherited by every key beneath, over `KEY_SET_VALUE | DELETE`. A handle
opened for writing anywhere in the policy tree carries that
continuous-audit mask, so each change to what is recorded can itself be
recorded. Only the SACL is set; the owner and DACL stay inherited from
the `Machine` hive. [*policy.seed-sacl-audits-writes]
