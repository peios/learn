---
title: Publishing a Repository's Docs to Learn
type: how-to
description: Add a repository's docs/learn tree to the Learn site, and make
  each push that changes its documentation redeploy Learn.
---

Learn is built from the central `learn` repository and from a
`docs/learn/` tree in each component's repository. Follow these steps when
a repository first contributes pages, so that its documentation is
published and stays current.

## Before you start

- Lay out the repository's `docs/learn/` tree as Trail
  [merged trees](~trail/structuring-a-site/merged-trees) require: the same
  shelves, products, and containers as Learn, with identical metadata.
- Push the repository to GitHub.

## Add the repository to the site

1. In `learn/trail.toml`, add a `[[merge]]` table after the existing ones:

   ```toml
   [[merge]]
   repo = "https://github.com/peios/authd"
   dir = "docs/learn"
   path = "../authd/docs/learn"
   ```

   `repo` and `dir` are where Learn's deploy fetches the tree. `path` is
   the repository's checkout beside `learn/` in a workspace. Trail uses it
   when it exists, so `trail serve learn` shows local edits.

2. From the workspace root, build the combined site strictly:

   ```sh
   trail build learn --strict --out local/learn-site
   ```

   Fix any duplicate pages, mismatched containers, or broken links it
   reports.

3. Commit the change to `learn` and push it.

## Redeploy when its documentation changes

1. In the component's repository, add this file as
   `.github/workflows/update-learn.yml`:

   ```yaml
   name: Update Learn

   # Asks Learn to redeploy when this repository's documentation changes. The
   # same file goes in every repository that contributes to Learn.
   on:
       push:
           paths: ["docs/**"]

   permissions: {}

   jobs:
       dispatch:
           if: github.ref_name == github.event.repository.default_branch
           runs-on: ubuntu-latest
           steps:
               - run: gh api repos/peios/learn/dispatches -f event_type=docs-changed
                 env:
                     GH_TOKEN: ${{ secrets.LEARN_DISPATCH_TOKEN }}
   ```

   The file is the same in every repository. It runs only for pushes to
   the default branch that change `docs/`.

2. For a repository outside the `peios` organization, add a
   `LEARN_DISPATCH_TOKEN` repository secret. The `peios` organization
   provides the secret to its own repositories.

3. For a private repository, give Learn's `LEARN_READ_TOKEN` read access to
   its contents. Learn's deploy fetches the tree with that token.

## Check the result

Push a documentation change to the default branch. The repository's
**Update Learn** run succeeds, and a **Deploy to GitHub Pages** run starts
in `peios/learn`. When it finishes, the change is on learn.peios.org.
