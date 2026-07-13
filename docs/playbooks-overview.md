# Playbooks Overview

All playbooks are orchestrated by `playbooks/site.yml`, which runs them in
this order:

| # | Playbook | Targets | Purpose |
|---|---|---|---|
| 1 | `os_tuning.yml` | `all` | Kernel/OS baseline tuning ([docs](playbooks/os-tuning.md)) |
| 2 | `python.yml` | `all` | Installs Python 3.12 alongside system Python ([docs](playbooks/python.md)) |
| 3 | `java.yml` | `all` | Installs JDK 8/11/17/21 side-by-side |
| 4 | `mysql.yml` | `mysql` | Installs and configures MySQL |
| 5 | `ambari-server.yml` | `ambari_server` | Installs Ambari Server on the master node |
| 6 | `ambari-agent.yml` | `ambari_agent` | Installs Ambari Agent on worker nodes |
| 7 | `distselect.yml` | `all` | Configures `bigtop-select` (fixes the distro-select symlink issue) |
| 8 | `hive-db.yml` | `mysql` | Creates the Hive metastore database |
| 9 | `ranger-db.yml` | `mysql` | Creates the Ranger + Ranger Audit databases |
| 10 | `hdp-services.yml`* | `ambari_agent` | Stages offline HDP service packages on agent nodes |

\* Note: the role backing this step is `hdp-services`, but the playbook
file on disk is currently named `hdp-packages.yml`. `site.yml` imports
`hdp-services.yml` — these need to be reconciled (rename the file or update
the import) before a full `ansible-playbook site.yml` run will work
end-to-end. See [known issues](#known-issues) below.

## Running the full deployment

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

## Running an individual stage

Every playbook after the first two carries a tag matching its name, so you
can re-run just one stage during troubleshooting:

```bash
ansible-playbook playbooks/site.yml --tags ambari-agent --ask-vault-pass
```

## Inventory groups these playbooks depend on

| Group | Used by |
|---|---|
| `all` | os_tuning, python, java, distselect |
| `mysql` | mysql, hive-db, ranger-db |
| `ambari_server` | ambari-server |
| `ambari_agent` | ambari-agent, hdp-services |

See `inventory/hosts.ini.example` for the expected shape.

## Known issues

- **`site.yml` vs `hdp-packages.yml` filename mismatch** — `site.yml`
  imports `hdp-services.yml`, but the actual playbook file is
  `hdp-packages.yml`. Rename one to match the other before running the
  full site playbook, or split into two intentionally separate steps if
  that was the original design.
