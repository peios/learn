---
title: Find where a setting lives
type: how-to
description: Find a registry setting by its purpose and consumer, then distinguish shared policy, program configuration, user preferences and runtime facts.
related:
  - peios/registry-concepts/overview
  - peios/registry-concepts/keys-values-and-types
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-administration/regman
  - peios/registry-administration/registry-editor
  - peios/registry-security/access-control
  - peios/networking/network-policy-reference
---

Start with the setting's purpose and the program that reads it. Search the
installed registry manual, find the key, then inspect its live values.
A path alone does not tell you whether a value is a setting to change,
a fact published by a service, or private to one user.

## Search before changing anything

These commands only read documentation and current state:

```sh
regman -k buffer
regman 'Machine\System\KMES' BufferCapacity
reg ls Machine/System/KMES -l
reg get Machine/System/KMES BufferCapacity -L
```

1. Search installed documentation with `regman -k`, using a word from
   the setting's name or purpose.
2. Look up the returned key and value; check type, valid values, default
   and application timing. A key-only lookup lists its documented values.
3. Inspect live values with `reg`. `-L` shows the winning layer and
   sequence, not every hidden entry.

For graphical browsing, [Registry Editor](~peios/registry-administration/registry-editor)
shows the same manual beside live values. `regman` reads documentation,
not live state: a documented entry need not be set. Full command syntax
is in [`regman`](~peios/registry-tools/regman) and [`reg`](~peios/registry-tools/reg).

## Common locations

These common locations are backed by pinned source revisions, not an
exhaustive schema or a guarantee about your installed release. Check your
installed manual before changing a field.

| What you are looking for | Start here | Who gives it meaning |
|---|---|---|
| A service definition | `Machine\System\Services\<name>` | peinit reads service definitions. See the [service key reference](~peios/services-and-jobs/registry-key-reference). |
| Init-wide settings | `Machine\System\Init` | peinit reads global control limits, environment and boot-time path provisioning. |
| Network configuration and reported state | `Machine\System\Network` | netd, resolvd and policy consumers use distinct subtrees. See the [network registry layout](~peios/networking/network-policy-reference#registry-layout) for details. |
| Shared authentication policy | `Machine\Generic\Authn\Policy` | Peios policy about a principal's authority, shared across authentication-authority implementations. |
| Shared security-descriptor suggestions | `Machine\Common\SecurityDescriptorBuilder` | A claim catalogue for programs that build security descriptors. `Common` holds stable shared formats that are not part of the Peios specifications. |
| authd's implementation configuration | `Machine\Software\Authd` | authd's `Sources` subkeys say which principal sources may register and what they are trusted to assert. |
| A particular user's settings | `Users\<SID>`; `CurrentUser` for the caller | Each consumer defines its per-user keys. Check the identity notes below. |

The service and init locations come from [peinit's key constants](https://github.com/peios/peinit/blob/0e20fef16f3c170d8fba0e3a169b617e7b4da3aa/src/registry/mod.rs#L47-L51);
its [init manual](https://github.com/peios/peinit/blob/0e20fef16f3c170d8fba0e3a169b617e7b4da3aa/peinit.regman#L909-L927)
explains the global settings.
The distinction between [shared authentication policy](https://github.com/peios/authd/blob/1a421053deb0cf9703ee1e109db3792f7e1bb95d/authd.regman#L1-L15)
and [authd configuration](https://github.com/peios/authd/blob/1a421053deb0cf9703ee1e109db3792f7e1bb95d/authd.regman#L316-L346)
is explicit in its manual. The [descriptor editor's catalogue documentation](https://github.com/peios/gxwi-sd-editor/blob/43fee424bdfd756996a63347f31abcb6af64eb62/man/gxwi-sd-editor.1#L67-L103)
explains the `Common` example.

## Check whose user settings you are reading

`Users\<SID>` identifies a principal by SID. authd [creates a private user root](https://github.com/peios/authd/blob/1a421053deb0cf9703ee1e109db3792f7e1bb95d/authd/src/user_registry.rs#L14-L39)
at authenticated sign-in, with access for that user, SYSTEM and Administrators;
it does not reset an existing root's permissions.

`CurrentUser` is an alias, not a separate hive. For a caller-supplied
absolute path, LCS resolves its leading `CurrentUser` component using the
calling thread's effective token. A service or impersonating thread may
therefore address a different user's settings from your interactive shell.
See [the alias's exact rules](~peios/lcs/the-data-model/hives-and-routing#currentuser-is-not-a-hive).

Machine-to-user fallback is consumer-specific. For example,
[session locale](~peios/locale/session-locales) combines machine and user
settings for new sessions' environment, under its own
[precedence rules](https://github.com/peios/authd/blob/1a421053deb0cf9703ee1e109db3792f7e1bb95d/authd.regman#L494-L562).
Those rules do not apply automatically to other programs.

## Separate settings from reported facts

The registry also contains state written by running components. Under
`Machine\System\Network`:

- Profiles and interface rules are [operator configuration](https://github.com/peios/netd/blob/23af1f6b84f3764d9327eb009ced56b2a16b7aa8/netd/src/config.rs#L167-L194).
- netd publishes `Status` and readiness facts. Its `Status` keys have
  [SYSTEM-only writes and Everyone reads](https://github.com/peios/netd/blob/23af1f6b84f3764d9327eb009ced56b2a16b7aa8/netd/src/inventory.rs#L1-L49).
  Inspect them; use the documented configuration keys to request changes.
- A network's status can include [remembered DNS server observations](https://github.com/peios/netd/blob/23af1f6b84f3764d9327eb009ced56b2a16b7aa8/netd/src/inventory.rs#L256-L295).
  These differ from both active resolver state and the fallbacks and
  overrides in resolvd's [configuration](https://github.com/peios/resolvd/blob/9c96d693c9672e635cc40ee1e2ea8122e64f017e/resolvd/src/config.rs#L1-L28)
  under `Machine\System\Network\Dns`.

Use [Configuring profiles](~peios/networking/configuring-profiles) and
[Name resolution](~peios/networking/name-resolution) to make and verify a
network change; a stored value alone does not prove active use.

## If you cannot find or read it

- **No manual entry:** check the owning component's documentation. The
  installed manual is only as complete as the documentation shipped with it.
- **No live value:** check the consumer's missing-value behavior. Do not
  create the key merely because the map or manual mentions it.
- **Access denied:** check [the exact key's permissions](~peios/registry-security/access-control).
  Listing a parent and reading a child are separate operations.

There is no universal Everyone-read rule. The [default hive descriptor](https://github.com/peios/loregd/blob/3cb9768b0586ab6563f3b3c50623998624926a8d/internal/sd/sd.go#L113-L128)
grants read access to Authenticated Users and full access to SYSTEM and
Administrators; individual keys can use different descriptors, including
the network `Status` keys above. Knowing a path does not grant access.

Once you have identified the setting and its consumer, follow
[Change a setting and verify it](~peios/registry-concepts/configuration-and-meaning)
for a controlled edit, read-back and consumer verification.
