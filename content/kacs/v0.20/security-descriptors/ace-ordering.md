---
title: ACE Ordering
order: 4
---

The order of ACEs in a DACL determines the outcome of AccessCheck. AccessCheck walks the DACL from first ACE to last, and the first-writer-wins principle means each bit is decided at most once. ACE ordering is semantically load-bearing.

## Canonical ordering

Tools that author SDs SHOULD produce canonically-ordered DACLs. KACS MUST NOT reject non-canonical DACLs -- it evaluates whatever order it receives -- but non-canonical ordering can produce results that contradict administrative intent.

The canonical order is:

1. **Explicit deny ACEs** — deny rules placed directly on this object (not inherited).
2. **Explicit allow ACEs** — allow rules placed directly on this object.
3. **Inherited deny ACEs** — deny rules inherited from parent objects (nearest parent first).
4. **Inherited allow ACEs** — allow rules inherited from parent objects.

Within each category, object-type ACEs (those scoped to a specific property GUID) SHOULD be ordered after whole-object ACEs.

This ordering guarantees: explicit rules override inherited rules, denials override allows at the same level, and whole-object rules override property-scoped rules.

## SACL ordering

SACLs do not have a canonical ordering requirement. Audit ACEs are evaluated independently (each matching ACE generates its own audit event). The mandatory label ACE, resource attribute ACEs, and scoped policy ID ACEs are located by type scan, not by position.
