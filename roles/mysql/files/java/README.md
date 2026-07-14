# files/java/

This directory must contain the MySQL JDBC connector jars before running
the `mysql` role — they are **not** committed to git (`.gitignore`
excludes `*.jar`):

```
mysql-connector-j-8.0.32.jar
mysql-connector-j-8.4.0.jar
mysql-connector-j-9.6.0.jar
```

Note: `roles/mysql/tasks/jdbc.yml` only actually copies the `9.6.0` and
`8.4.0` jars — `8.0.32.jar` is staged in this folder but currently unused
by any task. Keep it if other roles (e.g. `ambari-agent`, which has its
own copy) need it, otherwise it's safe to drop.

Download these from https://dev.mysql.com/downloads/connector/j/ on a
machine with internet access, then place them here before syncing this
repo to your offline nodes.
