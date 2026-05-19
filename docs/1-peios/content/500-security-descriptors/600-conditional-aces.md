---
title: Conditional ACEs
type: concept
description: A conditional ACE is an ACE whose grant or deny is gated by an expression. The expression references token claims, resource attributes, and local context. Evaluation produces TRUE, FALSE, or UNKNOWN — the third value makes a missing attribute fail closed for allows and fail closed for denies. This page covers the model, the expression language, and the three-valued logic.
related:
  - peios/security-descriptors/overview
  - peios/security-descriptors/acls-and-aces
  - peios/security-descriptors/resource-attributes
  - peios/identity/claims
  - peios/access-decisions/overview
---

A **conditional ACE** is an ACE whose effect depends on a boolean expression. Where an ordinary allow ACE says "grant these rights to this principal", a conditional allow ACE says "grant these rights to this principal *if this expression is true*". The expression can reference attributes of the calling token (the user's department, the device's compliance state), attributes of the object (its classification, its sensitivity), and runtime context supplied by the caller.

Conditional ACEs are how Peios expresses attribute-based access control — ABAC — as opposed to identity-based access control where every rule names a specific principal or group. The conditional model is strictly an extension: every conditional ACE is also keyed to a SID, so it composes naturally with the rest of the DACL. The expression is an extra gate on top.

This page covers the model, the expression language at a conceptual level, and the three-valued logic that makes the model fail safely when an expression cannot be evaluated.

## The model

A conditional ACE is one of the callback ACE types from [ACLs and ACEs](~peios/security-descriptors/acls-and-aces):

| Type | Behaviour |
|---|---|
| `ACCESS_ALLOWED_CALLBACK` | Allow ACE, gated by expression. |
| `ACCESS_DENIED_CALLBACK` | Deny ACE, gated by expression. |
| `ACCESS_ALLOWED_CALLBACK_OBJECT` | Allow ACE, gated by expression, scoped by GUID. |
| `ACCESS_DENIED_CALLBACK_OBJECT` | Deny ACE, gated by expression, scoped by GUID. |
| `SYSTEM_AUDIT_CALLBACK` | Audit ACE, gated by expression. |
| `SYSTEM_AUDIT_CALLBACK_OBJECT` | Audit ACE, gated by expression, scoped by GUID. |
| `SYSTEM_ALARM_CALLBACK` | Alarm ACE, gated by expression. |
| `SYSTEM_ALARM_CALLBACK_OBJECT` | Alarm ACE, gated by expression, scoped by GUID. |

The body of a callback ACE is the body of the corresponding non-callback ACE — Mask, optional GUIDs, SID — plus a trailing **ApplicationData** block holding the conditional expression in a binary bytecode format. The bytecode begins with the four-byte magic `0x61 0x72 0x74 0x78` (the ASCII string `artx`); a callback ACE whose ApplicationData does not start with that magic is treated as having an UNKNOWN expression and falls into the UNKNOWN-handling rules below.

During the DACL walk, the access check evaluates the expression at the moment the ACE is examined. The result is TRUE, FALSE, or UNKNOWN. What happens next depends on the ACE type and the result:

| ACE class | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| Allow callback | ACE applies (grants its rights) | ACE is skipped | ACE is skipped |
| Deny callback | ACE applies (denies its rights) | ACE is skipped | ACE applies (denies) |
| Audit callback | Emit event | Skip | Emit event |
| Alarm callback | Configure continuous-audit mask | Skip | Configure mask |

The asymmetry between allows and denies is deliberate. An UNKNOWN result on an allow is skipped (the allow does not get to grant access on incomplete information). The same UNKNOWN on a deny *does* apply (the deny errs on the side of denying). And UNKNOWN on audit fires the event (the audit errs on the side of recording).

The principle is: **UNKNOWN never accidentally grants. It can only fail safely closed or fail safely open for auditing.**

## The four attribute namespaces

Conditional expressions reference attributes through four namespaces, each backed by a different source:

| Namespace | Source | Set by |
|---|---|---|
| `@User.<name>` | The caller's token's `user_claims` field. | authd at token creation, from the user's directory object. |
| `@Device.<name>` | The caller's token's `device_claims` field. | authd at token creation, from the machine's directory object. |
| `@Resource.<name>` | A resource attribute ACE in the object's SACL. | The object's administrator, via `kacs_set_sd`. |
| `@Local.<name>` | A per-access-check parameter supplied by the caller. | Whatever code is making the access check. |

So an expression like `@User.Department == "Engineering"` refers to a claim on the caller's token. `@Resource.Classification == "Public"` refers to an attribute on the object being accessed. `@Local.Time > 9` refers to context the calling code passed in. The four namespaces let an ACE reference the caller, the object, and the runtime situation in one expression.

Two of the namespaces are token-side (caller properties), one is object-side (resource properties), and one is per-call context. They cover the three "where can an attribute come from?" possibilities cleanly.

User and device claims are covered on [Claims on a token](~peios/identity/claims). Resource attributes are covered on [Resource attributes](~peios/security-descriptors/resource-attributes). Local claims are passed by the caller; the API surface lives in the [Kernel ABI reference](~peios/kernel-abi-reference/overview).

## The expression language

The expression bytecode is **postfix** (reverse Polish notation), evaluated by a stack machine. Literal tokens push values onto the stack; operator tokens pop operands, do their work, and push a result. The final stack must contain exactly one tri-state value, which is the expression's result.

Conceptually — the syntax you would write if there were a textual form — expressions look like:

```
@User.Department == "Engineering"

@User.Department == "Engineering" && @Resource.Classification != "Secret"

Member_of({SID-of-AdminGroup})

@Device.Compliance == "Compliant" && @Local.Time >= 9 && @Local.Time <= 17

Exists(@User.ProjectAccess) && @User.ProjectAccess Any_of {"alpha", "beta"}
```

(There is no textual surface in v0.20; expressions are constructed as bytecode by SDK tools. The textual form here is illustrative.)

The operators fall into four families:

| Family | Operators |
|---|---|
| Relational | `==`, `!=`, `<`, `<=`, `>`, `>=` |
| Set / membership | `Contains`, `Exists`, `Any_of`, `Member_of`, `Device_Member_of`, `Member_of_Any`, `Device_Member_of_Any`, plus `Not_*` variants |
| Logical | `&&`, `||`, `!` |
| Attribute references | `@User.`, `@Device.`, `@Resource.`, `@Local.` |

The membership operators reference SID sets — `Member_of({S-1-5-21-...})` evaluates TRUE if the caller's token has that SID in its groups. `Any_of` evaluates TRUE if any value in a multi-valued attribute appears in a literal set. `Contains` and `Exists` test for presence rather than equality.

The full operator catalog with bytecode values lives in [Wire formats reference](~peios/wire-formats-reference/overview).

### Value types and comparisons

Expressions operate on six value types: `INT64`, `UINT64`, `STRING`, `SID`, `BOOLEAN`, `OCTET`. Comparisons follow rules you would expect:

- **Numeric comparisons** work across `INT64` and `UINT64` with sign-aware promotion: a negative `INT64` is always less than any `UINT64`.
- **String comparisons** are case-insensitive by default. A claim or attribute can opt into case sensitivity via the `CLAIM_SECURITY_ATTRIBUTE_VALUE_CASE_SENSITIVE` flag (see [Claims on a token](~peios/identity/claims)).
- **SID comparisons** are byte-exact, same as everywhere else.
- **Octet comparisons** are byte-exact.

Boolean coercion of other types happens when an expression treats a non-boolean as a boolean (rarely, but it can happen): a nonzero integer is TRUE, zero is FALSE, NULL is UNKNOWN, SIDs/octets/composites are UNKNOWN. Compositions of types that do not coerce cleanly produce UNKNOWN.

### The "missing attribute" case

The most common UNKNOWN producer is **a reference to an attribute the token or object does not carry**. `@User.ClearanceLevel` on a token that has no `ClearanceLevel` claim evaluates to UNKNOWN — not to NULL, not to FALSE, not to an empty string. UNKNOWN.

This is why the three-valued logic exists. Schemas evolve; not every user object has every defined attribute; the access check needs to behave well when an attribute is missing. The rule "UNKNOWN skips an allow, applies a deny, fires an audit" means a missing attribute can never accidentally upgrade access — at worst, the gated allow does nothing.

## Three-valued logic

The truth tables for `&&`, `||`, and `!` over `{TRUE, FALSE, UNKNOWN}`:

### AND (`&&`)

| | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| **TRUE** | TRUE | FALSE | UNKNOWN |
| **FALSE** | FALSE | FALSE | FALSE |
| **UNKNOWN** | UNKNOWN | FALSE | UNKNOWN |

### OR (`||`)

| | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| **TRUE** | TRUE | TRUE | TRUE |
| **FALSE** | TRUE | FALSE | UNKNOWN |
| **UNKNOWN** | TRUE | UNKNOWN | UNKNOWN |

### NOT (`!`)

| Input | Output |
|---|---|
| TRUE | FALSE |
| FALSE | TRUE |
| UNKNOWN | UNKNOWN |

The pattern: a definite value (TRUE or FALSE) combined with UNKNOWN can sometimes determine the result (FALSE `&&` UNKNOWN is FALSE; TRUE `||` UNKNOWN is TRUE) and sometimes cannot (TRUE `&&` UNKNOWN is UNKNOWN; FALSE `||` UNKNOWN is UNKNOWN). NOT preserves UNKNOWN.

This means **you cannot prove an UNKNOWN attribute is false by negating it**. `! Exists(@User.ClearanceLevel)` evaluates to UNKNOWN if the attribute is missing, because `Exists` returns UNKNOWN in that case and the NOT preserves it. The right way to check "the user does not have this attribute" is the `Not_Exists` operator, which returns TRUE for a missing attribute and FALSE for a present one.

## A worked example

Consider an SD on a sensitive file with this DACL:

1. `ACCESS_DENIED_CALLBACK Everyone (when @Resource.Classification == "TopSecret" && Not_Member_of({Cleared-SID}))` — deny everyone when the file is TopSecret and they are not in the Cleared group
2. `ACCESS_ALLOWED Authenticated_Users GENERIC_READ` — allow read to authenticated users
3. `ACCESS_ALLOWED Authenticated_Users GENERIC_WRITE` — allow write to authenticated users

The resource attribute is set on the file's SACL: `Classification = "TopSecret"`.

User Alice, who is not in the Cleared group, tries to read.

- ACE 1: matches Alice (Everyone matches all tokens). Expression: `Classification == "TopSecret"` is TRUE (the file's resource attribute matches), `Not_Member_of({Cleared-SID})` is TRUE (Alice is not in the group). Both TRUE, so AND is TRUE. The deny applies. `FILE_READ_DATA` and friends are decided and not granted.
- ACE 2: also matches Alice, but `FILE_READ_DATA` etc. are already decided. The allow has no effect.
- ACE 3: same.

Alice gets nothing. The conditional deny did its job.

Now user Bob, who *is* in the Cleared group:

- ACE 1: matches Bob. Expression: `Classification == "TopSecret"` is TRUE, `Not_Member_of({Cleared-SID})` is FALSE. TRUE AND FALSE is FALSE. The deny does not apply.
- ACE 2: matches Bob. `FILE_READ_DATA` not yet decided. Granted.
- ACE 3: matches Bob. `FILE_WRITE_DATA` not yet decided. Granted.

Bob gets read and write. The conditional deny knew not to apply to him.

Now suppose the file's classification attribute is missing (administrative mistake):

- ACE 1: expression `Classification == "TopSecret"` is UNKNOWN (the attribute does not exist). AND of UNKNOWN with anything: depends on the other operand. Even if `Not_Member_of` is TRUE, UNKNOWN AND TRUE is UNKNOWN. The deny ACE has UNKNOWN, which **applies** (denies err on the side of denying). `FILE_READ_DATA` is decided as denied.
- ACE 2, 3: same fate; already decided.

Both Alice and Bob get nothing. The missing attribute caused the deny to fire, not the allow to grant. Fail safe.

## When conditional ACEs are the right tool

Conditional ACEs are the right tool when:

- The set of principals who should have access varies based on attributes that change more often than the SD does. A "members of the Engineering department who joined after 2020" rule is one expression; encoding it as a group membership would require maintaining the group as people join.
- Access depends on something that is not the principal's identity at all — the resource's classification, the time of day, the integrity of the request.
- The same DACL needs to express many cases without duplication. One conditional ACE covers what would otherwise be N parallel ACEs.

They are the wrong tool when:

- The condition reduces to "is this user in this group?". Use a group SID and a plain ACE; it is simpler and faster.
- The condition is a static identity check at a fixed point in time. Use a SID and a plain ACE.
- The expression depends on state that changes faster than you can update the SD. Conditional ACEs evaluate at access-check time using the data on the token and object *now*; if the relevant data is stale, the result is stale.

Most DACLs in practice use no conditional ACEs at all. They appear in the SDs of objects whose access policy is genuinely attribute-driven — central access policies, data-classification-driven sharing, time-bound access. For everything else, plain ACEs are clearer.
