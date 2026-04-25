---
title: Section Addressing
---

## The `§` notation

Sections within a PSD MUST be addressable using the `§` symbol followed by the hierarchical section number derived from the document structure (see §4.3).

| Form | Meaning | Example |
|---|---|---|
| `§N` | Chapter N | `§3` |
| `§N.M` | Chapter N, section M | `§3.2` |
| `§N.M.K` | Chapter N, section M, subsection K | `§3.2.1` |
| `§N.M.K.L` | Deeper nesting | `§3.2.2.1` |
| `§N.M.K(C)` | Clause C within the most specific section | `§3.2.1(4)` |

## Citation format

A full citation combines the PSD number with a section address:

| Form | Use |
|---|---|
| `PSD-004` | Reference the whole specification |
| `PSD-004 §3` | Reference a chapter |
| `PSD-004 §3.2` | Reference a section |
| `PSD-004 §3.2.1` | Reference a subsection |
| `PSD-004 §3.2.1(4)` | Reference a specific clause |
| `§3.2.1(4)` | Reference within the same specification |

## Within-spec references

References to sections within the same specification SHOULD omit the PSD number:

```markdown
The SD assigned to a new key is computed as described in §3.4.2.
```

When a bare `§` reference would be opaque without context, a hybrid form combining prose and `§` notation MAY be used for readability:

```markdown
Sender authentication is performed via PID matching (§11.1.3).

The Notify socket subsection (§11.1.3) defines the
authentication protocol.
```

The `§` reference is the durable citation. The prose is a readability aid that MAY drift across versions without invalidating the reference.

## Between-spec references

References to other specifications MUST include the PSD number:

```markdown
Access checks are performed using the algorithm defined in
PSD-004 §10.1(1).
```

When referencing an entire specification without a specific section:

```markdown
All GUIDs in this specification conform to PSD-002.
```

No version annotation is needed -- the version resolution rule (§3.3) applies automatically.

## In code

Code comments referencing PSD clauses SHOULD use the full citation:

```c
/* Per PSD-002 §2.1(1) */
struct peios_guid {
    uint32_t time_low;
    uint16_t time_mid;
    uint16_t time_hi_ver;
    uint8_t  clock_seq_hi;
    uint8_t  clock_seq_low;
    uint8_t  node[6];
};
```

```go
// TestStartupSequence tests PSD-007 §2.1(3)
func TestStartupSequence(t *testing.T) { ... }
```

## In coverage matrices

Coverage matrices SHOULD use the full citation for each clause:

```
| Clause               | Code              | Test                    | Status |
|----------------------|-------------------|-------------------------|--------|
| PSD-004 §3.2.1(1)   | kacs/acl.c:142    | kacs_acl_test.c:test_1  | pass   |
| PSD-004 §3.2.1(2)   | kacs/acl.c:158    | kacs_acl_test.c:test_2  | pass   |
```
