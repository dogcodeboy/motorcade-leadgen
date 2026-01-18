# Risks & notes

- If nginx is not installed/managed on the host, set `leadgen_manage_nginx=false` (future enhancement: detect and skip automatically).
- The quadlet unit references an image that does not exist yet; the playbook intentionally leaves the service stopped.
- SELinux: `httpd_can_network_connect` is required for nginx->localhost proxying.
