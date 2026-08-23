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

One definition that fails to decode takes down the whole read (§3.2).
At boot that is recovery mode; on a reload it is a rejected reload with
the previous generation left in place.

The reload behaviour is the safe one — nothing changes and the caller is
told why. The boot behaviour is less forgiving: a single malformed
service key is enough to prevent the system booting, even though every
other definition is fine.
