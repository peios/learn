---
title: Changing Default Security Descriptors
type: how-to
description: Distinguish a supported creation-time descriptor override from the permissions already applied to objects.
related:
  - peios/registry/changing-a-setting
  - peios/authentication/granting-access
---

A component can accept a security descriptor to apply when creating or
preparing an object. Such a setting is policy for that component; it is not a
registry feature that rewrites objects automatically.

## Before you start

Find a documented override for the object in the component's registry manual.
The proposed `Machine\Software\<Software>\SdDefaults` convention is not
implemented universally. Creating a plausible key does nothing unless the
component reads it. In particular, Peinit's static device-node policy uses
compiled descriptors; a planned override name in its source is not an active
setting.

Read when the component applies the descriptor and how it handles absent or
invalid input. Do not assume every descriptor setting has the same fallback:
rejection, retaining a prior value, and using a compiled default are distinct
policies.

## Change and verify the default

1. Record the existing override, including whether it is absent, and the
   actual descriptor on the affected object.
2. Prepare the component's documented recovery path. Preserve the previous
   descriptor separately if permission changes need to be undone.
3. Change only the supported setting, with its documented type and layer.
4. Use the component's normal creation or preparation workflow. Do not
   delete a live state file merely to force it to be recreated.
5. Inspect the resulting object's descriptor and component diagnostics.
   Test the intended reader and writer identities, not only an administrator.

Valid descriptor syntax does not establish that its grants are appropriate.
A fallback after invalid input can also differ from the intended policy.

## What does not follow from an override

Changing the stored default does not automatically update existing objects
or descendants that already inherited permissions. Removing the registry
layer cannot undo descriptors stamped while that layer's value was effective.

The registry key's own permissions govern who can edit the configuration.
A descriptor stored as a value governs the different object whose creator
reads it. Review both boundaries; changing **Permissions…** on the key is
not the same operation as editing the stored descriptor.

Bootstrap descriptors, kernel mount-policy templates, and package payload
permissions have their own owners and application points. A token's
`DefaultDacl` is another mechanism, supplied by [authentication
policy](~peios/authentication/granting-access#defaults-for-newly-created-objects).
Do not substitute one mechanism for another without the consumer's explicit
support.
