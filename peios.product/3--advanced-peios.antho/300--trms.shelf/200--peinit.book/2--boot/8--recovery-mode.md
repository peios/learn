---
title: Recovery Mode
description: The last resort — no TCB guarantee, an administrator shell, offline registry access, and what remote recovery there is.
---

Recovery mode is the last resort. There is no TCB guarantee and no
degraded boot to speak of — it is a maintenance environment that hands
the administrator an unrestricted SYSTEM shell on the console.

## Entry

- The boot attempt counter reaching the threshold (§2.7).
- `peios.recovery=1` on the kernel command line.
- Any of the Phase 1 failures listed in §2.3, most importantly a
  registryd that will not start or will not serve.
- A Phase 2 registry read that fails or times out, or invalid boot
  configuration.
- A required provisioned path that cannot be created or secured.

## What peinit does

peinit records the reason as a KMES audit event, then:

1. Completes Phase 1 steps 1–5 if they have not been reached yet.
2. Ensures the base registry structure exists, so the shell sees a
   normal layout even on a system that has never been provisioned.
3. Attempts to start registryd. A failure here is ignored — recovery
   delivers a shell whatever registryd's state.
4. Skips all Phase 2 services.
5. Starts a shell on `/dev/console` from a compiled-in definition, with
   no registry dependency: `/bin/recsh` if it is present and
   executable, otherwise `/bin/sh`, running as SYSTEM with a fixed
   environment of `PATH=/sbin:/bin`, `TERM=linux` and `HOME=/`. peinit
   does not care where either binary comes from.
6. Logs the failure reason to the console.

If the shell exits, peinit respawns it. Recovery never exits to an
unmanaged PID 1.

If neither `/bin/recsh` nor `/bin/sh` can be exec'd, peinit cannot
deliver a shell at all. It logs the reason to the console, syncs, and
halts — PID 1 exiting would panic the kernel. A missing shell is a
binary-integrity failure and sits outside the boot-attempt machinery's
remit.

The shell receives `/dev/console` duplicated onto its standard streams,
but peinit does not call `setsid()` or acquire a controlling terminal
for it. The shell is not a session leader, so job control is not
available in the recovery shell.

Whether the earlier steps are re-run depends on where the failure came
from. A recovery entered from a Phase 2 or runtime failure has already
completed Phase 1 and has registryd running. A recovery entered from a
Phase 1 failure — a mount that would not mount, an RTC that would not
read, a control socket that would not bind — skips steps 1 and 3 above:
it neither completes the remaining Phase 1 steps nor attempts registryd.

> [!NOTE]
> Recovery mode is not a degraded boot; it is a maintenance environment.
> There are no security protections beyond what the kernel provides. The
> administrator has a SYSTEM shell and the corresponding responsibility.

## Offline registry access

If registryd is what caused the recovery, the administrator needs tools
that work without it. Three paths exist:

| Path | What it does |
|---|---|
| `loregd --inspector` | Reads the storage database directly, bypassing LCS, for diagnosis. |
| `loregd --recover-from-backup` | Restores from the automatic backup taken on every registryd startup. |
| `loregd --dangerously-clear-database` | Wipes the registry. Role definitions are the source of truth for service configuration, so a cleared registry is recoverable. |

These name loregd rather than registryd because in recovery the
administrator is interacting with the storage implementation, not with
the registry abstraction. It is the one context where that distinction
is visible.

> [!NOTE]
> `/bin/recsh` exists so a system can ship a purpose-built recovery
> shell — one that bundles the offline registry tools, presents
> guidance, or curates a command set — without making it mandatory.
> `/bin/sh` is the floor where it is absent. peinit treats both as
> opaque executables.

## Remote recovery

Recovery requires console access: physical, IPMI or serial. Two
post-v1 features address headless servers — rolling the registry back to
a last-known-good state from the recovery shell, and an emergency sshd
started without registry involvement.
