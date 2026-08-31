---
title: Test hooks
description: The securityfs rendezvous and fail points conformance tests use to hold a copy-up open or fail an internal step — doubly gated, inert on every production boot.
---

Several of this chapter's promises are about windows that no
arrangement of real filesystems can hold open. A copy-up is never
observable in a partial state (§4.5.2) — but a real copy-up publishes
within microseconds. A failed install rolls the lower link back
(§4.5.6) — but the install fails only under allocation pressure between
two steps of one syscall. A dentry whose provider identity no longer
matches yields `ESTALE` (§4.5.5) — but every walk rebuilds the dentry
moments before the operation, so the mismatch needs the provider to
change inside a single syscall.

The test hooks exist so conformance tests can steer exactly those
windows and nothing else. They are not conformance surface: no
behaviour in this chapter depends on them, and they carry no named
citations.

## Gating

The hooks are doubly gated:

- `CONFIG_STRATAFS_FS_TEST_HOOKS` compiles them in. Without it every
  hook site is an inline constant zero.
- `stratafs.test_hooks=1` on the kernel command line registers them.
  Without it nothing appears in securityfs and each hook site reduces to
  reading one never-true flag.

Production images build the option but never pass the parameter; only
the provium test profiles do. Arming a hook additionally requires
reaching a mounted securityfs, which on a managed system means a caller
able to establish the mount and satisfy its policy class.

## Interface

Each hook point is one securityfs file under `stratafs/hooks/`,
alongside KACS's own `kacs/` endpoints. securityfs rather than debugfs
is forced by kernel lockdown: the Peios kernel builds
`LOCK_DOWN_KERNEL_FORCE_INTEGRITY`, and the integrity set refuses every
debugfs open that is not a read of a mode-0444 file — a debugfs hook
would be visible and permanently untouchable. Lockdown does not gate
securityfs. Writing a hook's file arms or disarms it; reading reports
its state:

| Write     | Effect                                                       |
|-----------|--------------------------------------------------------------|
| `hold`    | Tasks reaching the point block until the hook is cleared     |
| `fail N`  | The next task to reach the point fails with errno `N`, once  |
| `clear`   | Disarm; every held task is released                          |

A read returns `<mode> waiting=<W> hits=<H>`, where `<mode>` is `none`,
`hold` or `fail`, `W` is the number of tasks currently blocked — poll
it to know the victim has arrived — and `H` is the number of arrivals
the hook has affected. A held task waits killably, so a fatal signal
always removes it. A `fail` arms exactly one failure and disarms
itself; `hold` persists until cleared.

## Points

| File              | Moment                                                                                                                                              |
|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `copy-up-begin`   | Before the copy-up context is created — before any staging exists. A failure here is a source descriptor that could not be read (§4.6.3).            |
| `copy-up-publish` | After the staged object is complete — content, attributes, metadata — and before publication. A hold here is an in-flight copy-up, staged but unpublished (§4.5.2). |
| `rename-provider` | In `rename`, after the walk-time provider is captured and before the locked re-lookup that verifies it (§4.5.5).                                     |
| `link-install`    | In `link`, between the lower link succeeding and the outer inode installing. A failure here exercises the rollback of §4.5.6.                         |

`copy-up-begin` and `copy-up-publish` sit on both copy-up shapes — the
anonymous regular-file stage and the named directory/symlink stage —
so a hold at `copy-up-publish` pins whichever kind is in flight.
