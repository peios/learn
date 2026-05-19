---
title: Resource attributes
type: concept
description: A resource attribute is a typed key-value attribute attached to an object via its SACL. Resource attributes do not grant or deny access by themselves — they exist so conditional ACEs can reference object properties as @Resource.<name>. This page covers what they are, how they are stored, and how they participate in access checks.
related:
  - peios/security-descriptors/overview
  - peios/security-descriptors/the-sacl
  - peios/security-descriptors/conditional-aces
  - peios/identity/claims
---

A **resource attribute** is a typed key-value attribute attached to an object — much like a claim on a token, but applied to the resource rather than the principal. A file might have `Classification = "Internal"`. A registry key might have `Department = "Finance"`. A process or token might have a `Compliance = TRUE` attribute. These attributes do not grant or deny access by themselves; they are inputs that **conditional ACEs** can reference as `@Resource.<name>`.

Resource attributes are stored in the SACL using the `SYSTEM_RESOURCE_ATTRIBUTE_ACE` type. They share the binary format used by token claims: same value types, same flags, same case-sensitivity rules. The key difference is location — claims live on a token, resource attributes live on an object's SD.

## What a resource attribute looks like

Each resource attribute carries:

- A **name** — a string, conventionally `Namespace.Attribute` (`Classification`, `Department`, `Project.Code`).
- A **value** — typed. One of `INT64`, `UINT64`, `STRING`, `SID`, `BOOLEAN`, `OCTET`. Single or multi-valued, but homogeneous (no mixed-type arrays).
- A set of **flags** controlling how the attribute participates in access checks.

The flags are the same set used for claims:

| Flag | Effect |
|---|---|
| `DISABLED` (0x0010) | The attribute is invisible to all conditional expressions. Effectively does not exist. |
| `USE_FOR_DENY_ONLY` (0x0004) | The attribute is invisible to conditions on allow ACEs, but visible to conditions on deny ACEs. Lets an administrator quickly demote an attribute. |
| `MANDATORY` (0x0020) | The attribute cannot be removed or modified without `SeTcbPrivilege`. Used for system-maintained attributes. |
| `CASE_SENSITIVE` (0x0002) | String and octet comparisons against this attribute are case-sensitive. Default is case-insensitive. |

These are the same flags described on [Claims on a token](~peios/identity/claims), applied here to attributes on the resource side.

## Storage in the SACL

A resource attribute lives in a `SYSTEM_RESOURCE_ATTRIBUTE_ACE` (type `0x12`). The ACE body uses a single-SID layout where the SID is always **`Everyone`** (`S-1-1-0`); the SID slot is structural, not semantic — resource attribute ACEs do not match against tokens like access-control ACEs do. The real payload is in the ApplicationData portion, which carries one claim entry in the same format as a token claim.

| ACE field | Resource attribute value |
|---|---|
| AceType | `SYSTEM_RESOURCE_ATTRIBUTE_ACE` (0x12) |
| Mask | Reserved. Not used in access decisions. |
| SID | Always `S-1-1-0` (Everyone). |
| ApplicationData | One claim entry: name, type, flags, value(s). |

A single SACL can hold many resource attribute ACEs — one per attribute. The full ABI layout of the claim entry is in the [Wire formats reference](~peios/wire-formats-reference/overview).

Two structural notes:

- **The first non-inherit-only ACE for each name wins.** If two `SYSTEM_RESOURCE_ATTRIBUTE_ACE` ACEs in the SACL define the same attribute name, only the first one is used. Duplicates after the first are ignored.
- **Resource attributes are located by type-scan, not position.** Unlike DACL ACEs, the order of resource attribute ACEs within a SACL is not load-bearing beyond the first-wins tiebreak. The access check finds them by scanning for the type, not by walking.

## How resource attributes are used

When the access check evaluates a conditional ACE that references `@Resource.<name>`, the lookup runs:

1. Scan the object's SACL for a `SYSTEM_RESOURCE_ATTRIBUTE_ACE` whose attribute name matches `<name>`.
2. If found, read the value(s) and use them in the expression.
3. If not found, the reference produces UNKNOWN. The expression continues with that value, subject to three-valued logic.

The "not found" case is what makes the design tolerant of schema evolution. A conditional ACE that references `@Resource.Classification` works whether or not the specific object has a Classification attribute — if it has one, the expression uses it; if not, the expression evaluates UNKNOWN at that subexpression, and the [three-valued logic](~peios/security-descriptors/conditional-aces) handles the rest.

Resource attributes do not need to be referenced to exist. An object can carry attributes that no current ACE references — perhaps the schema is being prepared for future use, or the attributes are read by separate tooling that scans the SACL directly. The access check ignores resource attribute ACEs that no conditional expression names; they are inert from its perspective.

## Setting and modifying resource attributes

Resource attributes are part of the SACL. Modifying them goes through `kacs_set_sd` with `SACL_SECURITY_INFORMATION` in the security-information mask, which requires `ACCESS_SYSTEM_SECURITY` on the object. In practice this means a caller holding `SeSecurityPrivilege` — the same privilege that gates other SACL modifications.

One additional rule: a resource attribute marked `MANDATORY` cannot be removed or modified except by a caller holding `SeTcbPrivilege`. This is the lever for system-maintained attributes — values the kernel or a TCB component sets that ordinary administrators should not be able to overwrite.

Replacing the SACL with a new one that omits a `MANDATORY` attribute is also rejected; the kernel checks the diff, not just the new value.

## Namespacing

Resource attribute names are arbitrary strings. By convention, attributes use a namespace prefix:

- `Project.Code` — the project this resource belongs to.
- `Department.Name` — the owning department.
- `Compliance.Status` — a compliance classification.

The convention is just a convention. The access check compares names as strings; `Project.Code` and `ProjectCode` are different attributes. Establishing a stable naming scheme is the administrator's job.

In the conditional expression, the reference is `@Resource.<name>` regardless of whether the name itself contains dots:

- `@Resource.Project.Code` references an attribute named exactly `Project.Code`.
- `@Resource.Department` references an attribute named exactly `Department`.

The expression parser treats the dot as part of the attribute name, not as a structural separator.

## Resource attributes vs claims vs local context

Resource attributes sit alongside two other attribute sources that conditional expressions can reference. The three together give the conditional model its expressiveness:

| Source | Lives on | Referenced as | Set by |
|---|---|---|---|
| User claims | Token | `@User.<name>` | authd, from the user directory object |
| Device claims | Token | `@Device.<name>` | authd, from the machine directory object |
| **Resource attributes** | **Object SACL** | **`@Resource.<name>`** | **Object administrator, via `kacs_set_sd`** |
| Local claims | Per AccessCheck call | `@Local.<name>` | The caller, passed as a parameter |

The four namespaces let a single conditional expression weave together "who is the caller", "what machine are they on", "what is the object's property", and "what is the runtime context". The most common pattern uses two of them — caller and resource — for classification-based access. The remaining two appear when machine identity matters or when the calling code wants to supply runtime context.

## What resource attributes are not

A few things resource attributes look like at a glance but are not:

- **Resource attributes are not part of the data.** They are policy metadata, stored in the SACL, separate from the object's content. Reading the object's data does not give you access to the attribute, and vice versa.
- **Resource attributes are not ACEs themselves.** They live in `SYSTEM_RESOURCE_ATTRIBUTE_ACE` entries, but the ACE form is structural — the attribute does not grant or deny anything. The access check skips it during the DACL walk and during the SACL audit walk.
- **Resource attributes do not propagate via inheritance.** They are not inherited from a parent object to a child. A child inherits the parent's inheritable DACL/SACL access-control ACEs; resource attribute ACEs do not have inheritance semantics. If you want the same attribute on every file in a directory, you set it on each one (or use tooling that walks the tree).
- **Resource attributes are not searchable through the access check.** The access check uses attributes for evaluating expressions, not for filtering objects. There is no "list all objects where `@Resource.Classification == 'Public'`" API. That would be a job for a separate indexing layer.
