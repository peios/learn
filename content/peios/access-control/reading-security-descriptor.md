---
title: Reading an Object's Security Descriptor
type: how-to
order: 110
description: How to use sd show to inspect the owner, group, DACL, and SACL on files, registry keys, and processes.
---

Use `sd show` to inspect the security descriptor on any object.

## Show a file's security descriptor

```bash
$ sd show /srv/data/reports
Owner:  S-1-5-21-...-1013 (alice)
Group:  S-1-5-21-...-513 (Domain Users)

DACL:
  Deny   S-1-5-21-...-1028 (bob)           FILE_WRITE_DATA
  Allow  S-1-5-21-...-1013 (alice)         FILE_ALL_ACCESS
  Allow  S-1-5-21-...-513  (Domain Users)  FILE_READ_DATA | FILE_READ_ATTRIBUTES
  Allow  S-1-5-21-...-513  (Domain Users)  FILE_WRITE_DATA                          (inherited, CI | OI)

SACL:
  Mandatory Label: High
  Audit  S-1-5-32-544 (Administrators)     FILE_WRITE_DATA  (success, failure)
```

Each section of the output corresponds to a component of the security descriptor:

- **Owner** and **Group** — the SIDs with resolved names
- **DACL** — each ACE on its own line, showing type (Allow/Deny), SID, and rights. Inherited ACEs are marked with their origin and inheritance flags.
- **SACL** — mandatory integrity labels and audit ACEs. Audit ACEs show whether they trigger on success, failure, or both.

## Show a registry key's security descriptor

The same command works on registry keys:

```bash
$ sd show registry://HKLM/Software/Peios
Owner:  S-1-5-18 (SYSTEM)
Group:  S-1-5-18 (SYSTEM)

DACL:
  Allow  S-1-5-18          (SYSTEM)          KEY_ALL_ACCESS
  Allow  S-1-5-32-544      (Administrators)  KEY_ALL_ACCESS
  Allow  S-1-5-11          (Authenticated Users)  KEY_QUERY_VALUE | KEY_ENUMERATE_SUB_KEYS | KEY_NOTIFY | READ_CONTROL
```

The rights are object-type-specific (`KEY_*` instead of `FILE_*`), but the structure is the same.

## Show a process's security descriptor

```bash
$ sd show --process 1482
Owner:  S-1-5-19 (Local Service)
Group:  S-1-5-19 (Local Service)

DACL:
  Allow  S-1-5-19          (Local Service)   PROCESS_ALL_ACCESS
  Allow  S-1-5-18          (SYSTEM)          PROCESS_ALL_ACCESS
  Allow  S-1-5-80-2739571183 (DNS Service)   PROCESS_QUERY_INFORMATION | READ_CONTROL
```

## Detailed output

For full detail including all flags and raw bit values, use `--raw`:

```bash
$ sd show --raw /srv/data/reports
```

This shows inheritance flags on every ACE, the full access mask in hexadecimal alongside the named rights, and ACE flags that the default output omits.

## Structured output

For scripting, use `--json`:

```bash
$ sd show --json /srv/data/reports
```

Returns the complete security descriptor as structured data — owner, group, DACL, and SACL with all ACEs, flags, and masks.
