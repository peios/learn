---
title: Service Identity
---

Every service process runs with a KACS token that determines its
identity and access rights. peinit is responsible for obtaining or
creating the token and installing it on the child process before
exec. peinit MUST NOT share its own SYSTEM token directly with any
service -- even `Identity=SYSTEM` services receive a clone.

## Token materialisation

Token materialisation depends on the Identity field:

| Identity value | Token source | Mechanism |
|---|---|---|
| `SYSTEM` | Clone of peinit's token | `kacs_duplicate_token`. Produces an independent copy. |
| Any other value | authd | Normal authd flow (below). |
| Absent or empty | authd | Defaults to `LocalService`. |

### SYSTEM path

peinit MUST clone its own SYSTEM token via `kacs_duplicate_token`
(or equivalent KACS syscall). The clone is an independent copy --
mutations to the clone (privilege stripping, per-service SID
addition) MUST NOT affect peinit's original token.

### authd path

For non-SYSTEM identities, peinit connects to authd and requests
a token:

1. peinit sends the Identity value to authd verbatim.
2. authd routes to the appropriate identity source:
   - Well-known principals (`LocalService`, `NetworkService`):
     built-in identity with predefined minimal privilege set.
   - Local service accounts: lpsd.
   - Domain accounts: AD connector.
3. The identity source returns principal information (user SID,
   group SIDs).
4. authd mints a KACS token via `kacs_create_token`, creates a
   logon session, and returns the token fd to peinit.

peinit does not know or care whether the identity is local or
domain. The routing is authd's responsibility.

## Per-service SID

Every service token MUST carry a per-service SID in its group
list. The SID uses authority `S-1-5-80` and is derived from the
service name using the service SID algorithm defined in the KACS
v0.20 specification: SHA-1 of the UTF-16LE uppercased service
name, with the 20-byte digest split into five little-endian 32-bit
sub-authorities.

- **authd-minted tokens:** authd adds the per-service SID
  automatically.
- **SYSTEM tokens:** peinit adds the per-service SID to the cloned
  token directly. The SID is a deterministic hash -- no authd
  involvement is needed.

Per-service SIDs enable fine-grained access control even when
services share an identity. Multiple `LocalService` services each
have a unique service SID, so ACLs can target a specific service
without requiring a unique principal account.

## Privilege restriction

After token materialisation (both paths), if the service definition
includes a RequiredPrivileges field, peinit MUST restrict the
token:

1. Read the RequiredPrivileges list from the service definition.
2. Remove every privilege NOT in the list from the token's
   **present** bitmask via `kacs_restrict_token` (or equivalent
   KACS syscall).

Restriction is purely subtractive -- peinit removes privileges but
MUST NOT add them. The enabled, enabled-by-default, and exercised
bitmasks are left as the token source (authd or the SYSTEM clone)
set them. Enable policy is authd's domain.

If RequiredPrivileges is absent, the token's default privilege set
is used unchanged.

## Exec contexts

The same token materialisation rules apply to all exec contexts
within a service:

| Context | Identity source |
|---|---|
| Main process | Service's Identity field. |
| ExecStartPre / ExecStartPost | HookIdentity field if set, otherwise the service's Identity field. |
| Health checks | Service's Identity field (always). |
| Ad-hoc jobs | Token provided by JFS (caller's effective token). |

If HookIdentity names `SYSTEM`, peinit clones its own token for
the hook. If HookIdentity names any other principal, peinit
requests a token from authd.

> [!INFORMATIVE]
> HookIdentity allows hooks to run with different (typically
> higher) privileges than the service itself -- for example,
> creating directories in privileged locations or running database
> migrations. peinit does not validate filesystem permissions on
> hook binaries. If HookIdentity grants elevated privileges, the
> administrator is responsible for ensuring the hook binary and its
> parent directories are not writable by lower-privileged
> identities.
