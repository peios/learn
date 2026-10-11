---
title: Candidate Selection
description: The ordered rules peipkg applies when several packages satisfy one dependency, and what happens when the rules run out.
---

After filtering by the requested constraint and installable architectures,
peipkg first selects one revision of each concrete package name. Within one
name, repository preferences come first (rules 2 and 3 below), then the
role version (rule 4), then the package's own version. An exact architecture
match breaks a remaining version tie before repository-name ordering.

This allows a newer `noarch` release to replace an older `x86_64` release
of the same package without making an older revision win merely because
of its architecture. An explicit version constraint or higher-priority
repository can still select the older release.

When distinct providers remain, peipkg compares their selected revisions
using rules 1 to 4 and 6 below. Rule 5 applies only to the first stage,
within one concrete package name. The first rule that distinguishes
two candidates decides.
Selecting the revision first also makes the result independent of catalogue
order when a package's architecture changes.

1. **An exact architecture match beats `noarch`.** A candidate whose
   architecture equals the system's primary architecture is preferred
   over a `noarch` candidate from a different provider.

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

5. **Within one package name, a higher package version is preferred.**
   This includes the package revision and breaks equal role-version ties
   during the first stage. An exact architecture match then breaks an
   equal package-version tie. This rule does not compare distinct providers.

6. **Ties break on the candidate's package name**, by byte order, and
   then on its repository name.

## Two versions of one package

When two revisions provide the same role version, including an unversioned
`provides`, the package's own version decides which revision represents that
package. This comparison is only within one concrete package name: distinct
providers have unrelated package version scales and continue to use the
role version and name ordering above.
