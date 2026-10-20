---
title: Object Security Policy
type: concept
description: Read descriptor components, ordered grants, inheritance, and conditional policy without treating one part as the whole decision.
---

A security descriptor carries an owner, primary group, DACL, and SACL.
The object manager supplies the object type and rights mapping; the caller
supplies the subject token and request. The descriptor contains neither the
object's data nor a live pointer to its parent's permissions.

## Read the whole applicable decision

The DACL's ordered ACEs contribute discretionary grants and denials. The
walk decides each right at its first applicable entry; a later deny does
not retroactively reverse an earlier allow. Builders should use canonical
explicit-before-inherited and deny-before-allow ordering rather than relying
on a later sort to repair intent.

An absent DACL has no discretionary restriction; a present, zero-entry DACL
contributes no grants. Neither result bypasses the rest of the pipeline.
An empty DACL can still coexist with owner or privilege contributions.
Do not describe either state as an unconditional whole-system verdict.

The owner normally receives descriptor-read and DACL-edit rights, not
automatic file-data access. An applicable Owner Rights ACE suppresses that
implicit grant through a pre-scan, even when its conditional expression
would not later grant access. Mandatory policy and later narrowing still
matter. Ownership change alone neither removes stale ACEs nor establishes a
safe recovery route.

[PCDS](~specifications/pcds/security-descriptor/structure) owns the structure;
the [kernel DACL reference](~kernel/internals/kacs/access-check/the-dacl-walk)
owns evaluation, matching, and maximum-access behavior. A successful
`MAXIMUM_ALLOWED` check still requires inspecting the returned rights mask.

## Inherit at creation

A creator can supply explicit policy, and a parent can contribute inheritable
entries. The token's default DACL is a fallback when explicit and inherited
sources supply none; it is not always combined with inherited entries.
A protected ACL prevents accepting parent entries into that ACL.

Creator Owner and Creator Group placeholders resolve for each created child.
A container can receive an effective resolved entry plus an inherit-only
unresolved entry for later descendants. Generic rights can require the same
two-part treatment. This keeps one creator's concrete SID from becoming the
owner policy for every future descendant.

Inheritance does not recompute during access, retroactively update children,
or automatically reapply after moving an existing object. An explicit
propagation operation is different from changing a parent's descriptor.
Copying creates a new object and has its own preservation options. See
[PCDS inheritance](~specifications/pcds/security-descriptor/inheritance) and
the [SDK inheritance interface](~peios/sdk-security/sd-inheritance).

## Conditions and resource attributes

User, device, resource, and local claims come from different authorities.
A resource claim resides in the object's SACL, not in its contents or the
caller's token. Attribute names can contain dots without becoming nested
objects: `@Resource.Project.Code` names the attribute `Project.Code`.
Coordinate names and types with the policy owner.

Conditions use three-valued logic. For a deny condition equivalent to
`Classification == "TopSecret" && not-cleared`, a missing classification
makes the comparison UNKNOWN. UNKNOWN AND TRUE remains UNKNOWN, so the deny
applies to an uncleared subject. UNKNOWN AND FALSE is FALSE, so the same
condition does not deny a cleared subject. Missing data does not make every
expression UNKNOWN; evaluate the complete expression.

An UNKNOWN allow does not grant. An UNKNOWN deny applies according to the
conditional-ACE rule. Review missing and mistyped attributes explicitly,
rather than assuming that any absent claim denies everyone or grants nobody
through other entries. The [conditional-ACE
specification](~specifications/pcds/security-descriptor/conditional-aces)
defines the operators and truth tables.

## The SACL has several jobs

Audit and continuous-audit ACEs, integrity labels, process-trust labels,
central-policy references, and resource attributes share the SACL. Its name
does not mean every entry produces an audit record. Access rights for reading
or replacing the SACL differ from `WRITE_DAC`; owner status alone is not
sufficient.

The label-only security-information interface affects the mandatory label
subset. It does not read or replace audit and central-policy entries. Full
SACL replacement and label-only update are different operations with their
own checks; do not infer their authority from a partial `sd show` display.
Mandatory resource attributes have additional TCB protection against changes
or removal. Use the [descriptor-management
reference](~kernel/internals/kacs/file-security/the-set-security-interface) for exact gates.

## Preserve an authorized repair route

Before changing policy, establish who can restore the intended descriptor
and what backup actually preserves. A text dump from a partial query cannot
reconstruct omitted SACL state. Neither ownership-taking nor a saved string
guarantees rollback. Verify actual application access with fresh handles
after a change and use [access diagnosis](~peios/identity-and-access/diagnosing-access)
when the result differs from intent.
