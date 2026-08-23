---
title: groups
type: reference
description: Print the groups a user belongs to.
related:
  - peios/system-and-processes/id
  - peios/managing-local-principals/resolving-names
  - peios/tokens/token-command
---

`groups` prints the groups a user belongs to.

```
groups [USERNAME]...
```

```
$ groups
Users Everyone Authenticated Users Administrators

$ groups jack
jack : Users Administrators
```

With no argument it reports the calling process. Given names, it reports on those.

## Those two answers are both correct

The example above is not a mistake, and it is the thing worth knowing about this command on Peios.

**`groups`** reads the calling process's credential — the projection of its [token's](~peios/tokens/overview) group set. That set includes the groups the authority *stapled on* when the token was minted: `Everyone`, `Authenticated Users`, and the like.

**`groups jack`** looks the name up through the [principal store](~peios/managing-local-principals/resolving-names), which returns **recorded** memberships — the ones something actually wrote down.

The stapled groups are not recorded anywhere, because membership in them is a **rule**, not a stored fact. Everyone is in `Everyone`; nothing needs to record it, and nothing can enumerate it. So they appear in the first answer and not the second.

On other Unixes these two forms differ only in the order they print.

## What cannot appear

Both forms are lossy in the same way, and unavoidably so — a group can only be listed if it has a group ID, and some deliberately do not:

- `Interactive`, `Network`, `Batch` and `Service` are **unnumbered on purpose**. They describe *how* you signed in rather than who you are, which is what lets a rule like "network logons cap at Low" be written at all. You are in `Interactive` at the console and not over the network, so there is no static answer to record.
- A group's **attributes** are not representable. A deny-only group — one that can block access through a deny entry but grant nothing through an allow entry — is printed exactly like an ordinary membership.

[`token groups`](~peios/tokens/token-command) is the lossless view, with every SID and its attributes.

## Exit status

| Code | Meaning |
|---|---|
| `0` | The groups were printed. |
| `1` | A named user could not be found, or the group list could not be read. |

A group ID with no name is printed as the bare number and sets the exit status, rather than stopping the listing.
