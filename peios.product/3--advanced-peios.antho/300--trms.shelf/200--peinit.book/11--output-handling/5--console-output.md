---
title: Console Output
description: peinit writes its own operational messages to the console and never a service's output — plus severity and the quiet setting.
---

peinit writes its own operational messages to `/dev/console`:

- Phase 1 progress — mount results, registryd starting.
- Phase 2 progress — services starting and failing, dependency errors.
- Shutdown progress.
- Recovery mode entry.
- Critical service failures.

Service output is never echoed to the console. The console is for
peinit's own messages; a service that wants a terminal asks for one with
`TTYPath`.

## Severity and quiet

Each message carries a severity, and `peios.quiet` (§2.6) decides what
that means:

- At `0`, everything is written.
- At `1`, the default, peinit stays out of a terminal held as the
  controlling terminal of a running service, except to announce loss of
  the system. Terminals are matched by device rather than by path, since
  `/dev/console` and `/dev/ttyS<n>` can be the same device; where the
  device cannot be determined peinit assumes the terminal is held.
- At `2`, ordinary progress is dropped everywhere while errors still
  get through.

Suppressed messages are discarded rather than buffered for later.

Shutdown progress carries ordinary status severity, so `peios.quiet=2`
suppresses it along with every other kind of progress.

The autorun step in Phase 1 (§2.3) bypasses the policy entirely, on the
grounds that a script running that early and going wrong is worth
interrupting anything for.
