---
title: Managing file security
type: how-to
description: Inspect a file's security descriptor, choose a narrow sd change, and verify the result without assuming ownership or a saved descriptor guarantees recovery.
related:
  - peios/file-access/overview
  - peios/file-access/the-handle-model
  - peios/sdk-access-control/securing-files
  - peios/security-descriptors/overview
  - peios/security-descriptors/ownership
  - peios/files-and-directories/sd
---

Use [`sd`](~peios/files-and-directories/sd) to inspect and change a file's owner, access rules, audit rules or integrity label. Start with one known path and one intended change. A permission failure is a reason to [diagnose the denied operation](~peios/access-decisions/debugging-a-denial), not to replace the descriptor or grant full control.

> [!WARNING]
> Ownership is not a recovery guarantee. An `OWNER RIGHTS` ACE can suppress the owner's implicit `READ_CONTROL` and `WRITE_DAC`, and other access layers can still deny a change. Taking ownership preserves the existing DACL, including that suppression. Before removing access, establish which authorized principal can still read and repair the policy. See [Ownership and implicit rights](~peios/security-descriptors/ownership).

## 1. Inspect the path and current policy

These commands only inspect the example file; replace `./report.txt` with the intended path:

```sh
sd show ./report.txt --all
sd show ./report.txt --sddl
sd check ./report.txt read --explain
```

Record the owner, DACL entries and their order, inheritance flags, and any displayed label or audit policy. Keep the output as a before-change record. It is not a tested rollback procedure: restoring it would require the relevant rights, and a partial or failed inspection is not a complete descriptor backup.

A named symlink follows its target by default. To inspect or change the link itself, use the documented `--no-follow-symlinks` (`-P`) flag consistently. Confirm which object you mean before writing.

`sd check` rehearses an access decision without performing the operation. Its result is evidence for the selected token and descriptor; it does not prove that an application's original operation will work. If inspection fails or leaves necessary policy unknown, resolve that visibility gap before changing it.

## 2. State the intended change

Choose the smallest component and scope that express the policy. The [command reference](~peios/files-and-directories/sd) has the complete syntax.

| Intended result | Documented command family | What to check first |
|---|---|---|
| Add an allow or deny ACE | `sd allow`, `sd deny` | Principal, exact rights, ACE order and inheritance flags. `--replace` removes existing rules for that principal and kind before adding. |
| Remove a principal's DACL rules | `sd remove` | It removes **every allow and deny** rule for each named principal. Removing a deny can increase access. |
| Change owner or primary group | `sd owner`, `sd group` | `WRITE_OWNER` and the new-owner SID restrictions below; ownership does not grant file-data access. |
| Change audit rules | `sd audit`, `sd unaudit` | SACL authority. `unaudit` removes every SACL rule for the named principals. |
| Change an integrity label | `sd integrity` | Intended mandatory policy, `WRITE_OWNER` and the caller's integrity constraint. Do not lower a label merely to make a denial disappear. |
| Change inheritance or refresh children | `sd inherit`, `sd reset`, `sd propagate` | Whether explicit child rules or protection should survive; inspect the affected descendants first. |
| Replace a reviewed descriptor or selected components | `sd set` | The full replacement and its recovery path. `--components` selects which owner/group/DACL/SACL parts to write; do not use a whole-descriptor replacement for a one-ACE change. |

> [!WARNING]
> Do not add `--recursive` as a convenience. It changes descendants as well as the named object, implies no-follow-symlinks, and is not a tree-wide transaction. `sd propagate` reports descendants it cannot change and continues. Protected descendants keep their own rules, but files below them can still be refreshed from those descendants. Review failures and partial results individually.

`sd reset` drops explicit rules and protection and rebuilds the DACL from the parent. `sd remove --allow-empty` permits a present-but-empty DACL, which grants no rights through its ACE list. An absent DACL has very different, permissive semantics. Neither is a routine way to fix an unexplained denial; see [DACL evaluation](~peios/security-descriptors/dacl-evaluation).

Inheritance is stored on the child. Changing the parent's rules does not update existing children automatically; propagation is a separate, intentional operation.

## 3. Make the bounded change

For example, if the approved policy is to add read access for the identity running `sd` on this one file:

```sh
sd allow ./report.txt @self:read
```

`@self` means the current caller's user SID, not the file owner and not the user of another application. Choose the intended principal explicitly. This adds an ACE; it does not remove earlier denies or bypass mandatory policy. A later allow cannot change a right already decided by an earlier matching ACE.

Run only the command matching the intended change. Avoid concurrent edits to the same descriptor. Component selection preserves unselected fields, but a read/edit/write sequence does not reserve the policy against another writer. The [kernel storage contract](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#caching) describes last-writer-wins behavior and a cache/xattr publication window, not an end-to-end transaction.

## 4. Verify policy and the original operation

After the change, inspect the same object again and compare it with the before-change record:

```sh
sd show ./report.txt --all
sd check ./report.txt read --explain
```

Check that the intended principal and rights changed and that unrelated owner, audit, label and inheritance policy stayed as intended. Then retry the original operation with its actual caller. Check both access that should succeed and access the policy should still refuse, where it is safe to do so.

Existing file handles keep the rights granted when they were opened. A DACL edit is not a revocation of those handles; use a fresh open to test future access. See [The handle model](~peios/file-access/the-handle-model).

A nonzero `sd` status can mean a failed operation, an unreachable path, or a denied `sd check`; read the diagnostic. After recursive work, inspect the reported failures and representative descendants rather than treating the whole tree as changed. If the result differs from the intention, stop widening the change and use the [denial guide](~peios/access-decisions/debugging-a-denial).

## Why the xattr layer is denied

Do not edit the backing `security.peios.sd` or `system.ntfs_security` xattr. Raw reads, writes and removal are denied. Use `sd`, or the component-aware SDK interface when writing a program; this keeps validation and the separate SACL gate intact. See [File Descriptor Storage](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage).

## Rights and constraints

| Component | Reading needs | Changing needs |
|---|---|---|
| Owner or primary group | `READ_CONTROL` | `WRITE_OWNER`; new-owner SID validation also applies. |
| DACL | `READ_CONTROL` | `WRITE_DAC` |
| SACL | `ACCESS_SYSTEM_SECURITY` | `ACCESS_SYSTEM_SECURITY`, gated by `SeSecurityPrivilege`. |
| Integrity label only | `READ_CONTROL` | `WRITE_OWNER`; without `SeRelabelPrivilege`, the new label cannot exceed the caller's integrity. |

Requests for several components must pass every required check. MIC, PIP and other access layers still apply; owner implicit rights are not an exception to all of them.

Without `SeRestorePrivilege`, a new owner must be the caller's user SID or a token group carrying `SE_GROUP_OWNER`. Being the owner or an administrator does not itself prove the operation can pass `WRITE_OWNER`. See [Changing ownership](~peios/security-descriptors/ownership#changing-ownership).

A label-only change preserves non-label SACL entries; a full SACL write replaces the whole SACL. The integrity constraint applies through either path. Existing mandatory resource attributes cannot be removed or modified without `SeTcbPrivilege`.

For programs, the [SDK guide](~peios/sdk-access-control/securing-files#raw-file-security-interface) covers `kacs_get_sd`, `kacs_set_sd`, mutually exclusive SACL/label requests, the 65,535-byte validation limit and component merging. Operator changes should use the component command rather than construct a binary descriptor.

## What about file mode (the POSIX rwx bits)?

`chmod` changes mode metadata, not the DACL. FACS does not use the ordinary rwx bits to authorize access; the execute bit still matters as an exec prerequisite. Use `sd` to change the access policy.

- `fchmod()` needs `WRITE_DAC` in the fd's granted mask; otherwise it fails with `EACCES` (`EBADF` for an `O_PATH` fd). Legacy opens request this as a compatibility right.
- `chmod()` runs a fresh check for `WRITE_DAC`.
- Neither operation changes the descriptor.

See [Use-Time Checks](~peios/advanced-peios/peios-kernel/kacs/facs/use-time) for the syscall behavior.

## Errors

If a change is denied, check the required component right, the caller, owner-SID constraints, integrity and other mandatory policy before retrying. A read-only mount can refuse a write even if the descriptor permits it. Do not infer that a failed multi-object run left every object unchanged.

The [SDK error reference](~peios/sdk-access-control/securing-files#file-security-errors) distinguishes access, validation, buffer and path errors for programs. For an operator, keep `sd`'s diagnostic and follow [Debugging a denial](~peios/access-decisions/debugging-a-denial).

## See also

- [The sd command](~peios/files-and-directories/sd) — exact command syntax and flags.
- [Ownership](~peios/security-descriptors/ownership) — owner-transfer rules and recovery limits.
- [Securing files](~peios/sdk-access-control/securing-files) — SDK examples and the moved raw-interface detail.
- [Caller-supplied descriptors](~peios/advanced-peios/peios-kernel/kacs/facs/native-open#caller-supplied-descriptors) — the kernel reference for supplying an SD at creation; see its [documentation discrepancies](~peios/advanced-peios/peios-kernel/kacs/kacs-abi-notes#open-interface-documentation-discrepancies) before using the developer examples.
