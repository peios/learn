---
title: Impersonation Gates
order: 2
---

When a server thread attempts to impersonate a client's token, two independent checks determine whether impersonation proceeds at the requested level or is capped downward. Both MUST pass for the requested level to be granted. If either fails, the effective level is reduced to Identification — never the reverse.

## The identity gate

The identity gate answers: is this server permitted to impersonate this particular user's identity?

Impersonation at the Impersonation or Delegation level is permitted if **any** of the following are true:

1. **Same user, same restriction status.** The server's primary token and the client's token have the same user SID, and both are either restricted or both unrestricted. A restricted token MUST NOT impersonate an unrestricted token of the same user — this would allow a sandbox to escape by impersonating its parent's unrestricted token.

2. **SeImpersonatePrivilege.** The server's primary token holds SeImpersonatePrivilege and it is enabled.

If neither condition holds, the impersonation level is **silently capped to Identification**. No error is returned; the impersonation call succeeds, but the resulting token is at Identification level.

The identity gate is checked against the server's **primary token** (`real_cred`), not the effective token. If the server is already impersonating another client, that impersonation MUST NOT affect the gate evaluation.

> [!INFORMATIVE]
> The reference model includes a third condition: an origin session check that allows the logon session which created a token to impersonate it without the privilege. KACS drops this check. If a service needs to impersonate a different user, it MUST hold SeImpersonatePrivilege. No hidden paths.

## The integrity ceiling

The integrity ceiling answers: is the client's token at an integrity level the server is allowed to assume?

The impersonation token's integrity level MUST be less than or equal to the server's primary token's integrity level. A Medium-integrity server can impersonate Low or Medium clients. It MUST NOT impersonate High-integrity clients at Impersonation level — the result is capped to Identification.

This constraint exists because MIC in AccessCheck uses the effective token's integrity level. Without the ceiling, a server could impersonate a higher-integrity token and gain write access to higher-integrity objects — integrity escalation through impersonation.

The integrity ceiling is checked against the server's **primary token**. It is always enforced, regardless of privileges — SeImpersonatePrivilege bypasses the identity gate but MUST NOT bypass the integrity ceiling.

> [!INFORMATIVE]
> The reference model allows SeImpersonatePrivilege to bypass all checks including the integrity ceiling. KACS enforces the ceiling unconditionally because `mandatory_policy` is immutable, making MIC a real security boundary. Allowing the privilege to bypass it would undermine the stronger MIC guarantee.

## Gate composition

The two gates are independent. Both are evaluated, and the effective impersonation level is the minimum permitted by all constraints:

1. Start with the level the client set on the socket.
2. If the identity gate fails, cap to Identification.
3. If the integrity ceiling fails, cap to Identification.
4. The result is the effective impersonation level.
