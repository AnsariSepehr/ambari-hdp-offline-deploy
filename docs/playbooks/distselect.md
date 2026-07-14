# Distselect (bigtop-select fix)

**Playbook:** `playbooks/distselect.yml`
**Role:** `roles/distselect`
**Targets:** `all`

Small, targeted role that patches a known gap in `bigtop-select`'s
`distro-select` script.

## The bug

`bigtop-select`'s `distro-select` component-mapping file is missing an
entry for `hadoop-hdfs-dfsrouter` (the HDFS Router service, used for
HDFS Federation / Router-based Federation setups). Without this entry,
`bigtop-select` doesn't know how to resolve the active version for that
component, which causes failures when Ambari tries to manage or start the
DFS Router service.

## What it does

1. Installs `bigtop-select` and `chkconfig`.
2. Backs up the original `distro-select` file to `BCK-distro-select`
   (idempotent — only backs up if a backup doesn't already exist, so
   re-running this role doesn't overwrite your one clean backup with an
   already-patched version).
3. Inserts a `"hadoop-hdfs-dfsrouter": "hadoop-hdfs"` mapping entry
   immediately after the existing `hadoop-hdfs-zkfc` entry, if it's not
   already present.

## Why `insertafter` + `regexp` together

The `lineinfile` task checks for the exact line via `regexp` first (so
re-runs are idempotent and don't duplicate the entry), and uses
`insertafter` to control *where* the new line lands if it needs to be
added — right after the `zkfc` entry, keeping the mapping file's grouping
sensible rather than appending at the end.
