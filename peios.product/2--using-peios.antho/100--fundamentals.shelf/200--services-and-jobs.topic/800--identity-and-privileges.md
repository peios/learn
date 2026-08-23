---
title: Service identity and privileges
type: concept
description: How a service token is materialised — minted for SYSTEM, requested from authd otherwise — plus the per-service SID and RequiredPrivileges trimming.
related:
  - peios/services-and-jobs/defining-a-service
  - peios/services-and-jobs/who-can-manage-a-service
  - peios/services-and-jobs/execution-environment
  - peios/tokens/overview
  - peios/identity/well-known-principals
  - peios/privileges/overview
  - peios/boot-and-trust-establishment/authd-handoff
---

Every service process runs under a [KACS token](~peios/tokens/overview) — the kernel object that carries identity into every system call and is the input to every access decision. peinit's responsibility is to get the *right* token for a service and install it on the child process *before* the binary execs, so the service runs as the intended principal from its very first instruction.

One rule frames everything else: **peinit never shares its own SYSTEM token with a service.** Even a service configured `Identity=SYSTEM` gets a *separately materialised* token of its own — never peinit's. This keeps every service's identity independent and auditable, and it is one of peinit's [security invariants](#security-invariants).

## How a token is materialised

The `Identity` field decides where the token comes from:

| `Identity` value | Token source |
|---|---|
| `SYSTEM` | **Minted by peinit** from its own SYSTEM identity. |
| Any other principal name or SID | **Requested from [authd](~peios/boot-and-trust-establishment/authd-handoff).** |
| Absent or empty | authd, defaulting to `LocalService`. |

### The SYSTEM path

For a `SYSTEM` service, peinit mints an independent SYSTEM token using its own token as the template: it reads its own identity (user SID `S-1-5-18`, the group list, the privilege set) and mints a fresh primary token with the same identity, adding the service's [per-service SID](#the-per-service-sid). The minted token is fully independent — the [privilege trimming](#privilege-restriction) that follows affects only this token, never peinit's.

This path exists because of a bootstrapping problem: the platform services that *make* the normal token flow possible cannot use it, because they have to start *before* it exists. `registryd`, `authd`, `lpsd`, and `eventd` all run as SYSTEM and are all minted this way during [boot](~peios/services-and-jobs/boot-and-boot-modes), before authd is available to mint anything.

> [!NOTE]
> There is no allow-list restricting which services *may* be `SYSTEM`. The security boundary is the [registry key descriptor](~peios/services-and-jobs/who-can-manage-a-service) on `Machine\System\Services\` — an administrator who can create service definitions is already trusted to assign any identity, so a second gate would add nothing. The dangerous case is never *implicit*, though: `SYSTEM` must be written out explicitly; an empty `Identity` defaults to the minimal `LocalService`, never to SYSTEM.

### The authd path

For any other identity, peinit asks [authd](~peios/boot-and-trust-establishment/authd-handoff) for a token: it sends the `Identity` value verbatim, and authd routes it to the right source —

- **Well-known principals** (`LocalService`, `NetworkService`, …) → a built-in identity with a predefined minimal privilege set;
- **Local service accounts** → [lpsd](~peios/identity/overview), the local principal store;
- **Domain accounts** → the directory connector;

— resolves the principal's SIDs, mints a token, creates a logon session, and hands the token back to peinit to install. peinit neither knows nor cares whether the identity is local or domain; routing is authd's job.

> [!IMPORTANT]
> Every non-SYSTEM service start depends on authd. peinit interacts with it over a non-blocking, timed channel — if authd is unreachable or unresponsive, the service start *fails* rather than hanging PID 1. This is why a broken authd takes down all non-platform service starts but leaves the SYSTEM-minted platform services unaffected. The authd wire interface is owned by authd, not by peinit, and is still being specified.

## The per-service SID

Every service token — minted or authd-issued — carries a **per-service SID** in its group list. It uses authority `S-1-5-80` and is derived deterministically from the service name: the SHA-1 of the uppercased name (as UTF-16LE), with the digest split into five sub-authorities. authd adds it automatically for the tokens it mints; peinit computes and adds it itself for SYSTEM tokens, no authd involvement needed.

The point of the per-service SID is **fine-grained access control even when services share an identity.** A dozen services might all run as `LocalService`, but each has a *unique* service SID, so an ACL can grant access to exactly one of them without inventing a dedicated account. It is also what keeps the platform services — all running as SYSTEM — distinguishable to [AccessCheck](~peios/access-decisions/overview). See [Well-known principals](~peios/identity/well-known-principals) for the SID landscape this fits into.

## Privilege restriction

A token comes from its source (authd or the SYSTEM mint) with a default set of [privileges](~peios/privileges/overview). `RequiredPrivileges` lets a definition trim that set down to only what the service needs:

- peinit reads the `RequiredPrivileges` allow-list and **removes every privilege not on it** from the token before exec.
- Restriction is **purely subtractive.** peinit removes privileges; it never adds them. A service cannot acquire a privilege its token's source did not grant.
- If `RequiredPrivileges` is absent, the token's default privilege set is used unchanged.

This is least-privilege made concrete: `eudev`, for instance, runs as SYSTEM (it needs device access during early boot) but with its privilege set stripped to the minimum it actually uses, so a compromise of `eudev` does not hand an attacker the full SYSTEM privilege set. Removal is permanent for the life of that token — it is not a disable that the service can re-enable. See [Privileges](~peios/privileges/overview) for what the individual privileges grant.

## Which identity runs what

A service is not just its main process — it has hooks, health checks, and a reload command, and each runs under a defined identity:

| Context | Runs as |
|---|---|
| **Main process** | The service's `Identity`. |
| **`ExecStartPre` / `ExecStartPost`** | `HookIdentity` if set, otherwise the service's `Identity`. |
| **Health checks** | The service's `Identity`, always. |
| **`ExecReload`** (command form) | The service's `Identity`, always — `HookIdentity` does not apply. |
| **[Ad-hoc jobs](~peios/services-and-jobs/jobs-and-operations)** | The token captured by JFS — the submitter's (possibly impersonated) identity. |

Token materialisation for hooks follows the same rules: a `HookIdentity` of `SYSTEM` is minted; any other principal is requested from authd, at the point the hook runs.

`HookIdentity` exists so hooks can run with *different* — usually higher — privileges than the service itself: creating directories in privileged locations, or running a database migration as an admin identity, before the long-running daemon drops to a lesser identity.

> [!WARNING]
> peinit does **not** validate filesystem permissions on hook binaries. If `HookIdentity` grants elevated privileges, it is the administrator's responsibility to ensure the hook binary and every parent directory are not writable by a lower-privileged identity — otherwise a less-trusted principal could replace the hook and run code as the elevated identity. ([FACS](~peios/file-access/overview) enforces KACS descriptors on managed filesystems, but peinit itself performs no such check — protecting hook binaries still depends on correct SDs from packaging and controlled paths.)

## Security invariants

The identity model rests on a few rules peinit never breaks:

1. **peinit never shares its SYSTEM token.** Even `Identity=SYSTEM` services get a separately minted token.
2. **peinit never drops its own SYSTEM identity.** PID 1 runs as SYSTEM for the life of the system — its identity is axiomatic, granted by the kernel at boot.
3. **Privileges are subtractive only.** `RequiredPrivileges` removes; it can never add.
4. **Identity is deterministic.** Every service runs as a known principal. `SYSTEM` must be declared explicitly; an empty `Identity` is the minimal `LocalService`, never SYSTEM.

## Where to start

`Identity` decides what a service *can do*; the [ServiceSecurity descriptor](~peios/services-and-jobs/who-can-manage-a-service) decides *who can manage it* — two independent concerns. Read [Who can manage a service](~peios/services-and-jobs/who-can-manage-a-service) for the other half.

To see how the token is installed alongside the rest of the process setup, read [The execution environment](~peios/services-and-jobs/execution-environment).

For the identity primitives themselves — tokens, SIDs, privileges — start at [Tokens](~peios/tokens/overview).
