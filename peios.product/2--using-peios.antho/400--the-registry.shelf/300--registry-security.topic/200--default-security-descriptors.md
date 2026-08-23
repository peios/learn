---
title: Default security descriptors
type: concept
description: Where a component keeps the security descriptors it stamps at runtime — the SdDefaults convention — and the reject-or-keep rule that guards it.
related:
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-security/access-control
  - peios/registry-administration/regman
  - peios/security-descriptors/overview
  - peios/security-descriptors/inheritance
---

Some software stamps [security descriptors](~peios/security-descriptors/overview) onto objects it creates at runtime — a freshly mounted filesystem root, a state file, a spool directory. Each of those descriptors is a policy decision: who can enumerate this directory, who can read this file, what everything created beneath this root will inherit. Decisions like that are configuration, and in Peios configuration has one home. The **SdDefaults** convention is the standard place a component keeps these descriptors, so that an operator can inspect them, change them, and trust that every component publishes them the same way.

## Default security descriptors, in one sentence

**A component keeps each security descriptor it stamps at runtime as a named SDDL value under `Machine\Software\<Software>\SdDefaults\`, with a compiled-in copy as the fallback — a value that is present and valid overrides the compiled default; a value that is invalid is ignored, loudly.**

## The convention

```
Machine\Software\<Software>\SdDefaults\<SD Name>
```

- `Machine\Software\<Software>` is the component's own configuration key — the same key the rest of its settings live under.
- `SdDefaults` is the literal subkey name.
- `<SD Name>` names the object the descriptor protects: `SpoolDirectory`, `StateFile`, `Run`. One value per descriptor, stored as a string containing SDDL.

A fictional spooler that creates its spool directory at startup would publish:

```
Machine\Software\ExampleSpooler\SdDefaults\SpoolDirectory
    REG_SZ  "O:SYG:SYD:(A;OICI;GA;;;SY)(A;OICI;GA;;;BA)"
```

The defaults are **per component, deliberately**. A single shared tree of default descriptors would need every SD name to be unique across every application ever written — a namespacing promise nobody can keep. Scoping the names under the component that reads them dissolves the problem, and it keeps discovery unsurprising: a component's descriptors live where the rest of its configuration lives.

## Compiled default, registry override

The registry value is an override, never the only copy. Every component that follows the convention carries a compiled-in default for each named descriptor, and resolves the one to use at the point where it stamps it:

| State of `SdDefaults\<SD Name>` | Descriptor in force |
|---|---|
| Absent | The compiled-in default. This is the normal state — the key need not exist at all. |
| Present, valid SDDL | The registry value. |
| Present, invalid | The compiled-in default. The stored value is ignored, and an event records the key, the rejected value, and the descriptor actually in force. |

This is the registry's general [reject-or-keep](~peios/registry-concepts/configuration-and-meaning) rule applied to descriptors, and here it is doing its most important work. A security descriptor that fails to parse is never repaired, never approximated, and never replaced with something broader: the descriptor in force is always one that was compiled in and reviewed. A typo in an SdDefaults value costs you your customisation, not your system.

## When a change takes effect

A default descriptor is read when the component stamps it — typically when the object is created. Two consequences follow:

- Changing a value affects objects stamped **after** the change. It does not rewrite objects that already exist.
- Where the stamped object is a directory whose descriptor carries inheritable ACEs, everything created beneath it derives its descriptor at creation time ([inheritance](~peios/security-descriptors/inheritance) is computed once, when the child is born). Changing the default later does not re-derive existing children.

So the honest answer to "when does my change apply?" varies by descriptor — next boot, next mount, next time the object is recreated — and the component's [`regman`](~peios/registry-administration/regman) documentation is where that answer lives. Every `<SD Name>` a component publishes has a regman entry, and its `Applies` line states exactly this.

## The values are access policy — protect them

Whoever can write a component's SdDefaults values decides what access the component will grant on the objects it creates. These values are not settings *about* security; they **are** the security. A component's `SdDefaults` key therefore carries a tight security descriptor of its own — writable by Administrators and SYSTEM, no wider — which the registry enforces like [any other key](~peios/registry-security/access-control). The arrangement is self-hosting: the store that holds the descriptors is protected by the same mechanism the descriptors configure.

## What the convention does not cover

**Bootstrap seeding.** The very first descriptors of a boot — the seed stamped onto a fresh root before any registry source is attached — are compiled into the tools that write them, and are not customisable through the registry. There is no registry to read at that point in boot; that is not a gap in the convention but the reason it has a floor.

**Kernel fallbacks.** The descriptors the kernel synthesises when a mount policy has no template, and the default DACL applied when a created object has no parent to inherit from, are fixed. They are the floor under a missing policy, not configuration.

**Files installed by packages.** A package payload entry gets its descriptor by inheritance from its destination directory, or from a declaration in the package manifest — see [PSPU §5.20](~peios/package-format-and-repository-protocol/security-descriptor-overrides). SdDefaults governs what software stamps at runtime, not what the package manager installs.

## For component authors

If your component stamps descriptors at runtime, follow the convention:

1. Ship a compiled default for every named descriptor. The registry value is an override; your component must work, with reviewed policy, on a system where the `SdDefaults` key has never been created.
2. Name each value for the object it protects, not for its content — `SpoolDirectory`, not `SystemOnlyOici`.
3. Resolve with reject-or-keep. An unparseable value is ignored in favour of the compiled default, and the rejection is recorded in an event naming the key, the rejected value, and the descriptor in force. Never substitute anything broader than the compiled default.
4. Document every name in `regman`, including an `Applies` line that says when a change is picked up.

## Where to go next

For the doctrine behind reject-or-keep — why the registry stores values it does not validate, and why readers keep their last known-good — read [Configuration, not storage](~peios/registry-concepts/configuration-and-meaning).

For what an SDDL string actually says — owner, DACL, ACEs, and the inheritance flags that make one descriptor govern a whole tree — start at [Security descriptors](~peios/security-descriptors/overview) and [Inheritance](~peios/security-descriptors/inheritance).

For protecting the `SdDefaults` key itself, read [Access control on keys](~peios/registry-security/access-control).
