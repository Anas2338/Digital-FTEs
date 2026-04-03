#!/bin/bash
# SSL Configuration Script for Odoo
# Sets up nginx reverse proxy with Let's Encrypt SSL
#
# Usage: sudo bash configure_ssl.sh <domain>
# Based on quickstart.md Phase 3

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: sudo bash configure_ssl.sh <domain>"
    echo "Example: sudo bash configure_ssl.sh odoo.example.com"
    exit 1
fi

DOMAIN=$1

echo "=== Configuring SSL for Odoo ==="
echo "Domain: $DOMAIN"
echo ""

echo "Step 1: Creating nginx configuration..."
cat > /etc/nginx/sites-available/odoo << EOF
upstream odoo {
    server 127.0.0.1:8069;
}

upstream odoochat {
    server 127.0.0.1:8072;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL certificates (will be added by certbot)
    # ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logging
    access_log /var/log/nginx/odoo-access.log;
    error_log /var/log/nginx/odoo-error.log;

    # Proxy settings
    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;
    proxy_set_header X-Forwarded-Host \$host;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header X-Real-IP \$remote_addr;

    # Increase buffer sizes
    proxy_buffers 16 64k;
    proxy_buffer_size 128k;

    # Odoo web interface
    location / {
        proxy_pass http://odoo;
        proxy_redirect off;
    }

    # Odoo longpolling
    location /longpolling {
        proxy_pass http://odoochat;
    }

    # Static files
    location ~* /web/static/ {
        proxy_cache_valid 200 90m;
        proxy_buffering on;
        expires 864000;
        proxy_pass http://odoo;
    }

    # File upload size
    client_max_body_size 100M;
}
EOF

echo "Step 2: Enabling nginx site..."
ln -sf /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/

echo "Step 3: Testing nginx configuration..."
nginx -t

echo "Step 4: Reloading nginx..."
systemctl reload nginx

echo "Step 5: Obtaining SSL certificate with Let's Encrypt..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

echo "Step 6: Setting up automatic certificate renewal..."
systemctl enable certbot.timer
systemctl start certbot.timer

echo ""
echo "=== SSL Configuration Complete ==="
echo ""
echo "Odoo is now accessible at: https://$DOMAIN"
echo ""
echo "SSL certificate will auto-renew via certbot.timer"
echo "Check certificate status: sudo certbot certificates"
echo ""
