# Same JAVA_HOME fallback fix as Hive, applied to the RANGER service's
# params.py. Replace <agent-node-x> with your actual agent hostnames
# (only the nodes running Ranger components need this).

for host in <agent-node-4> <agent-node-5>; do
  ssh $host "sed -i 's/ambari_java_home = config\[\"ambariLevelParams\"\]\[\"ambari_java_home\"\]/ambari_java_home = config[\"ambariLevelParams\"].get(\"ambari_java_home\") or \"\/usr\/lib\/jvm\/jdk-17.0.6\"/' \
    /var/lib/ambari-agent/cache/stacks/BIGTOP/3.4.0/services/RANGER/package/scripts/params.py"
done

# Verify
for host in <agent-node-4> <agent-node-5>; do
  echo "=== $host ==="
  ssh $host "grep -n 'ambari_java_home' /var/lib/ambari-agent/cache/stacks/BIGTOP/3.4.0/services/RANGER/package/scripts/params.py | head -5"
done
