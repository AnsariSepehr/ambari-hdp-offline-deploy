# files/

Stage these before running the role:

```
files/
├── ambari-agent.service                     # custom systemd unit
├── ambari-agent-internal-hostname.sh         # only copied if
├── ambari-agent-public-hostname.sh           #   ambari_agent_copy_hostname_scripts: true
├── mysql-connector-j-8.0.32.jar              # present but not referenced by any task —
│                                                confirm still needed, see docs/playbooks/ambari-agent.md
└── mysql-connector-j-9.6.0.jar               # actively used
```

`.jar` files are gitignored at the repo root — copy them here manually
before syncing to your offline nodes. The two hostname scripts and the
`.service` file are plain text/shell and safe to commit as-is.
