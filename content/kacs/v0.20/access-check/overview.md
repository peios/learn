---
title: AccessCheck Overview
order: 1
---

AccessCheck is the function that connects tokens to Security Descriptors. Given a token (who is asking?), a Security Descriptor (what are the rules?), and a desired access mask (what do they want to do?), AccessCheck returns a verdict: which of the requested rights are granted, and whether the request succeeds or fails.

AccessCheck is a pipeline that evaluates multiple layers of security policy in a specific order. Each layer can grant or constrain access, and the layers interact -- integrity policy can block what the DACL would allow, privileges can override what the DACL denied, and confinement can revoke what privileges granted. The order matters.

## API variants

AccessCheck has two API variants:

- **AccessCheck** — the common case. Returns a single verdict: the granted access mask and whether the request succeeded. When an object type list is provided, success requires all listed nodes to pass; the returned mask is the intersection.

- **AccessCheckResultList** — the per-property variant. Requires an object type list. Returns a separate verdict for each node -- a denial on one property fails that property only, not the whole request. Used by directory services where a single operation may touch multiple properties with independent access rules.

Both variants share the same evaluation pipeline. The only difference is how results are collected.

## Core mechanics

Three values track the state of every access check:

**`decided`** — which bits in the access mask have been resolved. Enforces first-writer-wins within the DACL walk: once a bit is decided, no later ACE in the same walk can change its outcome. However, pipeline layers that operate on top of the DACL result -- restricted token intersection, confinement intersection, PIP revocation, CAP intersection -- MAY revoke granted bits. Those layers narrow the result; they do not re-evaluate decided bits through the DACL.

**`granted`** — which bits have been resolved as "yes, access is granted." During the DACL walk, `granted` is a subset of `decided`. After the walk, pipeline layers MAY remove bits from `granted`. The final `granted` is what the caller receives.

**`privilege_granted`** — which bits in `granted` were specifically granted by a privilege rather than by the DACL. Exists for audit accuracy (distinguishing DACL-granted from privilege-granted access) and for the restricted token merge (privilege-granted bits are restored after the intersection so that privileges bypass the restricted pass). PIP MAY revoke privilege-granted bits.

When an object type list is present, each node carries its own `decided` and `granted` pair.
