---
title: Console Output
description: peinit writes its own operational messages to the console and never a service's output — the line format, the stage banner, severity, and the quiet setting.
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

## The line format

Every line carries a fixed-width outcome tag, then the component name,
then the message:

```
[      ] peinit: phase1 starting
[  OK  ] peinit: service authd started
[ SKIP ] peinit: service resolvd skipped: DependencyFailure
[ WARN ] peinit warning: calendar timer not armed: Malformed
[FAILED] peinit: service netd failed to launch: token materialisation failed
[ CRIT ] peinit: entering recovery: BootAttempts(3)
```

The tag column is the point of the format. An operator scanning a boot
reads down one column rather than reading sentences, and a failure stops
looking exactly like the twenty lines around it.

| Tag | Means |
|---|---|
| `[      ]` | Progress with no outcome yet. Holds the column while receding. |
| `[  OK  ]` | It worked. |
| `[ SKIP ]` | Deliberately not done. |
| `[ WARN ]` | Wrong, but the boot continues. |
| `[FAILED]` | It did not work. |
| `[ CRIT ]` | The machine is about to be lost. |

An `[  OK  ]` line reads "mounted", never "mounting": the tag already
claims the outcome, so the verb has to agree with it.

### Tag and severity are different axes

The tag is *presentation*. [Severity](#severity-and-quiet) decides who is
allowed to print. They correlate but neither determines the other — a
Normal service failing and a Critical service failing both render
`[FAILED]` while carrying different severities — and collapsing them
would quietly change what `peios.quiet=2` suppresses.

### Colour

Tags are coloured with ANSI SGR escapes: green for `OK`, yellow for
`SKIP` and `WARN`, red for `FAILED`, and white-on-red for `CRIT`.
Untagged progress is never coloured.

Colour is decided once, from the kernel command line, following the same
rule systemd uses: **on unless the command line says `TERM=dumb`.** peinit
is PID 1 and has no inherited `TERM` to consult, so the command line is
the only place an operator can say a console cannot render escapes.
Deliberately not a `peios.*` token — that set is kept small on purpose,
and `TERM=dumb` is a spelling people already know.

Colour changes the bytes and never the layout, so a serial log and a
virtual terminal agree about where the message starts.

### The stage banner

Before Phase 1 does any work, peinit prints a banner naming the stage and
the boot mode:

```
  ══════════════════════════════════════════════════════════════
   peinit · real root · PID 1 · Full boot                 v0.0.1
  ══════════════════════════════════════════════════════════════
```

It is punctuation rather than decoration. [prelude](~peios/boot-and-trust-establishment/initramfs-stage)
prints the matching one when the initramfs takes over, so the two mark the
handover from kernel to initramfs to real root — the one thing a boot log
otherwise never says out loud.

The mode is the one this boot **starts** in: `Full boot`, `Safe mode`, or
`RECOVERY MODE`. A later downgrade to Safe is announced by its own message
rather than by reprinting a banner, because a second banner would read as
a second stage.

Naming the mode is why the kernel command line is read at the very top of
`run_init`, before any Phase 1 work. That reverses an earlier ordering
which assumed mounting the virtual filesystems is what makes
`/proc/cmdline` readable. It is not: the mount step reads
`/proc/self/mountinfo` first, and `/proc` is provided by the initramfs. One
consequence — a machine with both an unreadable command line and another
Phase 1 fault now reports the command line as its recovery reason.

The banner carries ordinary status severity, so `peios.quiet=2` drops it
along with every other kind of progress.

### Who else writes to this console

The format is shared by **specification**, not by shared code. peinit,
[prelude](~peios/boot-and-trust-establishment/initramfs-stage) and the
[hook scripts](~peios/boot-and-trust-establishment/boot-hooks) each
implement it separately, because prelude is a size-critical initramfs PID 1
with no dependencies and the hooks are shell. Changing a tag word or a
width means changing it in all three.

Two other writers reach the console during boot and are **not** in this
format.

**`loregd` opens `/dev/console` itself** and points Go's logger at it. This
does not contradict "service output is never echoed to the console" above —
peinit is not echoing it; loregd is deliberately going around peinit's
capture. The reason is a real gap: peinit captures Phase 1 registryd's
stdout and stderr into a pipe it does **not** surface when the readiness
wait times out, so a registryd that failed for a reason it had printed would
have been reported only as `registryd readiness timeout expired before
READY=1`. Until Phase 1 surfaces that pipe, the workaround is load-bearing
and the lines stay unformatted.

**A general-purpose tool an autorun script invokes** — `reg apply`, for
instance — writes its own output, which reaches the console because the
autorun script's streams do. That output is correct for an interactive
shell and should not be reshaped to suit one caller; if a boot wants it
tagged, the autorun script is the place to do it.

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
interrupting anything for. Its lines are still tagged.

> [!NOTE]
> `peios.quiet` governs peinit only. What the **kernel** prints is
> governed separately by `loglevel`, which shipped images set to `4`. See
> [Boot and boot modes](~peios/services-and-jobs/boot-and-boot-modes).
