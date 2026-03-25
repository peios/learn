---
title: Working with Auditing
type: how-to
order: 110
description: Managing audit ACEs, enabling continuous auditing, and querying audit events with the sd and eventctl tools.
---

Audit rules are managed through the `sd` tool. Modifying audit rules requires `SeSecurityPrivilege` because they live in the SACL.

## Set audit rules on an object

Add an audit ACE to the SACL:

```
$ sd audit add /srv/data/finance/accounts.db \
    audit Administrators FILE_WRITE_DATA success
```

This audits every successful write to the file by members of the Administrators group.

## Audit both success and failure

```
$ sd audit add /srv/data/finance/accounts.db \
    audit Everyone FILE_READ_DATA failure
```

Auditing failures only — this logs every denied read attempt, which is useful for detecting unauthorized access patterns.

To audit both:

```
$ sd audit add /srv/data/sensitive.key \
    audit Everyone FILE_READ_DATA success,failure
```

Every read attempt — successful or denied — is logged.

## View audit rules on an object

```
$ sd show /srv/data/finance/accounts.db
...
SACL:
  Audit  Administrators  FILE_WRITE_DATA  (success)
  Audit  Everyone        FILE_READ_DATA   (failure)
```

## Remove an audit rule

```
$ sd audit remove /srv/data/finance/accounts.db \
    audit Administrators FILE_WRITE_DATA success
```

## Enable continuous auditing on a file

Continuous auditing logs every individual operation, not just the initial open:

```
$ sd audit add /srv/data/classified/plans.pdf \
    continuous Everyone FILE_READ_DATA success
```

Every read operation on this file — not just the open — generates an audit event.

## Set per-token audit overrides

Per-token audit policy forces auditing for a specific principal regardless of what the object's SACL says. This is configured in the token at creation time, typically through the service definition or authentication policy.

To inspect a token's audit policy:

```
$ idn show 2041
...
Audit Policy:
  FILE_WRITE_DATA  success,failure  (all objects)
```

This token generates audit events for every write attempt — successful or denied — on any object it accesses.

## Read audit events

Query the audit log through eventd:

```
$ eventctl query --type access-audit --last 1h
```

```
2026-03-25T14:23:01Z  ACCESS_GRANTED
  Subject: S-1-5-21-...-1013 (alice)
  Object:  /srv/data/finance/accounts.db
  Access:  FILE_WRITE_DATA
  Trigger: SACL ACE match (Administrators, success)
  Process: PID 3841 /usr/bin/dbadmin

2026-03-25T14:23:15Z  ACCESS_DENIED
  Subject: S-1-5-21-...-1028 (bob)
  Object:  /srv/data/finance/accounts.db
  Access:  FILE_READ_DATA
  Trigger: SACL ACE match (Everyone, failure)
  Process: PID 4102 /usr/bin/report-gen
```

## Filter audit events

Filter by principal, object, time, or outcome:

```
$ eventctl query --type access-audit --user alice --last 24h
$ eventctl query --type access-audit --path "/srv/data/finance/*" --outcome denied
$ eventctl query --type privilege-use --last 1h
```

Privilege-use events are a separate event type, showing when privileges were exercised to grant access the DACL would not have:

```
2026-03-25T14:30:00Z  PRIVILEGE_USE
  Subject: S-1-5-21-...-500 (Administrator)
  Object:  /srv/data/backup/full-2026-03-25.tar
  Access:  FILE_READ_DATA
  Privilege: SeBackupPrivilege
  Process: PID 5001 /usr/lib/peios/backup-agent
```
