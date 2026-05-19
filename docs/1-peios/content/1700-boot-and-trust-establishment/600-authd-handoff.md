---
title: authd handoff
type: concept
description: When authd starts, the system transitions from SYSTEM-everywhere to real identities. authd takes over token minting, populates the kernel's CAAP cache, becomes the answer to "what is this principal allowed to be". This page covers authd's startup work and the handoff from kernel-direct identity to authd-managed identity.
related:
  - peios/boot-and-trust-establishment/overview
  - peios/boot-and-trust-establishment/peinit-pid-1
  - peios/boot-and-trust-establishment/bootstrap-tokens
  - peios/identity/overview
  - peios/central-access-policies/distribution-and-recovery
---

The single most consequential transition during boot is the moment **authd** comes online. Before authd, every process is running on the SYSTEM token (inherited from init through peinit); identity is uniform and authority-maximal. After authd, processes start running as their actual principals — services as their service identities, users as themselves after they sign in. authd is the bridge between "kernel-direct bootstrap identity" and "real identities derived from the directory".

This page covers what authd does at startup, how the handoff from SYSTEM-everywhere to real-identities-everywhere happens, and what authd is responsible for in steady state.

## What authd is

`authd` is the authentication daemon. Its core responsibilities:

- **Authenticate principals.** When a user signs in, authd verifies their credentials against the directory (locally for standalone systems, against Active Directory for domain-joined ones).
- **Mint tokens.** Once a principal is authenticated, authd produces a token reflecting their identity, group memberships, privileges, integrity level, claims. The token is what the principal's processes run on.
- **Manage logon sessions.** authd creates a session per authentication event, attaches the minted tokens to it, tracks lifecycle via the `logon-session-destroyed` event.
- **Distribute CAAP.** authd reads central access policies from its source (registry or AD) and pushes them into the kernel's policy cache via `kacs_set_caap`.
- **Resolve identity-related queries.** authd is the answer to "what privileges does this user have?", "what claims should be on this token?", "is this user a member of this group?". These queries go to authd, which consults the directory.

authd is signed at TCB level, runs at `pip_type = Protected, pip_trust = 8192`, and is one of the PIP-protected processes. It is launched by peinit early in boot and runs continuously until shutdown.

## authd's startup sequence

When peinit forks-and-execs authd, the new process goes through several initialisation steps:

### 1. Verify own state

Just like peinit at startup, authd verifies it is running in the expected state — PIP-protected, holding the expected token, with the expected mitigations applied. Anything else indicates the boot is broken; authd refuses to proceed.

### 2. Connect to the directory

authd opens its connection to the directory. The connection mechanism depends on deployment:

- **Standalone systems** use loregd (the registry daemon). authd communicates with loregd over a Unix socket and reads policy from registry keys.
- **Domain-joined systems** use Samba 4. authd talks to a Samba 4 instance (locally or on another machine in the domain) for AD-compatible identity and policy resolution.

The directory is the source of truth for everything authd needs to know — principals, groups, privileges, CAAP, claims. authd's connection to the directory is established early because everything else depends on it.

If the directory connection fails (loregd not running, AD unreachable), authd cannot mint real tokens. The system continues on bootstrap tokens (everything as SYSTEM) until the directory becomes available. authd retries with exponential backoff; in the meantime peinit may proceed with whatever services don't need authd.

### 3. Populate the CAAP cache

For each central access policy in the directory, authd parses it and pushes it via `kacs_set_caap`. The kernel's policy cache fills up with the deployment's CAAP.

This step matters for the recovery policy: until this step completes, every CAAP-referencing object resolves to the recovery policy (administrators and SYSTEM only). After this step, the object's actual policy applies.

CAAP population happens before authd advertises itself as ready. This is what makes the boot ordering safe — services that depend on CAAP being live can wait for authd to signal readiness; by then, CAAP is in place.

### 4. Begin serving authentication requests

authd opens its socket — typically a Unix domain socket — and starts accepting connections from clients. The clients include:

- peinit, asking for tokens to assign to new services.
- Login frontends (console, SSH, terminal services) authenticating users.
- Services that handle their own re-authentication (rare, but possible).

Each authentication request follows a similar pattern:

1. Client connects to authd's socket and presents credentials.
2. authd verifies the credentials against the directory.
3. authd resolves the principal's full identity (groups, privileges, claims) from the directory.
4. authd creates a logon session via `kacs_create_session`.
5. authd calls `kacs_create_token` to mint the token, passing the wire-format specification with everything resolved.
6. authd returns the token (or token fd) to the client.

The client now has a token reflecting the authenticated principal. The client can install the token on a child process (if it's peinit launching a service) or on itself (if it's a login frontend completing the user's sign-in).

### 5. Signal readiness

authd writes a readiness signal to peinit — typically by closing a pre-existing pipe fd, by writing a sentinel value to a known location, or by reaching a state peinit can probe for. peinit, which has been blocked waiting for this, proceeds to launch the rest of the services.

## The handoff in one paragraph

The transition: before authd is ready, every userspace process is running on the SYSTEM token (or a SYSTEM-derived FilterToken variant). After authd is ready, peinit's subsequent service-launch operations assign each new service a token authd produces — derived from the directory, with the appropriate identity for the service. The system goes from "everything SYSTEM" to "services as themselves" gradually, over the course of however long peinit takes to launch the rest of userspace.

There is no single moment where the system "becomes secure" — it's a gradient. Even before authd, the kernel's access control is fully operational; SYSTEM just happens to be everywhere. As real tokens replace SYSTEM in process after process, the system's authorisation surface narrows. By the time login frontends are accepting users, every service is at its right identity, and users sign in to fresh sessions of their own.

## authd in steady state

After startup, authd's day-to-day work is:

- **Authenticate users when they sign in.** Each login produces a session and a token (or a pair of tokens for UAC-style elevation).
- **Mint tokens for new service starts.** When peinit needs a token for a service it's about to launch, authd produces one.
- **Track session lifecycle.** authd subscribes to the kernel's `logon-session-destroyed` event and uses it to release session-scoped state (Kerberos tickets, cached directory data).
- **Distribute CAAP updates.** When a policy in the directory changes, authd re-pushes it via `kacs_set_caap`. The kernel's cache is kept in sync with the directory.
- **Handle session revocation.** When a user must be forcibly logged out, authd walks `/proc/*/token` to find tokens with the offending `auth_id`, identifies the holding processes, and signals them to exit. This is the userspace-coordinated revocation pattern documented in [Session lifecycle](~peios/logon-sessions/lifecycle).

authd is a long-running daemon. It is not periodically restarted. Its uptime equals the system's uptime (modulo any administrative restarts in response to configuration changes).

## What authd does *not* do

A few clarifications:

- **authd does not make access decisions.** AccessCheck is in the kernel. authd produces inputs to it (tokens) but does not decide whether any specific access is granted.
- **authd does not enforce CAAP.** AccessCheck enforces CAAP; authd just distributes the policies into the kernel cache.
- **authd does not authenticate every operation.** Authentication is a sign-in event. Operations done after sign-in run against the token, not against authd. authd does not see most of the per-operation traffic.
- **authd does not store passwords.** Credential verification goes against the directory; authd is an intermediary. The directory (loregd's registry, or AD) is where the credentials live.
- **authd does not implement the directory.** authd consumes a directory; it doesn't *be* one. For standalone systems, loregd is the directory; for domain-joined, AD via Samba 4. authd talks to whichever is appropriate.

The cleanest mental model: authd is the *converter* between "directory state" and "kernel-resolvable identity". Everything else — access decisions, audit, lifecycle — happens around authd, not through it.

## When authd fails

authd is signed at TCB level, runs hardened, and is operationally critical. If authd crashes:

- New authentication requests fail. Users cannot sign in, peinit cannot get new tokens for new services.
- Existing tokens continue to be valid. Processes running on tokens authd already minted are unaffected.
- The kernel's policy cache continues to hold whatever CAAP authd had pushed. Updates to CAAP in the directory will not be reflected until authd is restarted.

peinit detects authd's exit (it's a child of peinit) and typically restarts it per policy. The restart goes through the same fork-install-mitigate-exec pattern as the initial launch; the new authd instance reads the directory fresh and re-establishes the CAAP cache.

Sessions that authd had been managing are still associated with the old authd's auth_id values; the new authd doesn't "inherit" them but doesn't need to — the existing sessions continue running on the tokens already minted; the kernel knows they exist.

A failure that exceeds the restart policy's retry budget is treated as a critical failure; peinit may transition the system to a recovery state where administrative intervention is required.

## Boot ordering implications

Knowing what authd does has implications for boot ordering:

- **Services that need CAAP** must start after authd has populated the cache. peinit enforces this by waiting for authd's readiness signal before launching such services.
- **Services that need real tokens** must start after authd is up. Similarly waited for.
- **Services that are happy with SYSTEM** can start before authd. This is mostly registry, observability, and other infrastructure services.
- **Login frontends** must start after authd is up. They can't authenticate users otherwise.

The exact graph of dependencies is part of peinit's configuration. peinit knows which services depend on what and starts them in the right order.

## The handoff is one-way

A subtle but important property: the handoff from kernel-direct tokens to authd-managed tokens is **one-way**. Once authd is running and has taken over identity creation, the system does not revert to "kernel-direct only" without a full restart.

If authd crashes and restarts, it picks up where it left off (re-reading the directory, re-populating CAAP). It doesn't reset the system to SYSTEM-everywhere; that initial transition happens only once per boot.

The reason: the running services have already been assigned real tokens. Going back to SYSTEM would require reassigning every service's token, which would mean restarting every service. That's a system-wide reboot, not a recovery.

So the trust establishment chain is a one-time event per boot. It happens early; it sets up the system's authority distribution; it stays in place until shutdown. Reboot is the only way to redo it.
