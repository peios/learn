---
title: Integrity Levels Explained
type: concept
order: 20
description: The five integrity levels from Untrusted to System, their trust semantics, and typical processes at each level.
---

Every token on Peios carries one of five integrity levels. The level represents how much the system trusts the process — and determines the minimum trust boundary it can write across.

## Untrusted

The lowest integrity level. Processes at Untrusted integrity have almost no ability to modify anything on the system. They cannot write to objects at any other integrity level — including Low.

Untrusted is used for completely sandboxed processes where even Low integrity provides too much access. In practice, very few processes run at this level.

## Low

Low integrity is for processes that handle **untrusted input** — data from the network, downloaded files, user-submitted content. A compromised Low-integrity process cannot modify objects at Medium or above.

Typical Low-integrity processes:

- Web-facing services that process external requests
- Download handlers and content parsers
- Any process where compromise is considered plausible

Low-integrity processes can write to objects explicitly labeled Low, and to objects they own that have no label (defaulting to Medium) only if the DACL grants it and there is no explicit label blocking them. In practice, Low-integrity processes are given dedicated storage areas labeled Low for their working data.

## Medium

The **default** integrity level. Standard user processes — shells, applications, background tasks in a user session — run at Medium. Objects without an explicit mandatory label are treated as Medium.

Medium is where most day-to-day work happens. MIC is effectively transparent at this level: Medium processes accessing Medium objects encounter no integrity barrier. MIC only becomes visible when a Medium process attempts to write to an object labeled High or System.

## High

High integrity is for **administrative processes** — processes running with an elevated token. When a user elevates, the elevated token carries High integrity.

High-integrity processes can write to objects labeled Medium and below. They are blocked from writing to System-labeled objects.

Typical High-integrity processes:

- Elevated administrative shells
- System configuration tools running after elevation
- Management processes that need to modify protected resources

The High integrity level is what separates a user's filtered (standard) session from their elevated session. Both carry the same user SID, but the integrity level determines which objects the process can modify.

## System

The highest integrity level. Reserved for the **operating system itself** — core services running as SYSTEM, the init process, the authentication service, the registry.

System-integrity processes can write to objects at any integrity level. They are the most trusted processes on the machine, and their compromise would void all security guarantees.

System integrity is not assigned to administrative users, even when elevated. Elevation takes a user to High, not System. The distinction between High and System ensures that even a fully elevated administrator operates below the trust level of the operating system's own services.

## Summary

| Level | Trust | Can write to | Typical processes |
|---|---|---|---|
| **Untrusted** | None | Untrusted objects only | Fully sandboxed code |
| **Low** | Minimal | Low and Untrusted | Web-facing services, content parsers |
| **Medium** | Standard | Medium and below | User shells, applications |
| **High** | Administrative | High and below | Elevated processes |
| **System** | Full | All levels | Core OS services |

Integrity levels are a one-way ratchet. A process can lower its own integrity level but cannot raise it. A High-integrity process can drop to Medium if it no longer needs elevated trust, but a Medium process can never become High without going through the elevation mechanism.
