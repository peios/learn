---
title: How Peios Fits Together
type: concept
description: A map of Peios's components, from the kernel's own subsystems through boot, system services, and the desktop, the order in which a machine starts, and the kinds of documentation each part has.
related:
  - peios/introduction/what-is-peios
  - peios/boot/boot-and-boot-modes
  - peios/introduction/finding-your-way
---

A Peios machine is built from a small number of components, each with one
job. This page names them, shows the order in which they start, and says
where each is documented. When something goes wrong, the component that owns
the job is where to look.

## The kernel

The kernel manages the hardware and runs every program. Peios adds five
subsystems of its own to it:

| Subsystem | Job |
|---|---|
| Kernel Access Control Subsystem (KACS) | Access control: tokens, security descriptors, privileges, and every access decision |
| Layered Configuration Subsystem (LCS) | The registry: keys, values, layers, watches, and transactions |
| Kernel Mediated Event Subsystem (KMES) | Events: the single path every event takes, with trusted details about its sender |
| StrataFS | Layered storage: several directories, the strata that give it its name, presented as one directory tree |
| Network Traffic Filtering Engine (NTFE) | The network packet filter, which enforces network policy from the registry |

The subsystems rely on each other. The registry and the file systems use
KACS security descriptors, and KACS reports its access decisions through
KMES. The [Peios Kernel](~kernel) product documents all five.

## Starting the machine

A machine starts in this order:

1. **The firmware** loads one boot file that holds the kernel, a temporary
   file system loaded into memory, and the kernel's settings.
2. **Prelude** runs from that temporary file system. It prepares the
   devices, mounts the real disk, and hands over to peinit. See
   [Prelude](~peios/boot/prelude).
3. **peinit**, the service manager, prepares the system, then starts the
   registry service, loregd, and the sign-in service, authd.
4. **peinit** then reads the service definitions from the registry and starts
   every service in dependency order. See
   [Boot and Boot Modes](~peios/boot/boot-and-boot-modes).
5. **You sign in** at the console, over SSH, or from a browser, and authd
   creates the token your session runs with. See
   [Signing In](~peios/signing-in/overview).

If the machine can't finish starting, peinit starts it in a recovery mode
with a console for repairs.

## System services

These services run on every machine:

| Service | Job | Guide |
|---|---|---|
| peinit | Starts, supervises, and stops services and scheduled jobs | [Services and Jobs](~peios/services-and-jobs/overview) |
| authd | Checks credentials and creates access tokens; its partner lpsd stores local accounts | [Local Accounts](~peios/local-accounts/overview) |
| loregd | Stores the registry's data | [The Registry](~peios/registry/the-registry) |
| eventd | Stores events, logs, and metrics and answers queries for them | [Reading Records](~peios/reading-records/stored-records) |
| netd | Configures network interfaces, addresses, and routes | [Network Configuration](~peios/network-configuration/configuring-profiles) |
| resolvd | Resolves names to addresses | [Diagnosing Name Resolution](~peios/network-configuration/name-resolution) |
| timed | Keeps the clock correct and manages the time zone | [Keeping the Time](~peios/time/overview) |
| trustd | Maintains the certificates the machine trusts | [The Trust Store](~peios/certificate-trust/overview) |

## The desktop

Three programs make the desktop that you use from a browser. The Graphical
Extensible Web Interface (GXWI) serves the
session and handles sign-in from the browser, Fenestra arranges the windows,
and Fenesh provides the dock, launcher, and settings. A set of desktop
applications covers files, terminals, and system administration. See
[The Desktop](~peios/desktop-basics/overview).

## Tools and development

The command-line utilities include the familiar file and text commands, and
tools for Peios's own features: `reg` for the registry, `sd` for security
descriptors, and `token` for identities. The installer installs Peios to a
disk and runs first-boot setup.

To build software for Peios, start with the
[Peios SDK](~peios/sdk-basics/what-is-the-peios-sdk).

## Kinds of documentation

Each kind of documentation answers a different question:

| Kind | Read it to find out |
|---|---|
| These Learn pages | How something works, and how to get a task done |
| Man pages, through `man` | Exactly what a command, file, or function does, with every option |
| Registry manuals, through `regman` | What a registry value means and which values are valid |
| Event manuals, through `evman` | What an event or one of its fields means |
| Technical reference manuals | How one component works inside |
| [Specifications](~specifications) | The contracts that independent programs must agree on |

A command's `--help` output is a short reminder of its man page.
