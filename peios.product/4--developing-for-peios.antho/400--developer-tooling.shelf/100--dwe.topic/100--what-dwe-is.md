---
title: What DWE is
type: concept
description: Developer Workflow Embeddings — development paths built into core Peios software. Its first component, dwed, is an unauthenticated SYSTEM control surface that lets you drive a running machine from outside, across as long as an investigation takes.
related:
  - peios/dwe/driving-a-machine
  - peios/dwe/protocol
  - peios/debugging-the-kernel/overview
  - peios/access-decisions/debugging-a-denial
---

**Developer Workflow Embeddings** are dedicated development paths built into core Peios software: the tools carry first-class support for developing against them, rather than being poked at from the outside by whatever a developer can improvise.

Its first and most general component is **`dwed`**, a service that gives you a persistent, maximally-privileged way to talk to a machine that is already running. Everything below is about that.

> [!CAUTION]
> `dwed` performs **no authentication of any kind**. Anything that can reach its socket owns that machine as `SYSTEM`. It exists only on a dedicated development ISO and must never be present on a machine you would not hand to a stranger.
>
> This is the design, not a gap to be closed later. See [The security posture](#the-security-posture).

## The problem it solves

Debugging a live system means asking it one question, reading the answer, and asking a better one. The loop is only as good as how quickly you can go round it.

Without something like `dwed`, driving a Peios machine from outside means a serial console: boot the machine, feed it a script, read what comes back, and start again. Three things about that hurt more than they look:

- **Nothing survives.** Each run is a fresh boot, so every question has to be planned in advance and packed into one script. A question that occurs to you halfway through the output cannot be asked without starting over.
- **The output is one stream.** A console interleaves what you typed, what the shell echoed, and what the program wrote to `stdout` and `stderr` — with no reliable way to pull them apart afterwards. Exit codes are not carried at all unless the script prints them itself.
- **You cannot be `SYSTEM`.** A console session is a logon session belonging to a person. The most privileged thing a machine has to offer is not reachable through it at all.

`dwed` exists because the machine is already persistent. What was missing was anything willing to talk to it in between questions.

## What it gives you

A socket into a running machine that answers **structured** requests as `SYSTEM`:

- `stdout` and `stderr` come back **separately**, as raw bytes, with a real exit status.
- Commands run **directly**, not through a shell, so there is no quoting layer between what you meant and what ran.
- Work can be **detached** — started now, collected several connections later. The job outlives the connection that started it, which is what makes an investigation spanning hours possible.
- Files move in and out **whole and binary-safe**, rather than through `base64` improvised into a shell pipeline.

## The privilege

`dwed` is started by peinit as an ordinary service with `Identity = SYSTEM`. It constructs no tokens of its own; the privilege arrives entirely from that one line in its service definition. Asked on a running machine, its token reports:

```text
user          Local System (S-1-5-18)
type          Primary
logon_type    5 (Service)
privileges    36, all enabled — including SeCreateToken, SeTcb,
              SeAssignPrimaryToken, SeDebug, SeBackup, SeRestore,
              SeImpersonate, SeLoadDriver, SeSecurity, SeAudit
```

This is the same privilege peinit itself holds, deliberately. A full `SYSTEM` account is not reachable from a console at all, and reaching one is the single capability that makes `dwed` worth having over a serial login.

It is also why the rest of this page is about containment.

## The security posture

`dwed` does not authenticate its peer, and **cannot**.

The transport is [vsock](~peios/dwe/protocol), which crosses a hypervisor boundary between two separate kernels. A guest kernel can be told a peer's context id, but it cannot *attest* anything about who is behind it — those are claims, not attestation, and no amount of work inside the guest changes that. Peios' identity model rules `AF_VSOCK` out as a carrier of process identity for exactly this reason.

So authentication is the job of whatever surrounds the machine — the host it runs on, the network it sits behind — and never of `dwed`.

Three things follow, and all three are load-bearing:

**It is never published as a package.** The `peios-dwe` package does not exist in the public repository and never will. It reaches a machine only inside a dedicated `peios-dwe` ISO, so it cannot arrive anywhere by way of an ordinary install.

**Distribution is the only real control.** The usual advice — "do not install it in production" — does not apply cleanly, because the machines DWE is wanted on are production in every sense except intent. There is no honest way to enforce the distinction from inside the software. Keeping it out of the repository is what stops it turning up somewhere by accident.

**Installing it is not enough to start it.** A package may ship a service definition but may not start it: the definition sits inert in the vendor seed library until an image names it in `[registry] autoapply`. For `dwed`, that opt-in is the moment a machine becomes remotely ownable — so it is a decision the image makes explicitly, not a consequence of a package being present.

## What DWE is not

**It is not a test harness.** Provium covers deterministic, repeatable testing of a whole system, from initramfs through to network interaction, and does it far better than anything built on `dwed` could. Tests belong there.

DWE is for the case Provium cannot serve: a machine that is *already* running, already misbehaving, and needs to be asked questions nobody thought to write down in advance. When a Provium test fails for a reason that is not obvious, DWE is how you go and look.

**It is not a general remote-administration tool.** There is no session model, no pty, no terminal multiplexing, and no plan for any of them until something concrete needs one. `dwed` is a way to ask a running machine questions, and the machine — not the connection — is the thing that persists.

> [!NOTE]
> `dwed` is a phase-2 service, so a boot that breaks before phase 2 has no DWE at all. It also goes down with a machine that wedges completely. Both are accepted limits: below that line, a serial console is still the tool.

## Next

- [Driving a machine](~peios/dwe/driving-a-machine) — booting with a vsock device, and the `dwe` command.
- [The DWE protocol](~peios/dwe/protocol) — the wire format, for building against it directly.
