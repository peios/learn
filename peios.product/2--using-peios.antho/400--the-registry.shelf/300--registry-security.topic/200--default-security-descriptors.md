---
title: Default security descriptors
type: how-to
description: Inspect a component’s SdDefaults overrides, check when new objects receive them, and avoid mistaking a default change for existing-object permission repair.
related:
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-security/access-control
  - peios/registry-administration/regman
  - peios/security-descriptors/overview
  - peios/security-descriptors/inheritance
---

An **SdDefaults** value tells a component which security descriptor to
stamp on an object it creates. Changing it affects future stamping; it
does not repair the permissions of objects already on disk or in memory.

<a id="default-security-descriptors-in-one-sentence"></a>
<span id="default-security-descriptors--default-security-descriptors-in-one-sentence"></span>
<span id="registry-security-default-security-descriptors--default-security-descriptors-in-one-sentence"></span>
<span id="using-peios-registry-security-default-security-descriptors--default-security-descriptors-in-one-sentence"></span>
<a id="the-convention"></a>
<span id="default-security-descriptors--the-convention"></span>
<span id="registry-security-default-security-descriptors--the-convention"></span>
<span id="using-peios-registry-security-default-security-descriptors--the-convention"></span>
## Find the component's default

The convention is a named `REG_SZ` value containing SDDL under:

```text
Machine\Software\<Software>\SdDefaults
```

The value name identifies the object, such as `SpoolDirectory`, `StateFile`
or `Run`. These are examples, not names every component provides. Each
component keeps its own names beside its own configuration.

Use `regman` for the exact key and value before editing it. Read its
**Applies** field: the relevant object may be stamped at startup, on a
mount, or only when it is first created. Inspect the current override
with `reg get` or Registry Editor, and record whether it was absent.

## Compiled default, registry override

| Override state | Descriptor the convention selects |
|---|---|
| Absent | The component's compiled-in default. The key need not exist. |
| Present and valid SDDL | The registry override. |
| Invalid | The compiled-in default, with an event identifying the rejection and descriptor in force. |

An invalid descriptor is not repaired or broadened automatically. This
fallback does not prove that the policy is the one you intended: inspect
the rejection event and verify the actual descriptor on the created object.
A syntactically valid descriptor can also grant more access than intended,
so validity alone is not a security review.

## When a change takes effect

1. Read the value's manual and understand when its component stamps the object.
2. Save the old value and the relevant recovery state.
3. Make the intended SDDL change with the correct type and destination layer.
4. Let the component create or stamp an object through its documented workflow.
5. Inspect that object's actual permissions and the component's events.

Changing the default does not rewrite existing objects. Children inherit
from their parent at creation, so existing descendants are not updated
either. Do not delete a live object merely to force restamping without
understanding that component's recovery procedure.

Layer removal can remove the override value, but it cannot undo descriptors
already stamped onto objects while the override was effective. This is
separate from the rule that a registry key's own descriptor is
[not layered](~peios/registry-security/access-control#the-sharp-edge-security-is-not-layered).

## The values are access policy — protect them

Whoever can write these values controls access to objects the component
will create. The convention protects the `SdDefaults` key so only SYSTEM
and Administrators can write. Check its actual permissions and the
[write destination layer](~peios/registry-security/access-control).

Do not confuse the key's **Permissions…** with the descriptor stored as a
value: the first governs who may change configuration, while the second
is consumed as policy for another object.

## What the convention does not cover

- **Bootstrap seeds:** descriptors needed before a registry source exists
  are compiled into the tools that stamp them.
- **Kernel fallback templates:** fixed fallbacks used when mount policy has
  no template are not SdDefaults settings. An object created without a
  parent instead uses the creating token's default DACL; `authd` obtains
  that from the principal's `DefaultDacl` policy value. A token with none
  leaves such an object with a null DACL. See
  [Assigning privileges](~peios/privileges/assigning-privileges).
- **Package payload files:** these inherit at their destination or use a
  package-manifest descriptor declaration; see
  [PSPU §5.20](~peios/package-format-and-repository-protocol/security-descriptor-overrides).

## For component authors

The convention requires a reviewed compiled default for each object-named
value, fallback to that default with a recorded rejection for invalid
SDDL, and a `regman` entry specifying when it is stamped. Do not substitute
a broader policy on parse failure.

## Where to go next

- [SDDL and security descriptors](~peios/security-descriptors/overview)
- [Inheritance](~peios/security-descriptors/inheritance)
- [Make and verify registry changes](~peios/registry-concepts/configuration-and-meaning)
