# files/

This directory must contain `Python-3.12.0.tgz` (the official CPython source
tarball) before running the `python` role.

It is intentionally **not** committed to git (see repo root `.gitignore` —
`*.tgz` / `*.tar.gz` are excluded) since this is an offline installation
and binary artifacts don't belong in version control.

Download it once from https://www.python.org/downloads/release/python-3120/
(source tarball, `Python-3.12.0.tgz`) on a machine with internet access,
then copy it here before staging this repo on your offline nodes:

```
roles/python/files/Python-3.12.0.tgz
```
