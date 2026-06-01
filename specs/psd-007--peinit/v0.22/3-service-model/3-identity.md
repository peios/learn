---
title: Service Identity
---

Every service process runs with a KACS token that determines its
identity and access rights. peinit is responsible for obtaining or
creating the token and installing it on the child process before
exec. peinit MUST NOT share its own SYSTEM token directly with any
service -- even `Identity=SYSTEM` services receive a separately
materialised token of their own.

## Token materialisation

Token materialisation depends on the Identity field:

| Identity value | Token source | Mechanism |
|---|---|---|
| `SYSTEM` | Minted by peinit from its own SYSTEM identity | `kacs_create_token` (see SYSTEM path below). |
| Any other value | authd | Normal authd flow (below). |
| Absent or empty | authd | Defaults to `LocalService`. |

### SYSTEM path

peinit MUST materialise an independent SYSTEM token by minting one
with `kacs_create_token`, using its own token as the template:
peinit reads its own SYSTEM token via `kacs_open_self_token` (user
SID `S-1-5-18`, group list, and privilege set) and mints a new
primary token with that same identity, adding the per-service SID
to the group list (see Per-service SID). The minted token is fully
independent -- the later privilege restriction MUST NOT affect
peinit's own token. Minting requires peinit to hold
`SeCreateTokenPrivilege`, which the boot SYSTEM token carries.

> [!INFORMATIVE]
> Minting is an interim mechanism. The intended model is for peinit
> to *derive* the token from its own token handle via a KACS
> duplicate-with-additions operation -- kernel-attested as a
> descendant of peinit's real token, and requiring no token-minting
> privilege. That operation does not exist in KACS yet; until it is
> added (a tracked KACS dependency), peinit mints.

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

**External dependency (authd).** The steps above describe what
peinit requires of authd -- send the Identity value, receive a
materialised token fd -- not the wire interface. authd's
request/response schema, its socket path, and the fd-passing
mechanism (expected to be `SCM_RIGHTS` over a Unix socket) are
owned by authd, and no authd spec exists yet (authd's design is
deliberately deferred until KACS and the registry are settled).
Every non-SYSTEM service start depends on this interface; it is not
fully implementable from PSD-007 alone, and this path becomes
normative once authd is specified.

Every service token MUST carry a per-service SID in its group
list. The SID uses authority `S-1-5-80` and is derived from the
service name using the service SID algorithm defined in PSD-004:
SHA-1 of the UTF-16LE uppercased service
name, with the 20-byte digest split into five little-endian 32-bit
sub-authorities.

- **authd-minted tokens:** authd adds the per-service SID
  automatically.
- **SYSTEM tokens:** peinit includes the per-service SID in the
  group list when it mints the token (`kacs_create_token`; see
  SYSTEM path). The SID is a deterministic hash -- no authd
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
   **present** bitmask via the `KACS_IOC_ADJUST_PRIVS` ioctl on the
   token fd -- one `kacs_priv_entry` per removed privilege, carrying
   the privilege-removed attribute, and requiring the
   `KACS_TOKEN_ADJUST_PRIVS` right on the fd. peinit MUST NOT use
   `KACS_IOC_RESTRICT`: that builds a restricted-SID token and does
   not alter the privilege bitmask.

Restriction is purely subtractive -- peinit removes privileges but
MUST NOT add them. The enabled, enabled-by-default, and exercised
bitmasks are left as the token source (authd or the minted SYSTEM
token) set them. Enable policy is authd's domain.

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
| ExecReload (external command) | Service's Identity field (always); HookIdentity does not apply. |
| Ad-hoc jobs | Token provided by JFS (caller's effective token). |

If HookIdentity names `SYSTEM`, peinit mints a SYSTEM token (SYSTEM
path) for the hook. If HookIdentity names any other principal, peinit
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
