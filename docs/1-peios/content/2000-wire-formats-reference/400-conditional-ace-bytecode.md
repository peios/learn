---
title: Conditional ACE bytecode
type: reference
description: The byte-level format for conditional ACE expressions and CAAP applies-to expressions. A stack-based postfix bytecode with four attribute namespaces, six value types, and a complete operator catalog. This page covers the encoding for every token, literal, and operator.
related:
  - peios/wire-formats-reference/overview
  - peios/wire-formats-reference/security-descriptors
  - peios/wire-formats-reference/caap-format
  - peios/security-descriptors/conditional-aces
  - peios/constants-and-catalogs/overview
---

Conditional ACE expressions are encoded as **postfix bytecode** — a stack-based instruction sequence where literals push values onto the stack and operators pop and push. The same bytecode is used in callback ACEs (`ACCESS_ALLOWED_CALLBACK`, `SYSTEM_AUDIT_CALLBACK`, etc.) and in CAAP rule applies-to expressions.

This page is the byte-level reference for the bytecode. The conceptual model (three-valued logic, four attribute namespaces, when expressions fire) is in [Conditional ACEs](~peios/security-descriptors/conditional-aces).

All multi-byte integers are little-endian.

## The magic header

Every conditional ACE expression bytecode starts with the four magic bytes:

```
0x61 0x72 0x74 0x78
```

These spell `artx` in ASCII (no actual significance beyond serving as a distinguishing prefix). Conditional ApplicationData buffers that do not start with these bytes are not recognised as conditional expressions; the kernel treats the expression as evaluating to **UNKNOWN**.

The magic bytes are followed by the bytecode proper. Total ApplicationData length is determined by the containing ACE's `AceSize` (for ACE-embedded expressions) or by the CAAP wire format's per-applies-to length (for CAAP).

## The bytecode model

The bytecode is a sequence of **tokens** (instructions). Each token has a 1-byte opcode followed by 0 or more bytes of inline data. The reader walks the bytecode left to right; at end, the stack must contain exactly one tri-state value (TRUE, FALSE, or UNKNOWN).

The stack holds values; operators pop their operands and push results. Stack depth grows with literal tokens, shrinks with operator tokens.

### Recommended stack depth limit

Implementations should enforce a maximum evaluation stack depth of **1024**. Expressions that would exceed this depth evaluate to UNKNOWN. This prevents pathological deep-nesting expressions from consuming unbounded stack space.

## Literal tokens

Literal tokens push a typed value onto the stack.

### Integer literals (0x01–0x04)

The four integer-width opcodes:

| Opcode | Width |
|---|---|
| 0x01 | INT8 (but value still encoded as 8-byte QWORD) |
| 0x02 | INT16 |
| 0x03 | INT32 |
| 0x04 | INT64 |

Each integer literal is encoded as **11 bytes**:

| Bytes | Field |
|---|---|
| 0 | Opcode (0x01–0x04) |
| 1–8 | QWORD value (8 bytes, two's-complement, little-endian) |
| 9 | Sign code: `0x01` (positive), `0x02` (negative), `0x03` (no sign) |
| 10 | Base code: `0x01` (octal), `0x02` (decimal), `0x03` (hex) |

The sign and base codes are metadata about how the integer was originally written; they do not affect evaluation. The same numeric value can appear with different sign/base codes; comparisons use the QWORD value.

### Unicode string literal (0x10)

| Bytes | Field |
|---|---|
| 0 | Opcode (0x10) |
| 1–4 | Length (u32le) — byte length of the UTF-16LE data |
| 5+ | UTF-16LE bytes |

The string's character count is `length / 2`; the byte length is what's in the length field.

### Octet string literal (0x18)

| Bytes | Field |
|---|---|
| 0 | Opcode (0x18) |
| 1–4 | Length (u32le) |
| 5+ | Raw bytes |

Used for binary data — file hashes, GUIDs, anything not naturally a string or number.

### Composite literal (0x50)

A heterogeneous array of values. Used for set-membership operators (`Any_of`, `Member_of`, etc.).

| Bytes | Field |
|---|---|
| 0 | Opcode (0x50) |
| 1–4 | Total length (u32le) — bytes of inline elements following |
| 5+ | Element tokens, packed back-to-back |

Each element is itself a literal token (integer, string, octet, or SID). The kernel reads elements until the total length is consumed.

### SID literal (0x51)

| Bytes | Field |
|---|---|
| 0 | Opcode (0x51) |
| 1–4 | Length (u32le) |
| 5+ | Binary SID |

Used in `Member_of`-family operators where the comparison is against a specific SID.

## Attribute reference tokens

Attribute references push the value of a named attribute onto the stack. Each namespace has its own opcode:

| Opcode | Namespace |
|---|---|
| 0xF8 | `@Local.` (caller-supplied per-call claims) |
| 0xF9 | `@User.` (token's user_claims) |
| 0xFA | `@Resource.` (object's resource_attribute_ACEs) |
| 0xFB | `@Device.` (token's device_claims) |

After the opcode, the attribute name follows in the same format as a string literal (without the 0x10 type-tag byte):

| Bytes | Field |
|---|---|
| 0 | Opcode (0xF8–0xFB) |
| 1–4 | Length (u32le) — UTF-16LE bytes |
| 5+ | UTF-16LE attribute name |

The attribute name is looked up in the corresponding namespace. If found, the attribute's value(s) are pushed. If not found, **UNKNOWN** is pushed.

The reference's stored value type matches the attribute's stored type. For multi-valued attributes, the resulting stack value is a composite-equivalent that subsequent operators handle as a set.

Attribute name lookups are **case-insensitive** by default. An attribute can opt into case-sensitive lookup via the `CLAIM_SECURITY_ATTRIBUTE_VALUE_CASE_SENSITIVE` flag on the attribute itself.

## Relational operators

Pop two operands, push TRUE / FALSE / UNKNOWN.

| Opcode | Operator | Meaning |
|---|---|---|
| 0x80 | `==` | Equal |
| 0x81 | `!=` | Not equal |
| 0x82 | `<` | Less than |
| 0x83 | `<=` | Less than or equal |
| 0x84 | `>` | Greater than |
| 0x85 | `>=` | Greater than or equal |

### Type-mixing rules

The kernel promotes operand types per these rules:

- **INT64 vs UINT64**: a negative INT64 is always less than any UINT64. Both can be compared in either direction.
- **String vs string**: lexicographic, case-insensitive by default (unless either operand was tagged case-sensitive).
- **Octet vs octet**: byte-exact.
- **SID vs SID**: byte-exact, no normalisation.
- **Boolean vs boolean**: TRUE > FALSE (rarely useful).
- **Mixed types where promotion is undefined**: result is UNKNOWN.

A comparison with UNKNOWN on either side produces UNKNOWN.

## Set-membership operators

For operations involving sets (composites or multi-valued attributes).

| Opcode | Operator | Pops | Pushes |
|---|---|---|---|
| 0x86 | `Contains` | 2 (set, value) | Whether the set contains the value |
| 0x87 | `Exists` | 1 (attribute reference) | Whether the attribute exists (not UNKNOWN) |
| 0x88 | `Any_of` | 2 (set, set) | Whether the sets share any element |
| 0x89 | `Member_of` | 1 (SID set) | Whether the token's groups contain any of the SIDs |
| 0x8A | `Device_Member_of` | 1 (SID set) | Same for device_groups |
| 0x8B | `Member_of_Any` | 1 (SID set) | Same as Member_of (alias used in some contexts) |
| 0x8C | `Device_Member_of_Any` | 1 (SID set) | Same |
| 0x8D | `Not_Exists` | 1 | Inverse of Exists |
| 0x8E | `Not_Contains` | 2 | Inverse of Contains |
| 0x8F | `Not_Any_of` | 2 | Inverse of Any_of |
| 0x90 | `Not_Member_of` | 1 | Inverse of Member_of |
| 0x91 | `Not_Device_Member_of` | 1 | Inverse of Device_Member_of |
| 0x92 | `Not_Member_of_Any` | 1 | Inverse of Member_of_Any |
| 0x93 | `Not_Device_Member_of_Any` | 1 | Inverse of Device_Member_of_Any |

`Exists` is special — it specifically returns TRUE if an attribute exists on its token/object, FALSE if not. This distinguishes "attribute is absent" from "attribute exists with UNKNOWN-producing value", which the other operators conflate.

`Not_Exists` is the conservative way to test "the attribute is not there" — it returns TRUE for missing attributes (in contrast to `!Exists(...)` which would return UNKNOWN if the attribute is missing because `Exists` returns UNKNOWN there).

## Logical operators

Three-valued logic over TRUE/FALSE/UNKNOWN.

| Opcode | Operator |
|---|---|
| 0xA0 | `AND` / `&&` |
| 0xA1 | `OR` / `||` |
| 0xA2 | `NOT` / `!` |

The truth tables:

### AND (pops 2)

| | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| TRUE | TRUE | FALSE | UNKNOWN |
| FALSE | FALSE | FALSE | FALSE |
| UNKNOWN | UNKNOWN | FALSE | UNKNOWN |

### OR (pops 2)

| | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| TRUE | TRUE | TRUE | TRUE |
| FALSE | TRUE | FALSE | UNKNOWN |
| UNKNOWN | TRUE | UNKNOWN | UNKNOWN |

### NOT (pops 1)

| Input | Output |
|---|---|
| TRUE | FALSE |
| FALSE | TRUE |
| UNKNOWN | UNKNOWN |

UNKNOWN propagates through NOT — there is no way to "prove an UNKNOWN value is FALSE" by negating. To test "the attribute is absent", use `Not_Exists`, not `!Exists`.

## Boolean coercion

When a non-boolean value reaches a position that requires a boolean (top of stack at the end of evaluation, operand of AND/OR/NOT), it is coerced:

| Source type | TRUE if | FALSE if | UNKNOWN if |
|---|---|---|---|
| INT64 / UINT64 | non-zero | zero | (never) |
| BOOLEAN | already | already | (never) |
| STRING | (never directly coerced) | (never) | always |
| OCTET | (never directly coerced) | (never) | always |
| SID | (never directly coerced) | (never) | always |
| Composite | (never directly coerced) | (never) | always |
| Missing attribute | (never) | (never) | always |

Strings, SIDs, and binary blobs do not coerce to a definite boolean — they yield UNKNOWN when forced into a boolean position. The relational operators (e.g. `@User.Department == "Engineering"`) are how to convert them to booleans by explicit comparison.

## Final result

The expression evaluates by walking the bytecode. The final stack should contain exactly one value, which is the result. If:

- The final stack is **empty** → UNKNOWN.
- The final stack has **more than one value** → UNKNOWN.
- The final stack's single value is **non-boolean and doesn't coerce** → UNKNOWN.
- The final stack's single value is TRUE / FALSE / UNKNOWN → that value.

Any stack-violation or coercion failure during evaluation also produces UNKNOWN. The kernel does not raise errors for malformed expressions during evaluation; UNKNOWN is the universal "I cannot decide" signal.

## Validation

The kernel validates conditional ACE bytecode at ingestion time (when the SD or CAAP is set):

- The magic bytes must be present.
- Each token's opcode must be recognised.
- Each literal's inline data must fit within the buffer.
- The expression must be structurally well-formed (in particular, each operator must have enough operands available at its point in the bytecode).

Failures at ingestion return `-EINVAL`. The kernel does **not** evaluate the expression at ingestion — that happens at access-check time. Ingestion validation catches structural problems; evaluation handles runtime semantics.

Structurally-valid expressions that produce UNKNOWN at runtime (because of missing attributes, type mismatches, etc.) are still valid; they just evaluate to UNKNOWN, with the standard fail-open-for-deny-and-audit behaviour.

## Encoded example

A concrete example. The expression `@User.Department == "Engineering"` would encode roughly as:

```
[magic: 0x61 0x72 0x74 0x78]
[@User. opcode: 0xF9]
[name length: 14 (u32le) — for UTF-16LE "Department"]
[name: UTF-16LE "Department"]
[string literal opcode: 0x10]
[string length: 22 (u32le) — for UTF-16LE "Engineering"]
[string bytes: UTF-16LE "Engineering"]
[== opcode: 0x80]
```

At evaluation:

1. Push the value of `@User.Department` (or UNKNOWN if absent).
2. Push the literal `"Engineering"`.
3. `==` pops both, compares, pushes TRUE / FALSE / UNKNOWN.
4. The single stack value is the result.

## Size limits

Per-expression:

| Limit | Value |
|---|---|
| Stack depth (recommended max) | 1024 |
| Bytecode length | Bounded by the containing structure (ACE size for ACEs, 64 KB for CAAP applies-to) |
| Stack-element size | Bounded by individual literal sizes (no aggregate limit) |

A pathological expression that approaches these limits will be rejected at ingestion or yield UNKNOWN at evaluation.
