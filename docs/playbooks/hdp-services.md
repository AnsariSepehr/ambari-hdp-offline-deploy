# HDP / Bigtop Services

**Playbook:** `playbooks/hdp-packages.yml` (see [known issue](playbooks-overview.md#known-issues) about the `site.yml` filename mismatch)
**Role:** `roles/hdp-services`
**Targets:** `ambari_agent` inventory group (all worker nodes)

Installs the actual Hadoop ecosystem packages from the offline Bigtop
repo, and — because Ambari's BIGTOP 3.4.0 stack (built in the
`ambari-server` role's `postinstall.yml`) expects a specific directory
layout that the raw offline packages don't produce on their own — this
role builds the version-bridging symlink structure Ambari needs to find
each component.

## What it does

1. Fully cleans the yum/dnf cache (`yum clean all`, then removes and
   recreates `/var/cache/dnf`) — belt-and-suspenders to avoid stale
   metadata from a previous repo pointing at the wrong package set.
2. Installs every package in `bigtop_packages` — Zookeeper, the full
   Hadoop stack (HDFS/YARN/MapReduce/client), Hive + HCatalog + WebHCat,
   Tez, Spark, Zeppelin, Solr, Ambari Metrics (collector/monitor/sink),
   Ambari Infra Solr, and the Ranger admin/usersync/KMS/plugin packages.
3. Creates the base Bigtop directory skeleton:
   `/usr/bigtop/3.4.0/usr/lib/` and `/usr/bigtop/current/`.
4. **Version-bridging symlinks**: links each package's real install path
   (`/usr/lib/hadoop`, `/usr/lib/hive`, etc.) into
   `/usr/bigtop/3.4.0/usr/lib/<name>` — this is what lets the custom
   BIGTOP 3.4.0 stack definition (built in the `ambari-server` role)
   actually resolve component paths at the version it claims to be.
5. Creates two directories some Ambari service checks expect but the raw
   packages don't always create: `/usr/lib/hive/lib` and
   `/usr/lib/spark/jars`.
6. **"Current" convenience symlinks**: a second set of symlinks under
   `/usr/bigtop/current/` for the specific component *roles* Ambari looks
   for by name — `hive-client`, `hive-server2`, `hive-webhcat`,
   `hbase-client`, `hbase-master`, `hbase-regionserver`, `spark-client`,
   `spark-historyserver` — each pointing back at the real package
   install directory.
7. Prints a debug summary of every symlink actually created (skipped for
   unchanged/idempotent runs).

## Why two layers of symlinks

This is the practical consequence of running a stack version (3.4.0) that
doesn't natively exist in Bigtop/Ambari — the packages install at their
real, versionless paths (`/usr/lib/hadoop`), but Ambari's stack
definitions expect to find components under version- and role-specific
paths. Rather than patching every stack service script, this role
recreates the expected directory shape once, cluster-wide, via symlinks.

## Key variables (`roles/hdp-services/defaults/main.yml`)

| Variable | Default | Purpose |
|---|---|---|
| `bigtop_version` | `3.4.0` | Must match the custom stack version built in `ambari-server` |
| `bigtop_base` | `/usr/bigtop` | Root of the bridging directory structure |
| `bigtop_packages` | (full list — see file) | Every package installed on agent nodes |

Override `bigtop_packages` in `group_vars/all.yml` if your cluster doesn't
need every service listed (e.g. skip Zeppelin, or add HBase explicitly —
note HBase is *symlinked* here but not in the default install list, since
Ambari Metrics ships its own embedded HBase; add a standalone `hbase`
package here only if you're running full HBase as a separate service).

## Relationship to the post-install wizard

This role gets packages *onto disk* and *discoverable* by Ambari. It does
**not** configure or start any Hadoop service — that happens through the
Ambari cluster install wizard (manual step), using the environment
templates in `docs/post-install/` to work around Java 17 compatibility
issues in each service's default configuration. See
`docs/post-install/README.md`.
