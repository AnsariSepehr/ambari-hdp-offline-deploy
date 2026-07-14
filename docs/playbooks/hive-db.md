# Hive Database

**Playbook:** `playbooks/hive-db.yml`
**Role:** `roles/hive-db`
**Targets:** `mysql` inventory group (runs, but delegates)

Creates the Hive metastore database and its dedicated MySQL user ahead of
the Hive service being installed via Ambari's cluster wizard.

## What it does

1. Creates the `hive` database (UTF8 / `utf8_general_ci`) if it doesn't exist.
2. Creates the `hive` MySQL user with full privileges on that database
   only (`hive_db_name.*:ALL` — **not** global privileges, unlike the
   `ambari`/`root` accounts elsewhere in this project), granted from
   `localhost`, `%`, the running host's FQDN, and the configured DB host.
3. Flushes privileges.

## `delegate_to` — why this always runs from the Ambari Server node

Every task delegates to `groups['ambari_server'][0]` — i.e., regardless
of which host the playbook's `hosts: mysql` targets, the actual MySQL
operations always execute *from* the Ambari Server node. This matters
because `hive_db_host`/`login_host` point at the MySQL server's address,
and delegating ensures the `community.mysql` modules connect over the
network the same way the eventual Hive service will, rather than
connecting locally via socket auth on the MySQL box itself — closer to a
real-world connectivity test of the path Hive will actually use.

## Key variables (`roles/hive-db/defaults/main.yml`)

| Variable | Default | Purpose |
|---|---|---|
| `hive_db_host` | placeholder — set to your MySQL node's IP/FQDN | Where Hive's metastore DB lives |
| `hive_db_name` | `hive` | Database name |
| `hive_db_user` | `hive` | Dedicated Hive DB user (scoped privileges, not root) |
| `hive_db_password` | `{{ vault_hive_db_password }}` | From vault |
| `hive_db_root_password` | `{{ vault_mysql_root_password }}` | Used only to perform the create/grant, not stored anywhere else |

## Notes

This mirrors the `ranger-db` role's pattern — expect that role to look
almost identical, just for the Ranger and Ranger Audit databases instead.
