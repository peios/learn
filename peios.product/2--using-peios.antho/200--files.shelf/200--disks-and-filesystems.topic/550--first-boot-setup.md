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

## In a browser

A machine with no screen has nobody at its console, so setup can also be done from a browser on another device, by opening the machine's address. This needs `oobe-gxwi`, the graphical surface, installed at `/bin/oobe-gxwi`; without it setup is on the console alone.

Where it is installed, `oobed` makes it GXWI's overlay for as long as setup is pending. Everyone who opens the address is sent to setup instead of the sign-in page. Both surfaces draw the same conversation, so it can be started on one and finished on the other.

An overlay runs as an account that needs no credential, and before setup the machine has no accounts. So `oobed` makes one as it starts: `peios-oobe-setup`, with no password and no groups, which its socket admits. When setup completes, `oobed` removes the overlay, so the sign-in page comes back, and then the account and its home directory. A setup that fails leaves all of it in place, as it leaves everything else, and the next boot offers it again.

> [!WARNING]
> While setup is pending, whoever opens the machine's address first answers its questions, including the administrator's name and password. The same is true of the console. Keep a machine that has not been set up off networks you do not trust.
>
> The page is served over plain HTTP, so the password you choose crosses the network unencrypted when you press Next, readable by anything that can see the traffic. The account page says so when it is opened over a network. On a network you do not trust, set the password at the machine's own screen.
>
> `peios-oobe-setup` has no password, so anything that signs in without a credential can sign in as it while it exists. It has no groups; what it can reach is setup itself, which the address offers anyone.

The account page will not take the name `peios-oobe-setup`: setup keeps an account that already exists, and would otherwise finish with no account you can use.

## What it asks

1. **Language and keyboard**, shown but not yet answerable — the fields are there so the flow's shape is settled, and disabled so it does not pretend to a choice it cannot honour.
2. **Network**, which never gates anything. Setup does not need a network; the page says what `net status` reports, a line for each interface (connected, not connected, not used), and **Check again** asks again, so a cable plugged in while the page is open shows up without leaving it. In a browser, the interface whose address the page was opened by is marked as the way in. Joining a wireless network is shown and disabled.

   **Configure manually** gives one wired interface an address of its own, with a gateway and name servers if you want them. It is checked as you save it (an address needs the length of its network, `192.168.1.20/24`, and a gateway must be on that network) but not applied: setup keeps it, says so on the network page, and applies it last, after the account and the machine's name. Until then the machine keeps the address it has, so a browser setting it up keeps reaching it. What it writes is an ordinary [profile and rule](~peios/networking/configuring-profiles), `Profiles\default\manual-<interface>` and an exception under `Rules\Interface\wired` naming the interface by its stable id, which you can change or delete afterwards like any other.
3. **An account and a password.** This is the one that matters, and the reason first-boot setup exists: it is where an installed machine gets its first administrator.

   The account is made at the very end, and a name or password the [principal store](~peios/managing-local-principals/creating-accounts) would refuse there would fail the whole of setup. So the page refuses them itself, when you press Next, and says why on the field: an empty password, two passwords that differ, and a name that is empty, is not plain ASCII, is longer than 256 characters, contains any of `@ \ / : ,`, or is the name of a group every machine has (`Administrators`, `Users`, `Guests`, `Everyone`, `Authenticated Users`). Spaces inside a name are fine; spaces around it are trimmed.

   In a browser, what you type stays in your browser until you press Next, and is never shown to anyone else who has the page open. The page shows who the account will be as you type the name, and whether the second password matches the first.
4. **A name for the machine**, offered as a suggestion you can accept with one keypress. Domain join is shown and disabled.

   The name is what the machine calls itself and what it tells a DHCP server it is called, so it has to be one name a network will carry: letters, digits and hyphens, at most 63 of them, with no hyphen at either end, no dots and no spaces. `localhost` is refused, since every machine is that to itself. Anything else is turned down on the page when you press Finish; spaces around the name are trimmed. In a browser, the page says as you type whether the name fits, and can put back the one setup offered.

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
