---
title: How Linked Tokens and Elevation Work
type: concept
order: 80
---

Administrators need full privileges sometimes, but running everything with full administrative power is dangerous. A compromised process with administrative privileges can do far more damage than one without. Peios solves this with **linked token pairs** — a mechanism that gives administrators standard-user permissions by default and full privileges only when they explicitly ask for them.

## Linked token pairs

When a user with administrative group memberships authenticates, the system creates **two tokens** instead of one:

| Token | What it contains |
|---|---|
| **Filtered token** | The user's identity with administrative groups set to deny-only and powerful privileges removed. This is a standard-user token. |
| **Elevated token** | The user's full identity — all group memberships active, all assigned privileges present. |

These two tokens are **linked** — they belong to the same logon session and represent the same user. The difference is how much authority they carry.

## The default is filtered

The user's session starts with the filtered token. Processes launched in the session — the shell, applications, background tasks — all inherit the filtered token. For day-to-day work, the user operates as a standard user.

The administrative groups are still present in the filtered token, but set to **deny-only**. This means they can cause access to be denied (if a deny rule targets the group) but cannot cause access to be granted. The user's administrative membership is visible but not exercisable.

## Elevation

When an operation requires administrative access, the user requests **elevation**. The system switches to the elevated token through a **trusted credential path** — a secure mechanism that cannot be intercepted or spoofed by other processes.

Elevation is explicit. The system does not silently retry a failed operation with higher privileges. If an action requires administrative access, the user must consciously choose to elevate.

Once elevated, the process runs with the full token — all groups active, all privileges available. The elevated process can launch child processes that inherit the elevated token. When the elevated work is done, those processes exit, and the user's session continues with the filtered token.

## How elevation differs from sudo

Users familiar with `sudo` might expect elevation to work similarly — running a command as a different, more powerful user. Elevation on Peios is fundamentally different.

With `sudo`, you authenticate as yourself and then run a process as root — a completely different identity with a different token. The process is not "you with more power," it is a different principal.

With elevation on Peios, both the filtered and elevated tokens represent **you**. They carry your SID, your group memberships, your logon session. The elevated token is not a different identity — it is the unrestricted version of your own. Audit logs show the same user in both cases, and access rules that reference your SID apply to both tokens.

> [!TIP]
> Elevation is an identity-preserving operation. You do not become someone else. You unlock the full authority that was already assigned to you.
