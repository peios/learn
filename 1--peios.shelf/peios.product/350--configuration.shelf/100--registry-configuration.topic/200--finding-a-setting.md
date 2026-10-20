---
title: Finding a Registry Setting
type: how-to
description: Identify the owner, scope, and live state of a setting before changing it.
related:
  - peios/registry-configuration/changing-a-setting
  - peios/registry-tools/regman
---

Find a setting by its purpose and consuming component. A path can contain
operator configuration, a runtime observation, or personal preferences;
those are different kinds of data.

## Find and inspect

1. Search installed manuals with a term from the setting's purpose:

   ```sh
   regman -k buffer
   ```

2. Read the matching key and value documentation. Confirm its owner, scope,
   type, accepted values, and application timing.
3. Inspect live state with `reg` or Registry Editor. Keep the key path and
   value name separate. A documented default can apply even when no live
   entry exists; do not create one solely because it appears in the manual.
4. Follow [Changing a Registry
   Setting](~peios/registry-configuration/changing-a-setting) when the intended
   change and recovery are understood.

## Common owners

| Purpose | Starting location | Owning guidance |
|---|---|---|
| Service definitions | `Machine\System\Services` | [Service configuration](~peios/services-and-jobs/registry-key-reference) |
| Boot and init settings | `Machine\System\Init` | [Boot modes](~peios/services-and-jobs/boot-and-boot-modes) |
| Network profiles and reported state | `Machine\System\Network` | [Profiles](~peios/networking/configuring-profiles) and [name resolution](~peios/networking/name-resolution) |
| Shared authentication grants | `Machine\Generic\Authn\Policy` | [Granting Access](~peios/authentication-policy/granting-access) |
| authd source registration | `Machine\Software\Authd\Sources` | [Registering a Principal Source](~peios/authentication-policy/registering-a-source) |
| Personal preferences | `Users\<SID>` | The component consuming the particular key |

This is an orientation map, not a complete schema. A shared format under
`Machine\Common`, such as `SecurityDescriptorBuilder`, is still defined by
its consumers' documentation; it is not automatically part of a specification.
Use the installed manual for the specific value.

## Identity and reported state

`CurrentUser` is an alias resolved from the calling thread's effective token.
A service or impersonating thread can therefore address a different account
from an interactive shell. The kernel's [hive routing
reference](~kernel/internals/lcs/data-model/hives-and-routing) defines the
alias's limits. It is not a separate hive or a universal substitution inside
every stored string.

Machine-to-user fallback is consumer-specific. [Session
locales](~peios/session-settings/session-locales) combine corresponding
machine and personal values; that rule does not apply to unrelated settings.

Services also publish facts. For example, netd's status and readiness describe
observed network state. Change its documented profiles to request behavior;
do not edit a reported address and assume that it configures an interface.
Remembered DNS observations are distinct from active resolver state and
configured resolver overrides.

## Missing or unreadable

A missing manual entry can mean documentation is absent. A missing live value
can select a documented fallback. Access denied means the caller lacks the
right for that operation; listing a parent does not establish access to a
child's contents.

Check the actual descriptor. There is no universal rule that every registry
key is readable by everyone, and knowing a path grants no access to it.
