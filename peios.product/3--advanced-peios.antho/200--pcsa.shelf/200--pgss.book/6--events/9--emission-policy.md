---
title: Emission Policy
description: How an event type is switched on or off — the per-segment Enabled values under Machine\Generic\Events, the walk that resolves them, tier defaults, essential types, gating, caching, and delegation through key descriptors.
---

An event type that is switched off is never written. Each emitter
decides, before it writes an event, whether its type is on, from a policy
kept in the registry. A consumer decides what to keep of what it reads;
it does not decide what is written.

## The policy tree

The policy is the registry key `Machine\Generic\Events` and the keys
beneath it. There is one key per segment of an event type: the policy
for `kacs.audit.access.checked` is found by walking
`Events\kacs\audit\access\checked`, and for
`org.jellyfin.server.playback.started` by walking
`Events\org\jellyfin\server\playback\started`.

Any key on such a path MAY hold a value named `Enabled`. A `REG_DWORD`
of `1` switches the event types beneath it on, and `0` switches them
off. An `Enabled` value of any other type or number is ignored, as
though it were absent.

## Resolving a type

Whether an event type is on is decided by this procedure. The deepest
`Enabled` value on the type's path wins, and the type's tier decides when
there is none.

```text
enabled(event_type, tier) → bool
    if tier == essential
        return true                       // never consults the policy
    setting = absent
    key = Machine\Generic\Events
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

An emitter MUST NOT write an event whose type this procedure finds off.
An emitter MUST write an essential event without consulting the policy.

An emitter SHOULD make the decision before it builds the event's
payload, so that a type that is off costs nothing beyond the decision.

## Gating

For an event type with gating (§6.2), the policy and the gating decide
together: the type is written for an occurrence only if the policy has
it on and its gating asks for that occurrence. The policy decides
whether a kind of event exists at all; the gating decides which
occurrences of it are recorded, and only the emitter can evaluate it,
because only the emitter can see the object.

An essential type's gating alone decides, because the policy never
switches it off (§6.8).

## Reading and caching the policy

An emitter MAY cache the policy in-process. An emitter that caches it
MUST notice a change, by watching the keys beneath its own roots or by
an equivalent mechanism, and MUST document how long a change may take to
apply. An emitter SHOULD watch only the subtrees of its own roots.

An emitter that cannot read the policy — the kernel before the registry
is available, for example — MUST decide by tier alone, as the procedure
does when no `Enabled` value is found.

## Who may change it

Each key's security descriptor decides who may change the policy beneath
it, and inheritance carries that down the tree. This is why the policy
has one key per segment rather than one flat key per pattern: a grant on
`Events\org\jellyfin` lets whoever runs Jellyfin switch its events, and
reaches nothing else.

A conforming system:

- lets every emitter read `Machine\Generic\Events` and every key beneath
  it;
- lets only administrators write `Machine\Generic\Events` itself, and the
  keys of platform roots (§6.A);
- SHOULD give `Machine\Generic\Events` a SACL that audits writes, so that
  a change to what is recorded is itself recorded.

> [!NOTE]
> Leaving the decision to the consumer was considered and rejected. The
> kernel's event stream drops its oldest events when a ring is full,
> whatever they are, so events nobody wanted would push the audit trail
> out of the ring. They would also cost an encoding on hot paths, and
> every reader of the ring would still see them.
