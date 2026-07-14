# Java (JDK 8 / 11 / 17 / 21)

**Playbook:** `playbooks/java.yml`
**Role:** `roles/java`

Installs four JDK versions side-by-side on every node from pre-downloaded
tarballs, wires them all into `update-alternatives`, and sets a
cluster-wide default via `JAVA_HOME`.

## Why four JDKs

Different Hadoop ecosystem components have different Java version
requirements/support levels (older HDP services often need 8/11, while
newer tooling and Ambari itself may run better on 17). Rather than picking
one version and fighting compatibility issues later, this installs all
four and lets `update-alternatives` manage which one is "active" —
individual services can still target a specific `JAVA_HOME` if needed.

## What it does

1. Ensures `tar`/`gzip` are present.
2. Creates `/usr/lib/jvm`, `/usr/share/java`, `/etc/java`.
3. Copies each enabled JDK tarball from `roles/java/files/java/` to the
   node and extracts it under `/usr/lib/jvm/`.
4. Registers every JDK with `update-alternatives --install ... java_home`,
   auto-discovering each JDK's `bin/` and `man/man1/` files to wire in as
   `--slave` entries (so `java`, `javac`, `jar`, etc. all switch together
   when the active JDK changes).
5. Sets **JDK 17 as the cluster default** via
   `update-alternatives --set java_home`.
6. Writes `JAVA_HOME`, `PATH`, `JRE_HOME`, `CLASSPATH` into
   `/etc/profile.d/dataplatform_java_profile.sh` and `/etc/environment`,
   plus `HADOOP_CLASSPATH` into a separate dataplatform profile script.
7. Marks itself done via a sentinel file (`/etc/java/javaOsConfigured`) so
   the environment-configuration block only runs once, even across repeat
   playbook runs.
8. Sets `/tmp` to `1777` and fixes ownership/permissions on the active
   JDK's own `java.io.tmpdir`.

## Key variables (`roles/java/defaults/main.yml`)

```yaml
java_install_base_dir: '/usr/lib/jvm'
java_home_link: '/usr/lib/jvm/current'
java_config_dir: '/etc/java'
java_profile_path: '/etc/profile.d/dataplatform_java_profile.sh'

jdk_versions:
  8:  { enabled: "y", filename: "jdk-8u202-linux-x64.tar.gz", ... }
  11: { enabled: "y", filename: "jdk-11.0.11_linux-x64_bin.tar.gz", ... }
  17: { enabled: "y", filename: "jdk-17.0.6_linux-x64_bin.tar.gz", ... }
  21: { enabled: "y", filename: "jdk-21.0.1_linux-x64_bin.tar.gz", ... }
```

Disable any version you don't need by setting its `enabled: "n"` — the
loop skips anything not `enabled == 'y'`.

## Offline prerequisite

The four JDK tarballs must be staged in `roles/java/files/java/` before
this role runs — see that folder's `README.md`. They're gitignored
(`*.tar.gz`) since binaries don't belong in version control.

## Notes / gotchas

- Changing the default JDK long-term: edit the "Set default Java to JDK 17"
  task in `roles/java/tasks/main.yml`, or convert it into a variable if
  you want per-environment control without editing the role.
- `roles/java/templates/java_config.sh.j2` exists in the role but isn't
  currently referenced by any task — it looks like scaffolding for a
  future per-version config drop that never got wired in. Either remove it
  or add the `template:` task that uses it.
- Because of the `javaOsConfigured` sentinel, if you need to force the
  profile/environment block to re-run (e.g. after changing
  `java_profile_path`), delete `/etc/java/javaOsConfigured` on the node
  first.
