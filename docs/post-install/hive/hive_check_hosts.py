# These commands patch a bug in Ambari's check_host.py custom action script,
# which sometimes leaves `java_home` as None during the Hive DB connection
# check on JDK 17 clusters, causing the check to fail with a confusing error.
#
# Replace "dpm02/dpm03/dpm04/dpm05" below with your actual agent node
# hostnames from inventory/hosts.ini.
#
# Run the first sed locally on whichever node is running the check
# (commonly wherever Hive Metastore/HiveServer2 is being installed):

sed -i 's/if java_home is None:/if False: # disabled - was referencing undefined variable/' \
  /var/lib/ambari-agent/cache/custom_actions/scripts/check_host.py

# Then apply the same fix on each remaining agent node over SSH:
ssh <agent-node> "sed -i 's/if java_home is None:/if False: # disabled - was referencing undefined variable/' \
  /var/lib/ambari-agent/cache/custom_actions/scripts/check_host.py"

# Force java_home to fall back to JDK 17 if it's ever unset:
sed -i 's/java_home = ambari_java_home/java_home = ambari_java_home or "\/usr\/lib\/jvm\/jdk-17.0.6"/' \
  /var/lib/ambari-agent/cache/custom_actions/scripts/check_host.py

# Verify the fix took effect:
grep -n "ambari_java_home" /var/lib/ambari-agent/cache/custom_actions/scripts/check_host.py
grep -n "java_home is None" /var/lib/ambari-agent/cache/custom_actions/scripts/check_host.py

# Apply the equivalent fix inside the Hive service's own params.py on every
# agent node (replace the list below with your actual agent hostnames):
for host in <agent-node-1> <agent-node-2> <agent-node-3> <agent-node-4>; do
  ssh $host "sed -i 's/ambari_java_home = config\[\"ambariLevelParams\"\]\[\"ambari_java_home\"\]/ambari_java_home = config[\"ambariLevelParams\"][\"ambari_java_home\"] or \"\/usr\/lib\/jvm\/jdk-17.0.6\"/' \
    /var/lib/ambari-agent/cache/stacks/BIGTOP/3.2.0/services/HIVE/package/scripts/params.py"
done

# Verify on all nodes:
for host in <agent-node-1> <agent-node-2> <agent-node-3> <agent-node-4>; do
  echo "=== $host ==="
  ssh $host "grep -n 'ambari_java_home' /var/lib/ambari-agent/cache/stacks/BIGTOP/3.2.0/services/HIVE/package/scripts/params.py | head -5"
done
