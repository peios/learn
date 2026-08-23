---
title: Assigning privileges
type: reference
description: The policy records under Machine\Generic\Authn\Policy that authd reads at every logon — which privileges a principal gets, and at what integrity level.
related:
  - peios/privileges/overview
  - peios/privileges/categories
  - peios/managing-local-principals/overview
  - peios/tokens/overview
  - peios/process-integrity-protection/overview
---

A principal source says **who someone is** — their SID, their memberships, their POSIX identifiers. It never says how much this machine trusts them. Privileges and integrity are **local policy**: `authd`'s alone, decided here, and there is no message with which a source could ask for one.

That policy lives in the registry:

```
Machine\Generic\Authn\Policy
```

`authd` reads it at **every logon**, not once at startup. A policy change takes effect the next time someone signs in, rather than the next time you restart the one daemon on the system that is most disruptive to restart.

## One record per principal

Each subkey is a principal, and holds everything this machine grants them:

```
Machine\Generic\Authn\Policy
  DeniedPrivileges  REG_MULTI_SZ  ["SeDebugPrivilege"]
  \Everyone
      Privileges    REG_MULTI_SZ  ["SeChangeNotifyPrivilege"]
  \Administrators
      Privileges    REG_MULTI_SZ  ["SeBackupPrivilege", "SeRestorePrivilege"]
      Integrity     REG_SZ        "High"
      Owner         REG_SZ        "Administrators"
      DefaultDacl   REG_SZ        "D:(A;;GA;;;SY)(A;;GA;;;BA)"
```

Keyed by principal rather than by privilege on purpose. One key shows the totality of a principal's authority — `reg ls` on `\Administrators` answers "what can an administrator do on this machine?" completely. Authority scattered across twenty per-privilege values is authority nobody audits: a right granted somewhere unexpected does not surface when you look at the principal, and you would have to know to check every other place.

It is also the only shape that holds more than privileges. Integrity, the default owner and the default DACL live on the same record, and logon rights will when they arrive.

### Naming a principal

A subkey's name is either a **well-known name** or a **literal SID**:

```
\Administrators
\S-1-5-21-2847362817-1094533892-3310298447-1000
```

Names are matched case-insensitively. The recognised ones are `SYSTEM`, `Everyone`, `Authenticated Users`, `Administrators`, `Users`, `Guests`, `Local Service`, `Network Service`, and the logon types `Interactive`, `Network`, `Batch`, `Service` and `Anonymous`.

Two limits are worth knowing before you hit them:

**`BUILTIN\Administrators` cannot be a subkey name.** A backslash is the registry's path separator, so the qualified spelling is unrepresentable. Write the bare name.

**A local group's name does not resolve.** `authd` cannot know what `developers` means without asking `lpsd`, and policy must never depend on a principal source being up — that would make "what may this principal do" unanswerable exactly when a source is broken. Name local groups by SID, which `lps group list` will show you.

A subkey that is neither a known name nor a parseable SID is **ignored with a warning**. It is worth checking for that warning after editing: a record naming nobody sits in the key looking authoritative and applying to no one.

## If the key exists, the key is the whole policy

This is the most important behaviour on the page.

`authd` carries a compiled-in floor, but it applies **only when the key is absent entirely**. It is not merged in value by value. So a policy you write is the complete policy: anything not granted below is not granted.

| State | What a principal gets |
|---|---|
| Key absent | The compiled floor — `Everyone` gets `SeChangeNotifyPrivilege`, and nothing else |
| Key present | Exactly what the records say |
| Key present but unreadable | Nothing, and a loud log line |

The alternative — a compiled default that each record replaces — fails in the wrong direction. An administrator who writes one record believing they have locked the machine down would still be handing out whatever a compiled table said for every principal they did not mention, from a table they cannot read. That is a security failure, and a silent one. Failing towards less privilege makes things stop working, which is far easier to diagnose than authority you did not know you were granting.

An unreadable key is treated as granting nothing rather than as absent, for the same reason: reading it as absent would silently restore every privilege an administrator may have deliberately removed, at the one moment nobody can check.

## What a machine ships with

The defaults are **registry data, not compiled in** — `authd-policy.reg`, shipped to `/usr/share/regim/` and applied if the image opts in. So they can be read, edited, and replaced wholesale by an image that wants a different policy, rather than being invisible inside a binary.

A stock machine grants:

| Principal | Privileges | Integrity |
|---|---|---|
| `Everyone` | `SeChangeNotifyPrivilege`, `SeCreateSymbolicLinkPrivilege` | (Medium, by default) |
| `Administrators` | the operational set below, plus both of the above | High |

The operational set is `SeBackupPrivilege`, `SeRestorePrivilege`, `SeShutdownPrivilege`, `SeRemoteShutdownPrivilege`, `SeSystemtimePrivilege`, `SeSecurityPrivilege`, `SeLoadDriverPrivilege`, `SeImpersonatePrivilege`, `SeIncreaseQuotaPrivilege`, `SeIncreaseBasePriorityPrivilege` and `SeProfileSingleProcessPrivilege`.

**`SeDebugPrivilege` is deliberately not granted.** It writes to any process regardless of integrity label, so it is the single privilege that most directly defeats the integrity boundary, and ordinary administration does not need it. Add it when a machine genuinely does.

Three privileges are never granted by the shipped policy and should not be added: `SeCreateTokenPrivilege` mints any identity without going near `authd`, which would make every other control here decorative; `SeTcbPrivilege` and `SeAssignPrimaryTokenPrivilege` belong to the trusted computing base.

Note that `Administrators` is granted `SeChangeNotifyPrivilege` **directly**, not only through `Everyone`. Privileges accumulate across every SID on a token, so that repetition is insurance: if someone edits the key and drops the `Everyone` record, ordinary users lose the ability to traverse a directory — but administrators keep working and can repair it.

## How the values compose

**Privileges accumulate.** A token holds the union of every record naming a SID it carries — the principal's own, and each of their groups. A group marked `USE_FOR_DENY_ONLY` contributes nothing.

**`DeniedPrivileges` wins.** Listed on the `Policy` key itself rather than on a record, it is applied *after* the union, so no record you have not read can defeat it. It is on the parent key so it cannot collide with a principal who happens to be called `Denied`.

**Integrity, `Owner` and `DefaultDacl` are single values**, so they cannot accumulate. The principal's own record wins outright; otherwise the groups decide:

- **Integrity** takes the **maximum** across the groups that name one.
- **`Owner`** and **`DefaultDacl`** have no ordering to compare, so two groups naming *different* values is a misconfiguration: it logs a warning and falls back to the default rather than picking by whichever the registry enumerated first. Two groups naming the same value is not a conflict.

The user's record winning outright is what makes a principal possible to **lower**. Under a plain maximum, a guest whose own record said `Low` would still come out Medium the moment any group they belonged to named Medium. The consequence is worth stating plainly: a group cannot impose an integrity floor on a member. If `Administrators` names High and a member's own record names Low, that member gets Low.

## Writing each value

### `Privileges` — `REG_MULTI_SZ`

Full ABI names, `SeBackupPrivilege` rather than `SeBackup`, matched **case-sensitively**. A name this build does not recognise is dropped with a warning and the rest of the list still applies — a policy written for a newer Peios should not lose the privileges it spelled correctly.

An empty list is meaningful: it grants nothing, and is different from the value being absent.

### `Integrity` — `REG_SZ` or `REG_DWORD`

A tier name, matched case-insensitively:

| Name | Value |
|---|---|
| `Untrusted` | 0 |
| `Low` | 4096 |
| `Medium` | 8192 |
| `High` | 12288 |
| `System` | 16384 |

Or a raw `REG_DWORD`. The kernel compares integrity numerically and any value is legal, so the numeric form reaches levels between the tiers — `8193` sits just above Medium. Use the name unless you need that.

A principal no record names gets **Medium**. That default is compiled in and is not affected by the key existing, because unlike a privilege it is not a grant: every token must carry some level to be valid at all.

### `Owner` — `REG_SZ`

Which principal owns objects this token creates. Names a principal, exactly like a subkey name does; `authd` converts it to the index the token actually carries, which is a number meaningful only within one token and different on the next logon.

Absent — the ordinary case — means objects are owned by their creator.

The case this exists for is a shared administrative estate: objects an administrator creates being owned by `Administrators` rather than by the individual, so they remain manageable when that person's account goes away.

### `DefaultDacl` — `REG_SZ`

The DACL objects this token creates inherit when nothing else supplies one, written as **SDDL**:

```
D:(A;;GA;;;SY)(A;;GA;;;BA)
```

SDDL rather than raw bytes because the whole argument for policy living in the registry is that an operator can read it. Conditional ACEs are preserved, so `D:(XA;;GA;;;WD;(@USER.Department == "Engineering"))` works and keeps its condition.

A value that does not parse is dropped with a warning and the system default applies — a typo costs the customisation, not the session.

## Locking a machine down

To forbid a privilege regardless of what any record says:

```
Machine\Generic\Authn\Policy
  DeniedPrivileges  REG_MULTI_SZ  ["SeDebugPrivilege", "SeLoadDriverPrivilege"]
```

That is one edit, in one place, that a record you have not read cannot defeat. Removing the privilege from each record individually relies on having found them all.

## What this cannot express yet

**Whether a principal may sign in at all.** Policy decides what a session gets, not whether one happens. `lps disable` covers the blunt case; per-logon-type restriction — allowed over the network but not at the console — is not built.

**Two privileges the kernel enforces but nothing can name.** `SeTakeOwnershipPrivilege` and `SeRelabelPrivilege` are honoured by the access check and appear in audit records, but are absent from the published ABI, so no policy can grant them. `SeSystemProfilePrivilege` is in the same position on current builds. Until that is resolved, a Peios machine has no way to grant take-ownership — which means the documented escape hatch for a file whose DACL excludes you is not currently reachable.

## Seeing what a token actually got

```
$ token show --all
```

`[privileges]` lists what the token holds and `integrity` shows the label. A privilege the tool cannot name appears as `<privilege bit N>` rather than being omitted, so the list is always complete even when the name table is not.

## See also

- [Privileges](~peios/privileges/overview) — the model these records feed.
- [The token command](~peios/tokens/token-command) — reading the privileges and integrity a live token actually carries.
- [Managing local principals](~peios/managing-local-principals/overview) — the accounts these records apply to.
