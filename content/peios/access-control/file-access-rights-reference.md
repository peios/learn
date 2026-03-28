---
title: File Access Rights Reference
type: how-to
order: 200
description: Reference table of file and directory specific rights, standard rights, and generic-to-specific mappings.
---

A reference for the specific access rights defined for files and directories on Peios.

## File-specific rights

| Right | Bit | Meaning |
|---|---|---|
| `FILE_READ_DATA` | 0 | Read the file's contents |
| `FILE_WRITE_DATA` | 1 | Write to the file (overwrite existing data) |
| `FILE_APPEND_DATA` | 2 | Append to the file (write without overwriting) |
| `FILE_READ_EA` | 3 | Read the file's extended attributes |
| `FILE_WRITE_EA` | 4 | Write the file's extended attributes |
| `FILE_EXECUTE` | 5 | Execute the file |
| `FILE_DELETE_CHILD` | 6 | Delete a child entry from a directory (files do not use this right) |
| `FILE_READ_ATTRIBUTES` | 7 | Read the file's metadata (size, timestamps, etc.) |
| `FILE_WRITE_ATTRIBUTES` | 8 | Modify the file's metadata |

## Directory-specific aliases

Directories use the same bit positions with different names reflecting directory operations:

| Directory right | Same bit as | Meaning |
|---|---|---|
| `FILE_LIST_DIRECTORY` | `FILE_READ_DATA` | List the directory's contents |
| `FILE_ADD_FILE` | `FILE_WRITE_DATA` | Create a file in the directory |
| `FILE_ADD_SUBDIRECTORY` | `FILE_APPEND_DATA` | Create a subdirectory in the directory |
| `FILE_TRAVERSE` | `FILE_EXECUTE` | Traverse through the directory (pass through it to reach a child) |
| `FILE_DELETE_CHILD` | (bit 6) | Delete a file or subdirectory within this directory |

## Standard rights (apply to all object types)

| Right | Meaning |
|---|---|
| `DELETE` | Delete the file or directory |
| `READ_CONTROL` | Read the security descriptor |
| `WRITE_DAC` | Modify the DACL |
| `WRITE_OWNER` | Change the owner |
| `SYNCHRONIZE` | Wait on the file handle |

## Generic mappings for files

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `FILE_READ_DATA \| FILE_READ_ATTRIBUTES \| FILE_READ_EA \| READ_CONTROL \| SYNCHRONIZE` |
| `GENERIC_WRITE` | `FILE_WRITE_DATA \| FILE_APPEND_DATA \| FILE_WRITE_ATTRIBUTES \| FILE_WRITE_EA \| READ_CONTROL \| SYNCHRONIZE` |
| `GENERIC_EXECUTE` | `FILE_EXECUTE \| FILE_READ_ATTRIBUTES \| READ_CONTROL \| SYNCHRONIZE` |
| `GENERIC_ALL` | All specific rights, all standard rights |

## Common open flag translations

When a file is opened, the open flags translate to access rights:

| Open flag | Access rights requested |
|---|---|
| `O_RDONLY` | `FILE_READ_DATA \| FILE_READ_ATTRIBUTES` |
| `O_WRONLY` | `FILE_WRITE_DATA \| FILE_READ_ATTRIBUTES` |
| `O_RDWR` | `FILE_READ_DATA \| FILE_WRITE_DATA \| FILE_READ_ATTRIBUTES` |
| `O_APPEND` | Replaces `FILE_WRITE_DATA` with `FILE_APPEND_DATA` |
| `O_TRUNC` | Adds `FILE_WRITE_DATA` (truncation requires overwrite authority) |

These translations happen before AccessCheck runs. The open flags determine the desired access mask; AccessCheck evaluates that mask against the file's security descriptor.
