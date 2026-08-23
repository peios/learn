---
title: pekit
description: The producer toolchain that turns a source tree into package files, and the three facts about it that matter here.
---

`pekit` is the producer: the build tool that turns an upstream source
tree into one or more package files. It is described in full in
chapter 12.

For the purposes of this chapter, three facts matter.

**pekit builds through the consumer's own decoder.** Packing runs the
manifest it just generated back through the consumer's validators, so a
package that packs successfully has already satisfied the rules a
consumer applies on the way in. A recipe error therefore often surfaces
as a manifest error at pack time rather than as a recipe error at
validation time.

**pekit's own version model is not the package version model.** pekit
tracks upstream releases — git tags, directory listings — and orders
them by its own rules, which exist to answer "is there something newer
upstream". Package versions are compared by PSPU §5.6. The two are
separate, and where a recipe's template variables expose version
components they come from pekit's model.

**pekit signs.** A package is signed at pack time with a key named by
the recipe's signing configuration, and the signature entry is the last
thing written into the archive before compression.
