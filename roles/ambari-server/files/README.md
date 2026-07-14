# files/

This role's `files/` directory needs several artifacts staged before the
role runs. None of these were shared in detail, so this is a checklist —
copy your actual files in here with these exact names (referenced by the
`copy:` tasks in `tasks/files.yml`, `db.yml`, `setup.yml`, `postinstall.yml`):

```
files/
├── ambari-server.service                  # custom systemd unit
├── Ambari-DDL-MySQL-CREATE.sql             # MySQL 8-compatible schema
├── Ambari-DDL-MySQL-CREATE-mysql8.sql      # (check which one is authoritative —
│                                              tasks/db.yml only references the
│                                              plain CREATE.sql file, not this one
│                                              or the .sql.1 backup — see docs)
├── BIGTOP-3.4.0-local.xml                  # local repo definition
├── mysql-connector-j-8.0.32.jar
├── mysql-connector-j-9.6.0.jar             # actively used by tasks
└── nginx/
    ├── nginx.conf                          # (role uses templates/nginx.conf.j2 instead —
    │                                          confirm if this static file is still needed)
    ├── certs.pem
    ├── dhparam.pem
    └── private.key
```

## ⚠️ Do not commit `nginx/private.key` (or any real cert material)

`nginx.conf.j2` currently serves HTTP only — no SSL block references these
files. If they're unused leftovers, delete them. If you *are* using them
somewhere outside what's shown here, treat `private.key` as a secret:
keep it out of git entirely (already covered by `.gitignore` — see repo
root), distribute it out-of-band, and rotate it before making this repo
public if it has ever been a real, working key.

## Also gitignored (stage manually)

`*.jar`, `*.tar.gz` — the JDBC connector jars belong here but aren't
committed; see the root `.gitignore`.
