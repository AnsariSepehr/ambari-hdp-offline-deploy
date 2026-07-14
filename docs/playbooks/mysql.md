# MySQL

**Playbook:** `playbooks/mysql.yml`
**Role:** `roles/mysql`
**Targets:** `mysql` inventory group only (single DB host in this cluster)

Installs a pinned MySQL 8.0.43 build, deploys the JDBC connector jars later
consumed by Ambari/Hive/Ranger, configures the instance, and secures the
root account — all driven by `group_vars/secrets.yml` (vault-encrypted).

## Execution order (`roles/mysql/tasks/main.yml`)

1. **`install.yml`** — installs pinned MySQL 8.0.43 packages
   (server, common, libs, devel) plus `python3-PyMySQL`, needed for
   Ansible's `community.mysql` modules used later in `secure.yml`.
2. **`jdbc.yml`** — copies the MySQL JDBC connector jars
   (`9.6.0`, `8.4.0`) from `roles/mysql/files/java/` into
   `/usr/share/java/`, and symlinks `mysql-connector-java.jar` →
   the 9.6.0 jar as the default driver Ambari/Hive will reference.
3. **`service.yml`** — resolves the correct systemd unit name (supports
   named instances via `mysql_instance_name`), touches the log file with
   correct ownership, enables and starts the service.
4. **`config.yml`** — creates the custom data directory and deploys
   `my.cnf` from a template.
5. **`secure.yml`** — sets the root password from vault, forces
   `mysql_native_password` auth (needed for compatibility with Ambari's
   DB connectivity checks), and grants root full privileges from both
   `%` (any host) and the node's own FQDN.

## Key variables (`roles/mysql/defaults/main.yml`)

```yaml
mysql_root_user: "root"
mysql_port: 3306
mysql_instance_name: ""       # set this to run a named instance (mysqld@<name>.service)
mysql_first_install: true     # controls the socket-auth root-password bootstrap task
mysql_datadir: "/var/lib/mysql"
```

Root password itself comes from vault: `vault_mysql_root_password`
(see `group_vars/secrets.yml.example`).

## Offline prerequisite

`roles/mysql/files/java/` must contain the JDBC jars before this role
runs — see that folder's `README.md`. Gitignored (`*.jar`), staged
manually.

## ⚠️ Security note

`secure.yml` grants `root@'%'` (i.e. root, reachable from **any** host)
`ALL,GRANT` privileges. This is intentional here because Ambari Server,
Hive, and Ranger all need to reach this MySQL instance from other cluster
nodes, and the cluster is fully offline / internal-network-only with no
external exposure. If you reuse this role outside a fully isolated
network, replace the wildcard host grant with the specific node IPs/FQDNs
that actually need DB access, and consider creating scoped service
accounts (`ambari`, `hive`, `ranger`) instead of using root for
application connectivity.

## Notes / gotchas

- `install.yml` pins exact package/version strings
  (`mysql-server-8.0.43-1.el9_6`, etc.) — these must exist in your offline
  repo mirror or the install will fail. If you're targeting a different
  MySQL point release, update every pinned name here consistently.
- `roles/mysql/templates/mysqld_auth.cnf.j2` exists but isn't referenced
  by any task in `config.yml` — `default_authentication_plugin` is instead
  set directly in `my.cnf.j2`. Looks like leftover/alternative config;
  safe to remove unless you plan to split it out as a drop-in
  `/etc/my.cnf.d/` file.
- `mysql-connector-j-8.0.32.jar` sits in `files/java/` but is never copied
  by `jdbc.yml` — only 9.6.0 and 8.4.0 are. Confirm whether another role
  (e.g. `ambari-agent`) needs the 8.0.32 jar specifically before removing
  it.
