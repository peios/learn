---
title: Credentials
---

A user's `credentials` field is a **set of typed credential factors**.
This is structurally the multi-valued credential store of a directory;
its contents are defined here and are private to lpsd (they never cross
the seam — §2.2).

## Credential factors

Each credential factor is:

```
{ type, version, params, public_part, secret_part }
```

- **`type`** — the factor kind. This version defines `password`. Later
  versions MAY add `webauthn` (passkey), `x509` (smartcard), and
  `recovery_code`; they reuse this shape and require no new machinery.
- **`version`** — the factor's format version, allowing the verifier
  scheme to evolve.
- **`params`** — verifier parameters (for `password`, the argon2id cost
  parameters and salt).
- **`public_part`** — non-secret material (e.g. a passkey credential id
  and public key); empty for `password`.
- **`secret_part`** — the stored verifier; a wrappable blob (§3.5).

A principal MAY hold more than one factor. For this version, exactly the
`password` factor participates in Logon.

## The password factor

The `password` factor's verifier MUST be an **argon2id** hash:

```
{ type: password, params: { m, t, p, salt }, secret_part: argon2id(params, password) }
```

lpsd MUST NOT store the NT hash, a Kerberos key, or any reversible or
unsalted password representation. The choice of argon2id (rather than
the Windows NT hash) is permitted precisely because the verifier never
crosses the seam: the broker is credential-agnostic, so the source's
verifier scheme is its own concern.

The default argon2id cost parameters and the salt and output lengths are
given in §9; lpsd MUST use the current policy parameters for new
verifiers, and the dummy verifier of the enumeration-resistance path
(below) MUST use those same parameters.

## Verification

On a verify request (§5.1), lpsd MUST:

1. select the `password` factor for the named principal;
2. compute `argon2id(params, presented_password)` and compare it to
   `secret_part` in constant time;
3. on success, optionally re-wrap the verifier if `params` are older
   than the current policy (lazy upgrade — §3.4); and
4. on failure, apply the lockout accounting of §3.4.

lpsd MUST reject an empty or absent presented credential outright; the
`password-not-required` account flag (§9) MUST NOT permit a
credential-free logon in this version (lpsd refuses it, or — only where a
deployment explicitly opts in — loudly audits).

The transient credential MUST be zeroized in lpsd immediately after the
comparison and MUST NOT be logged or persisted.

## Resistance to user enumeration

When the named principal does not exist, lpsd MUST still perform an
argon2id computation — over the presented credential against a **real,
precomputed dummy verifier** that uses the current policy parameters
(recomputed whenever those parameters change) — before returning failure,
so that the response time of "no such principal" is indistinguishable from
"wrong password." The failure returned to the broker MUST be the same in
both cases (§5.1).

> [!INFORMATIVE]
> Timing and the response are equalized, but lockout *state* remains a
> residual enumeration oracle: a non-existent name never locks, a real one
> does, so an attacker who already holds one valid credential can
> distinguish "locked real account" from "no such account." Per-caller
> throttling (§6.3) is the bound; the state oracle is not otherwise closed.
