---
title: Working with tokens
type: how-to
description: Answer "who am I?", "who is calling me?", and "act as someone else" with the KACS token API — opening tokens, peer identity over sockets, impersonation, and dropping privilege.
related:
  - peios-sdk/reference/token
  - peios-sdk/access-control/checking-access
  - peios/impersonation/overview
---

A **token** is the runtime carrier of an identity, and it is a file descriptor. This guide covers the everyday token tasks; [`token.h`](~peios-sdk/reference/token) is the exhaustive reference for every call and field.

## Who am I?

To inspect your own identity, open your effective token and query it:

```c
int tok = peios_token_open_self(0, KACS_TOKEN_QUERY);
if (tok < 0) { /* errno */ }

unsigned char sid[PEIOS_SID_MAX_BYTES];
ssize_t n = peios_token_user(tok, sid, sizeof sid);   /* the user SID */

uint32_t il;
peios_token_integrity(tok, &il);                      /* integrity level RID */

struct peios_privilege_set privs;
peios_token_privileges(tok, &privs);                  /* held/enabled privileges */

close(tok);
```

`peios_token_open_self` gives you the *effective* token — if your thread is impersonating, that's the impersonated identity. Pass `KACS_TOKEN_OPEN_REAL` in the flags to get your process's real primary token regardless. The `access` argument is the handle rights you want; `KACS_TOKEN_QUERY` is enough to read.

Group SIDs and other list-valued classes come back as buffers you parse with the [`security.h` views](~peios-sdk/reference/security#sid-and-attributes-arrays): read `CLASS_GROUPS` with [`peios_token_query`](~peios-sdk/reference/token#query), then `peios_sid_array_parse` it.

## Who is calling me?

The most useful token trick in a service is learning the identity of whoever connected to your socket. When a client connects over a Unix stream or seqpacket socket, KACS captures their token at `connect()` time, and you open it from the accepted connection:

```c
int conn = accept(listener, NULL, NULL);
int caller = peios_token_open_peer(conn);   /* QUERY | IMPERSONATE rights */
if (caller < 0) { /* errno */ }

/* Now query the caller's identity, or impersonate them (below). */
```

This is local authentication with no passwords and no handshake — the kernel vouches for who is on the other end. The handle comes with fixed `QUERY | IMPERSONATE` rights, which is exactly what a server needs.

## Acting as the caller

Once you hold a caller's (impersonation) token, you can **impersonate** them: adopt their identity on your current thread so every subsequent access check runs as *them*, not as your service. This is how you do work on a client's behalf without running privileged and re-implementing their permissions.

```c
if (peios_token_impersonate(caller) != 0) { /* errno */ }

/* ... do the work here: file opens, access checks, etc. all run as the caller ... */

peios_token_revert();   /* back to your own identity */
close(caller);
```

Always pair `peios_token_impersonate` with [`peios_token_revert`](~peios-sdk/reference/token#impersonation-and-installation), ideally in the cleanup path, so a failure partway through can't leave your thread wearing someone else's identity. `peios_token_revert` is a safe no-op if you weren't impersonating.

The full flow for a request handler is: `accept` → `peios_token_open_peer` → `peios_token_impersonate` → serve the request → `peios_token_revert` → `close`.

## Dropping power

To run less-trusted code with less authority than you hold, derive a **restricted** token and hand it over. `peios_token_restrict` can delete privileges, demote groups to deny-only, and add restricting SIDs:

```c
struct peios_token_restrict spec = {
    .privs_to_delete = KACS_SE_DEBUG_PRIVILEGE | KACS_SE_IMPERSONATE_PRIVILEGE,
    .flags           = KACS_TOKEN_RESTRICT_WRITE_RESTRICTED,
};
int weak = peios_token_restrict(my_primary, &spec);
```

The result is a strictly less-powerful token. Combined with [integrity levels](~peios-sdk/reference/security#integrity-levels) and confinement (both set when [minting a token](~peios-sdk/reference/token#the-token-spec-builder)), this is the basis of sandboxing on Peios.

## Minting tokens

Creating a token from scratch requires `SeCreateTokenPrivilege` and is the province of authentication authorities, not ordinary programs. When you do need it, the [token-spec builder](~peios-sdk/reference/token#the-token-spec-builder) is the ergonomic path — typed setters for the user SID, groups, privileges, integrity, claims, and the rest, then `peios_token_builder_create`. Mind the [index convention](~peios-sdk/reference/token#the-index-convention) for owner/primary-group references, and don't add the logon SID yourself — the kernel injects it.

## Next

- **[Checking access](~peios-sdk/access-control/checking-access)** — use a token to make an authorisation decision.
- **[`token.h` reference](~peios-sdk/reference/token)** — every token call in full.
- **[Impersonation](~peios/impersonation/overview)** — the operator-side model and its two gates.
