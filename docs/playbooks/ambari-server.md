# Ambari Server

**Playbook:** `playbooks/ambari-server.yml`
**Role:** `roles/ambari-server`
**Targets:** `ambari_server` inventory group (single master node)

This is the most involved role in the whole project. It doesn't just
`dnf install ambari-server` — it installs, wires up the MySQL backend,
fronts it with Nginx, runs Ambari's own silent setup wizard, and then
**builds a custom BIGTOP 3.4.0 stack** by cloning and patching the 3.3.0
stack shipped with Ambari, since 3.4.0 isn't natively available. Most of
the hard-won debugging on this whole project lives in this role.

## Execution order (`roles/ambari-server/tasks/main.yml`)

1. `install.yml` — packages (`ambari-server`, `httpd`, `php`, `sshpass`, etc.)
2. `files.yml` — stages the JDBC driver, the local BIGTOP repo definition, and a custom systemd unit
3. `db.yml` — creates the `ambari` MySQL user/database and imports the DDL schema
4. `config.yml` — writes every required key into `ambari.properties`
5. `setup.yml` — runs `ambari-server setup --silent` non-interactively
6. `nginx.yml` — installs and configures an Nginx reverse proxy in front of Ambari
7. `postinstall.yml` — builds the custom BIGTOP 3.4.0 stack

## The dual-JDK setup (JDK 17 server / JDK 8 cluster)

Ambari Server itself runs on **JDK 17** (`ambari_java_home`), but the
Hadoop cluster components it manages historically expect **JDK 8**
(`ambari_jdk_home`) at a specific path. Rather than fight that, this role:

- Sets `java.home` / `jdk.home` in `ambari.properties` to JDK 17 (for the
  server process).
- Sets `jdk1.8.home` to the real JDK 8 install path (for cluster
  components).
- **Symlinks JDK 17 into the path Ambari expects JDK 8 to live at**
  (`/usr/jdk64/jdk1.8.0_202` → real JDK 17), specifically so Ambari's
  internal JDK-detection logic skips the `--add-opens` JVM flag injection
  it would otherwise apply for "JDK 8" — that injection breaks JDK 17
  server startup. This is a deliberate hack, documented inline in
  `tasks/setup.yml`.

## Bugs fixed along the way (why the tasks look the way they do)

These are preserved as inline comments in the task files (`# FIX: ...`)
so the reasoning survives, not just the working code:

- **`files.yml` / `db.yml` — `copy: src:` paths.** Ansible resolves
  `copy`/`template` `src:` relative to the role's own `files/`/`templates/`
  directory automatically. Early versions of this role used `../files/...`
  paths, which broke — corrected to bare filenames.
- **`files.yml` — missing `become: yes`.** The `ambari-server/conf`
  directory and systemd unit paths are root-owned; tasks without
  `become: yes` failed silently or with permission errors.
- **`files.yml` — `daemon_reload` ordering.** systemd must be reloaded
  *after* the custom `.service` file is deployed, not before — moved to
  the end of the task file, and a stray `notify` on that task (reload
  isn't a "restart") was removed.
- **`db.yml` — schema-import condition.** The original `when:` checked
  `query_result[0].msg`, which only exists on a query error, not on an
  empty result. Corrected to check whether `query_result[0]` (the row
  list) is empty, since that's what actually tells you the `stacks` table
  doesn't exist yet.
- **`config.yml` — duplicate `server.jdbc.database` entries.** An earlier
  version of the properties file ended up with the same key written twice
  by two different tasks; consolidated into one authoritative task.
- **`setup.yml` — Python 3.12 compatibility.** Ambari's own setup scripts
  historically used `distutils.sysconfig` to find the site-packages path;
  `distutils` was removed in Python 3.12. Replaced with the standard
  library `sysconfig` module.
- **`setup.yml` — `args.creates` guard on the wrong file.** The setup
  command originally used `password.dat` as its idempotency marker, but
  `config.yml` already creates that file independently — meaning setup
  would get skipped on re-runs even when it still needed to run. Switched
  to a dedicated sentinel file (`/etc/ambari-server/.setup_done`) that
  only setup itself creates.
- **`nginx.yml` — template path.** Same class of bug as `files.yml`:
  `template: src:` had an incorrect `../templates/` prefix; removed.
- **`postinstall.yml` — ownership recursion had no effect.** The
  `file:` task setting ownership on the new BIGTOP 3.4.0 directory was
  missing `owner:`/`group:`, so `recurse: yes` had nothing to actually
  apply — added both.
- **`postinstall.yml` — service version `failed_when` logic.** The
  per-service version-bump task originally checked `.msg`, which doesn't
  reliably exist; switched to `ignore_errors: yes` since some services in
  `services_to_update` may not exist in every stack build and that's
  expected, not fatal.
- **`postinstall.yml` — `repoinfo.xml` OS family tag.** Ambari expects the
  literal string `redhat9` (not `rocky9` or similar) as the `os family=`
  value for RHEL-family/Rocky 9 hosts — this isn't documented clearly
  anywhere and cost real debugging time.
- **`ambari-agent/config.yml` — `java_home` typo.** An earlier version of
  the agent's `java_home=` line was written as `jdk-17-0.6` (hyphen
  instead of dot) — silently broke JDK detection on agents. Fixed to
  `jdk-17.0.6`.

## The BIGTOP 3.4.0 stack (`postinstall.yml`)

Ambari (via Bigtop) doesn't ship a 3.4.0 stack definition, so this role
manufactures one by:

1. Deep-copying the existing `BIGTOP/3.3.0` stack directory to `3.4.0`.
2. Editing `metainfo.xml`: marking it `active`, and setting
   `<extends>3.3.0</extends>` so it inherits everything not explicitly
   overridden.
3. Stripping the `_${stack_version}` suffix from service package names
   across **all** BIGTOP stack service `metainfo.xml` files (3.2.0 and
   3.4.0) — the offline repo's actual package names don't carry that
   version suffix, so Ambari's generated install commands would otherwise
   reference packages that don't exist in the local mirror.
4. Bumping individual service versions to match what's actually available
   offline (HDFS/YARN 3.3.6, Hive 4.0.1, Tez 0.10.4, Spark 3.5.3,
   ZooKeeper 3.8.4, Solr 8.11.4, Ranger 2.6.0, Ambari Metrics 3.1.0,
   Ambari Infra Solr 3.0.0).
5. Writing a fresh `repoinfo.xml` pointing at the offline BIGTOP 3.4.0
   repo, using the `redhat9` OS family tag Ambari expects for Rocky 9.

The repo base URL is templated via `bigtop_repo_baseurl` in
`roles/ambari-server/defaults/main.yml` — **set this to your own internal
Nexus/Artifactory mirror** before running; it's a placeholder in this
repo.

## Nginx reverse proxy

Ambari serves its UI on `:8080` by default. This role fronts it with
Nginx on port 80 (HTTP only, no TLS — see the `⚠️` note in
`roles/ambari-server/files/README.md` about the unused cert/key files),
disabling buffering for real-time responsiveness in the Ambari UI and
adding WebSocket upgrade headers, which some Ambari UI features rely on.

## Key variables (`roles/ambari-server/defaults/main.yml`)

| Variable | Default | Purpose |
|---|---|---|
| `ambari_java_home` | `/usr/lib/jvm/jdk-17.0.6` | JDK for the Ambari server process |
| `ambari_jdk_home` | `/usr/lib/jvm/jdk1.8.0_202` | JDK path exposed to cluster components |
| `ambari_db_name` | `ambari` | MySQL database name |
| `nginx_listen_port` | `80` | Reverse proxy port |
| `bigtop_repo_baseurl` | *(placeholder — set your mirror)* | Offline BIGTOP 3.4.0 repo URL |

Vault-backed: `vault_ambari_db_user`, `vault_ambari_db_password`,
`vault_mysql_root_password` (see `group_vars/secrets.yml.example`).

## Offline prerequisites

See `roles/ambari-server/files/README.md` — this role needs several
staged artifacts (DDL SQL, systemd unit, BIGTOP repo XML, JDBC jars)
that aren't committed to git.
