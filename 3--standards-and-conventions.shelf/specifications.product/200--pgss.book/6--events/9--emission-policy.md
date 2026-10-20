---
title: Emission Policy
description: How an event type is switched on or off — the per-segment Enabled values under Machine\Generic\Events, the walk that resolves them, tier defaults, essential types, the AND with SACLs and audit policy, noticing a change, and what an emitter does when it cannot read the policy.
---

An event type that is switched off is never written. Each emitter
decides, before it writes an event, whether its type is on, from a policy
kept in the registry. A consumer decides what to keep of what it reads;
it does not decide what is written.

The component that writes a record decides, whatever path the record
takes. A component that writes records of its own without going through
the kernel's event stream, straight into a store for example, is their
emitter for the purposes of this section, and applies the policy to
every type it writes that is not essential.
[*events.policy.whoever-writes-a-record-applies-the-policy]

## The policy tree

The policy is the registry key `Machine\Generic\Events` and the keys
beneath it. There is one key per segment of an event type, so the
policy for an event type is found on the path that spells its segments
beneath `Events`, one key each, in order: the policy for
`kacs.audit.access.checked` is found by walking
`Events\kacs\audit\access\checked`.
[*events.policy.one-key-per-segment]

A package-name root (§6.3) is split at its periods like the rest of the
type, so a package's events sit beneath one key per segment of its
name: `org.jellyfin.server.playback.started` is found by walking
`Events\org\jellyfin\server\playback\started`, and `Events\org\jellyfin`
is the key that covers every package named beneath `org.jellyfin`. A
segment is used as it is, including one a package name gives that the
segment grammar of §6.3 does not admit.
[*events.policy.package-root-splits-per-segment]

The registry compares key and value names ignoring case, so the walk
does too.

Any key on such a path MAY hold a value named `Enabled`. A `REG_DWORD`
of `1` switches the event types beneath it on, and `0` switches them
off. An `Enabled` value of any other type, or a `REG_DWORD` holding any
other number, is ignored, as though it were absent.
[*events.policy.other-enabled-values-are-ignored]

Nothing else in the tree has a meaning. A key on no event type's path,
and any value other than `Enabled`, decides nothing.

## Resolving a type

Whether an event type is on is decided by this procedure. The deepest
`Enabled` value on the type's path wins, and the type's tier decides when
there is none.

```text
enabled(event_type, tier) → bool
    if tier == essential
        return true                       // never consults the policy
    setting = absent
    key = Machine\Generic\Events          // absent if it does not exist
    for each segment in segments(event_type)
        if key == absent
            break
        setting = read_enabled(key, setting)
        key = subkey(key, segment)        // absent if it does not exist
    if key != absent
        setting = read_enabled(key, setting)
    if setting != absent
        return setting == 1
    return tier == standard               // standard on; verbose and debug
                                          // off; essential returned above

read_enabled(key, current) → setting
    value = value(key, "Enabled")         // absent if it does not exist
    if value is REG_DWORD and (value == 0 or value == 1)
        return value
    return current                        // ignored: keep what was found
```

Each rule of the procedure holds on its own:

- The `Enabled` value on the deepest key that has one decides. A
  value on `Events` itself applies to every type the keys beneath it
  do not decide. [*events.policy.deepest-enabled-wins]
- The key named by the whole type, its last segment included, is read
  like the keys above it. [*events.policy.the-types-own-key-counts]
- Where a key on the path does not exist, the keys beneath it do not
  either, and the deepest value found above it decides.
  [*events.policy.a-missing-key-ends-the-walk]
- A key the emitter may not read ends the walk as a missing one does.
  [*events.policy.an-unreadable-key-ends-the-walk]
- With no `Enabled` value on the path, a `standard` type is on, and a
  `verbose` or `debug` type is off (§6.8).
  [*events.policy.tier-decides-when-nothing-is-set]

An emitter MUST NOT write an event whose type this procedure finds off.
[*events.policy.an-off-type-is-not-written]

An emitter MUST write an essential event without consulting the policy,
whatever the tree holds. [*events.policy.essential-never-consults]

An emitter SHOULD make the decision before it builds the event's
payload, so that a type that is off costs nothing beyond the decision.
[*events.policy.decide-before-building]

### Example

With no value on `Events`, `Events\kacs` holding `Enabled = 0`, and
`Events\kacs\audit` holding `Enabled = 1`:

| Event type | Tier | Decided by | On |
|---|---|---|---|
| `lcs.config.value.rejected` | `standard` | its tier | Yes |
| `kacs.caap.staging.diverged` | `standard` | `Events\kacs` | No |
| `kacs.audit.handle.used` | `standard` | `Events\kacs\audit` | Yes |
| `kacs.audit.access.checked` | `essential` | its tier, always | Yes |

With `Enabled = 0` on `Events` as well, `lcs.config.value.rejected` is
off and the other three are as before. A `verbose` or `debug` type in
the place of `lcs.config.value.rejected` would be off in both trees, and
in the place of `kacs.audit.handle.used` on in both.

## Gating, SACLs and audit policy

For an event type with gating (§6.2), the policy and the gating decide
together, by AND: the type is written for an occurrence only if the
policy has it on and its gating asks for that occurrence.
[*events.policy.policy-and-gating-combine-by-and]

Neither widens the other. Switching a type on does not record an
occurrence that a SACL, or a token's audit policy, does not ask for; and
a SACL that asks for an occurrence does not record it while the policy
has its type off. The policy decides whether a kind of event exists at
all. The gating decides which occurrences of it are recorded, and only
the emitter can evaluate it, because only the emitter can see the
object.

An essential type's gating alone decides, because the policy never
switches it off (§6.8). The kernel's access audit is the case this is
for: `kacs.audit.access.checked` is essential, so whether an access
decision is recorded is the SACL's and the audit policy's choice alone,
and an administrator never has to switch the same thing on in two
places.

## Noticing a change

An emitter MAY cache the policy in-process.

An emitter MUST apply a change to the policy to every decision it makes
one second or more after the change was committed, whether or not it
caches. [*events.policy.a-change-applies-within-one-second]
An emitter SHOULD apply it to the first decision it makes after the
commit, which an emitter that watches the tree can do.

A watch on the subtree of `Events` sees every change. An emitter that
writes under few roots MAY instead watch only the keys on its own types'
paths. A key that does not exist cannot be watched, so an emitter
watching for one to be created watches the nearest key above it that
does exist.

A change is not retroactive. An event written before it stays written,
and an occurrence decided before it stays decided.

## When the policy cannot be read

An emitter that cannot read `Machine\Generic\Events` — before the
registry has a source for the `Machine` hive, where the key does not
exist, or where it may not read it — MUST decide by tier alone, as the
procedure does when no `Enabled` value is found.
[*events.policy.an-unreadable-policy-falls-back-to-tier]

It MUST NOT hold an event back to wait for the policy to become
readable. [*events.policy.no-waiting-for-the-policy]

Once the policy can be read, an emitter MUST apply it to every decision
it makes one second or more after it became readable.
[*events.policy.a-readable-policy-applies-within-one-second]

> [!NOTE]
> The kernel writes events from early in boot, before any registry
> source has registered. For that window its decisions are tier
> defaults: a `verbose` type the policy switches on is not written, and
> a `standard` type the policy switches off is. An operator who needs a
> boot-time event whatever the policy says has the essential tier, if
> the event meets one of its two reasons (§6.8), and nothing else.

## Who may change it

Each key's security descriptor decides who may change the policy beneath
it, and inheritance carries that down the tree. This is why the policy
has one key per segment rather than one flat key per pattern: a grant on
`Events\org\jellyfin` lets whoever runs Jellyfin switch its events, and
reaches nothing else.

A conforming system:

- lets every emitter read `Machine\Generic\Events` and every key beneath
  it; [*events.policy.every-emitter-may-read-the-tree]
- lets only administrators write `Machine\Generic\Events` itself, and the
  keys of platform roots (§6.A);
  [*events.policy.only-administrators-write-platform-keys]
- SHOULD give `Machine\Generic\Events` a SACL that audits writes, so that
  a change to what is recorded is itself recorded.

> [!NOTE]
> Leaving the decision to the consumer was considered and rejected. The
> kernel's event stream drops its oldest events when a ring is full,
> whatever they are, so events nobody wanted would push the audit trail
> out of the ring. They would also cost an encoding on hot paths, and
> every reader of the ring would still see them.
