---
title: Working with cgroups
type: how-to
description: Creating cgroups, setting limits, attaching processes, delegating subtrees, reading counters and pressure metrics, and diagnosing access denials.
related:
  - peios/resource-management/understanding-cgroups
  - peios/process-silos/working-with-process-silos
  - peios/access-control/security-descriptors
---

cgroup state is visible through standard filesystem tools on `/sys/fs/cgroup` and through `idn proc` for a process's cgroup membership. Access denials on cgroup operations are diagnosed with `sd explain`, the same as any other DACL-gated operation.

## Inspect a process's cgroup

`idn show` includes the process's cgroup path:

```bash
$ idn show 8492
User:         S-1-5-21-...-1055 (jellyfin)
Integrity:    System
Logon Session: 47812 (Service)
...
Cgroup:       /sys/fs/cgroup/services/jellyfin
```

The path is given in the process's own cgroup namespace view. From outside the namespace, the same cgroup may have a longer path; from inside, it is rooted at `/`.

## Inspect a cgroup

A cgroup is a directory; `ls` shows its files and children:

```bash
$ ls /sys/fs/cgroup/services/jellyfin
cgroup.controllers   cpu.max          memory.current  memory.swap.max
cgroup.events        cpu.pressure     memory.events   pids.current
cgroup.freeze        cpu.stat         memory.high     pids.max
cgroup.kill          cpu.weight       memory.low      pids.peak
cgroup.procs         io.max           memory.max      pids.events
cgroup.stat          io.pressure      memory.min      cgroup.subtree_control
cgroup.threads       io.stat          memory.pressure cgroup.type
cgroup.type          io.weight        memory.stat     cgroup.controllers
```

Read any control file to see its current value:

```bash
$ cat /sys/fs/cgroup/services/jellyfin/cpu.max
200000 100000
$ cat /sys/fs/cgroup/services/jellyfin/memory.current
1837498368
$ cat /sys/fs/cgroup/services/jellyfin/cpu.pressure
some avg10=0.04 avg60=0.02 avg300=0.01 total=18374923
full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

The DACL on each file gates the read. By default a cgroup's owner and members can read its counters; arbitrary processes cannot.

## View a cgroup's Security Descriptor

`sd show` works on cgroup paths the same way it works on any filesystem object:

```bash
$ sd show /sys/fs/cgroup/services/jellyfin
Owner: S-1-5-32-544 (Administrators)
Group: S-1-5-32-544 (Administrators)
DACL:
  Allow  S-1-5-32-544 (Administrators)        FILE_ALL_ACCESS
  Allow  S-1-5-21-...-1055 (jellyfin)         FILE_READ_DATA, FILE_WRITE_DATA
  Allow  S-1-5-1515-1-849273-... (silo-jellyfin) FILE_READ_DATA
SACL:
  (none)
```

Access rights have their normal filesystem meanings — `FILE_WRITE_DATA` on a control file lets you change the limit, `FILE_ADD_SUBDIRECTORY` on a directory lets you create child cgroups.

## Create a top-level cgroup

Creating directly under the cgroup root requires `SeCreateResourceGroupPrivilege`:

```bash
$ idn priv add SeCreateResourceGroupPrivilege
$ mkdir /sys/fs/cgroup/services
$ sd add /sys/fs/cgroup/services allow S-1-5-32-544 FILE_ALL_ACCESS
```

Without the privilege the `mkdir` is denied even if the root cgroup's DACL would otherwise permit it. The privilege gate is the primary control on top-level allocation; DACLs handle delegation within an established subtree.

## Create a child cgroup

Within an existing subtree, creating a child requires only `FILE_ADD_SUBDIRECTORY` on the parent:

```bash
$ mkdir /sys/fs/cgroup/services/jellyfin
$ mkdir /sys/fs/cgroup/services/postgres
$ mkdir /sys/fs/cgroup/services/postgres/replicas
```

The new cgroup inherits the parent's DACL under standard container inheritance.

## Enable controllers for a subtree

A cgroup can only use controllers its parent has enabled in `cgroup.subtree_control`. Enabling a controller in the subtree control file makes it available to children:

```bash
$ echo "+cpu +memory +io +pids" > /sys/fs/cgroup/services/cgroup.subtree_control
```

Disabling a controller is `-name`. The set of currently-available controllers is in `cgroup.controllers`.

## Set limits

Writing to a control file changes the limit:

```bash
# Limit jellyfin to 2 CPUs of bandwidth (200ms quota per 100ms period)
$ echo "200000 100000" > /sys/fs/cgroup/services/jellyfin/cpu.max

# Memory hard cap at 4 GiB
$ echo $((4 * 1024 * 1024 * 1024)) > /sys/fs/cgroup/services/jellyfin/memory.max

# Soft memory target at 3 GiB (triggers reclaim before hitting max)
$ echo $((3 * 1024 * 1024 * 1024)) > /sys/fs/cgroup/services/jellyfin/memory.high

# Cap process count
$ echo 256 > /sys/fs/cgroup/services/jellyfin/pids.max

# IO bandwidth on a specific device
$ echo "8:0 rbps=100000000 wbps=50000000" > /sys/fs/cgroup/services/jellyfin/io.max
```

Each write is gated by `FILE_WRITE_DATA` on the control file. The DACL on the cgroup directory propagates to its control files under inheritance, so granting an owner write access to the cgroup is enough.

## Attach a process

Writing a PID to `cgroup.procs` migrates that process into the cgroup:

```bash
$ echo 8492 > /sys/fs/cgroup/services/jellyfin/cgroup.procs
```

This is the operation with two access checks:

- `FILE_WRITE_DATA` on `/sys/fs/cgroup/services/jellyfin/cgroup.procs` — you have authority over this cgroup.
- `PROCESS_SET_QUOTA` on PID 8492's process SD — you have authority to constrain that process.

A failure on either denies the operation. The migration is atomic — either the process moves successfully and all controller limits begin applying, or nothing changes.

Forks inherit the parent's cgroup. To put a service and all its descendants in a cgroup, attach the supervisor process and let fork inheritance handle the rest.

## Delegate a subtree

Delegation is a standard DACL operation. Add an ACE granting management rights to the subtree owner:

```bash
$ sd add /sys/fs/cgroup/services/jellyfin allow S-1-5-21-...-1055 FILE_ALL_ACCESS:CI
```

The `:CI` (container inherit) propagates the ACE to every cgroup created within the subtree. From this point, the jellyfin user can:

- Create child cgroups under `/sys/fs/cgroup/services/jellyfin`
- Set any limits within their delegated allotment
- Attach their own processes
- Read all counters

They **cannot**:

- Expand limits beyond what the parent allows (the hierarchy enforces intersection)
- Create top-level cgroups (no `SeCreateResourceGroupPrivilege`)
- Move processes they don't have `PROCESS_SET_QUOTA` on into their subtree

This is the safe-delegation pattern: a privileged setup carves out a budget and hands it over; the recipient manages within bounds without further privilege escalation.

## Read counters

All accounting is via reading control files. Per-cgroup metrics include CPU usage, memory consumption, IO statistics, and pressure stall information:

```bash
# CPU usage breakdown
$ cat /sys/fs/cgroup/services/jellyfin/cpu.stat
usage_usec 38291847200
user_usec 24018372901
system_usec 14273474299
nr_periods 1827372
nr_throttled 0
throttled_usec 0
nr_bursts 0
burst_usec 0

# Memory accounting
$ cat /sys/fs/cgroup/services/jellyfin/memory.stat | head -10
anon 1283746816
file 384720384
kernel 24764416
...

# Pressure stall — fraction of time tasks waited for the resource
$ cat /sys/fs/cgroup/services/jellyfin/cpu.pressure
some avg10=0.04 avg60=0.02 avg300=0.01 total=18374923
full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

`some` is the time at least one task was stalled; `full` is the time *all* non-idle tasks were stalled. Autoscaling and oncall alerting typically watch the `avg10` and `avg60` fields.

## Freeze a cgroup

`cgroup.freeze` halts all processes in the cgroup atomically:

```bash
$ echo 1 > /sys/fs/cgroup/services/jellyfin/cgroup.freeze
# Processes are now frozen — no scheduling, no signals delivered
$ echo 0 > /sys/fs/cgroup/services/jellyfin/cgroup.freeze
# Resumed
```

Freezing is useful for snapshots, debugging, or planned maintenance. Frozen processes are not signal-stopped — they can't be interrupted with `SIGCONT` from outside. The only way out is writing `0` to `cgroup.freeze`.

## Kill a cgroup

`cgroup.kill` sends `SIGKILL` to every process in the cgroup at once:

```bash
$ echo 1 > /sys/fs/cgroup/services/jellyfin/cgroup.kill
```

This is the cleanest way to terminate a service group: every member dies simultaneously with no chance for one process to spawn replacements before the kill propagates. The cgroup itself remains and can be reused.

## Diagnose a denied operation

`sd explain` traces the AccessCheck for a cgroup operation the same as any filesystem operation:

```bash
$ sd explain /sys/fs/cgroup/services/jellyfin/cpu.max 8492 FILE_WRITE_DATA
Token:   S-1-5-21-...-1080 (alice)
Object:  /sys/fs/cgroup/services/jellyfin/cpu.max
Request: FILE_WRITE_DATA

[3] DACL walk
    ACE 1: Allow  Administrators           FILE_ALL_ACCESS
           SID match: no — skip
    ACE 2: Allow  jellyfin (S-1-5-21-...-1055)  FILE_READ_DATA, FILE_WRITE_DATA
           SID match: no — skip
    ACE 3: Allow  silo-jellyfin (S-1-5-1515-1-...)  FILE_READ_DATA
           SID match: no — alice is not in the silo — skip
    No matching grant.

Result: DENIED — no DACL ACE grants FILE_WRITE_DATA to alice
```

The fix depends on intent — either grant alice (or a group she's in) write access to the control file, or run the limit-setting from a process whose token does match an existing ACE.

## Diagnose a denied process attach

For attach failures, both checks must pass — `sd explain` shows which one failed:

```bash
$ sd explain --attach /sys/fs/cgroup/services/jellyfin/cgroup.procs 8492 9201
Token:    S-1-5-21-...-1080 (alice)
Cgroup:   /sys/fs/cgroup/services/jellyfin
Target:   PID 9201 (jellyfin user)

[1] cgroup.procs DACL check
    ACE 2: Allow  jellyfin (S-1-5-21-...-1055)  FILE_WRITE_DATA — granted

[2] Target process SD check (PROCESS_SET_QUOTA on PID 9201)
    No ACE grants alice PROCESS_SET_QUOTA — denied

Result: DENIED — alice has authority over the cgroup but not over PID 9201
```

This shape — two checks, both must pass — appears anywhere in Peios that one principal applies state to another (cross-process operations, namespace entry from outside a silo, etc.).

## Common mistakes

**Trying to attach a process you don't own.** Even if you have full write access to the destination cgroup, the target process's SD must grant `PROCESS_SET_QUOTA`. Use `sd show /proc/<pid>` to see the process SD; if you need to attach foreign processes, the operator setting up the cgroup needs to grant that right to your principal.

**Putting processes in non-leaf cgroups.** v2 forbids processes in cgroups that have controller-enabled children (the no-internal-process constraint). The write to `cgroup.procs` returns `EBUSY`. Move to a leaf cgroup or remove the children.

**Forgetting to enable controllers in the subtree.** A child cgroup's `cpu.max` doesn't exist if the parent didn't add `+cpu` to its `subtree_control`. The fix is `echo "+cpu +memory" > parent/cgroup.subtree_control`.

**Hitting hierarchy depth limits.** `EAGAIN` on `mkdir` usually means the system-wide `\System\Cgroups\DefaultMaxDepth` or a tighter per-subtree `cgroup.max.depth` was reached. Defaults are generous; hitting them usually indicates a runaway script. Check the current effective limit by reading `cgroup.max.depth` in the affected cgroup and its ancestors.

**Expecting cgroups to provide visibility isolation.** A process in a cgroup can still see and signal processes outside it, subject to standard process SD checks. For visibility isolation, use a [PID namespace](../process-silos/namespaces).
