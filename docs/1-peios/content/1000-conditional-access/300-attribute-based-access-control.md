---
title: How Attribute-Based Access Control Works
type: concept
description: When and how to use attribute-based access control (ABAC) to express policies that groups alone cannot handle.
---

Traditional access control answers the question "is this user in the right group?" Attribute-based access control (ABAC) answers a richer question: "given the properties of this user, this device, and this resource, should access be granted?"

ABAC on Peios is built on conditional ACEs, claims, and resource attributes. It does not replace group-based access control — it extends it. Every conditional ACE still has a SID that must match. The expression adds a second layer of evaluation on top of the SID match.

## A practical scenario

A company has the following requirements:

- Engineering staff can read project files
- Only engineers with clearance level 3 or above can read confidential files
- Confidential files can only be accessed from managed devices
- Finance staff can read finance files but not engineering files

### Without ABAC

Without conditional ACEs, this requires a group structure that encodes every combination:

- `Engineering-Readers` — gets read access to project files
- `Engineering-Clearance3` — gets read access to confidential project files
- `Finance-Readers` — gets read access to finance files

Each new dimension (clearance levels, device types, project assignments) multiplies the number of groups needed. A new clearance level or device classification means creating new groups, adding users to them, and updating ACLs across every affected resource.

### With ABAC

The same policy expressed with conditional ACEs and claims:

```
Project files DACL:
  Allow  Engineering  FILE_READ_DATA
  Allow  Engineering  FILE_READ_DATA
    IF (@Resource.classification == "confidential"
        && @User.clearance >= 3
        && @Device.managed == true)
  Allow  Finance      FILE_READ_DATA
    IF (@Resource.project AnyOf {"budgets", "forecasts"})
```

Wait — that first unconditional allow would grant all engineers access to all project files including confidential ones. The correct structure uses deny for the restriction:

```
Project files DACL:
  Deny   Engineering  FILE_READ_DATA
    IF (@Resource.classification == "confidential"
        && (@User.clearance < 3 || @Device.managed != true))
  Allow  Engineering  FILE_READ_DATA
  Allow  Finance      FILE_READ_DATA
    IF (@Resource.project AnyOf {"budgets", "forecasts"})
```

The conditional deny blocks engineers who lack sufficient clearance or are on an unmanaged device from confidential files. The unconditional allow grants all engineers read access to non-confidential files. The conditional allow gives finance staff access to files tagged with finance-related projects.

Adding a new clearance level or device classification means updating directory attributes — not restructuring groups or rewriting ACLs.

## When to use ABAC

ABAC is most valuable when access policy depends on **properties that change frequently** or that create **combinatorial complexity** with groups:

| Scenario | Why ABAC helps |
|---|---|
| Classification-based access | Policy adapts to each object's classification without per-classification groups |
| Location or device restrictions | Access varies by where or how the user connects |
| Project-based access | Users move between projects without group membership changes |
| Temporal or contextual rules | Expressions can reference attributes that reflect current context |

## When groups are enough

ABAC adds complexity. If access policy is straightforward — "this team can access this share" — regular ACEs with group SIDs are simpler, easier to audit, and easier to understand. ABAC is a tool for policies that groups alone cannot express cleanly.

## The building blocks

| Component | Role | Set by |
|---|---|---|
| **Conditional ACEs** | Express policy rules with expressions | Object owner or administrator |
| **User claims** | Describe the user's properties | Directory attributes, resolved at authentication |
| **Device claims** | Describe the machine's properties | Machine account attributes, resolved at machine authentication |
| **Resource attributes** | Describe the object's properties | Administrator, via resource attribute ACEs in the SACL |

The directory is the source of truth for user and device claims. Resource attributes are set per-object. Conditional ACEs tie them together into access policy. All of this is evaluated by the same AccessCheck function — no separate policy engine, no external service call.
