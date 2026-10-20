---
title: Interpreting Process State
type: how-to
description: Distinguish waiting, suspension, and completed work before taking a process or workload action.
---

Inspect the process and its managing workload before deciding that a state
means failure. Sleeping is normal for a program waiting for work.

## Read the state

| State | Interpretation |
|---|---|
| Running or runnable | Executing or ready to be scheduled. |
| Sleeping | Waiting for an event; this alone does not indicate failure. |
| Stopped | Suspended, with work able to continue after a resume. |
| Traced | Stopped under a debugger's control. |
| Uninterruptible wait | Waiting on an operation that ordinary signals cannot interrupt. |
| Zombie | Execution has ended; an exit result remains to be collected. |

A persistent uninterruptible wait calls for inspecting the underlying I/O or
kernel wait, not repeatedly sending a stronger signal. A zombie cannot be
fixed by terminating it again. Inspect the parent that should collect its
result; accumulated unreaped children can consume process-table resources.

## Choose and verify an action

1. Identify the current process, its owner, parent, and service or job. Save
   work before requesting termination.
2. Choose the intended scope. Use `svctl stop NAME` for a service or
   `svctl job stop ID` for a submitted job. Ending only a service's main
   process can trigger its restart policy.
3. For one process, use Task Manager's **End process**, or `kill PID` to
   request orderly termination. Give the application time to finish.
4. Refresh process and workload state. Successful signal delivery does not
   establish that termination has completed.
5. If orderly termination fails and loss of unfinished work is acceptable,
   use the tool's force-termination operation. Recheck a numeric PID before
   using it again. Force termination skips application cleanup and cannot
   resolve an underlying uninterruptible wait.

`kill -STOP PID` and `kill -CONT PID` suspend and resume one process when
permitted. They do not finish its work or target an entire service. Pausing a
process can leave resources held and dependent work blocked.

Signal permissions depend on the operation, and process protection remains
relevant. Sharing an account or terminal is not a general bypass. The
[kill guide](~peios/system-and-processes/kill) and
[service controls](~peios/services-and-jobs/controlling-services) describe the
owning interfaces.

## Exit and cleanup

The parent collects a child's result through a wait operation. That result
distinguishes ordinary exit from signal termination. Child-state notifications
prompt the parent to check; they are not a replacement for collecting results.
When a parent exits first, a subreaper or Peinit adopts remaining children.

Exit releases resources, but other owners can keep shared objects alive.
Token handles elsewhere and unreaped processes can keep a logon session
present after its visible work has ended. See [Inspecting and Ending
Sessions](~peios/system-and-processes/logonse) before interpreting a remaining
session as a still-running application.
