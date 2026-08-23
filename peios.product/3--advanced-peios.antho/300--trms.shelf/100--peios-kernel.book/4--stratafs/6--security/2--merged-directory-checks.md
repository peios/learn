---
title: Checks on Merged Directories
description: An operation on a merged directory is checked against every participating directory — including where the create stratum's directory does not exist.
---

A merged directory stands for several real directories, each with its
own security descriptor. An operation on one is checked against every
participating directory whose contents it depends on, and against the
directory it modifies. Where more than one applies, **all** must
succeed: the check walks participants in order and returns on the first
refusal, and nothing degrades an operation to the subset of strata the
caller may reach.

Two composite rights recur:

- **Search** — traverse on every participating directory, since every
  one is searched to resolve a name. The permission hook maps the
  kernel's execute intent onto it.
- **Enumerate** — Search plus list on every participating directory.
  The permission hook maps the read intent onto the list right, and
  directory open demands both together.

| Operation | Checked against |
|---|---|
| Resolving a name | Search |
| Enumerating | Enumerate, before the listing is captured |
| Reading an object's attributes | Search, plus whatever the object's own descriptor requires |
| Reading the origin attribute on a merged directory | Search, plus read-EA on **every** participant (§4.7) |
| Creating a name | Search, plus add-file or add-subdirectory on the **create stratum's** directory |
| Copy-up | Nothing beyond what the operation it serves already required |
| Removing a name | Search, plus delete-child on the **provider's** directory |
| Removing a directory | Enumerate — emptiness is judged across every participant — plus delete-child on the provider's directory |
| Rename, source | Search, plus delete-child on the source **provider's** directory |
| Rename, destination | Search, plus add-entry on the source provider's directory, which §4.5.5 requires to hold the destination, plus delete-child where that directory already holds the name |
| Rename of a directory | Both of the above, plus Enumerate on the object being renamed, and Enumerate on the destination where its provider is a directory |
| `RENAME_EXCHANGE` | Search on both, plus add-entry and delete-child on the directory of the stratum providing both names |
| Link | Search on both, plus add-file on the source provider's directory |
| Creating or linking an unnamed file | Search, plus add-file on the **create stratum's** directory |

The mutating rights land on the directory that actually changes, which
follows from §4.5: an entry appears in the create stratum's directory
and disappears from the provider's, so in each case it is that
directory's descriptor that decides. The two coincide whenever the
create stratum is also the provider.

One right the table does not name is required anyway: the underlying
`vfs_link` makes KACS demand write-attributes on the **source object**,
which is an object-descriptor right outside the directory scope this
section covers. Linking an unnamed file is exempt, since stratafs marks
the source for that purpose.

The effective rights on a merged directory are therefore the
intersection of the rights on its participants, with mutating rights
additionally required on the directory that is actually modified.
Requiring the intersection is fail-closed and admits no partial
results: the alternative would let the names held by a restrictively
protected directory be enumerated by a caller who could not enumerate
it directly, because a permissive directory of higher precedence
happened to provide the merged path.

One consequence is worth stating plainly. Because creation is governed
by the create stratum's directory descriptor, and a created name
shadows the same name in every lower stratum, the right to create in
the create stratum's directory is the right to determine what every
lower stratum's entry of that name resolves to.

## Where the create stratum's directory does not exist

A merged directory has a create stratum whether or not that
subdirectory exists (§4.3.2), so a check naming "the create stratum's
directory" has to be evaluated against a directory that is not there
yet.

Every such check is performed before any part of the operation is
carried out, and in particular before any directory is materialised:
the authorisation call strictly precedes parent materialisation in
creation, in tmpfile creation, and in the unnamed-link path. Where the
checks fail, nothing has been created, so the create stratum is left
exactly as it was.

Where the create stratum does not hold the path, the check falls back
to the **corresponding provider directory** — the merged provider of
that same relative path — which is the descriptor the directory will
carry once materialised (§4.6.3). It is never skipped, and never
substituted with an ancestor's descriptor. Where no provider exists
either, the result is `EROFS`.

Materialising the intervening directories is part of the operation, not
a separate one. No per-ancestor authorisation is taken; the mkdirs are
exempted by the copy-up context. Checking against the descriptor the
directory will have keeps the answer independent of how much of the
create stratum happens to have been materialised already: the first
caller to write into a deep path and the hundredth face the same check,
against the same descriptor.

A create that fails *after* materialisation for a reason other than a
check — `EEXIST`, `ENOSPC` — does leave the intervening directories in
place.

## Copy-up carries no separate authority

A copy-up requires no right beyond those the operation that provoked it
already required. In particular it does not require the caller to hold
the right to read the provider's object, nor the right to add an entry
to the create stratum's directory. Neither copy-up path takes any
authorisation at all.

Copy-up is the mechanism by which an authorised modification is
realised, not an operation a caller requests. The read of the provider
is stratafs's own, and the copy carries the source's descriptor
unchanged (§4.6.3), so the caller obtains nothing they did not already
have: the same content, under the same descriptor, at the same path.

The alternative cannot be expressed. Routing happens when a
modification is performed (§4.5.1), and by then the authority that
governed the open is a mask cached on the descriptor, immutable and
carrying no token — so there is nothing to evaluate a fresh right
against. Checking the *acting* token instead would break descriptor
delegation, since a descriptor passed to another process would stop
working there.

What remains is a resource consideration rather than an access one: a
caller entitled to write a file in a stratum that will not accept
modification can cause an entry to appear in the create stratum without
holding rights over that directory. They gain no access by it — though
they do gain the space, since §4.5.8 records that the copy is accounted
to them rather than to the preserved owner.

That exemption is only enforceable because KACS provides a copy-up
context; without it the access-control layer would check the caller
against the create stratum's directory at exactly the point where the
authority to check no longer exists. §3.9.7 describes the context, its
phase binding and its exhaustive list of exempt operations. What
matters here is what stratafs must hold up its end of: the context
exempts caller authorisation only, so every mutation still goes through
the ordinary VFS path under write access on the target mount, a
read-only filesystem still refuses, and filesystem errors still
propagate. Nothing is performed under a borrowed or elevated identity —
every copy-up mutation runs with the calling task's own credentials.

One adjacent path does borrow one. The stale-staging recovery scan
opens the create-stratum directory with the **mounter's** credentials
rather than the caller's, and since the KACS token derives from the
current credentials, that read is authorised as the mounter. It runs
inside a copy-up context in any case, so it changes no decision.
