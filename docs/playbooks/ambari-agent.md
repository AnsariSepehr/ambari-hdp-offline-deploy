# Ambari Agent

**Playbook:** `playbooks/ambari-agent.yml`
**Role:** `roles/ambari-agent`
**Targets:** `ambari_agent` inventory group (all worker nodes)

Installs the Ambari Agent and points it at the Ambari Server, with a
couple of targeted patches to work around JDK-detection issues seen in
practice on this cluster.

## What it does (`roles/ambari-agent/tasks/main.yml`)

1. `install.yml` — installs `ambari-agent`, `diffutils`, `net-tools`.
2. `config.yml`:
   - Stages a JDBC connector jar into the agent's lib dir "for future use"
     (agents don't need direct DB access, but some HDP service checks
     expect the driver to be present locally).
   - Sets `hostname=` in `ambari-agent.ini` to `ambari_server_host` — this
     is how the agent finds the server to register with.
   - Sets `java_home=` explicitly in `ambari-agent.ini`.
   - Patches `check_host.py` in the agent's cache directory to force a
     `JAVA_HOME` fallback when Ambari's own db-connection check leaves it
     `None`.
   - Optionally copies custom hostname-resolution scripts, gated by
     `ambari_agent_copy_hostname_scripts` (off by default).
3. `start.yml` — deploys a custom systemd unit and starts the service.

## ⚠️ Known caveat: the `check_host.py` patch doesn't survive reconnects

The `check_host.py` patch in `config.yml` targets a file under
`/var/lib/ambari-agent/cache/custom_actions/scripts/` — this cache
directory gets **overwritten by the Ambari Server** whenever the agent
reconnects or the server pushes updated action scripts. That means this
patch is not durable across the full cluster lifecycle; it was useful for
getting past a specific `JAVA_HOME` check failure during initial setup,
but don't rely on it surviving long-term. If `JAVA_HOME` detection issues
resurface after a server-side update, this patch will need to be
reapplied (or better: fixed at the source — i.e., make sure
`ambari_agent_java_home` / the agent's environment always has a valid
`JAVA_HOME` before this check ever runs, rather than patching around a
`None` value after the fact).

## Key variables (`roles/ambari-agent/defaults/main.yml`)

| Variable | Default | Purpose |
|---|---|---|
| `ambari_server_host` | placeholder — set to your master node's IP/FQDN | Where the agent registers |
| `ambari_agent_java_home` | `/usr/lib/jvm/jdk-17.0.6` | JDK the agent process uses |
| `ambari_agent_copy_hostname_scripts` | `false` | Opt-in for the custom hostname scripts |

## Offline prerequisites

See `roles/ambari-agent/files/README.md`. Note: `mysql-connector-j-8.0.32.jar`
is staged in that directory but not referenced by any task in this role —
confirm whether it's still needed before dropping it.
