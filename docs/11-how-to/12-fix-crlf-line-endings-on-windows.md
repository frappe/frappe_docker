---
title: Fix CRLF Scripts on Windows
---

# Fix CRLF line endings in shell scripts on Windows

Use this guide when containers built from a Windows clone keep restarting with an error such as:

```
exec /usr/local/bin/entrypoint.sh: no such file or directory
exec /usr/local/bin/nginx-entrypoint.sh: no such file or directory
```

The shell scripts in the image have `CRLF` line endings, so the shebang becomes `#!/bin/bash\r` and Linux cannot find the interpreter. The repository's `.gitattributes` checks out `*.sh` files with `LF`, so fresh clones are not affected. Clones made before `.gitattributes` was added keep their `CRLF` scripts until the scripts are checked out again.

## Prerequisites

- A clone of this repository on Windows, opened in Git Bash
- No uncommitted changes to tracked `.sh` files. Step 2 deletes and restores them, which discards such changes.

## Step 1: Update the clone

From the repository root, pull the commit that adds `.gitattributes`:

```sh
git pull
```

## Step 2: Check out the scripts again

Pulling alone does not rewrite files that are already checked out. Delete the tracked scripts and restore them:

```sh
git ls-files -z '*.sh' | xargs -0 rm -f
git checkout -- '*.sh'
```

Re-cloning the repository has the same effect.

## Step 3: Verify the line endings

```sh
git ls-files --eol '*.sh'
```

Every script should show `w/lf` and `attr/text eol=lf`.

## Step 4: Rebuild the images

Rebuild your images as described in [Build Setup](../02-setup/02-build-setup.md), then start the containers again. They should no longer restart with the error above.

## Scripts created outside Git

`.gitattributes` only applies to files that Git checks out. If you create or edit scripts on Windows yourself, save them with `LF` line endings, or convert them before building:

```sh
dos2unix path/to/script.sh
```
