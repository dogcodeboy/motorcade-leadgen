```bash
# stop + disable the service
sudo systemctl disable --now leadgen-api

# remove quadlet unit
sudo rm -f /etc/containers/systemd/leadgen-api.container
sudo systemctl daemon-reload

# remove installed app (optional)
sudo rm -rf /opt/motorcade-leadgen/app/api
```
