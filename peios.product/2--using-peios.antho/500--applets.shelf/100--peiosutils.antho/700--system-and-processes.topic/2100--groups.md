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
Authenticated Users Administrators

$ groups jack
jack : Authenticated Users Administrators
```

With no argument it reports the calling process. Given names, it reports on those.

The two forms reach the answer by different routes — the first reads the calling
process's credential, the second looks the name up through the [principal
store](~peios/managing-local-principals/resolving-names) — but both are limited
by the same thing, so in practice they agree.

## This list is much shorter than the truth

It is the most important thing to know about this command here, and it is easy to
miss because the output looks complete.

A group can only be printed if it has a **group ID**, and most of the SIDs in a
token do not have one. The two groups above are the whole of what projects. The
same token also holds:

- `Everyone` and `Local` — you are in both, always, and neither has a group ID.
- `Interactive`, `Network`, `Batch` and `Service` — **unnumbered on purpose**.
  They describe *how* you signed in rather than who you are, which is what lets a
  rule like "network logons cap at Low" be written at all. You are in
  `Interactive` at the console and not over the network, so there is no static
  answer to record.
- Your **logon session** SID, which is minted fresh for each sign-in.
- Your own user SID, which appears as a group so it can be named in an entry.

So a typical administrator's token holds seven groups and `groups` prints two.

This matters more than a cosmetic omission, because `Everyone` **grants real
access**. A rule that allows `Everyone` to connect to a socket is granting *you*,
through a group this command will tell you that you are not in. If you are
working out why an access succeeded or failed, `groups` is the wrong tool.

A group's **attributes** are not representable either. A deny-only group — one
that can block access through a deny entry but grant nothing through an allow
entry — is printed exactly like an ordinary membership.

[`token show --all`](~peios/tokens/token-command) is the lossless view, with every
SID and its attributes. Reach for it whenever the answer matters.

## Exit status

| Code | Meaning |
|---|---|
| `0` | The groups were printed. |
| `1` | A named user could not be found, or the group list could not be read. |

A group ID with no name is printed as the bare number and sets the exit status, rather than stopping the listing.
