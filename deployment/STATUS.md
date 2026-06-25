# Deployment Status

## Phase 1 Complete
- Reverse proxy: Caddy configured
- Backend: systemd unit created
- Frontend: static build served via Caddy (placeholder path)
- Database: SQLite with daily backup script
- Secrets: externalized to `.env`

## Remaining
- Replace `tool.example.com` with real domain
- Provision server and copy deployment files
- Validate TLS issuance
- Confirm health endpoints
