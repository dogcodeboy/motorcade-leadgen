# Rollback

If you need to revert the bootstrap changes:

1. Remove Nginx vhost:

```bash
sudo rm -f /etc/nginx/conf.d/leadgen.motorcade.vip.conf
sudo systemctl reload nginx
```

2. Optional: disable SELinux boolean (only if you are sure you don't need local upstream proxying):

```bash
sudo setsebool -P httpd_can_network_connect off
```

3. Optional: remove LeadGen directories (destructive):

```bash
sudo rm -rf /opt/motorcade-leadgen /var/lib/motorcade-leadgen /var/log/motorcade-leadgen
```
