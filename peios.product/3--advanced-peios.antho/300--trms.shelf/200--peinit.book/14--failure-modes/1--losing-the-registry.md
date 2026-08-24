---
title: Losing the Registry
description: peinit depends on the registry once, hard, and then never the same way again — what losing it does in each phase and at runtime.
---

peinit depends on the registry once, hard, and then never again in the
same way. The difference between those two situations is most of what
this section is about.

## During Phase 1

registryd failing to start, failing readiness, or failing the
schema-version probe sends peinit to recovery mode immediately. There is
no Phase 2 without a registry and nothing useful to degrade to. The
counter is incremented, so a persistently broken registryd burns boot
attempts even though every one of them fails the same way.

The recovery shell reached from a Phase 1 failure does not have
registryd running, and the offline tools (§2.8) are what an
administrator has.

## During Phase 2

A registry read that fails or times out during the definition read sends
peinit to recovery, for the same reason: there is no graph to boot.

## At runtime

This is where the design pays off. peinit holds a complete in-memory
model and does not read the registry during normal supervision, so
registryd going away does not stop peinit supervising anything. Services
keep running, restarts keep working, the control socket keeps answering,
and timers keep firing.

What stops working is anything that needs new configuration:
reload-config fails, change notifications stop arriving, and a timer's
last-run timestamp cannot be written — so a persistent timer may produce
a spurious catch-up on the next boot.

registryd itself is a Critical service, so its failure takes the
ordinary Critical path: restart budget, then sync and reboot. peinit
does not have to handle a permanently absent registryd at runtime,
because the system reboots first.

## A definition that will not decode

One definition that fails to decode fails that definition (§3.2). At
boot the key is marked Failed with cause `ValidationError` and every
other service starts normally; on a reload the whole reload is rejected
and the previous generation is left in place.

Both are the safe answer for their caller. A reload is atomic and has a
working configuration behind it, so refusing the change costs nothing. A
boot has no previous generation to fall back to, so refusing everything
would mean not booting at all over a single malformed key — which is
what it used to do.
