---
title: Candidate Selection
description: The ordered rules peipkg applies when several packages satisfy one dependency, and what happens when the rules run out.
---

When several available packages satisfy one dependency or goal, peipkg
chooses between them by applying the following rules in order. The first
rule that distinguishes two candidates decides.

1. **An exact architecture match beats `noarch`.** A candidate whose
   architecture equals the system's primary architecture is preferred
   over a `noarch` candidate of the same name.

2. **The depending package's own repository is preferred, bounded.**
   When resolving a dependency for a package D, a candidate from D's
   repository is preferred over a cross-repository one — but only when
   D's repository is at least as trusted as the alternative. When D
   comes from a lower-priority repository than the cross-repository
   candidate, this rule does not apply and rule 3 decides.

   > [!NOTE]
   > The bound is the point of the rule. Without it, a low-trust package
   > pulls in low-trust transitive dependencies that shadow higher-trust
   > alternatives, simply by virtue of being their depender.

   The rule applies when D is being installed or upgraded in this
   transaction. When D is already installed and is merely the reason a
   dependency is being resolved, peipkg does not consult the repository
   D was installed from, so the rule does not fire — and the same
   dependency can resolve to a different provider depending on whether D
   is being touched.

3. **Higher repository priority is preferred** — a lower numeric
   priority (§3.3).

4. **A higher version of the name being resolved is preferred.** That
   version is the candidate's own when it matched by name, and the
   matching `provides` entry's version when it matched through
   `provides`. A candidate matched through an unversioned `provides`
   states no version and is preferred *less* than any candidate that
   states one.

   > [!NOTE]
   > Rule 4 compares the role, not the package. Two packages filling one
   > role are unrelated software on unrelated version scales: asked
   > which `coreutils` they offer, one project's `9.9` and another's
   > `0.4` answer with the versions in their `provides` entries.
   > Comparing those as *package* versions would decide the role by
   > which project numbers its releases higher.

5. **A higher package revision is preferred** — already implied by rule
   4, retained for clarity.

6. **Ties break on the candidate's package name**, by byte order, and
   then on its repository name.

## When the rules run out

Rules 1 to 6 do not order two *different versions of the same package*
matched through an unversioned `provides`: they carry no role version to
compare at rule 4, and they agree on name and repository at rule 6. Such
a pair is a complete tie, and the candidate enumerated first wins.

The outcome is therefore an artefact of the order the index was read in
rather than a consequence of the rules — which means the same index
served in a different order can install a different version.
