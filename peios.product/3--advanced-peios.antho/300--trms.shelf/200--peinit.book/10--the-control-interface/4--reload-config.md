---
title: reload-config
description: A full atomic re-read of the registry rather than a live update — what changes, and how removals and the compiled-in service are handled.
---

`reload-config` takes a fresh snapshot of the configuration from the
registry. It does not live-update anything.

It is also the path a registry change notification takes: any drained
watch event triggers the same full reload, rather than a targeted
re-read of whatever changed.
[*control.reload-config.is-the-registry-watch-path]

## Atomicity

peinit reads everything first. Every registry read happens before any
mutation, so a read failure returns an error with nothing touched.
[*control.reload-config.reads-precede-every-mutation] It
then builds and validates a complete new graph in memory, and only swaps
it in if validation succeeds.

If validation fails, the previous generation stays live and the findings
are returned to the caller.
[*control.reload-config.a-failed-validation-changes-nothing] This is
where the reload path differs
sharply from boot: boot marks individual services Failed and carries on,
because it has to produce a running system; reload rejects the whole
thing, because it has a running system already and a half-applied
configuration would be worse than the one in place.

## What changes

- Every service definition is re-read.
  [*control.reload-config.every-definition-is-re-read]
- A new dependency graph is built and validated.
- Running services are unaffected and continue on their activation
  generation. [*control.reload-config.running-services-are-unaffected]
- New definitions take effect at the next start, restart, or trigger.
  [*control.reload-config.a-changed-definition-takes-effect-at-the-next-start]
- New services become available for `start` immediately.
  [*control.reload-config.a-new-service-is-startable-at-once]
- Timer triggers are re-evaluated and every calendar timer is re-armed,
  from the current time and with no catch-up.
  [*control.reload-config.calendar-timers-are-re-armed-without-catch-up]

A reload also refreshes things that are not service definitions: the
control descriptor, the three control socket limits, the log
configuration, the shutdown settings, the global environment layer, and
the eventd log socket path.
[*control.reload-config.refreshes-more-than-definitions] It also prunes
the fd stores of services that no longer exist.
[*control.reload-config.prunes-fd-stores-of-vanished-services]

## Removals and the compiled-in service

A definition that has disappeared is handled by §3.8 — discarded if
nothing is running, marked definition-removed if something is.

registryd is exempt. Its compiled-in definition survives a reload that
does not mention it, and its provenance survives a registry entry that
shadows it. [*control.reload-config.registryd-is-exempt] peinit started
registryd before the registry existed, and a
reload finding no definition for it cannot conclude that it should stop
being managed.
