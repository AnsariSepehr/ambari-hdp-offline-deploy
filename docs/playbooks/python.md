# Python 3.12

**Playbook:** `playbooks/python.yml`
**Role:** `roles/python`

Compiles and installs Python 3.12 from source on every node, **alongside**
the distro's existing Python (e.g. 3.9 on Rocky/AlmaLinux) — it does not
touch or replace the system Python, which Ambari/HDP itself depends on.

## Why build from source

This is an offline cluster with no internet access and no guarantee that
`python3.12` packages exist in the local offline repo/mirror. Building from
the official source tarball sidesteps that entirely — the only external
dependency is the tarball itself, staged in `roles/python/files/` ahead of
time (see that folder's `README.md`).

## What it does

1. Installs OS build dependencies (`gcc`, `openssl-devel`, `zlib-devel`,
   etc. — branches for both Debian/`apt` and RedHat/`yum` families, though
   the rest of this codebase targets RHEL-family hosts).
2. Copies `Python-3.12.0.tgz` from the control node to each target and
   extracts it under `/tmp/python3.12.0-build/`.
3. Runs `./configure --enable-optimizations --with-ensurepip=install`.
4. Compiles with `make -j<cores>` (auto-detects CPU count, capped by
   `python_make_jobs` if set) — wrapped in `async`/`poll` since this can
   take several minutes and would otherwise hit Ansible's default task
   timeout on slower nodes.
5. Installs via `make altinstall` — **not** `make install** — so this
   Python 3.12 never overwrites or symlinks over the system `python3`
   binary.
6. Drops shell aliases (`python312`, `pip312`) into
   `/etc/profile.d/python312.sh`.
7. Verifies the install and cleans up the build directory.

## Key variables (`roles/python/defaults/main.yml`)

| Variable | Default | Purpose |
|---|---|---|
| `python_version` | `3.12.0` | Version being built |
| `python_install_prefix` | `/usr/local` | Install location |
| `python_alias` | `python312` | Shell alias name |
| `python_make_jobs` | `0` (auto) | Parallel compile jobs |
| `python_cleanup_build_dir` | `true` | Remove build artifacts after install |

## Why this exists in the cluster

Some Hadoop ecosystem components/tooling used during setup and later
operational tooling need a newer Python than what ships with the base OS.
Rather than fight the system interpreter (which Ambari itself is sensitive
to), this installs a second, explicit, aliased interpreter side-by-side.

## Notes / gotchas

- Build time matters at 40-node scale — this runs in parallel across hosts
  by default (Ansible's `forks` setting), but a from-source build still
  takes several minutes per node. Budget time for this step.
- `make altinstall` is deliberate — using `make install` here would be a
  bug, since it would create a `python3`/`pip3` symlink collision with the
  system interpreter that Ambari agents rely on.
