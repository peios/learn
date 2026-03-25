---
title: Writing Conditional ACE Expressions
type: how-to
order: 110
---

Use `sd add` with an `if` clause to create conditional ACEs.

## Basic conditional ACE

```
$ sd add /srv/data/plans allow Engineering FILE_READ_DATA \
    if '@User.department == "Engineering"'
```

The ACE only applies when the SID matches **and** the expression evaluates to true.

## Expression syntax

### Comparisons

```
@User.clearance >= 3
@User.department == "Engineering"
@Resource.classification != "public"
@User.hireYear < 2025
```

### Logical operators

```
@User.department == "Engineering" && @User.clearance >= 3
@User.department == "Engineering" || @User.department == "Research"
!(@User.contractor == true)
```

### Set operations

```
@User.projects Contains "atlas"
@User.department AnyOf {"Engineering", "Research", "QA"}
@User.groups MemberOf {"project-leads"}
```

### Existence checks

```
Exists @User.clearance
Not_Exists @Resource.classification
```

## Practical examples

**Restrict confidential files to cleared users on managed devices:**

```
$ sd add /srv/data/confidential deny "Authenticated Users" FILE_READ_DATA \
    if '@User.clearance < 3 || @Device.managed != true'
$ sd add /srv/data/confidential allow "Authenticated Users" FILE_READ_DATA
```

The conditional deny blocks users without sufficient clearance or on unmanaged devices. The unconditional allow grants everyone else.

**Grant write access only to project members:**

```
$ sd add /srv/projects/atlas allow "Domain Users" FILE_WRITE_DATA \
    if '@User.projects Contains "atlas"'
```

Only users with "atlas" in their projects claim can write. Other Domain Users can't.

**Deny access to archived resources:**

```
$ sd add /srv/data deny Everyone FILE_WRITE_DATA ci,oi \
    if '@Resource.status == "archived"'
```

Files tagged as archived become read-only for everyone. The inheritable flags ensure the deny propagates through the directory tree.

## Combining with resource attributes

Conditional ACEs are most powerful when combined with resource attributes on the objects. Tag the objects:

```
$ sd attr /srv/data/report.pdf set classification confidential
$ sd attr /srv/data/report.pdf set project atlas
```

Then write ACEs that reference those attributes:

```
$ sd add /srv/data deny Everyone FILE_READ_DATA ci,oi \
    if '@Resource.classification == "confidential" && !(@User.projects Contains @Resource.project)'
```

This single rule denies access to any confidential file unless the user is assigned to that file's project. The same ACE works across all files in the tree — the policy adapts based on each file's attributes.

## Verify with sd explain

Check that the expression evaluates as expected:

```
$ sd explain /srv/data/report.pdf 2041 FILE_READ_DATA
Token:   S-1-5-21-...-1013 (alice)
Object:  /srv/data/report.pdf
Request: FILE_READ_DATA

[3] DACL walk
    ACE 1: Deny  Everyone  FILE_READ_DATA
           IF (@Resource.classification == "confidential"
               && !(@User.projects Contains @Resource.project))
           SID match: yes
           @Resource.classification = "confidential" — true
           @User.projects = ["atlas", "nova"]
           @Resource.project = "atlas"
           @User.projects Contains "atlas" — true
           !(true) — false
           Expression: false — ACE skipped
    ACE 2: Allow Domain Users FILE_READ_DATA
           SID match: yes
           FILE_READ_DATA — granted

Result: GRANTED
```

The explain output shows each sub-expression evaluated, making it clear why the conditional ACE did or did not fire.
