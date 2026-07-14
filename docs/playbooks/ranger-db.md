# Ranger Databases (Admin + Audit)

**Playbook:** `playbooks/ranger-db.yml`
**Role:** `roles/ranger-db`
**Targets:** `mysql` inventory group (delegates to `ambari_server`)

Creates both databases Ranger needs — the Admin (policy store) DB and the
Audit (access-log) DB — plus their users, in one role. Mirrors the
`hive-db` role's pattern almost exactly, with one addition: an explicit
post-creation verification step.

## What it does

1. Creates the Ranger Admin database (`ranger`).
2. Creates the Ranger Audit database (`ranger_logger`).
3. Creates the Ranger Admin user and grants it privileges on **both**
   databases in a single grant (`append_privs: yes` so a second grant call
   doesn't clobber the first), across `localhost`, `%`, a literal
   `RemoteServer` host entry, and the running host's FQDN.
4. Conditionally creates a *separate* Ranger Audit user — only if
   `ranger_audit_db_user` differs from `ranger_db_user` (by default they're
   the same user, so this task is a no-op unless you override the audit
   user name).
5. Flushes privileges.
6. **Verifies** both users actually exist in `mysql.user` afterward, and
   fails loudly (`fail:`) if they don't — a safety net that isn't present
   in the otherwise-identical `hive-db` role, worth carrying over there
   too if you want consistency.

## `delegate_to` — same pattern as `hive-db`

All tasks delegate to `groups['ambari_server'][0]`, so the actual DB
operations run from the Ambari Server node's network path, regardless of
which host the playbook nominally targets. See `docs/playbooks/hive-db.md`
for the full reasoning.

## Key variables (`roles/ranger-db/defaults/main.yml`)

| Variable | Default | Purpose |
|---|---|---|
| `ranger_db_host` | placeholder — set to your MySQL node | Admin DB host |
| `ranger_db_name` | `ranger` | Admin/policy database |
| `ranger_audit_db_name` | `ranger_logger` | Audit database |
| `ranger_grant_hosts` | `[localhost, %, RemoteServer, {{ ansible_fqdn }}]` | Hosts the Ranger user is granted from |

Vault-backed: `vault_ranger_db_password`, `vault_ranger_audit_db_password`
(falls back to the admin password if unset), `vault_mysql_root_password`.

## Note on `RemoteServer`

The literal hostname `RemoteServer` in `ranger_grant_hosts` looks like a
leftover placeholder from wherever this pattern was originally sourced —
it's not a real host in this cluster's inventory. It's harmless (MySQL
will just never match a connection from a host literally named
`RemoteServer`), but worth removing if you want the grant list to only
reflect real, intentional access paths.
