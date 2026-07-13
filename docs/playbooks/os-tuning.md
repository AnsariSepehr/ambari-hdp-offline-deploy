# OS Tuning

**Playbook:** `playbooks/os_tuning.yml`
**Role:** `roles/os_tuning`

Baseline OS preparation applied to every node in the cluster before any
Hadoop/Ambari component is installed. This is the first playbook in
`site.yml` — nothing else should run before it.

## What it does

| Task file | Purpose |
|---|---|
| `sysctl.yml` | Applies kernel parameters required by Hadoop workloads: lowers swappiness, raises `vm.max_map_count` and `fs.file-max`, tunes networking (`somaxconn`, ephemeral port range). |
| `swap.yml` | Fully disables swap — `swapoff -a`, removes swap entries from `/etc/fstab`, deletes common swap files. HDFS/YARN/HBase perform poorly and unpredictably with active swap. |
| `limits.yml` | Raises `nofile` (open file descriptors) and `nproc` (max processes) soft/hard limits via PAM — HDFS DataNodes and HBase RegionServers routinely exceed default OS limits under load. |
| `thp.yml` | Disables Transparent Huge Pages at runtime and installs a systemd unit so it stays disabled after reboot. THP causes latency spikes/stalls in JVM-heavy workloads (this is a very well-known HBase/Hadoop recommendation). |
| `selinux.yml` | Disables SELinux. HDP/Ambari components are not SELinux-aware out of the box and installation frequently breaks with it enforcing. |
| `setup-os.yml` | Sets a system-wide umask/locale, and installs the base package set every node needs (utilities, compression tools, `pdsh` for cluster-wide shell commands, `etckeeper` to track `/etc` changes over time, plus Hadoop-related native libraries like `snappy` for compression codecs). |

## Key variables (`roles/os_tuning/defaults/main.yml`)

```yaml
os_tuning_sysctl:
  vm.swappiness: 1
  vm.max_map_count: 262144
  fs.file-max: 1000000
  net.core.somaxconn: 4096
  net.ipv4.ip_local_port_range: "10000 65535"

os_tuning_nofile_soft: 65536
os_tuning_nofile_hard: 65536
os_tuning_nproc_soft: 65536
os_tuning_nproc_hard: 65536

disable_thp: true
disable_selinux: true
```

Override any of these in `group_vars/all.yml` if a given environment needs
different values.

## Notes / gotchas

- `setup-os.yml` uses `dnf`, so this role targets RHEL-family systems
  (Rocky/AlmaLinux/CentOS) — the `swap.yml` file has an Ubuntu/Debian branch
  for the swap-file cleanup step, but the package installation tasks are
  RHEL-specific.
- `os_run_distro_sync` is `false` by default and opt-in only — full
  `distro_sync` on 40 nodes is disruptive and should be a deliberate choice,
  not a default.
- Since this is a fully offline install, `dnf` here relies on your local
  offline repo already being configured on each node (see
  [prerequisites.md](../prerequisites.md)) — this role does not configure
  the repo itself.
