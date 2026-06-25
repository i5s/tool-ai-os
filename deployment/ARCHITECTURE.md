# Deployment Architecture

## Target Environment
- Provider: Hetzner Cloud
- Server: 4 vCPU, 8 GB RAM, 80 GB SSD
- OS: Ubuntu 24.04 LTS

## Services
- Reverse Proxy: Caddy (HTTPS, auto-cert, HTTP->HTTPS redirect)
- Backend: FastAPI via systemd
- Frontend: static build served via Caddy
- Database: SQLite (Phase 1), daily backup with 14-day retention

## Networking
- Domain: tool.example.com
- Caddy binds 80/443 and auto-renews TLS
- HTTPS enforced; HSTS recommended after beta validation
