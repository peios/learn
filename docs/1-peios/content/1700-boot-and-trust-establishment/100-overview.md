---
title: Boot and trust establishment
type: concept
description: Boot is the sequence that takes a freshly-started kernel from "no userspace" to "fully-running system with real identities and policies". The kernel sets up bootstrap tokens before any userspace exists; prelude runs the initramfs and mounts the real root; peinit takes over as PID 1; authd starts and assumes responsibility for real identity creation. This page is the map for the sequence.
related:
  - peios/boot-and-trust-establishment/bootstrap-tokens
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/boot-and-trust-establishment/boot-hooks
  - peios/boot-and-trust-establishment/peinit-pid-1
  - peios/boot-and-trust-establishment/authd-handoff
  - peios/boot-and-trust-establishment/kernel-invariants
  - peios/tokens/overview
  - peios/process-integrity-protection/overview
---

Boot is the sequence by which Peios goes from "a kernel has been loaded and is starting" to "a fully-running system with real principals, real services, real policy". Most operating systems have a boot sequence, but Peios has a specific *trust* sequence — the kernel needs to establish how authority works on this running system from a starting point where no userspace exists yet, no authd is running, no directory has been consulted, and no tokens have been minted by anything but the kernel itself.

The chain of events is short and well-defined. The kernel sets up its own bootstrap tokens directly, attaches one to the first userspace process, and starts it. That first process is **prelude**, the PID 1 of an in-memory startup environment — the *initramfs* — whose job is to mount the system's real root filesystem and hand the machine over to it. **peinit** (signed at TCB, sitting at PID 1 of the real root) then takes over and begins launching services. Eventually **authd** starts and assumes responsibility for creating real identities for users and services. Each step relies on the previous; the chain has to be intact for the resulting system to be trustworthy.

This page covers the chain at a high level. Later pages cover each part in depth.

## What boot establishes

By the time boot is complete, the system has:

- Two kernel-direct bootstrap tokens (SYSTEM and Anonymous) that exist for the lifetime of the running kernel.
- A peinit process running as PID 1, signed at TCB level, holding the SYSTEM token's privileges plus knowledge of which services to launch.
- An authd process running (started by peinit), populated with the deployment's policy (privileges, claims, CAAP), ready to authenticate users and services.
- A set of service processes running under tokens authd minted, each with their own identity and authority.
- A populated CAAP cache in the kernel (pushed by authd).
- Mount policies applied (set by peinit at boot).
- The handle model in steady state — services have opened the files they need; their fds have cached masks.

Once all of this is in place, the system is "up". Users can sign in (authd handles the authentication; produces tokens; peinit launches their session processes); access checks resolve normally; audit events flow through KMES; everything that the rest of these docs describes is operating.

The interesting question is what happens *during* boot, when each of those pieces is being established. The chain is a sequence of "this couldn't work before, but now it can":

1. Before the kernel finishes init, nothing works. The kernel is itself.
2. After kernel init, the kernel has constructed the SYSTEM and Anonymous tokens. The first userspace process — prelude, the initramfs PID 1 — starts running on the SYSTEM token.
3. After prelude has run the initramfs, the system's real root filesystem is mounted. prelude switches `/` to it and execs the real init.
4. After peinit takes over at PID 1 of the real root, the kernel has a userspace component that can launch other userspace components. peinit can fork-and-exec services.
5. After authd starts, the system has a way to mint *real* identities for users and services. Until now, every process was running on SYSTEM (inherited from init); from this point on, services can run as their own identities, and users can sign in.
6. After authd has populated the CAAP cache, central access policies actually apply. Objects referencing CAAP get evaluated against the policy rather than the recovery policy.
7. After mount policies have been applied, FACS knows what to do on each filesystem.

Each transition is the "next thing that has to happen for the system to be coherent". They roughly correspond to the pages in this topic.

## The bootstrap problem

The deeper question: how does any of this work in the first place? authd creates tokens, but authd is itself a process — what token does it run on? peinit launches services, but peinit is also a process — what privilege does it hold to be allowed to mint child tokens? The system has to have authority and identity to do anything, but authority and identity are exactly what boot is supposed to establish.

The kernel solves this with a few "primordial" operations that don't go through the normal pipeline:

- The SYSTEM token is constructed directly by the kernel, not via `kacs_create_token`. It's there from the moment the kernel finishes initialising, before any userspace process exists.
- The SYSTEM token has every privilege enabled, integrity System, every group SID that any token might ever need. It's authority-maximal.
- init runs on the SYSTEM token. Every child it forks inherits the SYSTEM token until something replaces it.
- peinit is signed at TCB level (verified by the kernel at exec — the verification happens through the same signing path every binary does). Once peinit is running on the SYSTEM token, it has authority to do anything; once peinit is *also* signed at TCB level, it has PIP authority too.
- authd is similarly signed at TCB and run by peinit with the SYSTEM token. Authd then uses its `SeCreateTokenPrivilege` (from the SYSTEM token) to mint other tokens for other processes.

The chain works because each link is held by the previous. The kernel builds the SYSTEM token (link 1); prelude, the initramfs PID 1, runs on it (link 2); peinit takes over from prelude when the system switches to the real root (link 3); peinit launches authd (link 4); authd creates real tokens (link 5). Each link can do its job because the previous link gave it the authority.

The risk: anything that breaks a link breaks the chain. A peinit not signed at TCB level wouldn't get PIP protection at exec; a compromised authd would mint malicious tokens. The signing-and-PIP machinery is what makes the chain trustworthy: each binary in the chain is one whose signature the kernel verifies, and that signature anchors the kernel's trust in what the binary does next.

## The "everything is SYSTEM" phase

There is a brief window during boot where every userspace process is running on the SYSTEM token. From prelude starting in the initramfs, through the early phases of peinit, up until peinit starts launching real services as themselves, every process is SYSTEM.

This is a feature, not a bug. The SYSTEM token is authority-maximal. Whatever early-boot work needs to happen — reading configuration, populating mount policies, launching authd itself — can be done without worrying about whether the running process has the right privileges. It does, because everything is SYSTEM.

The window is short. peinit aims to launch authd as quickly as possible because most of the system is not useful until authd is running. From the moment authd is up, identities can be real, services can run as themselves, users can sign in. The SYSTEM-everywhere phase is what enables the bootstrap, then ends as soon as the real identity machinery can take over.

Services that **must not start before authd is ready** include anything that handles user requests. A file-server that started in the SYSTEM phase would have its access checks running as SYSTEM, not as the principal it should be acting for — which is operationally wrong even though it's authoritatively allowed. peinit waits for authd to be ready before launching such services.

Services that **may start before authd** include things that only need their own state — the registry daemon, observability daemons. These can run as SYSTEM for the rest of the boot if they need to, then ideally drop privileges or get reassigned a more specific token once authd is up.

The exact ordering — which services need to wait for what — is part of peinit's startup configuration, not a kernel concern.

## Where to start

If you want the kernel-direct bootstrap tokens — what SYSTEM and Anonymous contain, why they're constructed without going through `kacs_create_token`, how they relate to the rest of the token model — read [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens).

If you want the initramfs stage — prelude, the in-memory startup environment, the `/system/boot/prelude/` directory it is built from, and the handoff to the real root — read [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage).

If you want how the initramfs is composed — boot hooks, the capabilities they declare, how their order is resolved, and how to write one — read [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks).

If you want peinit's role — what makes it the right thing to be PID 1, the service-launching pattern, the lifecycle-manager role that falls out of PIP — read [peinit at PID 1](~peios/boot-and-trust-establishment/peinit-pid-1).

If you want the authd transition — what authd does at startup, the CAAP cache population, the SYSTEM-everywhere-handoff — read [authd handoff](~peios/boot-and-trust-establishment/authd-handoff).

If you want the kernel-level invariants that the boot chain depends on — the LSM stack, the build config flags, what the kernel refuses to do — read [Kernel invariants](~peios/boot-and-trust-establishment/kernel-invariants).
