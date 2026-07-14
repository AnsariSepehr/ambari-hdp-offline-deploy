# files/java/

This directory must contain the following JDK tarballs before running the
`java` role — they are **not** committed to git (`.gitignore` excludes
`*.tar.gz`):

```
jdk-8u202-linux-x64.tar.gz
jdk-11.0.11_linux-x64_bin.tar.gz
jdk-17.0.6_linux-x64_bin.tar.gz
jdk-21.0.1_linux-x64_bin.tar.gz
```

Download each from Oracle (or your preferred OpenJDK/Adoptium mirror) on a
machine with internet access, matching the exact filenames referenced in
`roles/java/defaults/main.yml` under `jdk_versions.*.filename` — the role
copies these by that exact name, so renaming a downloaded file will break
the `copy` task's `src:` lookup.

Stage these files here before syncing this repo to your offline nodes.
