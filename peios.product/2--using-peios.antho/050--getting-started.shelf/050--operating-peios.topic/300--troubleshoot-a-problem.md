---
title: Troubleshoot a problem
type: how-to
description: Start with the symptom, inspect state and logs, and follow the recovery guide for the affected service, network, sign-in or package operation.
related:
  - peios/operating-peios/manage-the-machine
  - peios/services-and-jobs/troubleshooting
  - peios/logs-and-events/event-viewer
  - peios/networking/the-net-command
---

Start with what failed and when. Keep the error text and the name of the
service, package, account or interface involved. Read the current state
and relevant records before restarting a service, changing permissions or
repeating an operation that changes the machine.

## The browser cannot reach the desktop

1. Check the address and port against
   [Sign in from a browser](~peios/signing-in-from-a-browser/open-the-desktop).
   A machine configured to listen only on `127.0.0.1` is not reachable
   from another device.
2. If the browser shows a certificate warning, follow
   [The machine's certificate](~peios/signing-in-from-a-browser/the-certificate).
   Do not enter credentials when the certificate fingerprint does not match.
3. At a console you can still reach, use
   [`net status`](~peios/networking/the-net-command) to inspect the address,
   link and readiness. Check the GXWI service, `gxwid`, through
   [Controlling services](~peios/services-and-jobs/controlling-services).
4. If this happened during installation or first boot, return to that
   installer's guide. Network changes, reboot and completion of setup
   can change the address or what the browser shows.

## Sign-in is refused

An unknown account and a wrong credential intentionally produce the same
sign-in failure. Check that you are using an account on this machine and
follow [Creating accounts](~peios/managing-local-principals/creating-accounts)
for local-account administration. Do not infer that an account is missing
from the sign-in error alone.

For an administrator investigating the failure, the
[sign-in audit trail](~peios/signing-in/overview#what-the-audit-trail-records)
explains the authority's and local account service's events. Those records
are available only to accounts permitted to read them.

## A service will not start, stops, or keeps restarting

Use [Service troubleshooting](~peios/services-and-jobs/troubleshooting).
It covers configuration, identity, dependency and crash-loop failures.
Inspect the service's state and its latest output before retrying: a
running process is not always a ready or healthy service.

In Services Manager, select the service and choose **Logs…** to open
[Event Viewer](~peios/logs-and-events/event-viewer) on its output, including
hooks and health checks. Widen the time range if the failure is older
than the default last 24 hours.

## Networking is missing or changed unexpectedly

Use [Network Manager](~peios/networking/network-manager) or
[`net status`](~peios/networking/the-net-command) to check the interface's
verdict, selected profile, address, gateway and warnings.

- **Not managed / IGNORE:** check which profile rule applies.
- **A rejected configuration:** the last working rules can remain active;
  read the rejection before assuming the new settings took effect.
- **An address but no route:** distinguish local connectivity from a route
  out of the machine.
- **Addresses work but names do not:** follow
  [Name resolution](~peios/networking/name-resolution).

Make lasting changes through the supported network settings or registry
profiles. Manual changes to a managed interface can be reverted by netd.
Network Manager labels some firewall displays **Example data**; do not use
those displays as evidence of live traffic.

## A package or feature change was interrupted

For a package operation, follow
[Transactions and recovery](~peios/package-management/transactions-and-recovery)
before starting another transaction. For a feature, follow
[Interrupted features](~peios/features/overview#interrupted); their recovery
uses the feature's own lifecycle, rather than package transaction recovery.

## An action is denied, or records seem to be missing

A desktop app uses your account's authority. Check the required access in
the task guide rather than changing unrelated permissions.

Event queries omit records you may not read. Event Viewer can show whether
its read policy hides records, or whether it could not read that policy.
An empty list is not proof that nothing happened. Also check the time
range and filters, and remember that logs are best effort.

[What the machine records](~peios/logs-and-events/overview) explains logs,
events and metrics; [Event Viewer](~peios/logs-and-events/event-viewer)
explains filtering, older records and access notices.
