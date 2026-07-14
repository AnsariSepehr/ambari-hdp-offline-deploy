# Offline Ambari/HDP Cluster Deployment (Ansible)

Ansible playbooks and roles that fully prepare and bootstrap a **40-node
Apache Ambari / Bigtop (HDP-style) Hadoop cluster**, entirely offline —
no internet access required on any cluster node. Every package,
dependency, and JDK is installed from a locally staged offline
repository/mirror.

This repo covers everything **up to and including a working Ambari Server
UI with a custom offline BIGTOP 3.4.0 stack registered**. From there, the
actual Hadoop services (HDFS, YARN, Hive, Ranger, etc.) are installed
through Ambari's own cluster wizard — manually, service by service — using
the JDK-17-compatibility fixes documented in
[`docs/post-install/`](docs/post-install/).

## Why this exists

Running a modern JDK (17) against an older Bigtop/Ambari stack, fully
offline, surfaces a long list of small but blocking issues — JDK
detection bugs, missing `--add-opens` module flags, stack version
mismatches, broken symlink paths. This project fixes all of them once, in
a repeatable way, instead of re-discovering them by hand on every
environment.

## Architecture

- **1x Ambari Server node** (also runs MySQL) — `[ambari_server]` / `[mysql]`
- **~39x Ambari Agent nodes** — `[ambari_agent]`
- All nodes get: OS tuning, Python 3.12, JDK 8/11/17/21 side-by-side
- MySQL backs Ambari, Hive, and Ranger (all as separate databases/users)
- Nginx fronts the Ambari UI on port 80
- A custom **BIGTOP 3.4.0** stack is built on top of the shipped 3.3.0
  stack, since 3.4.0 isn't natively available

## Repository structure

```
.
├── ansible.cfg
├── inventory/hosts.ini.example       # copy → hosts.ini, fill in real IPs
├── group_vars/secrets.yml.example    # copy → secrets.yml, vault-encrypt it
├── playbooks/                        # one per stage, orchestrated by site.yml
├── roles/                            # one role per playbook
├── files/                            # HDP service config templates (JDK 17 fixes)
└── docs/
    ├── playbooks-overview.md         # execution order + inventory groups
    ├── playbooks/                    # what each playbook/role does, and why
    └── post-install/                 # manual Ambari wizard steps, per service
```

## Prerequisites — do these BEFORE running any playbook

These are manual, one-time setup steps on your actual infrastructure —
Ansible doesn't (and can't, offline) do these for you:

1. **SSH connectivity.** The Ambari Server node must be able to SSH to
   every Ambari Agent node (root, or a sudo-capable user matching
   `ansible.cfg`'s `remote_user`). Several roles (`hive-db`, `ranger-db`)
   delegate MySQL operations to the Ambari Server node specifically, and
   the Ambari Server itself needs SSH reachability to agents for its own
   internal orchestration later.
2. **Clock sync across all nodes.** Kerberos (if you enable security
   later), HBase, and Ambari's own heartbeat mechanism are all sensitive
   to clock drift. Set up NTP/chrony pointed at a consistent time source
   before running anything.
3. **Offline repo (Nexus/Artifactory/etc.) reachable from every node.**
   Every `dnf`/`yum` task in this project assumes the node's package
   manager is already pointed at your internal mirror. This repo doesn't
   configure that mirror or the node's repo files — set that up first,
   per your own internal repo layout.
4. **Stage the binaries this repo doesn't commit.** JDK tarballs, the
   Python source tarball, JDBC driver jars, and a few Ambari-specific
   files are gitignored (see `.gitignore`) since they're large binaries
   that don't belong in version control. Each role that needs one has a
   `README.md` in its `files/` directory listing exactly what's needed —
   check `roles/*/files/README.md` before your first run.

## Deploying

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd <repo>

cp inventory/hosts.ini.example inventory/hosts.ini
# edit hosts.ini: real IPs, real host groupings

cp group_vars/secrets.yml.example group_vars/secrets.yml
# edit secrets.yml: real passwords
ansible-vault encrypt group_vars/secrets.yml
```

Also review and adjust, per-environment:
- `roles/ambari-agent/defaults/main.yml` → `ambari_server_host`
- `roles/hive-db/defaults/main.yml` → `hive_db_host`
- `roles/ranger-db/defaults/main.yml` → `ranger_db_host`
- `roles/ambari-server/defaults/main.yml` → `bigtop_repo_baseurl`

(All currently ship with placeholder values — see each file's comments.)

### 2. Run the full playbook

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

This runs, in order: OS tuning → Python → Java → MySQL → Ambari Server →
Ambari Agent → distselect fix → Hive DB → Ranger DB → HDP service
packages. See [`docs/playbooks-overview.md`](docs/playbooks-overview.md)
for the full breakdown, including one important known filename mismatch
to resolve before your first run.

At the end of this step, you should have:
- Ambari Server reachable at `http://<server-ip>/` (via the Nginx proxy)
- A registered, custom BIGTOP 3.4.0 stack
- Every agent node with `ambari-agent` running and able to register

### 3. Open the Ambari UI and add the BIGTOP repository

Log into the Ambari UI, and when prompted for the stack repository URL,
point it at your offline BIGTOP 3.4.0 repo (the same one set in
`bigtop_repo_baseurl`).

### 4. Add hosts, register manually

Add all cluster hosts to the wizard. **Because `ambari-agent` was already
installed and started by this repo's playbooks**, choose the "manually
register hosts" option rather than letting Ambari SSH out and install
agents itself — that install already happened.

### 5. Add services one by one in the Ambari UI

This is the step where [`docs/post-install/`](docs/post-install/) comes
in. For each service:

1. Add it through the wizard as normal.
2. At the **Customize Services** step, replace that service's
   `*-env template` with the JDK-17-compatible version from
   `docs/post-install/<service>/` (see that directory's `README.md` for
   the exact mapping).
3. Install and start just that service.
4. Confirm it's healthy (green, no alerts) in Ambari before adding the
   next one.

Recommended order — start with **Ambari Metrics**, since several other
services report health metrics to it and it has minimal dependencies of
its own:

```
Ambari Metrics → HDFS/YARN (core Hadoop) → ZooKeeper → Hive → Tez →
Spark → HBase (if standalone) → Ranger → Ranger KMS → Infra Solr → Zeppelin
```

Full details, every template, and every one-off command needed per
service: **[`docs/post-install/README.md`](docs/post-install/README.md)**.

## Known issues

See [`docs/playbooks-overview.md`](docs/playbooks-overview.md#known-issues)
for the `site.yml` / `hdp-packages.yml` filename mismatch that needs
resolving before a full end-to-end run.

## Security notes

- `group_vars/secrets.yml` is vault-encrypted and gitignored — never
  commit the decrypted version.
- Several MySQL grants in this project (`root@'%'`, Ambari's DB user)
  are intentionally broad because every node here lives on a single
  closed, offline internal network. See the security note in
  [`docs/playbooks/mysql.md`](docs/playbooks/mysql.md) before reusing
  any of this outside a fully isolated environment.
- Nginx currently serves HTTP only. If `roles/ambari-server/files/nginx/`
  cert/key material exists in your working copy, treat it as sensitive
  and do not commit it (see `roles/ambari-server/files/README.md`).

## Credits / context

Built and debugged against a real 40-node offline deployment. Every
"why" documented in `docs/playbooks/*.md` reflects an actual issue hit
during that build, not theoretical advice — see especially
[`docs/playbooks/ambari-server.md`](docs/playbooks/ambari-server.md) for
the BIGTOP 3.4.0 stack-cloning process and the dual-JDK (17 server / 8
cluster) setup, and [`docs/post-install/README.md`](docs/post-install/README.md)
for the recurring `JAVA_HOME` detection bug that shows up across Hive,
Ranger, and Ranger KMS.
