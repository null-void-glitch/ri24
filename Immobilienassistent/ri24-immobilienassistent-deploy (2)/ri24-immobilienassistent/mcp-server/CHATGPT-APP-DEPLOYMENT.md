# RI24 MCP Server – FreeBSD Deployment Guide

## Package Contents

The deployment archive `ri24-mcp-deploy.tar.gz` contains:

```
├── server/
│   ├── dist/
│   │   ├── index.js          # Main server (compiled)
│   │   └── db.js             # XML parser + search logic (compiled)
│   ├── package.json          # Runtime dependencies
│   └── .env                  # Configuration (credentials)
├── web/
│   └── dist/
│       └── assets/
│           ├── index.js      # React frontend bundle (460 KB)
│           └── index.css     # Tailwind styles (26 KB)
├── nginx-ri24-mcp.conf       # Nginx reverse proxy config
└── ri24_mcp.rc               # FreeBSD rc.d service script
```

> [!IMPORTANT]
> The `web/dist/` folder must be located alongside `server/` — the server reads the frontend bundle from `../web/dist/assets/` relative to its working directory.

---

## Prerequisites

| Requirement | Minimum | Notes |
|---|---|---|
| FreeBSD | 13+ | Any recent version |
| Node.js | 18+ | `pkg install node20` or `node22` |
| npm | 9+ | Comes with Node.js |
| Nginx | 1.24+ | `pkg install nginx` |
| RAM | 512 MB free | The 189 MB XML is parsed into memory |
| SSL cert | Required | ChatGPT only connects via HTTPS |

---

## Step-by-Step Installation

### 1. Install Node.js

```sh
pkg install node20 npm-node20
```

Verify:
```sh
node --version    # Should show v20.x+
npm --version     # Should show 9.x+
```

### 2. Create the application directory

```sh
mkdir -p /opt/ri24-mcp
```

### 3. Upload and extract the deployment package

Copy `ri24-mcp-deploy.tar.gz` to the server, then:

```sh
cd /opt/ri24-mcp
tar xzf /path/to/ri24-mcp-deploy.tar.gz
```

The directory should now look like:
```
/opt/ri24-mcp/
├── server/
│   ├── dist/
│   ├── package.json
│   └── .env
├── web/
│   └── dist/
├── nginx-ri24-mcp.conf
└── ri24_mcp.rc
```

### 4. Install Node.js dependencies

```sh
cd /opt/ri24-mcp/server
npm install --production
```

This installs the runtime dependencies (~50 MB in `node_modules/`).

### 5. Configure environment

Edit `/opt/ri24-mcp/server/.env`:

```env
OPENIMMO_URL=https://zbv.regionalimmobilien24.de/webapi/openimmo/export.full.xml
OPENIMMO_USER=pitcom
OPENIMMO_PASS=test
```

> [!CAUTION]
> These are real credentials. Set file permissions accordingly:
> ```sh
> chmod 600 /opt/ri24-mcp/server/.env
> chown www:www /opt/ri24-mcp/server/.env
> ```

### 6. Test manually

```sh
cd /opt/ri24-mcp/server
node dist/index.js
```

You should see:
```
MCP SSE Server listening at http://127.0.0.1:3000/mcp
Starting OpenImmo XML download...
Download succeeded. Parsing XML...
Loaded XXXXX properties.
```

Press `Ctrl+C` to stop once confirmed.

### 7. Set up the rc.d service

```sh
cp /opt/ri24-mcp/ri24_mcp.rc /usr/local/etc/rc.d/ri24_mcp
chmod 755 /usr/local/etc/rc.d/ri24_mcp
```

Add to `/etc/rc.conf`:

```sh
sysrc ri24_mcp_enable="YES"
sysrc ri24_mcp_dir="/opt/ri24-mcp/server"
sysrc ri24_mcp_user="www"
sysrc ri24_mcp_logfile="/var/log/ri24-mcp.log"
```

Start the service:

```sh
service ri24_mcp start
```

Check it's running:

```sh
service ri24_mcp status
cat /var/log/ri24-mcp.log
```

### 8. Set up Nginx reverse proxy

#### a. Obtain an SSL certificate

```sh
pkg install py311-certbot py311-certbot-nginx
certbot certonly --nginx -d mcp.regionalimmobilien24.de
```

> [!NOTE]
> Replace `mcp.regionalimmobilien24.de` with whatever subdomain you decide to use. You'll need a DNS A record pointing to your server's IP first.

#### b. Install the Nginx config

Edit `nginx-ri24-mcp.conf` to replace the domain name if needed, then:

```sh
cp /opt/ri24-mcp/nginx-ri24-mcp.conf /usr/local/etc/nginx/conf.d/ri24-mcp.conf
```

If your nginx doesn't use `conf.d/`, include it in your main `nginx.conf`:
```nginx
http {
    # ... existing config ...
    include /usr/local/etc/nginx/conf.d/*.conf;
}
```

#### c. Test and reload Nginx

```sh
nginx -t            # Test config
service nginx reload
```

### 9. Verify the deployment

From any machine:

```sh
# Health check
curl https://mcp.regionalimmobilien24.de/mcp/sse

# Domain verification (ChatGPT uses this)
curl https://mcp.regionalimmobilien24.de/.well-known/openai-apps-challenge
```

The SSE endpoint should start streaming (it keeps the connection open). The challenge endpoint should return a verification token.

---

## ChatGPT App Configuration

Once the server is running and accessible via HTTPS, the MCP Server URL to provide to ChatGPT is:

```
https://mcp.regionalimmobilien24.de/mcp/sse
```

---

## Maintenance

### Viewing logs

```sh
tail -f /var/log/ri24-mcp.log
```

### Restarting the service

```sh
service ri24_mcp restart
```

### Updating the application

```sh
service ri24_mcp stop
cd /opt/ri24-mcp
tar xzf /path/to/new-ri24-mcp-deploy.tar.gz
cd server && npm install --production
service ri24_mcp start
```

### Auto-renew SSL certificates

Add to root's crontab (`crontab -e`):

```
0 3 1 * *  /usr/local/bin/certbot renew --quiet && service nginx reload
```

### XML data refresh

The server downloads `export.full.xml` on startup automatically. To refresh the property data, simply restart the service:

```sh
service ri24_mcp restart
```

> [!TIP]
> To auto-refresh the property data daily, add a cron job:
> ```
> 0 4 * * *  /usr/sbin/service ri24_mcp restart
> ```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| ChatGPT can't connect | Firewall blocking 443 | `ipfw add allow tcp from any to any 443` |
| SSE events buffered/delayed | Nginx proxy_buffering on | Verify `proxy_buffering off;` in nginx config |
| "502 Bad Gateway" | Node process not running | `service ri24_mcp status` → restart if needed |
| "No properties found" | XML download failed | Check `.env` credentials + check logs |
| High memory usage | Normal — XML in memory | ~300-500 MB is expected for the full dataset |
| Service won't start | Wrong Node.js path | Check `which node` and update `node_cmd` in rc script |

---

## Directory Structure (after install)

```
/opt/ri24-mcp/
├── server/
│   ├── dist/
│   │   ├── index.js              # Express + MCP server
│   │   └── db.js                 # XML parser + property search
│   ├── node_modules/             # Created by npm install
│   ├── package.json
│   ├── .env                      # Credentials
│   └── export.full.xml           # Downloaded at startup (~189 MB)
├── web/
│   └── dist/
│       └── assets/
│           ├── index.js          # React frontend
│           └── index.css         # Styles
├── nginx-ri24-mcp.conf
└── ri24_mcp.rc
```
