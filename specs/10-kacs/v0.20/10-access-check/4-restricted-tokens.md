---
title: Restricted Tokens
---

A restricted token carries a secondary SID list -- the restricting SIDs. When AccessCheck encounters a restricted token, it evaluates the DACL twice:

1. **Normal pass.** The DACL is evaluated against the token's normal identity (user SID, group SIDs). This is the standard evaluation.

2. **Restricted pass.** The same DACL is evaluated again, but SID matching uses only the restricting SID list. The token's normal groups are invisible. Conditional membership operators (`Member_of`, `Member_of_Any`, and their device variants) also use this restricted identity view: only the restricting SID list is visible, plus any virtual groups injected from that list.

The restricting SID list is presence-based. A SID participates in the restricted identity whenever it appears in `restricted_sids`; `SE_GROUP_ENABLED` and `SE_GROUP_USE_FOR_DENY_ONLY` on those entries are ignored for restricted-pass SID matching and restricted-pass non-device conditional membership. This matches Windows restricted-token behavior, where restricting SIDs are always enabled for access checks.

Access is granted only for rights that **both passes agree on** -- the intersection. The restricting SID list acts as a filter: the principal can never receive more access than the restricting SIDs would independently permit.

## Write-restricted tokens

A variant where the intersection applies only to write-category bits. Read and execute access comes from the normal pass alone. What constitutes "write" is defined by the object type's GenericMapping: the bits that GENERIC_WRITE maps to are subject to the restricted check.

## Privileges bypass the restricted pass

Rights granted by privileges are added back after the intersection. Privileges are system-level grants from security policy, not from the object's DACL. Token restriction reduces the token's identity-based access surface; privilege-based grants are orthogonal.

## Owner implicit rights in the restricted pass

The restricted pass evaluates owner implicit rights independently: if the object's owner SID appears in the restricting SID list, the restricted pass grants READ_CONTROL and WRITE_DAC (subject to the same OWNER RIGHTS suppression rules as the normal pass). If the owner SID is not a restricting SID, the restricted pass does not grant implicit rights.

## Virtual groups in the restricted pass

If the object's owner SID appears in the restricting SIDs, S-1-3-4 (OWNER RIGHTS) is injected as a virtual restricting SID. If `self_sid` appears in the restricting SIDs, S-1-5-10 (PRINCIPAL_SELF) is injected. This ensures the restricted pass handles these well-known SIDs consistently.

## Restricted device groups

If the token has restricted device groups, the restricted pass swaps them in so that conditional expression operators (`Device_Member_of`, etc.) evaluate against the restricted set, not the unrestricted device groups.
