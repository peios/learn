---
title: Compatibility
---

## Format compatibility

LCS has one hard external format compatibility requirement:
**registry.pol**. The registry MUST support every data type, path
semantic, and operation that registry.pol can express -- the binary
format used by Active Directory Group Policy to deliver configuration
to domain-joined machines. registry.pol compatibility is the reason
the registry exists.

LCS is not responsible for parsing registry.pol files. Parsing is a
userspace concern -- the Group Policy client reads registry.pol and
translates its contents into registry syscalls. LCS provides the
data model and operations necessary to faithfully represent
everything registry.pol can express.

registry.pol drives the following format decisions:

- **Value types.** The full Windows registry value type set (REG_SZ,
  REG_EXPAND_SZ, REG_BINARY, REG_DWORD, REG_DWORD_BIG_ENDIAN,
  REG_LINK, REG_MULTI_SZ, REG_QWORD, REG_NONE) MUST be supported.
  LCS treats values as opaque typed blobs -- it stores the type tag
  but does not interpret the data, except REG_LINK which triggers
  symlink resolution.

- **Path format.** Registry paths use backslash separators and are
  case-preserving, case-insensitive. registry.pol paths follow this
  convention.

- **Access right bit positions.** Registry-specific access rights
  (KEY_QUERY_VALUE, KEY_SET_VALUE, KEY_CREATE_SUB_KEY, etc.) occupy
  the same bit positions as Windows registry access rights. This
  ensures Security Descriptors containing registry ACEs are
  binary-compatible. The bit positions are defined in the Access
  Rights section of this specification; the SD binary format itself
  is specified by KACS.

No other format parity with Windows is claimed or required by LCS.
SD binary format compatibility is a KACS guarantee, not an LCS one.

## Architectural divergences

LCS is modelled on the Windows Configuration Manager but diverges
in several areas. These are intentional design decisions, not
compatibility gaps.

| Divergence | Windows | LCS | Rationale |
|---|---|---|---|
| Backing store | Kernel-internal hive files | Userspace sources via RSI | Enables different storage backends without kernel changes. Storage is a source concern, not a kernel concern. |
| Hive routing | Fixed set of predefined hives | Extensible -- any source can register any hive name at runtime | Supports role installation, testing, and future hive types without kernel changes. |
| Layer system | No equivalent. registry.pol is applied by flattening values. | Precedence-ordered layers with tombstones. Reads resolve at query time. | Automatic revert on layer deletion (no-tattoo semantics). Role uninstall and GP removal are layer deletion. |
| Change observation | RegNotifyChangeKeyValue is single-shot (must re-register after each event) | Persistent watches (remain armed until fd closes) | Eliminates the race window between notification and re-registration where changes can be missed. Matches the inotify model. |
| Key identity | Hive cell offsets (internal) | GUIDs (128-bit, kernel-assigned, source-persisted) | Stable across storage reorganisation. Consistent with Peios's identifier model. |
| Forward slash | Not accepted in registry paths | Accepted on input, normalised to backslash | Convenience for Linux users. The canonical form is always backslash. |
| Case comparison | RtlCompareUnicodeString | Unicode Simple Case Folding (CaseFolding.txt, status S and C entries) | Practical compatibility with Windows behaviour, not byte-identical in all edge cases. Fixed one-to-one codepoint mapping with no locale dependency. |

## Excluded Windows features

The following Windows registry features have been evaluated and
excluded from LCS.

| Feature | Why excluded |
|---|---|
| Key classes | The "class" parameter in RegCreateKeyEx is documented as reserved by Microsoft. No known consumer. |
| RegOverridePredefKey | Per-process key redirection. COM-specific. Would require unbounded per-process state in the kernel. Private hives and private layers cover the legitimate use cases. |
| WoW64 redirection | 32/64-bit registry key splitting. Peios has no 32-bit compatibility concern. |
| HKEY_CLASSES_ROOT merged overlay | Merges HKLM and HKCU Software\Classes. COM-specific. No Peios equivalent. |
