# Deployment

## Steps
1. Provision Hetzner server (Ubuntu 24.04).
2. Create user `tool` and app directory `/opt/tool`.
3. Copy repo and install dependencies in `.venv`.
4. Create `/opt/tool/.env` from `deployment/.env.example`.
5. Install `deployment/toll.service` to `/etc/systemd/system/`.
6. Install `deployment/Caddyfile` to `/etc/caddy/Caddyfile`.
7. Enable and start services.
8. Verify health endpoints.

## Commands
- systemctl enable --now toll
- systemctl enable --now caddy
- curl -I https://tool.example.com/api/health
