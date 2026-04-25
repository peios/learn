---
title: Conditional ACE Bytecode Reference
---

This section specifies the binary encoding for conditional ACE expressions. The format is byte-compatible with MS-DTYP section 2.4.4.17.4. Conditional expressions are stored in the ApplicationData member of CALLBACK ACE types, encoded in postfix (reverse Polish) notation.

## Magic signature

A CALLBACK ACE contains a conditional expression if the ApplicationData begins with `0x61 0x72 0x74 0x78` (the string "artx"). If the signature is absent or the expression is shorter than 4 bytes, evaluation MUST return UNKNOWN.

## Token formats

Each token begins with a single byte-code identifying the token type. All multibyte integers, including Unicode characters, are stored least-significant byte first (little-endian). Expressions end at the ACE boundary; any bytes needed for DWORD alignment MUST be set to 0x00.

## Literal tokens

| Token type | Byte-code | Token data encoding |
|---|---|---|
| Padding | 0x00 | No data. Used for DWORD alignment padding at end of expression. |
| Signed int8 | 0x01 | 1 QWORD (8 bytes LE) for the value (2's complement, range -128 to +127). 1 byte for sign. 1 byte for base. Total: 10 bytes. |
| Signed int16 | 0x02 | 1 QWORD (8 bytes LE) for the value (2's complement, range -32768 to +32767). 1 byte for sign. 1 byte for base. Total: 10 bytes. |
| Signed int32 | 0x03 | 1 QWORD (8 bytes LE) for the value (2's complement). 1 byte for sign. 1 byte for base. Total: 10 bytes. |
| Signed int64 | 0x04 | 1 QWORD (8 bytes LE) for the value (2's complement). 1 byte for sign. 1 byte for base. Total: 10 bytes. |
| Unicode string | 0x10 | 1 DWORD (4 bytes LE) for length in bytes. Then UTF-16LE code units (2 bytes each, LSB first). Not null-terminated. |
| Octet string | 0x18 | 1 DWORD (4 bytes LE) for length in bytes. Then raw bytes. |
| Composite | 0x50 | 1 DWORD (4 bytes LE) for total length in bytes of all contained elements. Then elements stored contiguously, each encoded per its own type rules. May be heterogeneous. |
| SID | 0x51 | 1 DWORD (4 bytes LE) for length in bytes. Then SID in binary representation (revision, sub-authority count, identifier authority, sub-authorities). |

### Sign codes

Integer literals include a sign byte after the QWORD value:

| Sign | Code | Description |
|---|---|---|
| + | 0x01 | Explicit positive sign. |
| - | 0x02 | Negative. |
| None | 0x03 | No sign. Relational operators treat as positive. |

### Base codes

Integer literals include a base byte after the sign byte. The base is for display purposes only — the value is always stored as binary 2's complement regardless of base:

| Base | Code | Description |
|---|---|---|
| Octal | 0x01 | Display as octal. |
| Decimal | 0x02 | Display as decimal. |
| Hexadecimal | 0x03 | Display as hexadecimal. |

### Integer encoding example

The decimal value -1 encoded as a signed int64:

```
0x04 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0x02 0x02
 ^    ^-------- QWORD (2's complement) --------^  ^    ^
 |                                                 |    base=decimal
 byte-code=int64                                   sign=negative
```

## Relational operator tokens

### Binary relational operators

LHS is the second element on the stack, RHS is the top. If LHS and RHS are different types, the entire conditional expression evaluates to UNKNOWN — with the exception of INT64 and UINT64 which are promoted for comparison (see the Conditional ACEs section for promotion rules). If either operand is UNKNOWN, the operation returns UNKNOWN.

| Token type | Byte-code | Processing |
|---|---|---|
| == | 0x80 | TRUE if RHS equals LHS (single or set value); FALSE otherwise. |
| != | 0x81 | FALSE if RHS equals LHS; TRUE otherwise. |
| < | 0x82 | TRUE if LHS < RHS; FALSE otherwise. |
| <= | 0x83 | TRUE if LHS <= RHS; FALSE otherwise. |
| > | 0x84 | TRUE if LHS > RHS; FALSE otherwise. |
| >= | 0x85 | TRUE if LHS >= RHS; FALSE otherwise. |
| Contains | 0x86 | TRUE if LHS value(s) include all of RHS value(s); FALSE otherwise. |
| Any_of | 0x88 | TRUE if RHS includes any of LHS value(s); FALSE otherwise. |
| Not_Contains | 0x8e | Logical inverse of Contains. |
| Not_Any_of | 0x8f | Logical inverse of Any_of. |

String and octet string comparisons are byte-by-byte, case-insensitive by default. If the CLAIM_SECURITY_ATTRIBUTE_VALUE_CASE_SENSITIVE flag (0x0002) is set on either operand's attribute, comparison is case-sensitive.

### Unary relational operators (SID membership)

The operand is the top of the stack and MUST be a SID literal or a composite of SID literals.

| Token type | Byte-code | Processing |
|---|---|---|
| Member_of | 0x89 | TRUE if the token's group SIDs contain all SIDs in the operand. |
| Device_Member_of | 0x8a | TRUE if the token's device group SIDs contain all SIDs in the operand. |
| Member_of_Any | 0x8b | TRUE if the token's group SIDs contain any SID in the operand. |
| Device_Member_of_Any | 0x8c | TRUE if the token's device group SIDs contain any SID in the operand. |
| Not_Member_of | 0x90 | Logical inverse of Member_of. |
| Not_Device_Member_of | 0x91 | Logical inverse of Device_Member_of. |
| Not_Member_of_Any | 0x92 | Logical inverse of Member_of_Any. |
| Not_Device_Member_of_Any | 0x93 | Logical inverse of Device_Member_of_Any. |

For an empty SID operand set:

- `Member_of({})` and `Device_Member_of({})` return TRUE (vacuous truth).
- `Member_of_Any({})` and `Device_Member_of_Any({})` return FALSE.
- The `Not_*` forms are the logical inverse of those results.

## Logical operator tokens

Logical operators test the logical value of operands and produce TRUE, FALSE, or UNKNOWN. The logical value of an operand is determined by:

- Literal-origin value → error (entire expression returns UNKNOWN)
- Attribute with null value → UNKNOWN
- Attribute with integer value → TRUE if nonzero, FALSE if zero
- Attribute with string value → TRUE if non-empty, FALSE if empty
- Result value → the result's tri-state value

### Unary logical operators

| Token type | Byte-code | Processing |
|---|---|---|
| Exists | 0x87 | TRUE if the operand is an attribute (@Local., @Resource., @User., or @Device.) with a non-null value. FALSE if the attribute is absent or null. Returns error (→ UNKNOWN) for literal operands. KACS divergence: extends Exists to all four namespaces (MS-DTYP restricts to Local/Resource only). |
| Not_Exists | 0x8d | Logical inverse of Exists. |
| NOT (!) | 0xa2 | TRUE→FALSE, FALSE→TRUE, UNKNOWN→UNKNOWN. |

### Binary logical operators

LHS is the second element on the stack, RHS is the top.

| Token type | Byte-code | Processing |
|---|---|---|
| AND (&&) | 0xa0 | If either operand is FALSE, return FALSE. Else if either is UNKNOWN, return UNKNOWN. Else return TRUE. |
| OR (\|\|) | 0xa1 | If either operand is TRUE, return TRUE. Else if either is UNKNOWN, return UNKNOWN. Else return FALSE. |

## Attribute reference tokens

Attribute names are encoded as Unicode strings (same format as the 0x10 literal: DWORD length + UTF-16LE code units). The byte-code determines which namespace to look up the attribute in.

Attribute lookup is case-insensitive: the encoded name is matched against the namespace's attribute names without regard to case.

| Token type | Byte-code | Namespace |
|---|---|---|
| @Local. | 0xf8 | Local claims (passed as AccessCheck parameter). |
| @User. | 0xf9 | User claims (from token.user_claims). |
| @Resource. | 0xfa | Resource attributes (from SACL resource attribute ACEs). |
| @Device. | 0xfb | Device claims (from token.device_claims). |

## Complete byte-code summary

For quick reference, all byte-codes in numeric order:

| Byte-code | Token |
|---|---|
| 0x00 | Padding |
| 0x01 | Signed int8 literal |
| 0x02 | Signed int16 literal |
| 0x03 | Signed int32 literal |
| 0x04 | Signed int64 literal |
| 0x10 | Unicode string literal |
| 0x18 | Octet string literal |
| 0x50 | Composite literal |
| 0x51 | SID literal |
| 0x80 | == |
| 0x81 | != |
| 0x82 | < |
| 0x83 | <= |
| 0x84 | > |
| 0x85 | >= |
| 0x86 | Contains |
| 0x87 | Exists |
| 0x88 | Any_of |
| 0x89 | Member_of |
| 0x8a | Device_Member_of |
| 0x8b | Member_of_Any |
| 0x8c | Device_Member_of_Any |
| 0x8d | Not_Exists |
| 0x8e | Not_Contains |
| 0x8f | Not_Any_of |
| 0x90 | Not_Member_of |
| 0x91 | Not_Device_Member_of |
| 0x92 | Not_Member_of_Any |
| 0x93 | Not_Device_Member_of_Any |
| 0xa0 | AND (&&) |
| 0xa1 | OR (\|\|) |
| 0xa2 | NOT (!) |
| 0xf8 | @Local. attribute |
| 0xf9 | @User. attribute |
| 0xfa | @Resource. attribute |
| 0xfb | @Device. attribute |

> [!INFORMATIVE]
> This byte-code table is reproduced from MS-DTYP sections 2.4.4.17.4 through 2.4.4.17.8 for specification self-containment. KACS implementations MUST be byte-compatible with these encodings. KACS-specific evaluation semantics (three-valued logic tables, INT64/UINT64 promotion, virtual group visibility in Member_of, polarity-aware SID matching) are defined in the Conditional ACEs section.
