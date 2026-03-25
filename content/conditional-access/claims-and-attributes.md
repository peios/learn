---
title: User Claims, Device Claims, and Resource Attributes
type: concept
order: 20
---

Conditional ACE expressions operate on three kinds of data: **user claims**, **device claims**, and **resource attributes**. These are the key-value pairs that make attribute-based access control possible.

## User claims

A user claim is a key-value pair attached to the token. Claims are populated at authentication time from the user's directory attributes.

For example, a user's directory entry might have:

| Attribute | Value |
|---|---|
| department | Engineering |
| clearance | 3 |
| location | London |

When the user authenticates, these become claims on the token. Conditional ACEs can reference them:

```
Allow  Authenticated Users  FILE_READ_DATA
  IF (@User.department == "Engineering")
```

User claims are **immutable** on the token — they are a snapshot of the directory attributes at authentication time. If the directory is updated after the token is created, existing tokens are unaffected until the user reauthenticates.

### Claim types

Claims carry typed values:

| Type | Examples |
|---|---|
| **String** | `@User.department == "Engineering"` |
| **Integer** | `@User.clearance >= 3` |
| **Boolean** | `@User.isManager == true` |
| **String set** | `@User.projects Contains "atlas"` |

The type is defined in the directory schema. Conditional ACE expressions perform type-appropriate comparisons — integer comparison for numbers, case-insensitive comparison for strings.

## Device claims

Device claims are key-value pairs from the **machine's** identity. When a user logs into a domain-joined machine, the machine's own claims can be made available alongside the user's claims.

```
Allow  Authenticated Users  FILE_READ_DATA
  IF (@User.department == "Engineering" && @Device.managed == true)
```

This rule grants access only when an Engineering user is on a managed device. The same user on an unmanaged device would not match.

Device claims enable policies that consider **where** the access is coming from, not just **who** is requesting it. Common device claims include:

| Claim | Meaning |
|---|---|
| `@Device.managed` | Whether the machine is managed by the organization |
| `@Device.site` | The physical or logical site the machine belongs to |
| `@Device.trustLevel` | A trust classification for the machine |

Device claims are populated from the machine account's directory attributes, resolved when the machine authenticates to the domain.

## Resource attributes

Resource attributes are key-value pairs attached to the **object**, not the token. They describe properties of the resource itself.

Resource attributes are stored as special ACEs in the object's SACL — **resource attribute ACEs**. They do not grant or deny access on their own. They exist solely to provide data for conditional ACE expressions.

For example, a file might carry:

| Attribute | Value |
|---|---|
| classification | confidential |
| project | atlas |
| retentionYears | 7 |

A conditional ACE can reference these:

```
Deny  Everyone  FILE_READ_DATA
  IF (@Resource.classification == "confidential" && !(@User.projects Contains "atlas"))
```

This denies read access to confidential files unless the user is assigned to the atlas project. The same DACL protects all files — the policy adapts based on each file's resource attributes.

### Setting resource attributes

Resource attributes are set using `sd`:

```
$ sd attr /srv/data/report.pdf set classification confidential
$ sd attr /srv/data/report.pdf set project atlas
$ sd attr /srv/data/report.pdf set retentionYears 7
```

View the attributes on an object:

```
$ sd attr /srv/data/report.pdf
classification:  confidential  (string)
project:         atlas          (string)
retentionYears:  7              (integer)
```

Modifying resource attributes requires `SeSecurityPrivilege` — they are stored in the SACL.

## How claims and attributes work together

The power of conditional ACEs comes from combining all three data sources in a single expression:

```
Allow  Authenticated Users  FILE_WRITE_DATA
  IF (@User.department == "Engineering"
      && @Device.managed == true
      && @Resource.classification != "readonly")
```

This single rule expresses: "Engineering users on managed devices can write to files that are not marked readonly." Without conditional ACEs, this would require separate groups, multiple ACEs, and careful coordination across every object.

Claims and attributes shift access policy from "which groups is this user in" to "what properties does this user, this machine, and this resource have." The groups still matter — the ACE's SID must match — but the expression adds a second dimension of policy that adapts to context.
