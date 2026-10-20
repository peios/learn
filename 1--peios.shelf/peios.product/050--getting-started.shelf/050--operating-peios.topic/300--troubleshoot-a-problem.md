---
title: Troubleshooting a Problem
type: how-to
description: Preserve the failure, inspect the responsible component, and verify one correction at a time.
related:
  - peios/operating-peios/manage-the-machine
  - peios/services-and-jobs/troubleshooting
---

Investigate the failed operation before changing the machine. A restart can
remove useful state, and retrying a request can repeat a change whose reply
was lost.

## Before you start

Keep the exact error, time, affected account, and resource name. Preserve a
working console or administrator session if the problem affects remote
access. Save unsaved work before an action that can end a session.

## Investigate and verify

1. Identify which component performs the operation. Use the symptom guide
   below to inspect its state and relevant records.
2. Distinguish a rejected request from an unavailable service or a lost
   reply. Read back inspectable state before repeating a mutation.
3. Record the proposed correction and existing value. Change one cause at
   a time through the component's documented interface.
4. Repeat the original operation and inspect the resulting state. Keep the
   initial evidence and the outcome of the correction.

## Browser access or sign-in

Check the address and port in [Signing in from a
Browser](~peios/signing-in-from-a-browser/open-the-desktop). A listener
bound only to loopback is not reachable from another machine. For a
certificate warning, follow [The Machine's
Certificate](~peios/signing-in-from-a-browser/the-certificate); do not enter
credentials when the fingerprint differs from a trusted observation.

At a reachable console, inspect `net status` and the `gxwid` service. During
installation and first boot, an address, overlay, or reboot can change what
the browser reaches. Return to that workflow's guide.

For a credential refusal, use [Diagnosing
Authentication](~peios/authentication-operations/diagnosing). A wrong
credential and an unknown account share an authentication failure response;
the response alone does not prove the account is absent. Authority and source
[events](~peios/authentication-operations/audit-events) answer different
parts of the decision.

## Services and network state

[Service Troubleshooting](~peios/services-and-jobs/troubleshooting) covers
identity, dependencies, configuration, and repeated exits. A process existing
is not proof that it is ready. In Services Manager, **Logs…** opens the
relevant Event Viewer filter; widen the time range when the failure is older.

Use [Network Manager](~peios/system-tools/network-manager) or `net status`
to distinguish these cases:

- An unmanaged interface needs its profile-selection rules checked.
- A rejected configuration can leave the last complete configuration active.
- A local address does not prove there is a route beyond the local network.
- Working addresses with failing names need [resolver
  diagnosis](~peios/networking/name-resolution).

Displays labeled **Example data** are not measurements of live traffic.
For clock problems, inspect [time sources and clock
state](~peios/time/overview) before changing the time or time zone.

## Storage and interrupted changes

Keep the failing path and exact error. [`df`](~peios/files-and-directories/df)
and [`du`](~peios/files-and-directories/du) answer different questions about
filesystem capacity and reachable directory contents. Permission failures or
incomplete scans do not establish that deletion is the appropriate remedy.

For interrupted package, upgrade, or feature work, inspect that tool's
recorded state and recovery instructions. Feature cleanup and package
transaction recovery are separate operations. Repeating the original action
without checking its state can make diagnosis harder.

## Denied access or missing records

Inspect the operation's required access, the caller's token, and the target's
security descriptor before widening permissions. The task guide identifies
the needed access; the permissions editor does not grant extra authority.

An empty event query does not prove that nothing happened. Check the time
range, filters, read policy, retention, and collection failures. [Event
Viewer](~peios/desktop-event-viewer/event-viewer) explains its access notices;
[Saving Event Evidence](~peios/reading-records/saving-evidence) covers a
capture for later investigation.
