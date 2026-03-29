---
title: Conditional ACEs
order: 7
---

Standard ACEs match on SID alone. Conditional ACEs add a boolean expression that MUST also evaluate to TRUE for the rule to take effect. This enables attribute-based access control (ABAC).

A conditional ACE is structurally identical to its non-conditional counterpart with a conditional expression appended after the SID. The expression is stored in a binary format defined by MS-DTYP section 2.4.4.17.

## Attribute sources

Conditional expressions operate on four sources of attributes:

- **@User.** — attributes on the caller's token (e.g., `department`, `clearance`). Populated by authd at token creation time.

- **@Device.** — attributes on the machine's token (e.g., `location`, `complianceLevel`). When device claims are not populated, @Device. references resolve as absent.

- **@Resource.** — attributes on the object, stored as SYSTEM_RESOURCE_ATTRIBUTE_ACEs in the SACL. Describe properties of the thing being accessed.

- **@Local.** — per-call context provided by the caller at AccessCheck time. Not stored on the token or object — passed as an AccessCheck parameter. Enables dynamic context that varies between access checks: "this request was authenticated via MFA," "this connection uses TLS."

> [!INFORMATIVE]
> The reference model resolves @Local. from a token field. KACS resolves it from an AccessCheck parameter, giving it a genuinely distinct purpose: per-call context that varies between access checks.

## Three-valued evaluation

Conditional expressions produce one of three results:

- **TRUE** — the condition is satisfied.
- **FALSE** — the condition is not satisfied.
- **UNKNOWN** — the condition could not be determined (missing attribute, type mismatch, malformed expression).

How the result affects the ACE depends on the ACE type:

| ACE type | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| Allow | ACE takes effect | ACE skipped | ACE skipped |
| Deny | ACE takes effect | ACE skipped | **ACE takes effect** |
| Audit | Event emitted | Event skipped | **Event emitted** |

This asymmetry is the fail-safe principle: uncertainty about whether to grant results in no grant; uncertainty about whether to deny results in denial.

## Expression language

The expression supports:

- **Relational operators:** `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Set operators:** `Contains`, `Any_of`, `Not_Contains`, `Not_Any_of`
- **Membership operators:** `Member_of`, `Member_of_Any`, `Not_Member_of`, `Not_Member_of_Any`, `Device_Member_of`, `Device_Member_of_Any`, `Not_Device_Member_of`, `Not_Device_Member_of_Any`
- **Logical operators:** AND, OR, NOT
- **Existence tests:** `Exists`, `Not_Exists`
- **Literal values:** integers, strings, SIDs, octet strings, composites

## Three-valued logic

| AND | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| TRUE | TRUE | FALSE | UNKNOWN |
| FALSE | FALSE | FALSE | FALSE |
| UNKNOWN | UNKNOWN | FALSE | UNKNOWN |

| OR | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| TRUE | TRUE | TRUE | TRUE |
| FALSE | TRUE | FALSE | UNKNOWN |
| UNKNOWN | TRUE | UNKNOWN | UNKNOWN |

NOT: TRUE↔FALSE; UNKNOWN→UNKNOWN.

Boolean coercion for logical operands: integer nonzero → TRUE, zero → FALSE. String non-empty → TRUE, empty → FALSE. NULL → UNKNOWN. SID, octet, composite → UNKNOWN. Literal-origin values in logical operators → UNKNOWN.

## Claim flags

Attributes carry flags affecting participation in evaluation:

- **DISABLED (0x0010)** — the attribute is invisible to all conditions. Resolves as absent.
- **USE_FOR_DENY_ONLY (0x0004)** — the attribute participates only in deny ACE conditions. For allow ACE conditions, it resolves as absent.

Empty attributes (zero values) are normalized to absent (NULL) at resolution time.

## SID matching in expressions

The `Member_of` family evaluates group membership on the token. These operators are polarity-aware: deny-only groups do not satisfy allow-ACE conditions.

> [!INFORMATIVE]
> KACS makes virtual groups (S-1-3-4 for owner, S-1-5-10 for PRINCIPAL_SELF) visible to conditional expressions. `Member_of({S-1-3-4})` returns TRUE when the caller is the owner. This is an intentional divergence for semantic consistency between the SID matcher and the expression evaluator.

> [!INFORMATIVE]
> KACS promotes between INT64 and UINT64 for relational operators: negative INT64 is always less than any UINT64. Without promotion, UINT64 claims are unusable in conditions because the bytecode encodes integer literals as signed.

## Binary format

Conditional expressions are encoded as a stack-based bytecode program in reverse Polish notation. The binary format is defined by MS-DTYP section 2.4.4.17.4 and MUST be byte-compatible.

The expression bytecode begins with a 4-byte magic: `0x61 0x72 0x74 0x78` ("artx"). If the magic is absent or the expression is shorter than 4 bytes, evaluation MUST return UNKNOWN.

The full operator bytecodes, literal encodings, and evaluation semantics are specified in the AccessCheck algorithm section.
