# Verification

After running `00-bootstrap.yml`:

```bash
sudo nginx -t
sudo systemctl status nginx --no-pager
sudo getsebool httpd_can_network_connect
sudo ls -lah /opt/motorcade-leadgen
sudo ls -lah /var/lib/motorcade-leadgen
sudo ls -lah /var/log/motorcade-leadgen
```

You should see:
- nginx config test passes
- `httpd_can_network_connect --> on`
- LeadGen directories exist and are owned by the `leadgen` user
