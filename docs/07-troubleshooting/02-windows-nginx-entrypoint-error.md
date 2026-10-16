---
title: Entrypoint errors on Windows
---

# Resolving Docker Entrypoint Script Not Found Errors on Windows

If containers built from a Windows clone keep restarting with an error like one of these, the shell scripts in the image most likely have `CRLF` line endings:

```
exec /usr/local/bin/entrypoint.sh: no such file or directory
exec /usr/local/bin/nginx-entrypoint.sh: no such file or directory
```

## Why it happens

Git for Windows usually checks out text files with `CRLF` line endings (`core.autocrlf=true`). A script copied into an image with `CRLF` has the shebang `#!/bin/bash\r`. Linux looks for an interpreter literally named `/bin/bash\r`, doesn't find it, and reports that the script doesn't exist.

The repository's `.gitattributes` forces `LF` for `*.sh` files, so fresh clones are not affected.

## Fixing an existing clone

Clones made before `.gitattributes` was added keep their `CRLF` scripts until they are checked out again. Re-clone the repository, or, if you have no uncommitted changes to the scripts, run this from the repository root in Git Bash:

```bash
git pull
git ls-files -z '*.sh' | xargs -0 rm -f
git checkout -- '*.sh'
```

Check that every script now shows `w/lf`:

```bash
git ls-files --eol '*.sh'
```

Then rebuild the image.

## Scripts outside Git

`.gitattributes` only applies to files checked out by Git. If you edit or create scripts on Windows yourself, save them with `LF` line endings, or convert them with `dos2unix`:

```bash
dos2unix resources/core/nginx/nginx-entrypoint.sh
```
