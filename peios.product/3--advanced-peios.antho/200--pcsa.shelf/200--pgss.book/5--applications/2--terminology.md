---
title: Terminology
description: The nouns this chapter is specified in — application, declaration, id, catalogue, program, title, listed, media type pattern.
---

**Application.** A program as a desktop knows it: something with a
title that can be started from a launcher or opened with. In this
chapter an application is always what a declaration says, and nothing
is an application without one.

**Declaration.** The file that says what an application is, in the form
of §5.3. One file declares one application.

**Id.** The name of an application: the reverse-DNS string the
declaration's file is named for, in the form of an icon identifier
(PGSS Icons §4.3). `dev.peios.gexora` is an id.

**Catalogue.** The directory holding every declaration on the system,
in the form of §5.4. A consumer that wants to know what applications
there are reads it.

**Program.** The file a declaration says to run: an absolute path. The
program is what a consumer executes, and what a consumer matches a
running process against (§5.5).

**Title.** What an application is called wherever a consumer shows it
to a person.

**Listed.** Whether a launcher shows the application among what can be
started. An application that is not listed is still an application: it
can be opened with, and a running one is still named by its
declaration.

**Media type pattern.** Either a media type, `image/png`, or a
top-level type and `*`, `image/*`, which stands for every subtype of
it. A declaration says what an application opens in these.

Terms defined in PGSS Icons (identifier, chain, consumer as one who
draws) are used with the same meaning and are not redefined. *Media
type* is used as RFC 6838 defines it. *TOML* is the format at
toml.io, version 1.0.
