# nginx reverse-proxy config for self-hosted explorer

Reference nginx vhost for running the PWM web explorer Docker container
behind nginx + Let's Encrypt on a Linux server. This is Option 3 in
`pwm-team/coordination/EXPLORER_HOSTING_OPTIONS.md`.

## Install

Copy the config into place and enable it:

```bash
sudo cp explorer.pwm.platformai.org.conf \
    /etc/nginx/sites-available/explorer.pwm.platformai.org
sudo ln -s /etc/nginx/sites-available/explorer.pwm.platformai.org \
    /etc/nginx/sites-enabled/explorer.pwm.platformai.org
sudo nginx -t && sudo systemctl reload nginx
```

## TLS via certbot

Once DNS points the hostname at the server:

```bash
sudo certbot --nginx \
    -d explorer.pwm.platformai.org \
    --non-interactive --agree-tos --redirect \
    -m you@example.com
```

`certbot --nginx` modifies the server block in place, adding the
`listen 443 ssl` + `ssl_certificate` lines and a 301 redirect from 80.

## What the config does

| Component | Role |
|-----------|------|
| `listen 80` | Plain HTTP (certbot adds `listen 443 ssl` on first run and a 301 redirect) |
| `include snippets/security-headers.conf` | Site-wide headers (present on this server; adjust for yours) |
| `proxy_pass http://127.0.0.1:3000` | Target: the Docker container |
| `proxy_set_header ...` | Preserves `Host`, `X-Real-IP`, etc. for the Next.js app |
| `Upgrade/Connection` headers | Supports Next.js RSC streaming + any future websockets |

## Docker run

```bash
docker run -d \
  --name pwm-explorer \
  --restart unless-stopped \
  -p 127.0.0.1:3000:3000 \
  -e PWM_NETWORK=testnet \
  -e PWM_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com \
  pwm-explorer:latest
```

Note the `127.0.0.1:3000:3000` bind — the container is only reachable
from nginx on the same host, not from the public internet directly.

## Deployed instance (current)

This exact config is what runs at `explorer.pwm.platformai.org` on a
GCP server (public IP `34.63.169.185`), same host as `pwm.platformai.
org` and ~10 other `platformai.org` subdomains.
