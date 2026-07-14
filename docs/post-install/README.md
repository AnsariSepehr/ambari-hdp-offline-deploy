# Post-Install: Ambari Cluster Wizard Fixes

Everything in `docs/post-install/` exists for one reason: **the offline
BIGTOP 3.4.0 stack this cluster uses ships default config templates that
assume an older JDK.** Running on JDK 17 (see
[`docs/playbooks/ambari-server.md`](../playbooks/ambari-server.md) for why
JDK 17 was chosen for the server), several services fail to start unless
their default `*-env.template` is replaced with a JDK-17-compatible
version, or a handful of one-off commands are run to fix broken paths,
permissions, or a Java-detection bug in Ambari's own action scripts.

None of this is applied by Ansible. It's applied **manually, per service,
during the Ambari cluster install wizard**, immediately after you add
each service and before moving on to the next one. See the top-level
[README.md](../../README.md#step-4-add-services-one-by-one-in-the-ambari-ui)
for where this fits in the overall deployment sequence.

## The general pattern, for every service below

1. In the Ambari **Add Service Wizard**, add the service as normal and let
   it get to the **Customize Services** step.
2. Find that service's config group containing the `*-env template`
   (usually under "Advanced <service>-env").
3. **Replace the entire template content** with the corresponding
   `*.template` file from this directory — don't try to hand-edit the
   default, just wholesale replace it. Ambari will still substitute its
   own `{{variable}}` values into the template at deploy time; you're only
   swapping which template those values get poured into.
4. Deploy/install the service.
5. **Before adding the next service**, start this one and confirm it's
   healthy in Ambari (green, no alerts). If any of the `*.commands` files
   below apply to this service, run them now, then restart and re-check.
6. Only then move on to the next service.

Doing this one service at a time, rather than adding everything and
deploying in one shot, makes it dramatically easier to tell which fix
belongs to which failure if something doesn't come up clean.

## Service-by-service reference

| Directory | Service | What's inside |
|---|---|---|
| [`ambari-metrics/`](ambari-metrics/) | Ambari Metrics (AMS) | `ams-env.template`, `ams-hbase-env.template` — replace both. AMS has its own embedded HBase, hence two templates. |
| [`hadoop-yarn/`](hadoop-yarn/) | HDFS + YARN (core Hadoop) | `hadoop-env.template`, `yarn-env.template` — replace both when adding the core Hadoop services. |
| [`hbase/`](hbase/) | HBase (if running standalone, not just via AMS) | `Hbase-env.template` |
| [`hive/`](hive/) | Hive | `Hive-env.template` to replace, plus `hive_check_hosts.py` — a set of commands (not an Ansible script, run manually) that patches a `JAVA_HOME` detection bug in Ambari's `check_host.py` custom action, seen specifically during Hive's DB connectivity check. |
| [`infra-solr/`](infra-solr/) | Ambari Infra Solr | `infra-solr-env.template` to replace, plus `infra-solr-gc-log-options`, `infra-solr-gc.tune` (GC tuning fragments referenced by the env template — check whether your Ambari version expects these as separate files or inlined), and `infra-solr-jaxb-commands` — copies two JAXB library jars into Solr's webapp that JDK 17 no longer bundles by default. |
| [`ranger/`](ranger/) | Ranger Admin / UserSync / TagSync | `ranger_check_hosts.py` (same `JAVA_HOME` fallback pattern as Hive, applied to Ranger's `params.py`) and `ranger.commands` (fixes the BIGTOP 3.4.0 path-bridging symlinks and file permissions for Ranger's own binaries, since Ranger installs outside the `hdp-services` role's symlink loop). |
| [`ranger-kms/`](ranger-kms/) | Ranger KMS | `ranger-kms-env.template` to replace, plus `ranger-kms.commands` — ownership/permission fixes, the same symlink pattern, MySQL password sync (**edit the placeholder passwords to your real vault values before running — never paste real passwords back into this repo**), and the same `JAVA_HOME` fallback fix applied to `RANGER_KMS`'s `params.py`. |
| [`spark/`](spark/) | Spark | `spark-env.template` to replace, plus `spark-env` — a small Hive-Metastore-compatibility snippet (pins `spark.sql.hive.metastore.version`/`jars` so Spark's built-in Hive client matches your actual Metastore version instead of guessing). |
| [`zeppelin/`](zeppelin/) | Zeppelin | `zeppelin-commands` — fixes ownership on the BIGTOP-bridged Zeppelin path and creates the notebook directory Zeppelin expects but the package doesn't create. |

## The recurring `JAVA_HOME` detection bug

You'll notice the same fix pattern in `hive/hive_check_hosts.py`,
`ranger/ranger_check_hosts.py`, and `ranger-kms/ranger-kms.commands`:
patching a stack service's `params.py` so that if Ambari's
`ambari_java_home` config value ever comes back empty, it falls back to
the real JDK 17 path instead of leaving `java_home` as `None` — which
otherwise causes a same-shaped but confusingly-worded failure in each
service's own DB/host connectivity check. This is the single most
recurring class of bug in this whole offline JDK-17 setup.

**⚠️ Caveat also noted in
[`docs/playbooks/ambari-agent.md`](../playbooks/ambari-agent.md):** these
patches target files under `/var/lib/ambari-agent/cache/`, which the
Ambari Server can overwrite when it pushes stack/action script updates to
agents. If a `JAVA_HOME`-related failure reappears on a service that was
previously fixed, re-apply the relevant `*_check_hosts` commands for that
service before assuming something else broke.

## Before you start: replace the placeholder hostnames/IPs

Several command files here use `<agent-node-x>` or `<mysql_host_ip>`
placeholders instead of real hostnames/IPs, since the originals were
specific to this cluster's internal network. Swap those for your actual
node names (from `inventory/hosts.ini`) before running any commands.
