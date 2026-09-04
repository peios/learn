---
title: First boot
type: concept
description: What an installed Peios asks the first time it starts — an account, a password, a name for the machine — and how that flow gets the console and gives it back.
related:
  - peios/disks-and-filesystems/installing-to-disk
  - peios/services-and-jobs/triggers-and-timers
  - peios/managing-local-principals/creating-accounts
  - peios/peiso/editions-and-upgrades/release-toml
---

An installer writes a system to a disk. It does not ask who you are — deliberately, because every question asked before the copy is a question answered while a progress bar could have been running instead. So the machine asks once, the first time it boots, and that is **first-boot setup**.

It is two services and one conversation:

| | |
|---|---|
| `oobed` | The engine. Runs as SYSTEM because it creates the machine's first account and writes its name. Speaks [MSIP](~peios/services-and-jobs/overview) on `/run/oobed.sock`. |
| `oobe-tui` | The surface. Draws the form on the console and holds no privilege of its own. |

The split is the same one the installer makes, for the same reason: creating an administrator needs privilege that a program drawing boxes on a terminal must not have.

## What it asks

1. **Language and keyboard**, shown but not yet answerable — the fields are there so the flow's shape is settled, and disabled so it does not pretend to a choice it cannot honour.
2. **Network**, which never gates anything. Setup does not need a network; the page reports what the machine can currently do and moves on.
3. **An account and a password.** This is the one that matters, and the reason first-boot setup exists: it is where an installed machine gets its first administrator.
4. **A name for the machine**, offered as a suggestion you can accept with one keypress. Domain join is shown and disabled.

Then it applies, and says so.

## How it gets the console

Both first-boot setup and the [login prompt](~peios/signing-in/overview) want `/dev/console`, and a terminal has one owner at a time. Setup's surface names a higher [`TTYPrecedence`](~peios/services-and-jobs/triggers-and-timers), so peinit gives it the console and **skips** the login prompt for that boot — the prompt is not started and written over, it is not started at all.

When setup's surface exits, the console is released and the login prompt's `tty:released` trigger brings it up. That happens however setup ended: finished, abandoned with Esc, or crashed. The console is never left with nobody on it.

### How big the form is

A serial console cannot say how large it is. There is no geometry in a byte stream, so the kernel leaves the terminal at no size at all and a hypervisor has nothing to pass through — which is why a form on one used to be drawn 80 columns by 24 rows in the corner of whatever window was really there.

So the surface asks. It moves the cursor past the bottom-right corner, where the terminal stops it at the real edge, and reads back where it ended up. The form is then drawn to that. The installer's surface does the same thing, being the same renderer.

Two consequences worth knowing:

- **The size is taken once, when the form starts.** Resizing the window after that changes nothing, because the guest is never told. Reboot, or accept the shape you have.
- **A console that does not answer gets 80x24**, the old behaviour — a real serial port with nothing on the far end, or output captured to a file.

### The console goes quiet while a form is open

The kernel writes to `/dev/console` too, and it does not take turns: a message lands wherever the cursor is, and one landing on the bottom row scrolls the screen. A surface repaints only the cells it believes changed, so it never learns what the kernel did, and the damage stays until something forces a full repaint.

So `oobed` lowers the kernel's console output for as long as a conversation is open, and puts it back when the conversation ends — however it ends, the daemon dying included. The engine does this rather than the surface because it needs privilege and the surface deliberately has none. `installerd` does the same for the installer.

Only `KERN_EMERG` still prints, so a panic is never hidden. And only the *kernel* is quieted — peinit and the services write to the console themselves and are unaffected, which is why a page change repaints in full and why **Ctrl-L** repaints on demand.

## It runs once

On success `oobed` removes both service definitions — its own and the surface's — and exits. The second boot has no setup to do and nothing left over to explain.

**Only on success.** A run that failed, or that you left with Esc, removes nothing, so the next boot asks again. That is not tidiness: retiring after a failure would delete the only route back to the question, and a machine with no account yet cannot be logged into to put it back by hand.

> [!NOTE]
> Which means a machine whose setup keeps failing is a machine you cannot log into. The recovery is the install medium, the same as for any system that will not boot. It is the reason setup asks as little as it does.

## Where it comes from

`oobe-service` is a registry seed, shipped inert by `dev.peios.oobe` and opted into by the edition's [`install_autoapply`](~peios/peiso/editions-and-upgrades/release-toml) list. That list exists for exactly this: seeds an installed machine applies and a boot medium does not. Setup running on the medium would take the console away from the installer.

An image with no `dev.peios.oobe`, or an edition that does not list the seed, simply boots to a login prompt — on a machine with whatever accounts its own seeds provisioned.
