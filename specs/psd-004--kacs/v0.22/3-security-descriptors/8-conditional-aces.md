---
title: Conditional ACEs
---

Standard ACEs match on SID alone. Conditional ACEs add a boolean expression that MUST also evaluate to TRUE for the rule to take effect. This enables attribute-based access control (ABAC).

A conditional ACE is structurally identical to its non-conditional counterpart with a conditional expression appended after the SID. The expression is stored in a binary format defined by MS-DTYP section 2.4.4.17.

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

Boolean coercion for logical operands: integer nonzero → TRUE, zero → FALSE. String non-empty → TRUE, empty → FALSE. NULL → UNKNOWN. SID, octet, composite → UNKNOWN. Literal-origin values (values pushed directly from the bytecode, not obtained via attribute lookup) used as operands in AND/OR/NOT → UNKNOWN for the entire expression.

## Attribute sources

Four attribute namespaces exist, resolved via bytecode opcodes:

| Opcode | Prefix | Source | Description |
|--------|--------|--------|-------------|
| 0xf9 | @User. | `token.user_claims` | Token-level claims set by authd at creation. |
| 0xfb | @Device. | `token.device_claims` | Device-level claims from the device token. |
| 0xfa | @Resource. | SD's SACL resource attribute ACEs | Per-object attributes, extracted in Pre-SACL walk. |
| 0xf8 | @Local. | `local_claims` parameter to AccessCheck | Per-call contextual attributes passed by the caller. Structured as a KACS claim array of length-prefixed claim entries, using the Claim Attribute Format section. |

Attribute names are matched case-insensitively. `@User.Clearance`, `@User.clearance`, and `@User.CLEARANCE` all resolve the same attribute.

## Claim flags

Claim flags apply to token claims (@User., @Device.) and resource attributes (@Resource.). @Local. claims also carry flags.

- **DISABLED (0x0010)** — the attribute is invisible to all conditions. Resolves as absent.
- **USE_FOR_DENY_ONLY (0x0004)** — the attribute participates only in deny ACE conditions. For allow ACE conditions, it resolves as absent.

Empty attributes (zero values) are normalized to absent (NULL) at resolution time (when the expression evaluator reads the attribute value during AccessCheck).

Comparisons involving absent attributes evaluate to UNKNOWN. This includes
comparing two absent attributes with `==` or `!=`:
`@User.Missing == @Device.AlsoMissing` is UNKNOWN, not TRUE.

## SID matching in expressions

The `Member_of` family evaluates group membership on the token. These operators are polarity-aware: deny-only groups do not satisfy allow-ACE conditions.

An empty SID operand set uses normal set semantics: `Member_of({})` and
`Device_Member_of({})` return TRUE, while `Member_of_Any({})` and
`Device_Member_of_Any({})` return FALSE. The `Not_*` forms are the logical
inverse of those results.

> [!INFORMATIVE]
> KACS makes virtual groups (S-1-3-4 for owner, S-1-5-10 for PRINCIPAL_SELF) visible to conditional expressions. `Member_of({S-1-3-4})` returns TRUE when the active SID-matching view treats the caller as the owner. Normal evaluation, restricted evaluation, and confinement evaluation may supply different virtual-group views as defined in their respective sections. This is an intentional divergence for semantic consistency between the SID matcher and the expression evaluator.

> [!INFORMATIVE]
> KACS promotes between INT64 and UINT64 for relational operators: negative INT64 is always less than any UINT64. Without promotion, UINT64 claims are unusable in conditions because the bytecode encodes integer literals as signed.

## Binary format

Conditional expressions are encoded as a stack-based bytecode program in reverse Polish notation. The binary format is defined by MS-DTYP section 2.4.4.17.4 and MUST be byte-compatible.

The expression bytecode begins with a 4-byte magic: `0x61 0x72 0x74 0x78` ("artx"). If the magic is absent or the expression is shorter than 4 bytes, evaluation MUST return UNKNOWN.

Evaluation succeeds only if the final stack contains exactly one tri-state result. If evaluation ends with zero entries, more than one entry, or a raw non-boolean value still on the stack, the expression MUST evaluate to UNKNOWN.

The full operator bytecodes and literal encodings are specified in the Conditional ACE Bytecode Reference section. KACS implementations MUST be byte-compatible with MS-DTYP section 2.4.4.17.4.

## Limits

Implementations SHOULD enforce a maximum evaluation stack depth (recommended: 1024) and SHOULD return UNKNOWN for expressions that exceed it. Any bounds violation during parsing (reading beyond the expression buffer, underflowing the stack, integer overflow) MUST return UNKNOWN.
